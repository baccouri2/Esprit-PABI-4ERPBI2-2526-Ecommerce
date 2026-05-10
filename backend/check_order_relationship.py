import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=HEDIRE\\MSSQLSERVER05;'
    'DATABASE=dw_pi;'
    'Trusted_Connection=yes',
    timeout=15
)
cursor = conn.cursor()

# Get dim_order columns and sample data
print("=== DIM_ORDER TABLE ===")
cursor.execute("SELECT TOP 1 * FROM dim_order")
columns = [col[0] for col in cursor.description]
print(f"Columns: {columns}")

cursor.execute("SELECT TOP 10 * FROM dim_order ORDER BY pk_id_order DESC")
rows = cursor.fetchall()
print("\nSample data:")
for row in rows:
    print(dict(zip(columns, row)))

# Get fact_sale sample with fk_order
print("\n=== FACT_SALE TABLE (with fk_order) ===")
cursor.execute("SELECT TOP 10 pk_id_sale, fk_order, fk_product, unit_price, quantity, total_price FROM fact_sale WHERE fk_order IS NOT NULL ORDER BY pk_id_sale DESC")
rows = cursor.fetchall()
print("Sample data:")
for row in rows:
    print(f"pk_id_sale={row[0]}, fk_order={row[1]}, fk_product={row[2]}, unit_price={row[3]}, quantity={row[4]}, total_price={row[5]}")

# Try to find matching pattern
print("\n=== TESTING DIFFERENT JOIN STRATEGIES ===")

# Strategy 1: fk_order = pk_id_order
print("\n1. Testing: fact_sale.fk_order = dim_order.pk_id_order")
cursor.execute("""
    SELECT COUNT(*) as match_count
    FROM fact_sale s
    INNER JOIN dim_order o ON s.fk_order = o.pk_id_order
""")
count = cursor.fetchone()[0]
print(f"   Matches found: {count}")

# Strategy 2: Check if there's a pattern with id_order
print("\n2. Checking if fk_order relates to id_order somehow")
cursor.execute("""
    SELECT TOP 5 s.fk_order, o.pk_id_order, o.id_order
    FROM fact_sale s
    CROSS JOIN dim_order o
    WHERE s.fk_order IS NOT NULL
    ORDER BY ABS(CAST(s.fk_order AS INT) - o.pk_id_order)
""")
rows = cursor.fetchall()
print("   Closest matches by pk_id_order:")
for row in rows:
    print(f"   fk_order={row[0]}, pk_id_order={row[1]}, id_order={row[2]}")

# Strategy 3: Check all dim_order columns for potential matches
print("\n3. Looking for other potential matching columns in dim_order")
cursor.execute("SELECT * FROM dim_order WHERE pk_id_order IN (SELECT TOP 1 fk_order FROM fact_sale WHERE fk_order IS NOT NULL)")
rows = cursor.fetchall()
if rows:
    print("   Found matching order!")
    for row in rows:
        print(f"   {dict(zip(columns, row))}")
else:
    print("   No direct match found")

# Strategy 4: Check if there's an invoice relationship
print("\n4. Checking invoice relationship")
cursor.execute("""
    SELECT TOP 5 s.fk_invoice, s.fk_order, COUNT(*) as sale_count
    FROM fact_sale s
    WHERE s.fk_order IS NOT NULL
    GROUP BY s.fk_invoice, s.fk_order
""")
rows = cursor.fetchall()
print("   Invoice-Order relationships:")
for row in rows:
    print(f"   fk_invoice={row[0]}, fk_order={row[1]}, sales={row[2]}")

conn.close()
