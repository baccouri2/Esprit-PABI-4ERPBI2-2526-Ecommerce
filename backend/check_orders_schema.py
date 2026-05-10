import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=HEDIRE\\MSSQLSERVER05;'
    'DATABASE=dw_pi;'
    'Trusted_Connection=yes'
)

cursor = conn.cursor()

# Check if fact_order exists
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE='BASE TABLE' AND TABLE_NAME LIKE '%order%'
    ORDER BY TABLE_NAME
""")
print("Tables with 'order' in name:")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# Check fact_sale structure (similar to orders)
print("\nfact_sale columns:")
cursor.execute("SELECT TOP 1 * FROM fact_sale")
for col in cursor.description:
    print(f"  - {col[0]}")

# Check dim_delivery if exists
try:
    cursor.execute("SELECT TOP 1 * FROM dim_delivery")
    print("\ndim_delivery columns:")
    for col in cursor.description:
        print(f"  - {col[0]}")
except:
    print("\ndim_delivery table does not exist")

conn.close()
