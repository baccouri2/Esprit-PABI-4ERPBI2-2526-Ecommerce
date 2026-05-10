"""
Supplier Management — CRUD for dim_supplier
Columns: Pk_id_supplier (auto), name_supplier, company, Payment_Method
"""

import warnings
warnings.filterwarnings('ignore')

from flask import Blueprint, jsonify, request
import pyodbc

suppliers_bp = Blueprint('suppliers', __name__)

PAYMENT_METHODS = ['Espèces', 'Virement', 'Chèque', 'Carte bancaire', 'Traite']

def _conn():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=HEDIRE\\MSSQLSERVER05;'
        'DATABASE=dw_pi;'
        'Trusted_Connection=yes',
        timeout=15
    )


@suppliers_bp.route('', methods=['GET'])
def get_all():
    """Return all suppliers with purchase count from fact_purchace."""
    search = request.args.get('q', '').strip()
    try:
        conn = _conn()
        cursor = conn.cursor()

        if search:
            cursor.execute("""
                SELECT s.Pk_id_supplier, s.name_supplier, s.company, s.Payment_Method,
                       COUNT(p.pk_id_purchase) AS purchase_count
                FROM dim_supplier s
                LEFT JOIN fact_purchace p ON p.fk_supplier = s.Pk_id_supplier
                WHERE s.name_supplier LIKE ? OR s.company LIKE ? OR s.Payment_Method LIKE ?
                GROUP BY s.Pk_id_supplier, s.name_supplier, s.company, s.Payment_Method
                ORDER BY s.Pk_id_supplier
            """, f'%{search}%', f'%{search}%', f'%{search}%')
        else:
            cursor.execute("""
                SELECT s.Pk_id_supplier, s.name_supplier, s.company, s.Payment_Method,
                       COUNT(p.pk_id_purchase) AS purchase_count
                FROM dim_supplier s
                LEFT JOIN fact_purchace p ON p.fk_supplier = s.Pk_id_supplier
                GROUP BY s.Pk_id_supplier, s.name_supplier, s.company, s.Payment_Method
                ORDER BY s.Pk_id_supplier
            """)

        rows = [
            {
                'id':             r[0],
                'name_supplier':  r[1],
                'company':        r[2],
                'payment_method': r[3],
                'purchase_count': r[4]
            }
            for r in cursor.fetchall()
        ]
        conn.close()
        return jsonify({'success': True, 'suppliers': rows, 'total': len(rows)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
def get_one(supplier_id):
    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.Pk_id_supplier, s.name_supplier, s.company, s.Payment_Method,
                   COUNT(p.pk_id_purchase) AS purchase_count
            FROM dim_supplier s
            LEFT JOIN fact_purchace p ON p.fk_supplier = s.Pk_id_supplier
            WHERE s.Pk_id_supplier = ?
            GROUP BY s.Pk_id_supplier, s.name_supplier, s.company, s.Payment_Method
        """, supplier_id)
        r = cursor.fetchone()
        conn.close()
        if not r:
            return jsonify({'success': False, 'error': 'Supplier not found'}), 404
        return jsonify({'success': True, 'supplier': {
            'id': r[0], 'name_supplier': r[1],
            'company': r[2], 'payment_method': r[3], 'purchase_count': r[4]
        }})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@suppliers_bp.route('', methods=['POST'])
def create():
    """
    Body: { "name_supplier": "...", "company": "...", "payment_method": "Espèces" }
    """
    body           = request.get_json(force=True) or {}
    name_supplier  = body.get('name_supplier', '').strip()
    company        = body.get('company', '').strip()
    payment_method = body.get('payment_method', '').strip()

    if not name_supplier:
        return jsonify({'success': False, 'error': 'name_supplier is required'}), 400
    if not company:
        return jsonify({'success': False, 'error': 'company is required'}), 400
    if not payment_method:
        return jsonify({'success': False, 'error': 'payment_method is required'}), 400

    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dim_supplier (name_supplier, company, Payment_Method) VALUES (?, ?, ?)",
            name_supplier, company, payment_method
        )
        conn.commit()
        cursor.execute("SELECT @@IDENTITY")
        new_id = int(cursor.fetchone()[0])
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Supplier "{name_supplier}" created',
            'id': new_id
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update(supplier_id):
    body           = request.get_json(force=True) or {}
    name_supplier  = body.get('name_supplier', '').strip()
    company        = body.get('company', '').strip()
    payment_method = body.get('payment_method', '').strip()

    if not name_supplier:
        return jsonify({'success': False, 'error': 'name_supplier is required'}), 400
    if not company:
        return jsonify({'success': False, 'error': 'company is required'}), 400
    if not payment_method:
        return jsonify({'success': False, 'error': 'payment_method is required'}), 400

    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE dim_supplier SET name_supplier=?, company=?, Payment_Method=? WHERE Pk_id_supplier=?",
            name_supplier, company, payment_method, supplier_id
        )
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Supplier not found'}), 404
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Supplier #{supplier_id} updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete(supplier_id):
    try:
        conn = _conn()
        cursor = conn.cursor()

        # Block delete if supplier has purchases
        cursor.execute(
            "SELECT COUNT(*) FROM fact_purchace WHERE fk_supplier = ?", supplier_id
        )
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Cannot delete: supplier has {count} existing purchases'
            }), 409

        cursor.execute("DELETE FROM dim_supplier WHERE Pk_id_supplier = ?", supplier_id)
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Supplier not found'}), 404
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Supplier #{supplier_id} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@suppliers_bp.route('/payment-methods', methods=['GET'])
def payment_methods():
    return jsonify({'success': True, 'methods': PAYMENT_METHODS})
