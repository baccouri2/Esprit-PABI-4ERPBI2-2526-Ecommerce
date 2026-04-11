import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=HEDIRE\\MSSQLSERVER05;'
    'DATABASE=dw_pi;'
    'Trusted_Connection=yes'
)
cursor = conn.cursor()

for table in ['dim_product', 'dim_clientB2B', 'dim_clientB2C', 'dim_category']:
    try:
        cursor.execute(f'SELECT TOP 1 * FROM {table}')
        print(f'{table}:', [col[0] for col in cursor.description])
    except Exception as e:
        print(f'{table}: ERROR - {e}')

# Sample data
cursor.execute("""
    SELECT TOP 5
        COALESCE(s.fk_clientB2B, s.fk_clientB2C) as client_id,
        s.fk_product,
        p.name_product,
        SUM(s.quantity) as total_qty
    FROM fact_sale s
    INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
    GROUP BY COALESCE(s.fk_clientB2B, s.fk_clientB2C), s.fk_product, p.name_product
""")
print('\nSample purchase data:')
for row in cursor.fetchall():
    print(row)

conn.close()
