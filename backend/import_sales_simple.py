"""
Simple ETL script to import sales from etl (3).sql
Fixes schema issues by:
1. Getting a default fk_invoice value
2. Using correct dim_product schema (no fk_supplier, fk_material)
"""

import pyodbc
import re
from datetime import datetime

def get_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=HEDIRE\\MSSQLSERVER05;'
        'DATABASE=dw_pi;'
        'Trusted_Connection=yes',
        timeout=15
    )

def parse_sales_from_etl(file_path):
    """Extract sales data from etl (3).sql"""
    print("Reading etl (3).sql...")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find INSERT INTO `sales` statements
    pattern = r"INSERT INTO `sales`[^;]*?VALUES\s*(.*?);"
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    
    print(f"Found {len(matches)} INSERT statements")
    
    all_sales = []
    for match in matches:
        # Simple row extraction
        rows = re.findall(r"\(([^)]+(?:\([^)]*\)[^)]*)*)\)", match, re.DOTALL)
        
        for row in rows:
            try:
                # Split by comma, handling quoted strings
                parts = []
                current = ""
                in_quotes = False
                
                for char in row:
                    if char == "'" and (not current or current[-1] != '\\'):
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        parts.append(current.strip().strip("'"))
                        current = ""
                        continue
                    current += char
                
                if current:
                    parts.append(current.strip().strip("'"))
                
                if len(parts) >= 32:
                    all_sales.append({
                        'order_number': parts[0],
                        'order_date': parts[2],
                        'product_sku': parts[27],
                        'product_name': parts[29],
                        'quantity': parts[30],
                        'unit_price': parts[31]
                    })
            except:
                continue
    
    print(f"Parsed {len(all_sales)} sales records")
    return all_sales

