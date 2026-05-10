"""
Diagnose why sales import is failing
"""

import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=HEDIRE\\MSSQLSERVER05;'
    'DATABASE=dw_pi;'
    'Trusted_Connection=yes',
    timeout=15
)
cursor = conn.cursor()

print("=== DIAGNOSING SALES IMPORT ISSUES ===\n")

# Check fact_sale schema
print("1. fact_sale schema:")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'fact_sale'
    ORDER BY ORDINAL_POSITION
""")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}, Nullable={row[2]}, Default={row[3]}")

print("\n2. Check if pk_id_sale is IDENTITY:")
cursor.execute("""
    SELECT COLUMNPROPERTY(OBJECT_ID('fact_sale'), 'pk_id_sale', 'IsIdentity')
""")
is_identity = cursor.fetchone()[0]
print(f"   pk_id_sale is IDENTITY: {is_identity == 1}")

print("\n3. Sample existing sales:")
cursor.execute("SELECT TOP 3 * FROM fact_sale")
for row in cursor.fetchall():
    print(f"   {row}")

print("\n4. Check orders from etl (3).sql:")
cursor.execute("""
    SELECT TOP 5 pk_id_order, id_order, date_commande
    FROM dim_order
    WHERE id_order IN ('14148', '14146', '14145', '14144', '14143')
    ORDER BY id_order DESC
""")
print("   Orders found:")
for row in cursor.fetchall():
    print(f"   {row}")

print("\n5. Test INSERT:")
try:
    # Get required FKs
    cursor.execute("SELECT TOP 1 pk_id_date FROM dim_date")
    fk_date = cursor.fetchone()[0]
    
    cursor.execute("SELECT TOP 1 pk_id_place FROM dim_place")
    fk_place = cursor.fetchone()[0]
    
    cursor.execute("SELECT TOP 1 pk_id_product FROM dim_product")
    fk_product = cursor.fetchone()[0]
    
    cursor.execute("SELECT TOP 1 pk_id_order FROM dim_order")
    fk_order = cursor.fetchone()[0]
    
    cursor.execute("SELECT TOP 1 pk_id_channel FROM dim_channel")
    fk_channel = cursor.fetchone()[0]
    
    cursor.execute("SELECT TOP 1 pk_id_invoice FROM dim_invoice")
    fk_invoice = cursor.fetchone()[0]
    
    print(f"   Using FKs: date={fk_date}, place={fk_place}, product={fk_product}, order={fk_order}, channel={fk_channel}, invoice={fk_invoice}")
    
    # Try INSERT
    cursor.execute("""
        INSERT INTO fact_sale (
            fk_date, fk_place, fk_product, fk_claim, fk_order,
            fk_clientB2B, fk_clientB2C, fk_channel, fk_invoice,
            quantity, ugs, tax_status, unit_price, discount, total_price
        ) VALUES (?, ?, ?, NULL, ?, NULL, NULL, ?, ?, 1, 'TEST', 'taxable', 10.0, 0, 10.0)
    """, fk_date, fk_place, fk_product, fk_order, fk_channel, fk_invoice)
    
    conn.rollback()  # Don't actually save it
    print("   ✅ Test INSERT succeeded!")
    
except Exception as e:
    print(f"   ❌ Test INSERT failed: {e}")
    conn.rollback()

conn.close()
