"""
Analyze the relationships between sales, clients (B2B/B2C), and claims in the database
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

print("=" * 80)
print("ANALYZING CLIENT AND CLAIM RELATIONSHIPS")
print("=" * 80)

# 1. Check dim_clientB2B schema
print("\n1. dim_clientB2B Schema:")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'dim_clientB2B'
    ORDER BY ORDINAL_POSITION
""")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}, Nullable={row[2]}")

# 2. Check dim_clientB2C schema
print("\n2. dim_clientB2C Schema:")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'dim_clientB2C'
    ORDER BY ORDINAL_POSITION
""")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}, Nullable={row[2]}")

# 3. Check dim_claim schema
print("\n3. dim_claim Schema:")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'dim_claim'
    ORDER BY ORDINAL_POSITION
""")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}, Nullable={row[2]}")

# 4. Check fact_sale foreign keys
print("\n4. fact_sale Foreign Keys to Clients and Claims:")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'fact_sale'
    AND COLUMN_NAME IN ('fk_clientB2B', 'fk_clientB2C', 'fk_claim')
    ORDER BY ORDINAL_POSITION
""")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]}, Nullable={row[2]}")

# 5. Sample B2B clients
print("\n5. Sample B2B Clients (Top 10):")
cursor.execute("SELECT TOP 10 * FROM dim_clientB2B")
for row in cursor.fetchall():
    print(f"   ID: {row[0]}, MF: {row[1]}, Company: {row[2]}, Date: {row[3]}")

# 6. Sample B2C clients
print("\n6. Sample B2C Clients (Top 10):")
cursor.execute("SELECT TOP 10 * FROM dim_clientB2C")
for row in cursor.fetchall():
    print(f"   ID: {row[0]}, Name: {row[1]} {row[2]}, Date: {row[3]}")

# 7. Sample claims
print("\n7. Sample Claims (Top 10):")
cursor.execute("SELECT TOP 10 * FROM dim_claim")
for row in cursor.fetchall():
    print(f"   {row}")

# 8. Sales with B2B clients
print("\n8. Sales with B2B Clients:")
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(DISTINCT fk_clientB2B) as unique_clients
    FROM fact_sale
    WHERE fk_clientB2B IS NOT NULL
""")
row = cursor.fetchone()
print(f"   Total sales with B2B clients: {row[0]}")
print(f"   Unique B2B clients: {row[1]}")

# 9. Sales with B2C clients
print("\n9. Sales with B2C Clients:")
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(DISTINCT fk_clientB2C) as unique_clients
    FROM fact_sale
    WHERE fk_clientB2C IS NOT NULL
""")
row = cursor.fetchone()
print(f"   Total sales with B2C clients: {row[0]}")
print(f"   Unique B2C clients: {row[1]}")

# 10. Sales with claims
print("\n10. Sales with Claims:")
cursor.execute("""
    SELECT COUNT(*) as total,
           COUNT(DISTINCT fk_claim) as unique_claims
    FROM fact_sale
    WHERE fk_claim IS NOT NULL
""")
row = cursor.fetchone()
print(f"   Total sales with claims: {row[0]}")
print(f"   Unique claims: {row[1]}")

# 11. Sales distribution
print("\n11. Sales Distribution:")
cursor.execute("""
    SELECT 
        COUNT(*) as total_sales,
        SUM(CASE WHEN fk_clientB2B IS NOT NULL THEN 1 ELSE 0 END) as with_b2b,
        SUM(CASE WHEN fk_clientB2C IS NOT NULL THEN 1 ELSE 0 END) as with_b2c,
        SUM(CASE WHEN fk_claim IS NOT NULL THEN 1 ELSE 0 END) as with_claim,
        SUM(CASE WHEN fk_clientB2B IS NULL AND fk_clientB2C IS NULL THEN 1 ELSE 0 END) as no_client
    FROM fact_sale
""")
row = cursor.fetchone()
print(f"   Total sales: {row[0]}")
print(f"   With B2B client: {row[1]} ({row[1]*100/row[0]:.1f}%)")
print(f"   With B2C client: {row[2]} ({row[2]*100/row[0]:.1f}%)")
print(f"   With claim: {row[3]} ({row[3]*100/row[0]:.1f}%)")
print(f"   No client: {row[4]} ({row[4]*100/row[0]:.1f}%)")

# 12. Sample sales with client info
print("\n12. Sample Sales with Client Information:")
cursor.execute("""
    SELECT TOP 5
        s.pk_id_sale,
        o.id_order,
        b2b.company as b2b_company,
        b2b.MF as b2b_mf,
        CONCAT(b2c.first_name, ' ', b2c.last_name) as b2c_name,
        s.total_price
    FROM fact_sale s
    LEFT JOIN dim_order o ON s.fk_order = o.pk_id_order
    LEFT JOIN dim_clientB2B b2b ON s.fk_clientB2B = b2b.pk_id_client
    LEFT JOIN dim_clientB2C b2c ON s.fk_clientB2C = b2c.pk_id_client
    WHERE s.fk_clientB2B IS NOT NULL OR s.fk_clientB2C IS NOT NULL
""")
for row in cursor.fetchall():
    client_info = row[2] if row[2] else row[4]
    print(f"   Sale #{row[0]}, Order: {row[1]}, Client: {client_info}, Total: {float(row[5]):.2f} TND")

# 13. Check if sales table has client info
print("\n13. Checking 'sales' table from etl (3).sql:")
try:
    cursor.execute("""
        SELECT TOP 5
            Numero_de_commande,
            Prenom__Facturation,
            NOM_DE_FAMILLE__FACTURATION,
            Ville__Facturation
        FROM sales
    """)
    print("   Found 'sales' table with client information:")
    for row in cursor.fetchall():
        print(f"   Order: {row[0]}, Client: {row[1]} {row[2]}, City: {row[3]}")
except Exception as e:
    print(f"   'sales' table not found or error: {e}")

conn.close()

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
