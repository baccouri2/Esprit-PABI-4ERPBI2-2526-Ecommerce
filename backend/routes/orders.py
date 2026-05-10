"""
Order Management — CRUD for dim_order with invoice generation
Columns: pk_id_order (auto), fk_delivery, id_order, order_status, date_commande

NOTE: The correct join is fact_sale.fk_order = dim_order.pk_id_order
However, current data shows orphaned records - fact_sale references old order IDs that don't exist in dim_order.
This is a data warehouse integrity issue that needs ETL fix.
"""

import warnings
warnings.filterwarnings('ignore')

from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import pyodbc
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

orders_bp = Blueprint('orders', __name__)

ORDER_STATUSES = ['En attente', 'Confirmée', 'En préparation', 'Expédiée', 'Livrée', 'Annulée']

def _conn():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=HEDIRE\\MSSQLSERVER05;'
        'DATABASE=dw_pi;'
        'Trusted_Connection=yes',
        timeout=15
    )


@orders_bp.route('', methods=['GET'])
def get_all():
    """Return all orders with delivery and client info."""
    search = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    
    try:
        conn = _conn()
        cursor = conn.cursor()

        query = """
            SELECT 
                o.pk_id_order,
                o.id_order,
                o.order_status,
                o.date_commande,
                o.fk_delivery,
                d.num_bl,
                d.company AS delivery_company,
                d.costs AS delivery_cost,
                COUNT(DISTINCT s.pk_id_sale) AS item_count,
                SUM(s.total_price) AS total_amount
            FROM dim_order o
            LEFT JOIN dim_delivery d ON o.fk_delivery = d.pk_id_delivery
            LEFT JOIN fact_sale s ON s.fk_order = o.pk_id_order
        """
        
        conditions = []
        params = []
        
        if search:
            conditions.append("(o.id_order LIKE ? OR d.num_bl LIKE ? OR d.company LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if status:
            conditions.append("o.order_status = ?")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += """
            GROUP BY o.pk_id_order, o.id_order, o.order_status, o.date_commande, 
                     o.fk_delivery, d.num_bl, d.company, d.costs
            ORDER BY o.date_commande DESC, o.pk_id_order DESC
        """
        
        cursor.execute(query, *params)
        
        rows = [
            {
                'id': r[0],
                'id_order': r[1],
                'order_status': r[2],
                'date_commande': r[3].strftime('%Y-%m-%d') if r[3] and hasattr(r[3], 'strftime') else (str(r[3]) if r[3] else None),
                'fk_delivery': r[4],
                'delivery_num_bl': r[5],
                'delivery_company': r[6],
                'delivery_cost': float(r[7]) if r[7] else 0,
                'item_count': r[8] or 0,
                'total_amount': float(r[9]) if r[9] else 0
            }
            for r in cursor.fetchall()
        ]
        conn.close()
        return jsonify({'success': True, 'orders': rows, 'total': len(rows)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@orders_bp.route('/<int:order_id>', methods=['GET'])
def get_one(order_id):
    """Get order details with items."""
    try:
        conn = _conn()
        cursor = conn.cursor()
        
        # Get order info
        cursor.execute("""
            SELECT 
                o.pk_id_order, o.id_order, o.order_status, o.date_commande, o.fk_delivery,
                d.num_bl, d.company, d.costs,
                COALESCE(b2b.company, b2c.first_name + ' ' + b2c.last_name) AS client_name,
                COALESCE(b2b.MF, '') AS client_mf,
                '' AS client_address,
                '' AS client_phone
            FROM dim_order o
            LEFT JOIN dim_delivery d ON o.fk_delivery = d.pk_id_delivery
            LEFT JOIN fact_sale s ON s.fk_order = o.pk_id_order
            LEFT JOIN dim_clientb2b b2b ON s.fk_clientB2B = b2b.pk_id_client
            LEFT JOIN dim_clientb2c b2c ON s.fk_clientB2C = b2c.pk_id_client
            WHERE o.pk_id_order = ?
            GROUP BY o.pk_id_order, o.id_order, o.order_status, o.date_commande, o.fk_delivery,
                     d.num_bl, d.company, d.costs,
                     b2b.company, b2c.first_name, b2c.last_name, b2b.MF
        """, order_id)
        
        order_row = cursor.fetchone()
        if not order_row:
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get order items
        cursor.execute("""
            SELECT 
                s.pk_id_sale,
                p.ref_product,
                p.name_product,
                s.unit_price,
                s.quantity,
                s.discount,
                s.total_price
            FROM fact_sale s
            INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
            INNER JOIN dim_order o ON s.fk_order = o.pk_id_order
            WHERE o.pk_id_order = ?
        """, order_id)
        
        items = [
            {
                'id': r[0],
                'reference': r[1],
                'description': r[2],
                'unit_price': float(r[3]) if r[3] else 0,
                'quantity': float(r[4]) if r[4] else 0,
                'discount': float(r[5]) if r[5] else 0,
                'total_price': float(r[6]) if r[6] else 0
            }
            for r in cursor.fetchall()
        ]
        
        conn.close()
        
        order = {
            'id': order_row[0],
            'id_order': order_row[1],
            'order_status': order_row[2],
            'date_commande': order_row[3].strftime('%Y-%m-%d') if order_row[3] and hasattr(order_row[3], 'strftime') else (str(order_row[3]) if order_row[3] else None),
            'fk_delivery': order_row[4],
            'delivery_num_bl': order_row[5],
            'delivery_company': order_row[6],
            'delivery_cost': float(order_row[7]) if order_row[7] else 0,
            'client_name': order_row[8],
            'client_mf': order_row[9],
            'client_address': order_row[10],
            'client_phone': order_row[11],
            'items': items
        }
        
        return jsonify({'success': True, 'order': order})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@orders_bp.route('', methods=['POST'])
def create():
    """
    Create new order
    Body: {
        "id_order": "FAC25-07",
        "order_status": "En attente",
        "date_commande": "2025-02-10",
        "fk_delivery": 1
    }
    """
    body = request.get_json(force=True) or {}
    id_order = body.get('id_order', '').strip()
    order_status = body.get('order_status', 'En attente').strip()
    date_commande = body.get('date_commande', datetime.now().strftime('%Y-%m-%d'))
    fk_delivery = body.get('fk_delivery')

    if not id_order:
        return jsonify({'success': False, 'error': 'id_order is required'}), 400
    
    if order_status not in ORDER_STATUSES:
        return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {ORDER_STATUSES}'}), 400

    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dim_order (id_order, order_status, date_commande, fk_delivery) VALUES (?, ?, ?, ?)",
            id_order, order_status, date_commande, fk_delivery
        )
        conn.commit()
        cursor.execute("SELECT @@IDENTITY")
        new_id = int(cursor.fetchone()[0])
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Order "{id_order}" created',
            'id': new_id
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@orders_bp.route('/<int:order_id>', methods=['PUT'])
def update(order_id):
    """Update order"""
    body = request.get_json(force=True) or {}
    id_order = body.get('id_order', '').strip()
    order_status = body.get('order_status', '').strip()
    date_commande = body.get('date_commande')
    fk_delivery = body.get('fk_delivery')

    if not id_order:
        return jsonify({'success': False, 'error': 'id_order is required'}), 400
    
    if order_status and order_status not in ORDER_STATUSES:
        return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {ORDER_STATUSES}'}), 400

    try:
        conn = _conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE dim_order SET id_order=?, order_status=?, date_commande=?, fk_delivery=? WHERE pk_id_order=?",
            id_order, order_status, date_commande, fk_delivery, order_id
        )
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Order #{order_id} updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@orders_bp.route('/<int:order_id>', methods=['DELETE'])
def delete(order_id):
    """Delete order (only if no sales attached)"""
    try:
        conn = _conn()
        cursor = conn.cursor()

        # Check if order has sales
        cursor.execute("SELECT COUNT(*) FROM fact_sale WHERE fk_order = ?", order_id)
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Cannot delete: order has {count} sales attached'
            }), 409

        cursor.execute("DELETE FROM dim_order WHERE pk_id_order = ?", order_id)
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Order #{order_id} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@orders_bp.route('/statuses', methods=['GET'])
def get_statuses():
    """Get available order statuses"""
    return jsonify({'success': True, 'statuses': ORDER_STATUSES})


