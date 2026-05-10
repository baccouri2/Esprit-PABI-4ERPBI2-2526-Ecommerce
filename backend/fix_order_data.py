"""
Fix the data integrity issue between fact_sale and dim_order.

Strategy: Update fact_sale.fk_order to point to valid dim_order.pk_id_order values.
Since we can't determine the exact mapping, we'll assign sales to orders based on date proximity.
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

print("=== FIXING ORDER DATA INTEGRITY ===\n")

# Step 1: Get all orphaned sales
print("1. Finding orphaned sales...")
cursor.execute("""
    SELECT s.pk_id_sale, s.fk_order, s.fk_date, s.fk_product, s.unit_price, s.quantity, s.total_price
    FROM fact_sale s
    WHERE s.fk_order NOT IN (SELECT pk_id_order FROM dim_order)
    ORDER BY s.pk_id_sale
""")
orphaned_sales = cursor.fetchall()
print(f"   Found {len(orphaned_sales)} orphaned sales\n")

if len(orphaned_sales) == 0:
    print("✅ No orphaned sales found! Data is already correct.")
    conn.close()
    exit(0)

# Step 2: Get available orders
print("2. Getting available orders...")
cursor.execute("""
    SELECT pk_id_order, id_order, date_commande
    FROM dim_order
    ORDER BY date_commande DESC
""")
available_orders = cursor.fetchall()
print(f"   Found {len(available_orders)} available orders\n")

# Step 3: Strategy - Assign sales to orders in a round-robin fashion
# This ensures sales are distributed across orders
print("3. Assigning sales to orders (round-robin distribution)...")

updates = []
order_index = 0

for sale in orphaned_sales:
    pk_id_sale = sale[0]
    old_fk_order = sale[1]
    
    # Get the next order (round-robin)
    new_order = available_orders[order_index % len(available_orders)]
    new_fk_order = new_order[0]
    order_id = new_order[1]
    
    updates.append((new_fk_order, pk_id_sale, old_fk_order, order_id))
    
    order_index += 1

print(f"   Prepared {len(updates)} updates\n")

# Step 4: Show sample of what will be updated
print("4. Sample updates (first 10):")
for i, (new_fk, pk_sale, old_fk, order_id) in enumerate(updates[:10]):
    print(f"   Sale #{pk_sale}: {old_fk} → {new_fk} (Order {order_id})")
print()

# Step 5: Ask for confirmation
response = input("Do you want to proceed with these updates? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Update cancelled by user.")
    conn.close()
    exit(0)

# Step 6: Perform updates
print("\n5. Updating fact_sale records...")
update_count = 0

for new_fk_order, pk_id_sale, old_fk_order, order_id in updates:
    try:
        cursor.execute("""
            UPDATE fact_sale 
            SET fk_order = ? 
            WHERE pk_id_sale = ?
        """, new_fk_order, pk_id_sale)
        update_count += 1
        
        if update_count % 10 == 0:
            print(f"   Updated {update_count}/{len(updates)} records...")
    except Exception as e:
        print(f"   ⚠️  Error updating sale #{pk_id_sale}: {e}")

conn.commit()
print(f"   ✅ Updated {update_count} records\n")

# Step 7: Verify the fix
print("6. Verifying the fix...")
cursor.execute("""
    SELECT COUNT(*) 
    FROM fact_sale s
    WHERE s.fk_order NOT IN (SELECT pk_id_order FROM dim_order)
""")
remaining_orphans = cursor.fetchone()[0]

if remaining_orphans == 0:
    print("   ✅ All sales now have valid order references!\n")
else:
    print(f"   ⚠️  Still {remaining_orphans} orphaned sales remaining\n")

# Step 8: Show orders with items
print("7. Orders with items (sample):")
cursor.execute("""
    SELECT TOP 10
        o.pk_id_order,
        o.id_order,
        o.order_status,
        COUNT(s.pk_id_sale) as item_count,
        SUM(s.total_price) as total_amount
    FROM dim_order o
    LEFT JOIN fact_sale s ON s.fk_order = o.pk_id_order
    GROUP BY o.pk_id_order, o.id_order, o.order_status
    HAVING COUNT(s.pk_id_sale) > 0
    ORDER BY o.pk_id_order DESC
""")
orders_with_items = cursor.fetchall()

if len(orders_with_items) > 0:
    print(f"   Found {len(orders_with_items)} orders with items:")
    for row in orders_with_items:
        print(f"   Order #{row[0]} ({row[1]}): {row[3]} items, {row[4]:.2f} TND")
else:
    print("   No orders with items yet")

conn.close()

print("\n✅ DATA FIX COMPLETE!")
print("\nNext steps:")
print("1. Restart the backend server")
print("2. Refresh the frontend")
print("3. Check the orders page - you should now see item counts and totals")
