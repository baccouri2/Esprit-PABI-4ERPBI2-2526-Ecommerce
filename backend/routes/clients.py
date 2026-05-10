"""
Client Management — CRUD for B2B and B2C clients
Tables: dim_clientb2b (pk_id_client, MF, company, date_participation)
        dim_clientb2c (pk_id_client, first_name, last_name, date_participation)
Order count from: fact_sale (fk_clientB2B / fk_clientB2C)
"""

import warnings
warnings.filterwarnings('ignore')

from flask import Blueprint, jsonify, request
import pyodbc
from datetime import datetime

clients_bp = Blueprint('clients', __name__)

# ── DB connection ─────────────────────────────────────────────────────────────

def _conn():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=HEDIRE\\MSSQLSERVER05;'
        'DATABASE=dw_pi;'
        'Trusted_Connection=yes',
        timeout=15
    )

# ── helpers ───────────────────────────────────────────────────────────────────

def _fmt_date(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val[:10]
    return str(val)[:10]


# ── GET all clients ───────────────────────────────────────────────────────────

@clients_bp.route('', methods=['GET'])
def get_all_clients():
    """Return all B2B and B2C clients with order count."""
    client_type = request.args.get('type', 'all').lower()  # all | b2b | b2c
    try:
        conn = _conn()
        cursor = conn.cursor()
        results = []

        if client_type in ('all', 'b2b'):
            cursor.execute("""
                SELECT
                    b.pk_id_client,
                    b.MF, 
                    b.company,
                    b.date_participation,
                    COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2b b
                LEFT JOIN fact_sale s ON s.fk_clientB2B = b.pk_id_client
                GROUP BY b.pk_id_client, b.MF, b.company, b.date_participation
                ORDER BY b.pk_id_client
            """)
            for r in cursor.fetchall():
                results.append({
                    'id':                 r[0],
                    'type':               'B2B',
                    'MF':                 r[1],
                    'company':            r[2],
                    'date_participation': _fmt_date(r[3]),
                    'order_count':        r[4]
                })

        if client_type in ('all', 'b2c'):
            cursor.execute("""
                SELECT
                    b.pk_id_client,
                    b.first_name,
                    b.last_name,
                    b.date_participation,
                    COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2c b
                LEFT JOIN fact_sale s ON s.fk_clientB2C = b.pk_id_client
                GROUP BY b.pk_id_client, b.first_name, b.last_name, b.date_participation
                ORDER BY b.pk_id_client
            """)
            for r in cursor.fetchall():
                results.append({
                    'id':                 r[0],
                    'type':               'B2C',
                    'first_name':         r[1],
                    'last_name':          r[2],
                    'full_name':          f"{r[1]} {r[2]}",
                    'date_participation': _fmt_date(r[3]),
                    'order_count':        r[4]
                })

        conn.close()
        return jsonify({'success': True, 'clients': results, 'total': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── GET single client ─────────────────────────────────────────────────────────

@clients_bp.route('/<string:client_type>/<int:client_id>', methods=['GET'])
def get_client(client_type, client_id):
    """Get a single client by type (b2b|b2c) and id."""
    try:
        conn = _conn()
        cursor = conn.cursor()

        if client_type.lower() == 'b2b':
            cursor.execute("""
                SELECT b.pk_id_client, b.MF, b.company, b.date_participation,
                       COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2b b
                LEFT JOIN fact_sale s ON s.fk_clientB2B = b.pk_id_client
                WHERE b.pk_id_client = ?
                GROUP BY b.pk_id_client, b.MF, b.company, b.date_participation
            """, client_id)
            r = cursor.fetchone()
            if not r:
                return jsonify({'success': False, 'error': 'Client not found'}), 404
            client = {
                'id': r[0], 'type': 'B2B', 'MF': r[1],
                'company': r[2], 'date_participation': _fmt_date(r[3]),
                'order_count': r[4]
            }
        else:
            cursor.execute("""
                SELECT b.pk_id_client, b.first_name, b.last_name, b.date_participation,
                       COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2c b
                LEFT JOIN fact_sale s ON s.fk_clientB2C = b.pk_id_client
                WHERE b.pk_id_client = ?
                GROUP BY b.pk_id_client, b.first_name, b.last_name, b.date_participation
            """, client_id)
            r = cursor.fetchone()
            if not r:
                return jsonify({'success': False, 'error': 'Client not found'}), 404
            client = {
                'id': r[0], 'type': 'B2C',
                'first_name': r[1], 'last_name': r[2],
                'full_name': f"{r[1]} {r[2]}",
                'date_participation': _fmt_date(r[3]),
                'order_count': r[4]
            }

        conn.close()
        return jsonify({'success': True, 'client': client})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── CREATE client ─────────────────────────────────────────────────────────────

@clients_bp.route('', methods=['POST'])
def create_client():
    """
    Create a new client.
    B2B body: { "type": "b2b", "MF": "...", "company": "...", "date_participation": "2024-01-01" }
    B2C body: { "type": "b2c", "first_name": "...", "last_name": "...", "date_participation": "2024-01-01" }
    """
    body = request.get_json(force=True) or {}
    client_type = body.get('type', '').lower()
    date_p = body.get('date_participation') or None

    try:
        conn = _conn()
        cursor = conn.cursor()

        if client_type == 'b2b':
            mf      = body.get('MF', '').strip()
            company = body.get('company', '').strip()
            if not company:
                return jsonify({'success': False, 'error': 'company is required'}), 400

            cursor.execute(
                "INSERT INTO dim_clientb2b (MF, company, date_participation) VALUES (?, ?, ?)",
                mf or None, company, date_p
            )
            conn.commit()
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
            conn.close()
            return jsonify({
                'success': True,
                'message': f'B2B client "{company}" created',
                'id': new_id, 'type': 'B2B'
            }), 201

        elif client_type == 'b2c':
            first = body.get('first_name', '').strip()
            last  = body.get('last_name', '').strip()
            if not first or not last:
                return jsonify({'success': False, 'error': 'first_name and last_name are required'}), 400

            cursor.execute(
                "INSERT INTO dim_clientb2c (first_name, last_name, date_participation) VALUES (?, ?, ?)",
                first, last, date_p
            )
            conn.commit()
            cursor.execute("SELECT @@IDENTITY")
            new_id = int(cursor.fetchone()[0])
            conn.close()
            return jsonify({
                'success': True,
                'message': f'B2C client "{first} {last}" created',
                'id': new_id, 'type': 'B2C'
            }), 201

        else:
            return jsonify({'success': False, 'error': 'type must be "b2b" or "b2c"'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── UPDATE client ─────────────────────────────────────────────────────────────

@clients_bp.route('/<string:client_type>/<int:client_id>', methods=['PUT'])
def update_client(client_type, client_id):
    """Update an existing client."""
    body   = request.get_json(force=True) or {}
    date_p = body.get('date_participation') or None

    try:
        conn = _conn()
        cursor = conn.cursor()

        if client_type.lower() == 'b2b':
            mf      = body.get('MF', '').strip() or None
            company = body.get('company', '').strip()
            if not company:
                return jsonify({'success': False, 'error': 'company is required'}), 400
            cursor.execute(
                "UPDATE dim_clientb2b SET MF=?, company=?, date_participation=? WHERE pk_id_client=?",
                mf, company, date_p, client_id
            )
        else:
            first = body.get('first_name', '').strip()
            last  = body.get('last_name', '').strip()
            if not first or not last:
                return jsonify({'success': False, 'error': 'first_name and last_name are required'}), 400
            cursor.execute(
                "UPDATE dim_clientb2c SET first_name=?, last_name=?, date_participation=? WHERE pk_id_client=?",
                first, last, date_p, client_id
            )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Client not found'}), 404

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Client #{client_id} updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── DELETE client ─────────────────────────────────────────────────────────────

@clients_bp.route('/<string:client_type>/<int:client_id>', methods=['DELETE'])
def delete_client(client_type, client_id):
    """Delete a client. Blocked if client has existing orders."""
    try:
        conn = _conn()
        cursor = conn.cursor()

        # Check for existing orders
        if client_type.lower() == 'b2b':
            cursor.execute(
                "SELECT COUNT(*) FROM fact_sale WHERE fk_clientB2B = ?", client_id
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM fact_sale WHERE fk_clientB2C = ?", client_id
            )

        order_count = cursor.fetchone()[0]
        if order_count > 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Cannot delete: client has {order_count} existing orders'
            }), 409

        # Safe to delete
        table = 'dim_clientb2b' if client_type.lower() == 'b2b' else 'dim_clientb2c'
        cursor.execute(f"DELETE FROM {table} WHERE pk_id_client = ?", client_id)

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Client not found'}), 404

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Client #{client_id} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── SEARCH clients ────────────────────────────────────────────────────────────

@clients_bp.route('/search', methods=['GET'])
def search_clients():
    """Search clients by name/company. ?q=term&type=all|b2b|b2c"""
    q           = request.args.get('q', '').strip()
    client_type = request.args.get('type', 'all').lower()

    if not q:
        return jsonify({'success': False, 'error': 'Search term required'}), 400

    try:
        conn = _conn()
        cursor = conn.cursor()
        results = []

        if client_type in ('all', 'b2b'):
            cursor.execute("""
                SELECT b.pk_id_client, b.MF, b.company, b.date_participation,
                       COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2b b
                LEFT JOIN fact_sale s ON s.fk_clientB2B = b.pk_id_client
                WHERE b.company LIKE ? OR b.MF LIKE ?
                GROUP BY b.pk_id_client, b.MF, b.company, b.date_participation
                ORDER BY b.company
            """, f'%{q}%', f'%{q}%')
            for r in cursor.fetchall():
                results.append({
                    'id': r[0], 'type': 'B2B', 'MF': r[1],
                    'company': r[2], 'date_participation': _fmt_date(r[3]),
                    'order_count': r[4]
                })

        if client_type in ('all', 'b2c'):
            cursor.execute("""
                SELECT b.pk_id_client, b.first_name, b.last_name, b.date_participation,
                       COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2c b
                LEFT JOIN fact_sale s ON s.fk_clientB2C = b.pk_id_client
                WHERE b.first_name LIKE ? OR b.last_name LIKE ?
                   OR CONCAT(b.first_name, ' ', b.last_name) LIKE ?
                GROUP BY b.pk_id_client, b.first_name, b.last_name, b.date_participation
                ORDER BY b.first_name
            """, f'%{q}%', f'%{q}%', f'%{q}%')
            for r in cursor.fetchall():
                results.append({
                    'id': r[0], 'type': 'B2C',
                    'first_name': r[1], 'last_name': r[2],
                    'full_name': f"{r[1]} {r[2]}",
                    'date_participation': _fmt_date(r[3]),
                    'order_count': r[4]
                })

        conn.close()
        return jsonify({'success': True, 'clients': results, 'total': len(results)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