def main():
    print("=" * 70)
    print("Simple ETL: Import Sales from etl (3).sql")
    print("=" * 70)
    
    # Parse sales
    sales_data = parse_sales_from_etl('../etl (3).sql')
    
    if not sales_data:
        print("No sales data found")
        return
    
    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get default foreign keys
    print("\nGetting default foreign keys...")
    
    cursor.execute("SELECT TOP 1 pk_id_invoice FROM dim_invoice")
    fk_invoice_row = cursor.fetchone()
    fk_invoice = fk_invoice_row[0] if fk_invoice_row else None
    
    if not fk_invoice:
        print("ERROR: No invoices found in dim_invoice. Creating a default one...")
        try:
            cursor.execute("INSERT INTO dim_invoice (num_invoice) VALUES ('DEFAULT')")
            conn.commit()
            cursor.execute("SELECT @@IDENTITY")
            fk_invoice = int(cursor.fetchone()[0])
            print(f"Created default invoice with ID: {fk_invoice}")
        except Exception as e:
            print(f"ERROR creating default invoice: {e}")
            conn.close()
            return
    
    cursor.execute("SELECT TOP 1 pk_id_place FROM dim_place")
    fk_place = cursor.fetchone()[0]
    
    cursor.execute("SELECT TOP 1 pk_id_channel FROM dim_channel")
    fk_channel = cursor.fetchone()[0]
    
    cursor.execute("SELECT TOP 1 pk_id_category FROM dim_category")
    fk_category = cursor.fetchone()[0]
    
    print(f"Using: fk_invoice={fk_invoice}, fk_place={fk_place}, fk_channel={fk_channel}, fk_category={fk_category}")
    
    # Statistics
    created = 0
    skipped = 0
    no_order = 0
    errors = 0
    
    # Group by order
    orders_dict = {}
    for sale in sales_data:
        order_num = sale['order_number']
        if order_num:
            if order_num not in orders_dict:
                orders_dict[order_num] = []
            orders_dict[order_num].append(sale)
    
    print(f"\nProcessing {len(orders_dict)} unique orders...")
    
    processed = 0
    for order_num, order_sales in orders_dict.items():
        try:
            # Get order
            cursor.execute("SELECT pk_id_order FROM dim_order WHERE id_order = ?", order_num)
            order_row = cursor.fetchone()
            
            if not order_row:
                no_order += len(order_sales)
                continue
            
            fk_order = order_row[0]
            
            # Get/create date
            first_sale = order_sales[0]
            date_str = first_sale['order_date']
            
            try:
                date_obj = datetime.strptime(date_str.strip(), '%d-%m-%Y %H:%M:%S')
            except:
                date_obj = datetime.now()
            
            full_date = date_obj.strftime('%Y-%m-%d')
            
            cursor.execute("SELECT pk_id_date FROM dim_date WHERE full_date = ?", full_date)
            date_row = cursor.fetchone()
            
            if date_row:
                fk_date = date_row[0]
            else:
                # Create date
                cursor.execute("""
                    INSERT INTO dim_date (full_date, day, month, trimester, semester, year)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, full_date, date_obj.day, date_obj.month,
                    (date_obj.month - 1) // 3 + 1,
                    (date_obj.month - 1) // 6 + 1,
                    date_obj.year)
                cursor.execute("SELECT @@IDENTITY")
                fk_date = int(cursor.fetchone()[0])
            
            # Process each sale
            for sale in order_sales:
                # Get/create product
                sku = sale['product_sku'].strip() if sale['product_sku'] else f"PROD-{abs(hash(sale['product_name'])) % 100000}"
                product_name = sale['product_name']
                
                cursor.execute("SELECT pk_id_product FROM dim_product WHERE ref_product = ?", sku)
                product_row = cursor.fetchone()
                
                if product_row:
                    fk_product = product_row[0]
                else:
                    # Create product with correct schema
                    cursor.execute("""
                        INSERT INTO dim_product (ref_product, name_product, fk_category)
                        VALUES (?, ?, ?)
                    """, sku, product_name, fk_category)
                    cursor.execute("SELECT @@IDENTITY")
                    fk_product = int(cursor.fetchone()[0])
                
                # Parse quantity and price
                try:
                    quantity = float(sale['quantity'])
                except:
                    quantity = 1.0
                
                try:
                    unit_price = float(sale['unit_price'])
                except:
                    unit_price = 0.0
                
                total_price = quantity * unit_price
                
                # Check if sale exists
                cursor.execute("""
                    SELECT COUNT(*) FROM fact_sale
                    WHERE fk_order = ? AND fk_product = ? AND quantity = ? AND unit_price = ?
                """, fk_order, fk_product, quantity, unit_price)
                
                if cursor.fetchone()[0] > 0:
                    skipped += 1
                    continue
                
                # Create sale with fk_invoice
                cursor.execute("""
                    INSERT INTO fact_sale (
                        fk_date, fk_place, fk_product, fk_claim, fk_order,
                        fk_clientB2B, fk_clientB2C, fk_channel, fk_invoice,
                        quantity, ugs, tax_status, unit_price, discount, total_price
                    ) VALUES (?, ?, ?, NULL, ?, NULL, NULL, ?, ?, ?, ?, 'taxable', ?, 0, ?)
                """, fk_date, fk_place, fk_product, fk_order, fk_channel, fk_invoice,
                    quantity, sku, unit_price, total_price)
                
                created += 1
            
            conn.commit()
            
            processed += 1
            if processed % 50 == 0:
                print(f"   Processed {processed}/{len(orders_dict)} orders (Created: {created}, Skipped: {skipped})")
        
        except Exception as e:
            errors += 1
            if errors <= 5:  # Only print first 5 errors
                print(f"   ERROR processing order {order_num}: {e}")
            conn.rollback()
    
    print()
    print("=" * 70)
    print("ETL COMPLETE")
    print("=" * 70)
    print(f"✅ Sales created: {created}")
    print(f"⏭️  Sales skipped (already exist): {skipped}")
    print(f"⚠️  Sales without matching order: {no_order}")
    print(f"❌ Errors: {errors}")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM fact_sale")
    total_sales = cursor.fetchone()[0]
    print(f"\n📊 Total sales in database: {total_sales}")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT o.pk_id_order)
        FROM dim_order o
        INNER JOIN fact_sale s ON s.fk_order = o.pk_id_order
    """)
    orders_with_sales = cursor.fetchone()[0]
    print(f"📊 Orders with sales: {orders_with_sales}")
    
    cursor.execute("""
        SELECT COUNT(*)
        FROM dim_order o
        WHERE NOT EXISTS (SELECT 1 FROM fact_sale s WHERE s.fk_order = o.pk_id_order)
    """)
    orders_without_sales = cursor.fetchone()[0]
    print(f"📊 Orders without sales: {orders_without_sales}")
    
    conn.close()
    
    print("\n✅ Import completed!")
    print("Refresh the frontend to see updated order data.")

if __name__ == '__main__':
    main()
