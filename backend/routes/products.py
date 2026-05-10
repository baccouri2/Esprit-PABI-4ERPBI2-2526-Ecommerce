"""
Product Management — CRUD for dim_product
Columns: pk_id_product (auto), fk_category, ref_product, name_product
Category shown by name (joined from dim_category)
"""

import warnings
warnings.filterwarnings('ignore')

from flask import Blueprint, jsonify, request
import pyodbc

products_bp = Blueprint('products', __name__)


def _conn():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=HEDIRE\\MSSQLSERVER05;'
        'DATABASE=dw_pi;'
        'Trusted_Connection=yes',
        timeout=15
    )


# ── GET all categories (for dropdown) ────────────────────────────────────────

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute("SELECT pk_id_category, name_category FROM dim_category ORDER BY name_category")
        cats = [{'id': r[0], 'name': r[1]} for r in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'categories': cats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── GET all products ──────────────────────────────────────────────────────────

@products_bp.route('', methods=['GET'])
def get_all():
    search   = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    try:
        conn = _conn()
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if search:
            where_clauses.append("(p.name_product LIKE ? OR p.ref_product LIKE ?)")
            params += [f'%{search}%', f'%{search}%']
        if category:
            where_clauses.append("c.name_category = ?")
            params.append(category)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        cursor.execute(f"""
            SELECT
                p.pk_id_product,
                p.ref_product,
                p.name_product,
                p.fk_category,
                c.name_category,
                COUNT(s.pk_id_sale) AS sale_count
            FROM dim_product p
            LEFT JOIN dim_category c ON p.fk_category = c.pk_id_category
            LEFT JOIN fact_sale s    ON s.fk_product  = p.pk_id_product
            {where_sql}
            GROUP BY p.pk_id_product, p.ref_product, p.name_product, p.fk_category, c.name_category
            ORDER BY p.pk_id_product
        """, *params)

        rows = [
            {
                'id':            r[0],
                'ref_product':   r[1],
                'name_product':  r[2],
                'fk_category':   r[3],
                'name_category': r[4] or 'Uncategorized',
                'sale_count':    r[5]
            }
            for r in cursor.fetchall()
        ]
        conn.close()
        return jsonify({'success': True, 'products': rows, 'total': len(rows)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── GET single product ────────────────────────────────────────────────────────

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_one(product_id):
    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.pk_id_product, p.ref_product, p.name_product,
                   p.fk_category, c.name_category,
                   COUNT(s.pk_id_sale) AS sale_count
            FROM dim_product p
            LEFT JOIN dim_category c ON p.fk_category = c.pk_id_category
            LEFT JOIN fact_sale s    ON s.fk_product  = p.pk_id_product
            WHERE p.pk_id_product = ?
            GROUP BY p.pk_id_product, p.ref_product, p.name_product, p.fk_category, c.name_category
        """, product_id)
        r = cursor.fetchone()
        conn.close()
        if not r:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        return jsonify({'success': True, 'product': {
            'id': r[0], 'ref_product': r[1], 'name_product': r[2],
            'fk_category': r[3], 'name_category': r[4] or 'Uncategorized',
            'sale_count': r[5]
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── CREATE product ────────────────────────────────────────────────────────────

@products_bp.route('', methods=['POST'])
def create():
    """
    Body: { "name_product": "...", "ref_product": "...", "fk_category": 1 }
    """
    body         = request.get_json(force=True) or {}
    name_product = body.get('name_product', '').strip()
    ref_product  = body.get('ref_product', '').strip()
    fk_category  = body.get('fk_category')

    if not name_product:
        return jsonify({'success': False, 'error': 'name_product is required'}), 400
    if not ref_product:
        return jsonify({'success': False, 'error': 'ref_product is required'}), 400
    if not fk_category:
        return jsonify({'success': False, 'error': 'category is required'}), 400

    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dim_product (fk_category, ref_product, name_product) VALUES (?, ?, ?)",
            int(fk_category), ref_product, name_product
        )
        conn.commit()
        cursor.execute("SELECT @@IDENTITY")
        new_id = int(cursor.fetchone()[0])
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Product "{name_product}" created',
            'id': new_id
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── UPDATE product ────────────────────────────────────────────────────────────

@products_bp.route('/<int:product_id>', methods=['PUT'])
def update(product_id):
    body         = request.get_json(force=True) or {}
    name_product = body.get('name_product', '').strip()
    ref_product  = body.get('ref_product', '').strip()
    fk_category  = body.get('fk_category')

    if not name_product:
        return jsonify({'success': False, 'error': 'name_product is required'}), 400
    if not ref_product:
        return jsonify({'success': False, 'error': 'ref_product is required'}), 400
    if not fk_category:
        return jsonify({'success': False, 'error': 'category is required'}), 400

    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE dim_product SET fk_category=?, ref_product=?, name_product=? WHERE pk_id_product=?",
            int(fk_category), ref_product, name_product, product_id
        )
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Product #{product_id} updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── DELETE product ────────────────────────────────────────────────────────────

@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete(product_id):
    try:
        conn = _conn()
        cursor = conn.cursor()

        # Block if product has sales
        cursor.execute("SELECT COUNT(*) FROM fact_sale WHERE fk_product = ?", product_id)
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Cannot delete: product has {count} existing sales'
            }), 409

        cursor.execute("DELETE FROM dim_product WHERE pk_id_product = ?", product_id)
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Product #{product_id} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
