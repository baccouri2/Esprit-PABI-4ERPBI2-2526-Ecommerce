"""
ETL Script to import sales data from sales.sql into the data warehouse.

This script:
1. Reads sales data from sales.sql
2. Creates/updates orders in dim_order
3. Creates/updates products in dim_product
4. Creates sales records in fact_sale
5. Links everything with proper foreign keys
"""

import pyodbc
import re
from datetime import datetime
from decimal import Decimal

# Database connection
def get_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=HEDIRE\\MSSQLSERVER05;'
        'DATABASE=dw_pi;'
        'Trusted_Connection=yes',
        timeout=15
    )

def parse_sales_sql(file_path):
    """Parse the sales.sql file and extract INSERT statements"""
    print("Reading sales.sql file...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all INSERT INTO sales VALUES statements
    pattern = r"INSERT INTO `sales`.*?VALUES\s*(.*?);"
    matches = re.findall(pattern, content, re.DOTALL)
    
    if not matches:
        print("ERROR: No INSERT statements found in sales.sql")
        return []
    
    # Parse the VALUES part
    all_sales = []
    for match in matches:
        # Split by "),(" to get individual rows
        rows = re.findall(r"\((.*?)\)(?:,|\s*$)", match, re.DOTALL)
        
        for row in rows:
            # Parse the values
            values = []
            current_value = ""
            in_quotes = False
            
            for char in row:
                if char == "'" and (not current_value or current_value[-1] != '\\'):
                    in_quotes = not in_quotes
                    current_value += char
                elif char == ',' and not in_quotes:
                    values.append(current_value.strip().strip("'"))
                    current_value = ""
                else:
                    current_value += char
            
            # Add the last value
            if current_value:
                values.append(current_value.strip().strip("'"))
            
            if len(values) >= 32:  # Ensure we have all columns
                all_sales.append({
                    'order_number': values[0],
                    'order_status': values[1],
                    'order_date': values[2],
                    'customer_note': values[3],
                    'billing_first_name': values[4],
                    'billing_last_name': values[5],
                    'billing_address': values[6],
                    'billing_city': values[7],
                    'billing_state': values[8],
                    'billing_postal': values[9],
                    'billing_country': values[10],
                    'shipping_first_name': values[11],
                    'shipping_last_name': values[12],
                    'shipping_address': values[13],
                    'shipping_city': values[14],
                    'shipping_state': values[15],
                    'shipping_postal': values[16],
                    'shipping_country': values[17],
                    'payment_method': values[18],
                    'cart_discount': values[19],
                    'cart_discount_tax': values[20],
                    'order_subtotal': values[21],
                    'shipping_method': values[22],
                    'shipping_amount': values[23],
                    'refund_amount': values[24],
                    'order_total': values[25],
                    'tax_total': values[26],
                    'product_sku': values[27],
                    'article_number': values[28],
                    'product_name': values[29],
                    'quantity': values[30],
                    'product_price': values[31],
                    'channel': values[32] if len(values) > 32 else 'popup store'
                })
    
    print(f"SUCCESS: Found {len(all_sales)} sales records")
    return all_sales

def get_or_create_order(cursor, order_number, order_status, order_date, shipping_method, shipping_amount):
    """Get existing order or create new one"""
    
    # Check if order exists
    cursor.execute("SELECT pk_id_order FROM dim_order WHERE id_order = ?", order_number)
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Parse date
    try:
        date_obj = datetime.strptime(order_date, '%d-%m-%Y %H:%M:%S')
        date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    except:
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get or create delivery
    delivery_cost = float(shipping_amount) if shipping_amount and shipping_amount != '0.00' else 0
    
    cursor.execute("""
        SELECT pk_id_delivery FROM dim_delivery 
        WHERE company = ? AND costs = ?
    """, shipping_method or 'Standard', delivery_cost)
    
    delivery_row = cursor.fetchone()
    
    if delivery_row:
        fk_delivery = delivery_row[0]
    else:
        # Create delivery
        cursor.execute("""
            INSERT INTO dim_delivery (num_bl, company, costs)
            VALUES (?, ?, ?)
        """, date_str, shipping_method or 'Standard', delivery_cost)
        cursor.execute("SELECT @@IDENTITY")
        fk_delivery = int(cursor.fetchone()[0])
    
    # Map status
    status_map = {
        'En cours': 'En cours',
        'Terminée': 'Terminée',
        'En attente': 'En attente',
        'Confirmée': 'Confirmée',
        'En préparation': 'En préparation',
        'Expédiée': 'Expédiée',
        'Livrée': 'Livrée',
        'Annulée': 'Annulée'
    }
    
    mapped_status = status_map.get(order_status, 'En attente')
    
    # Create order
    cursor.execute("""
        INSERT INTO dim_order (id_order, order_status, date_commande, fk_delivery)
        VALUES (?, ?, ?, ?)
    """, order_number, mapped_status, date_str, fk_delivery)
    
    cursor.execute("SELECT @@IDENTITY")
    return int(cursor.fetchone()[0])

def get_or_create_product(cursor, sku, product_name):
    """Get existing product or create new one"""
    
    if not sku or sku == 'NULL':
        sku = f"PROD-{hash(product_name) % 10000}"
    
    # Check if product exists by SKU
    cursor.execute("SELECT pk_id_product FROM dim_product WHERE ref_product = ?", sku)
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Create product
    cursor.execute("""
        INSERT INTO dim_product (ref_product, name_product, fk_category, fk_supplier, fk_material)
        VALUES (?, ?, 1, 1, 1)
    """, sku, product_name or 'Unknown Product')
    
    cursor.execute("SELECT @@IDENTITY")
    return int(cursor.fetchone()[0])

def get_or_create_date(cursor, date_str):
    """Get or create date dimension"""
    
    try:
        date_obj = datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S')
    except:
        date_obj = datetime.now()
    
    full_date = date_obj.strftime('%Y-%m-%d')
    
    cursor.execute("SELECT pk_id_date FROM dim_date WHERE full_date = ?", full_date)
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Create date
    cursor.execute("""
        INSERT INTO dim_date (full_date, day, month, trimester, semester, year)
        VALUES (?, ?, ?, ?, ?, ?)
    """, full_date, date_obj.day, date_obj.month, 
        (date_obj.month - 1) // 3 + 1,  # trimester
        (date_obj.month - 1) // 6 + 1,  # semester
        date_obj.year)
    
    cursor.execute("SELECT @@IDENTITY")
    return int(cursor.fetchone()[0])

def create_sale(cursor, sale_data, fk_order, fk_product, fk_date):
    """Create a sale record in fact_sale"""
    
    quantity = float(sale_data['quantity']) if sale_data['quantity'] else 1
    unit_price = float(sale_data['product_price']) if sale_data['product_price'] else 0
    
    # Calculate total (quantity * unit_price)
    total_price = quantity * unit_price
    
    # Check if sale already exists
    cursor.execute("""
        SELECT pk_id_sale FROM fact_sale 
        WHERE fk_order = ? AND fk_product = ? AND unit_price = ?
    """, fk_order, fk_product, unit_price)
    
    if cursor.fetchone():
        return  # Sale already exists
    
    # Create sale
    cursor.execute("""
        INSERT INTO fact_sale (
            fk_date, fk_place, fk_product, fk_claim, fk_order,
            fk_clientB2B, fk_clientB2C, fk_channel, fk_invoice,
            quantity, ugs, tax_status, unit_price, discount, total_price
        ) VALUES (?, 1, ?, NULL, ?, NULL, NULL, 1, 1, ?, ?, 'taxable', ?, 0, ?)
    """, fk_date, fk_product, fk_order, quantity, 
        sale_data['product_sku'] or '', unit_price, total_price)

def main():
    print("=" * 60)
    print("ETL: Import Sales from sales.sql")
    print("=" * 60)
    print()
    
    # Parse sales.sql
    sales_data = parse_sales_sql('../sales.sql')
    
    if not sales_data:
        print("ERROR: No sales data to import")
        return
    
    # Connect to database
    print("\nConnecting to database...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Statistics
    orders_created = 0
    products_created = 0
    sales_created = 0
    errors = 0
    
    # Group sales by order
    orders_dict = {}
    for sale in sales_data:
        order_num = sale['order_number']
        if order_num not in orders_dict:
            orders_dict[order_num] = []
        orders_dict[order_num].append(sale)
    
    print(f"\nProcessing {len(orders_dict)} unique orders...")
    print()
    
    # Process each order
    for order_num, order_sales in orders_dict.items():
        try:
            # Get first sale for order info
            first_sale = order_sales[0]
            
            # Create/get order
            fk_order = get_or_create_order(
                cursor,
                order_num,
                first_sale['order_status'],
                first_sale['order_date'],
                first_sale['shipping_method'],
                first_sale['shipping_amount']
            )
            
            if cursor.rowcount > 0:
                orders_created += 1
            
            # Get date
            fk_date = get_or_create_date(cursor, first_sale['order_date'])
            
            # Process each sale item
            for sale in order_sales:
                # Create/get product
                fk_product = get_or_create_product(
                    cursor,
                    sale['product_sku'],
                    sale['product_name']
                )
                
                if cursor.rowcount > 0:
                    products_created += 1
                
                # Create sale
                create_sale(cursor, sale, fk_order, fk_product, fk_date)
                
                if cursor.rowcount > 0:
                    sales_created += 1
            
            # Commit after each order
            conn.commit()
            
            if (orders_created + errors) % 10 == 0:
                print(f"   Processed {orders_created + errors} orders...")
        
        except Exception as e:
            errors += 1
            print(f"   WARNING: Error processing order {order_num}: {e}")
            conn.rollback()
    
    print()
    print("=" * 60)
    print("ETL COMPLETE")
    print("=" * 60)
    print(f"SUCCESS: Orders created/updated: {orders_created}")
    print(f"SUCCESS: Products created: {products_created}")
    print(f"SUCCESS: Sales created: {sales_created}")
    print(f"ERRORS: {errors}")
    print()
    
    # Verify results
    print("Verification:")
    cursor.execute("SELECT COUNT(*) FROM dim_order")
    print(f"   Total orders in database: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM dim_product")
    print(f"   Total products in database: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM fact_sale")
    print(f"   Total sales in database: {cursor.fetchone()[0]}")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT o.pk_id_order)
        FROM dim_order o
        INNER JOIN fact_sale s ON s.fk_order = o.pk_id_order
    """)
    print(f"   Orders with sales: {cursor.fetchone()[0]}")
    
    conn.close()
    
    print()
    print("SUCCESS: ETL process completed successfully!")
    print()
    print("Next steps:")
    print("1. Restart the backend server")
    print("2. Refresh the frontend")
    print("3. Check the orders page - all orders should now have items and totals")

if __name__ == '__main__':
    main()
