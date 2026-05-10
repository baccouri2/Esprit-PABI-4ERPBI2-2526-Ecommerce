import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=HEDIRE\\MSSQLSERVER05;'
    'DATABASE=dw_pi;'
    'Trusted_Connection=yes',
    timeout=15
)
cursor = conn.cursor()

# Find all tables
print("=== ALL TABLES IN DATABASE ===")
cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

# Check if there's a dim_invoice
print("\n=== CHECKING FOR INVOICE TABLES ===")
invoice_tables = [t[0] for t in tables if 'invoice' in t[0].lower() or 'facture' in t[0].lower()]
if invoice_tables:
    print(f"Found: {invoice_tables}")
    for table in invoice_tables:
        cursor.execute(f"SELECT TOP 1 * FROM {table}")
        columns = [col[0] for col in cursor.description]
        print(f"\n{table} columns: {columns}")
        cursor.execute(f"SELECT TOP 5 * FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  {dict(zip(columns, row))}")
else:
    print("No invoice/facture tables found")

# Check the relationship between fk_invoice and fk_order in fact_sale
print("\n=== FACT_SALE: fk_invoice vs fk_order ===")
cursor.execute("""
    SELECT TOP 10 pk_id_sale, fk_invoice, fk_order
    FROM fact_sale
    WHERE fk_order IS NOT NULL
    ORDER BY pk_id_sale DESC
""")
rows = cursor.fetchall()
for row in rows:
    print(f"  pk_id_sale={row[0]}, fk_invoice={row[1]}, fk_order={row[2]}")

conn.close()