@orders_bp.route('/<int:order_id>/invoice', methods=['GET'])
def generate_invoice(order_id):
    """Generate PDF invoice for order"""
    try:
        conn = _conn()
        cursor = conn.cursor()
        
        # Get order details (same query as get_one)
        cursor.execute("""
            SELECT 
                o.pk_id_order, o.id_order, o.order_status, o.date_commande, o.fk_delivery,
                d.num_bl, d.company, d.costs,
                COALESCE(b2b.company, b2c.first_name + ' ' + b2c.last_name) AS client_name,
                COALESCE(b2b.MF, '') AS client_mf,
                '' AS client_address,
                '' AS client_phone
            FROM dim_order o
            LEFT JOIN dim_delivery d ON o.fk_delivery = d.pk_id_delivery
            LEFT JOIN fact_sale s ON s.fk_order = o.pk_id_order
            LEFT JOIN dim_clientb2b b2b ON s.fk_clientB2B = b2b.pk_id_client
            LEFT JOIN dim_clientb2c b2c ON s.fk_clientB2C = b2c.pk_id_client
            WHERE o.pk_id_order = ?
            GROUP BY o.pk_id_order, o.id_order, o.order_status, o.date_commande, o.fk_delivery,
                     d.num_bl, d.company, d.costs,
                     b2b.company, b2c.first_name, b2c.last_name, b2b.MF
        """, order_id)
        
        order_row = cursor.fetchone()
        if not order_row:
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get order items
        cursor.execute("""
            SELECT 
                p.ref_product,
                p.name_product,
                s.unit_price,
                s.quantity,
                s.total_price
            FROM fact_sale s
            INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
            INNER JOIN dim_order o ON s.fk_order = o.pk_id_order
            WHERE o.pk_id_order = ?
        """, order_id)
        
        items = cursor.fetchall()
        conn.close()
        
        # Generate PDF
        buffer = io.BytesIO()
        pdf = _generate_invoice_pdf(buffer, order_row, items)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Facture_{order_row[1]}.pdf'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _generate_invoice_pdf(buffer, order_row, items):
    """Generate invoice PDF matching the screenshot"""
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1e3a5f'), alignment=TA_RIGHT)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=10, textColor=colors.white, alignment=TA_LEFT)
    
    # Header with logo and title
    header_data = [
        [Paragraph('<b>SOUGUI ESHOP</b>', styles['Heading2']), Paragraph('<b>Facture</b>', title_style)]
    ]
    header_table = Table(header_data, colWidths=[10*cm, 9*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Invoice details
    date_str = order_row[3].strftime('%d/%m/%Y') if order_row[3] and hasattr(order_row[3], 'strftime') else (str(order_row[3]) if order_row[3] else '')
    invoice_details = [
        ['Date:', date_str],
        ['Facture #:', order_row[1]],
        ['Client ID:', '']
    ]
    details_table = Table(invoice_details, colWidths=[3*cm, 6*cm])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    # Position details table on the right
    details_wrapper = Table([[details_table]], colWidths=[19*cm])
    details_wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'RIGHT')]))
    story.append(details_wrapper)
    story.append(Spacer(1, 0.5*cm))
    
    # Expediteur and Client sections
    info_data = [
        [
            Paragraph('<b>Expéditeur :</b>', header_style),
            Paragraph('<b>A envoyer à :</b>', header_style)
        ],
        [
            f"Nom: SOUGUI E SHOP\nMF: 1797689/E\nAdresse: 18 Rue Mokhtar Attia Megrine, Ben Arous, 2033\nTéléphone: +216 55 466 087",
            f"Nom: {order_row[8] or ''}\nMatricule Fiscal: {order_row[9] or ''}\nAdresse: {order_row[10] or ''}\nTéléphone: {order_row[11] or ''}"
        ]
    ]
    
    info_table = Table(info_data, colWidths=[9.5*cm, 9.5*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Items table
    items_data = [['Référence', 'Description', 'PU HT', 'Quantité', 'Prix Total HT']]
    subtotal = 0
    
    for item in items:
        items_data.append([
            item[0] or '',  # reference
            item[1] or '',  # description
            f"{float(item[2]):.2f}" if item[2] else '0.00',  # unit_price
            f"{float(item[3]):.2f}" if item[3] else '0.00',  # quantity
            f"{float(item[4]):.2f} TND" if item[4] else '0.00 TND'  # total
        ])
        subtotal += float(item[4]) if item[4] else 0
    
    # Add empty rows to match screenshot
    for _ in range(max(0, 8 - len(items))):
        items_data.append(['', '', '', '', ''])
    
    items_table = Table(items_data, colWidths=[2.5*cm, 7*cm, 3*cm, 3*cm, 3.5*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Payment conditions and totals
    tva_rate = 0.19
    timbre = 1.00
    avance_rate = 0.30
    
    tva_amount = subtotal * tva_rate
    avance = subtotal * avance_rate
    total_ttc = subtotal + tva_amount + timbre
    
    bottom_data = [
        [
            Paragraph('<b>Conditions de paiement :</b>', header_style),
            'Montant Total HT',
            f'{subtotal:.2f} TND'
        ],
        [
            'Les modes de paiement acceptés incluent le chèque et le virement bancaire',
            'TVA',
            '19%'
        ],
        [
            Paragraph('<b>Détails bancaires</b>', styles['Normal']),
            'Timbre',
            f'{timbre:.2f}'
        ],
        [
            'Banque: 00004    Agence: 00144    Compte: 144008283183    Clé: 3',
            f'Avance 30% HT',
            f'{avance:.2f} TND'
        ],
        [
            'Domiciliation: Attijari Bank Tunis',
            Paragraph('<b>Total TTC</b>', styles['Normal']),
            Paragraph(f'<b>{total_ttc:.2f} TND</b>', styles['Normal'])
        ],
        [
            'IBAN: TN5904038144008283183345',
            '',
            ''
        ]
    ]
    
    bottom_table = Table(bottom_data, colWidths=[10*cm, 5*cm, 4*cm])
    bottom_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (1, 0), (2, 0), colors.lightgrey),
        ('BACKGROUND', (1, 4), (2, 4), colors.lightgrey),
        ('FONTNAME', (1, 4), (2, 4), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOX', (0, 0), (0, -1), 1, colors.HexColor('#1e3a5f')),
        ('BOX', (1, 0), (2, -1), 1, colors.grey),
        ('GRID', (1, 0), (2, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(bottom_table)
    story.append(Spacer(1, 1*cm))
    
    # Footer
    footer_text = """
    <para align=center fontSize=9>
    <b>Thank you for your business!</b><br/>
    18 Rue Mokhtar Attia , Megrine, Ben Arous, 2033<br/>
    Tel: +216 55 466 087  Fax: -  E-mail: contact@sougui.tn Web: www.sougui.tn
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(story)
    return buffer
