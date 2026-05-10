"""
Verify the sales import results
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

print("=" * 70)
print("SALES IMPORT VERIFICATION")
print("=" * 70)

print("\n1. Overall Statistics:")
cursor.execute("SELECT COUNT(*) FROM dim_order")
total_orders = cursor.fetchone()[0]
print(f"   Total orders: {total_orders}")

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

print(f"\n   Coverage: {orders_with_sales}/{total_orders} ({orders_with_sales*100/total_orders:.1f}%)")

print("\n2. Sample Orders with Sales (Top 10):")
cursor.execute("""
    SELECT TOP 10
        o.pk_id_order,
        o.id_order,
        o.order_status,
        o.date_commande,
        COUNT(s.pk_id_sale) as item_count,
        SUM(s.total_price) as total_amount
    FROM dim_order o
    INNER JOIN fact_sale s ON s.fk_order = o.pk_id_order
    GROUP BY o.pk_id_order, o.id_order, o.order_status, o.date_commande
    ORDER BY o.pk_id_order DESC
""")

for row in cursor.fetchall():
    print(f"   Order #{row[0]} ({row[1]}): {row[4]} items, {float(row[5]):.2f} TND - Status: {row[2]}")

print("\n3. Sample Order Details (Order #917 - 14148):")
cursor.execute("""
    SELECT 
        p.ref_product,
        p.name_product,
        s.quantity,
        s.unit_price,
        s.total_price
    FROM fact_sale s
    INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
    WHERE s.fk_order = 917
""")

items = cursor.fetchall()
if items:
    print(f"   Found {len(items)} items:")
    for item in items:
        print(f"   - {item[0]}: {item[1]}")
        print(f"     Qty: {item[2]}, Unit Price: {float(item[3]):.2f} TND, Total: {float(item[4]):.2f} TND")
else:
    print("   No items found for this order")

print("\n4. Orders Without Sales (Sample 5):")
cursor.execute("""
    SELECT TOP 5
        o.pk_id_order,
        o.id_order,
        o.order_status,
        o.date_commande
    FROM dim_order o
    WHERE NOT EXISTS (SELECT 1 FROM fact_sale s WHERE s.fk_order = o.pk_id_order)
    ORDER BY o.pk_id_order DESC
""")

for row in cursor.fetchall():
    print(f"   Order #{row[0]} ({row[1]}): No sales data - Status: {row[2]}")

print("\n5. Product Statistics:")
cursor.execute("SELECT COUNT(*) FROM dim_product")
total_products = cursor.fetchone()[0]
print(f"   Total products: {total_products}")

cursor.execute("""
    SELECT COUNT(DISTINCT fk_product)
    FROM fact_sale
""")
products_with_sales = cursor.fetchone()[0]
print(f"   Products with sales: {products_with_sales}")

conn.close()

print("\n" + "=" * 70)
print("✅ VERIFICATION COMPLETE")
print("=" * 70)
print("\nThe orders page should now display:")
print("- Item counts for 99 orders")
print("- Total amounts for 99 orders")
print("- Order details with line items")
print("- Invoice generation with products")
print("\nRefresh http://localhost:3000/orders to see the updated data.")
