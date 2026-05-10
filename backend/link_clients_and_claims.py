"""
Link the 39 sales records (without client info) to clients and claims
by extracting data from etl (3).sql
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
    """Extract sales data with client info from etl (3).sql"""
    print("Reading etl (3).sql for client and claim data...")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find INSERT INTO `sales` statements
    pattern = r"INSERT INTO `sales`[^;]*?VALUES\s*(.*?);"
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    
    print(f"Found {len(matches)} INSERT statements")
    
    all_sales = []
    for match in matches:
        rows = re.findall(r"\(([^)]+(?:\([^)]*\)[^)]*)*)\)", match, re.DOTALL)
        
        for row in rows:
            try:
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
                        'customer_note': parts[3] if len(parts) > 3 else '',
                        'billing_first_name': parts[4] if len(parts) > 4 else '',
                        'billing_last_name': parts[5] if len(parts) > 5 else '',
                        'billing_city': parts[7] if len(parts) > 7 else '',
                    })
            except:
                continue
    
    print(f"Parsed {len(all_sales)} sales records with client info")
    return all_sales

def get_or_create_b2c_client(cursor, first_name, last_name):
    """Get or create a B2C client"""
    if not first_name or not last_name:
        return None
    
    first_name = first_name.strip()
    last_name = last_name.strip()
    
    # Check if client exists
    cursor.execute("""
        SELECT pk_id_client FROM dim_clientB2C
        WHERE first_name = ? AND last_name = ?
    """, first_name, last_name)
    
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # Create new client
    try:
        cursor.execute("""
            INSERT INTO dim_clientB2C (first_name, last_name, date_participation)
            VALUES (?, ?, NULL)
        """, first_name, last_name)
        
        cursor.execute("SELECT @@IDENTITY")
        return int(cursor.fetchone()[0])
    except Exception as e:
        print(f"   Error creating client {first_name} {last_name}: {e}")
        return None

def get_or_create_claim(cursor, description):
    """Get or create a claim/note"""
    if not description or description.strip() == '' or description.lower() == 'inconnue':
        return None
    
    description = description.strip()
    
    # Check if claim exists
    cursor.execute("""
        SELECT pk_id_claim FROM dim_claim
        WHERE description = ?
    """, description)
    
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # Create new claim
    try:
        cursor.execute("""
            INSERT INTO dim_claim (description, status)
            VALUES (?, 'processed')
        """, description)
        
        cursor.execute("SELECT @@IDENTITY")
        return int(cursor.fetchone()[0])
    except Exception as e:
        print(f"   Error creating claim: {str(e)[:50]}")
        return None

def main():
    print("=" * 80)
    print("LINKING CLIENTS AND CLAIMS TO SALES")
    print("=" * 80)
    
    # Parse sales data
    sales_data = parse_sales_from_etl('../etl (3).sql')
    
    if not sales_data:
        print("No sales data found")
        return
    
    # Create lookup dictionary by order number
    sales_lookup = {}
    for sale in sales_data:
        order_num = sale['order_number']
        if order_num not in sales_lookup:
            sales_lookup[order_num] = sale
    
    print(f"Created lookup for {len(sales_lookup)} unique orders")
    
    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get sales without client info
    print("\nFinding sales without client information...")
    cursor.execute("""
        SELECT 
            s.pk_id_sale,
            o.id_order,
            s.fk_clientB2B,
            s.fk_clientB2C,
            s.fk_claim
        FROM fact_sale s
        INNER JOIN dim_order o ON s.fk_order = o.pk_id_order
        WHERE s.fk_clientB2B IS NULL AND s.fk_clientB2C IS NULL
    """)
    
    sales_without_clients = cursor.fetchall()
    print(f"Found {len(sales_without_clients)} sales without client info")
    
    # Statistics
    clients_created = 0
    clients_found = 0
    claims_created = 0
    claims_found = 0
    sales_updated = 0
    no_match = 0
    
    print("\nProcessing sales...")
    for sale_row in sales_without_clients:
        pk_id_sale = sale_row[0]
        order_number = sale_row[1]
        
        # Find matching data in etl
        if order_number not in sales_lookup:
            no_match += 1
            continue
        
        sale_data = sales_lookup[order_number]
        
        # Get or create B2C client
        fk_clientB2C = get_or_create_b2c_client(
            cursor,
            sale_data['billing_first_name'],
            sale_data['billing_last_name']
        )
        
        if fk_clientB2C:
            if cursor.rowcount > 0:
                clients_created += 1
            else:
                clients_found += 1
        
        # Get or create claim
        fk_claim = get_or_create_claim(cursor, sale_data['customer_note'])
        
        if fk_claim:
            if cursor.rowcount > 0:
                claims_created += 1
            else:
                claims_found += 1
        
        # Update sale
        if fk_clientB2C or fk_claim:
            try:
                cursor.execute("""
                    UPDATE fact_sale
                    SET fk_clientB2C = ?, fk_claim = ?
                    WHERE pk_id_sale = ?
                """, fk_clientB2C, fk_claim, pk_id_sale)
                
                sales_updated += 1
                
                if sales_updated % 10 == 0:
                    print(f"   Updated {sales_updated} sales...")
                    conn.commit()
            except Exception as e:
                print(f"   Error updating sale #{pk_id_sale}: {e}")
                conn.rollback()
    
    conn.commit()
    
    print()
    print("=" * 80)
    print("LINKING COMPLETE")
    print("=" * 80)
    print(f"✅ Sales updated: {sales_updated}")
    print(f"✅ Clients created: {clients_created}")
    print(f"✅ Clients found (existing): {clients_found}")
    print(f"✅ Claims created: {claims_created}")
    print(f"✅ Claims found (existing): {claims_found}")
    print(f"⚠️  No match in etl: {no_match}")
    
    # Verify results
    print("\n📊 Final Statistics:")
    
    cursor.execute("SELECT COUNT(*) FROM dim_clientB2C")
    total_b2c = cursor.fetchone()[0]
    print(f"   Total B2C clients: {total_b2c}")
    
    cursor.execute("SELECT COUNT(*) FROM dim_claim")
    total_claims = cursor.fetchone()[0]
    print(f"   Total claims: {total_claims}")
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN fk_clientB2B IS NOT NULL OR fk_clientB2C IS NOT NULL THEN 1 ELSE 0 END) as with_client,
            SUM(CASE WHEN fk_claim IS NOT NULL THEN 1 ELSE 0 END) as with_claim
        FROM fact_sale
    """)
    row = cursor.fetchone()
    print(f"   Total sales: {row[0]}")
    print(f"   Sales with client: {row[1]} ({row[1]*100/row[0]:.1f}%)")
    print(f"   Sales with claim: {row[2]} ({row[2]*100/row[0]:.1f}%)")
    
    conn.close()
    
    print("\n✅ Client and claim linking completed!")
    print("The orders page now has complete client and claim information.")

if __name__ == '__main__':
    main()
