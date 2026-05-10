"""
ETL Script to import sales data from etl (3).sql into fact_sale.
Only imports sales that don't already exist in the database.

This script:
1. Reads sales data from the `sales` table in etl (3).sql
2. Matches orders by order number (Numero_de_commande)
3. Matches products by SKU or creates new products
4. Creates sales records in fact_sale (only if they don't exist)
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

def parse_etl_sales(file_path):
    """Parse the etl (3).sql file and extract sales INSERT statements"""
    print("Reading etl (3).sql file...")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find all INSERT INTO `sales` VALUES statements
    pattern = r"INSERT INTO `sales`[^;]*?VALUES\s*(.*?);"
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if not matches:
        print("ERROR: No INSERT statements found for sales table")
        return []
    
    print(f"Found {len(matches)} INSERT statements")
    
    # Parse the VALUES part
    all_sales = []
    for match_idx, match in enumerate(matches):
        # Split by "),(" to get individual rows
        # Handle both ),( and ), ( patterns
        rows_text = match.strip()
        
        # Find all complete row patterns
        row_pattern = r"\(([^)]+(?:\([^)]*\)[^)]*)*)\)(?:,|\s*$)"
        rows = re.findall(row_pattern, rows_text, re.DOTALL)
        
        for row in rows:
            try:
                # Parse the values - handle quoted strings with commas inside
                values = []
                current_value = ""
                in_quotes = False
                escape_next = False
                
                for char in row:
                    if escape_next:
                        current_value += char
                        escape_next = False
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        current_value += char
                        continue
                    
                    if char == "'" and not escape_next:
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
                
                # Ensure we have at least the minimum required columns
                if len(values) >= 32:
                    all_sales.append({
                        'order_number': values[0] if values[0] else None,
                        'order_status': values[1] if values[1] else 'En attente',
                        'order_date': values[2] if values[2] else None,
                        'customer_note': values[3] if len(values) > 3 else '',
                        'billing_first_name': values[4] if len(values) > 4 else '',
                        'billing_last_name': values[5] if len(values) > 5 else '',
                        'shipping_method': values[22] if len(values) > 22 else 'Standard',
                        'shipping_amount': values[23] if len(values) > 23 else '0.00',
                        'product_sku': values[27] if len(values) > 27 else '',
                        'article_number': values[28] if len(values) > 28 else '',
                        'product_name': values[29] if len(values) > 29 else 'Unknown Product',
                        'quantity': values[30] if len(values) > 30 else '1',
                        'product_price': values[31] if len(values) > 31 else '0.00',
                        'channel': values[32] if len(values) > 32 else 'popup store'
                    })
            except Exception as e:
                print(f"   Warning: Error parsing row in match {match_idx}: {e}")
                continue
    
    print(f"SUCCESS: Parsed {len(all_sales)} sales records")
    return all_sales

def get_order_by_number(cursor, order_number):
    """Get order pk_id_order by order number (id_order)"""
    if not order_number:
        return None
    
    cursor.execute("SELECT pk_id_order FROM dim_order WHERE id_order = ?", order_number)
    row = cursor.fetchone()
    return row[0] if row else None

def get_or_create_product(cursor, sku, product_name):
    """Get existing product or create new one"""
    
    # Clean up SKU
    if not sku or sku == 'NULL' or sku.strip() == '':
        sku = f"PROD-{abs(hash(product_name)) % 100000}"
    
    sku = sku.strip()
    
    # Check if product exists by SKU
    cursor.execute("SELECT pk_id_product FROM dim_product WHERE ref_product = ?", sku)
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Check if product exists by name
    cursor.execute("SELECT pk_id_product FROM dim_product WHERE name_product = ?", product_name)
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Create product - need to get valid foreign keys
    cursor.execute("SELECT TOP 1 pk_id_category FROM dim_category")
    fk_category = cursor.fetchone()
    fk_category = fk_category[0] if fk_category else 1
    
    cursor.execute("SELECT TOP 1 pk_id_supplier FROM dim_supplier")
    fk_supplier = cursor.fetchone()
    fk_supplier = fk_supplier[0] if fk_supplier else 1
    
    cursor.execute("SELECT TOP 1 pk_id_material FROM dim_material")
    fk_material = cursor.fetchone()
    fk_material = fk_material[0] if fk_material else 1
    
    try:
        cursor.execute("""
            INSERT INTO dim_product (ref_product, name_product, fk_category, fk_supplier, fk_material)
            VALUES (?, ?, ?, ?, ?)
        """, sku, product_name or 'Unknown Product', fk_category, fk_supplier, fk_material)
        
        cursor.execute("SELECT @@IDENTITY")
        return int(cursor.fetchone()[0])
    except Exception as e:
        print(f"   Error creating product {sku}: {e}")
        return None

def get_or_create_date(cursor, date_str):
    """Get or create date dimension"""
    
    if not date_str or date_str.strip() == '':
        date_obj = datetime.now()
    else:
        try:
            # Try multiple date formats
            for fmt in ['%d-%m-%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y', '%Y-%m-%d']:
                try:
                    date_obj = datetime.strptime(date_str.strip(), fmt)
                    break
                except:
                    continue
            else:
                # If no format worked, use current date
                date_obj = datetime.now()
        except:
            date_obj = datetime.now()
    
    full_date = date_obj.strftime('%Y-%m-%d')
    
    cursor.execute("SELECT pk_id_date FROM dim_date WHERE full_date = ?", full_date)
    row = cursor.fetchone()
    
    if row:
        return row[0]
    
    # Create date
    try:
        cursor.execute("""
            INSERT INTO dim_date (full_date, day, month, trimester, semester, year)
            VALUES (?, ?, ?, ?, ?, ?)
        """, full_date, date_obj.day, date_obj.month, 
            (date_obj.month - 1) // 3 + 1,  # trimester
            (date_obj.month - 1) // 6 + 1,  # semester
            date_obj.year)
        
        cursor.execute("SELECT @@IDENTITY")
        return int(cursor.fetchone()[0])
    except Exception as e:
        print(f"   Error creating date {full_date}: {e}")
        # Return a default date
        cursor.execute("SELECT TOP 1 pk_id_date FROM dim_date")
        row = cursor.fetchone()
        return row[0] if row else 1

def sale_exists(cursor, fk_order, fk_product, quantity, unit_price):
    """Check if a sale already exists"""
    cursor.execute("""
        SELECT COUNT(*) FROM fact_sale 
        WHERE fk_order = ? AND fk_product = ? AND quantity = ? AND unit_price = ?
    """, fk_order, fk_product, quantity, unit_price)
    
    count = cursor.fetchone()[0]
    return count > 0

def create_sale(cursor, sale_data, fk_order, fk_product, fk_date):
    """Create a sale record in fact_sale"""
    
    try:
        quantity = float(sale_data['quantity']) if sale_data['quantity'] else 1.0
    except:
        quantity = 1.0
    
    try:
        unit_price = float(sale_data['product_price']) if sale_data['product_price'] else 0.0
    except:
        unit_price = 0.0
    
    # Calculate total (quantity * unit_price)
    total_price = quantity * unit_price
    
    # Check if sale already exists
    if sale_exists(cursor, fk_order, fk_product, quantity, unit_price):
        return False  # Sale already exists
    
    # Get default foreign keys
    cursor.execute("SELECT TOP 1 pk_id_place FROM dim_place")
    fk_place = cursor.fetchone()
    fk_place = fk_place[0] if fk_place else 1
    
    cursor.execute("SELECT TOP 1 pk_id_channel FROM dim_channel")
    fk_channel = cursor.fetchone()
    fk_channel = fk_channel[0] if fk_channel else 1
    
    # Create sale
    try:
        cursor.execute("""
            INSERT INTO fact_sale (
                fk_date, fk_place, fk_product, fk_claim, fk_order,
                fk_clientB2B, fk_clientB2C, fk_channel, fk_invoice,
                quantity, ugs, tax_status, unit_price, discount, total_price
            ) VALUES (?, ?, ?, NULL, ?, NULL, NULL, ?, NULL, ?, ?, 'taxable', ?, 0, ?)
        """, fk_date, fk_place, fk_product, fk_order, fk_channel,
            quantity, sale_data['product_sku'] or '', unit_price, total_price)
        
        return True  # Sale created
    except Exception as e:
        print(f"   Error creating sale: {e}")
        return False

def main():
    print("=" * 70)
    print("ETL: Import Sales from etl (3).sql into fact_sale")
    print("=" * 70)
    print()
    
    # Parse etl (3).sql
    sales_data = parse_etl_sales('../etl (3).sql')
    
    if not sales_data:
        print("ERROR: No sales data to import")
        return
    
    print(f"\nTotal sales records found: {len(sales_data)}")
    
    # Connect to database
    print("\nConnecting to database...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Statistics
    sales_created = 0
    sales_skipped = 0
    sales_no_order = 0
    products_created = 0
    errors = 0
    
    # Group sales by order
    orders_dict = {}
    for sale in sales_data:
        order_num = sale['order_number']
        if order_num:
            if order_num not in orders_dict:
                orders_dict[order_num] = []
            orders_dict[order_num].append(sale)
    
    print(f"\nProcessing {len(orders_dict)} unique orders...")
    print()
    
    # Process each order
    processed = 0
    for order_num, order_sales in orders_dict.items():
        try:
            # Get order by number
            fk_order = get_order_by_number(cursor, order_num)
            
            if not fk_order:
                sales_no_order += len(order_sales)
                continue
            
            # Get first sale for date info
            first_sale = order_sales[0]
            fk_date = get_or_create_date(cursor, first_sale['order_date'])
            
            # Process each sale item
            for sale in order_sales:
                # Create/get product
                fk_product = get_or_create_product(
                    cursor,
                    sale['product_sku'],
                    sale['product_name']
                )
                
                if not fk_product:
                    errors += 1
                    continue
                
                if cursor.rowcount > 0:
                    products_created += 1
                
                # Create sale
                created = create_sale(cursor, sale, fk_order, fk_product, fk_date)
                
                if created:
                    sales_created += 1
                else:
                    sales_skipped += 1
            
            # Commit after each order
            conn.commit()
            
            processed += 1
            if processed % 50 == 0:
                print(f"   Processed {processed}/{len(orders_dict)} orders... "
                      f"(Created: {sales_created}, Skipped: {sales_skipped}, No Order: {sales_no_order})")
        
        except Exception as e:
            errors += 1
            print(f"   ERROR processing order {order_num}: {e}")
            conn.rollback()
    
    print()
    print("=" * 70)
    print("ETL COMPLETE")
    print("=" * 70)
    print(f"✅ Sales created: {sales_created}")
    print(f"⏭️  Sales skipped (already exist): {sales_skipped}")
    print(f"⚠️  Sales without matching order: {sales_no_order}")
    print(f"✅ Products created: {products_created}")
    print(f"❌ Errors: {errors}")
    print()
    
    # Verify results
    print("Database Statistics:")
    cursor.execute("SELECT COUNT(*) FROM dim_order")
    print(f"   Total orders: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM dim_product")
    print(f"   Total products: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM fact_sale")
    total_sales = cursor.fetchone()[0]
    print(f"   Total sales: {total_sales}")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT o.pk_id_order)
        FROM dim_order o
        INNER JOIN fact_sale s ON s.fk_order = o.pk_id_order
    """)
    orders_with_sales = cursor.fetchone()[0]
    print(f"   Orders with sales: {orders_with_sales}")
    
    cursor.execute("""
        SELECT COUNT(*)
        FROM dim_order o
        WHERE NOT EXISTS (SELECT 1 FROM fact_sale s WHERE s.fk_order = o.pk_id_order)
    """)
    orders_without_sales = cursor.fetchone()[0]
    print(f"   Orders without sales: {orders_without_sales}")
    
    conn.close()
    
    print()
    print("✅ ETL process completed successfully!")
    print()
    print("Next steps:")
    print("1. Restart the backend server (if needed)")
    print("2. Refresh the frontend at http://localhost:3000/orders")
    print("3. All orders should now have correct item counts and totals")

if __name__ == '__main__':
    main()
