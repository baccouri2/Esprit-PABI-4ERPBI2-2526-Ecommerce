import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=HEDIRE\\MSSQLSERVER05;'
    'DATABASE=dw_pi;'
    'Trusted_Connection=yes',
    timeout=15
)
cursor = conn.cursor()

print("=== TESTING: Can we link fact_sale to dim_order via dim_invoice? ===\n")

# Test 1: Check if dim_invoice.num_document matches dim_order.id_order
print("1. Checking if dim_invoice.num_document matches dim_order.id_order")
cursor.execute("""
    SELECT COUNT(*) as match_count
    FROM dim_invoice i
    INNER JOIN dim_order o ON i.num_document = o.id_order
""")
count = cursor.fetchone()[0]
print(f"   Matches found: {count}\n")

if count > 0:
    print("   Sample matches:")
    cursor.execute("""
        SELECT TOP 5 i.pk_id_invoice, i.num_document, o.pk_id_order, o.id_order, o.order_status
        FROM dim_invoice i
        INNER JOIN dim_order o ON i.num_document = o.id_order
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"   invoice_pk={row[0]}, num_document={row[1]}, order_pk={row[2]}, id_order={row[3]}, status={row[4]}")

# Test 2: Try the full join from fact_sale to dim_order
print("\n2. Testing full join: fact_sale -> dim_invoice -> dim_order")
cursor.execute("""
    SELECT 
        o.pk_id_order,
        o.id_order,
        COUNT(s.pk_id_sale) as item_count,
        SUM(s.total_price) as total_amount
    FROM dim_order o
    LEFT JOIN dim_invoice i ON i.num_document = o.id_order
    LEFT JOIN fact_sale s ON s.fk_invoice = i.pk_id_invoice
    WHERE o.id_order IN ('14148', '14145', '14146')
    GROUP BY o.pk_id_order, o.id_order
""")
rows = cursor.fetchall()
print("   Results for orders 14148, 14145, 14146:")
for row in rows:
    print(f"   pk={row[0]}, id_order={row[1]}, items={row[2]}, total={row[3]}")

# Test 3: Check all orders with items
print("\n3. Finding ALL orders that have items:")
cursor.execute("""
    SELECT 
        o.pk_id_order,
        o.id_order,
        o.order_status,
        COUNT(s.pk_id_sale) as item_count,
        SUM(s.total_price) as total_amount
    FROM dim_order o
    LEFT JOIN dim_invoice i ON i.num_document = o.id_order
    LEFT JOIN fact_sale s ON s.fk_invoice = i.pk_id_invoice
    GROUP BY o.pk_id_order, o.id_order, o.order_status
    HAVING COUNT(s.pk_id_sale) > 0
    ORDER BY o.pk_id_order DESC
""")
rows = cursor.fetchall()
print(f"   Found {len(rows)} orders with items:")
for row in rows[:10]:
    print(f"   pk={row[0]}, id_order={row[1]}, status={row[2]}, items={row[3]}, total={row[4]}")

conn.close()
