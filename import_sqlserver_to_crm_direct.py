#!/usr/bin/env python3
"""
Script pour importer les données depuis SQL Server vers la base de données CRM Odoo (PostgreSQL)
Import direct dans les tables PostgreSQL pour plus de performance
"""

import pyodbc
import psycopg2
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION SQL SERVER (Source)
# ============================================================================
SQL_SERVER = 'localhost'
SQL_DATABASE = 'dw_pi'
SQL_USERNAME = 'sa'
SQL_PASSWORD = 'reallyStrongPwd123'  # CHANGEZ ICI

# ============================================================================
# CONFIGURATION POSTGRESQL ODOO (Destination)
# ============================================================================
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DATABASE = 'sougui_crm'  # Nom de votre base Odoo
PG_USERNAME = 'odoo'
PG_PASSWORD = 'odoo'

# ============================================================================
# CONNEXIONS
# ============================================================================
def connect_sqlserver():
    """Se connecter à SQL Server"""
    print("🔌 Connexion à SQL Server...")
    print(f"   Serveur: {SQL_SERVER}")
    print(f"   Base: {SQL_DATABASE}")
    
    try:
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SQL_SERVER};'
            f'DATABASE={SQL_DATABASE};'
            f'UID={SQL_USERNAME};'
            f'PWD={SQL_PASSWORD}'
        )
        conn = pyodbc.connect(conn_str)
        print("✅ Connexion SQL Server réussie!\n")
        return conn
    except Exception as e:
        print(f"❌ Erreur SQL Server: {e}\n")
        return None

def connect_postgresql():
    """Se connecter à PostgreSQL Odoo"""
    print("🔌 Connexion à PostgreSQL Odoo...")
    print(f"   Host: {PG_HOST}")
    print(f"   Database: {PG_DATABASE}")
    
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USERNAME,
            password=PG_PASSWORD
        )
        print("✅ Connexion PostgreSQL réussie!\n")
        return conn
    except Exception as e:
        print(f"❌ Erreur PostgreSQL: {e}\n")
        return None

# ============================================================================
# EXTRACTION SQL SERVER
# ============================================================================
def extract_clients(sql_conn):
    """Extraire les clients depuis SQL Server"""
    print("📊 Extraction des clients depuis SQL Server...")
    
    try:
        cursor = sql_conn.cursor()
        query = """
        SELECT TOP 50
            CustomerKey,
            FirstName,
            LastName,
            EmailAddress,
            Phone,
            AddressLine1,
            City,
            PostalCode
        FROM DimCustomer
        WHERE EmailAddress IS NOT NULL
        ORDER BY CustomerKey
        """
        cursor.execute(query)
        clients = cursor.fetchall()
        print(f"✅ {len(clients)} clients extraits\n")
        return clients
    except Exception as e:
        print(f"❌ Erreur extraction: {e}\n")
        return []

def extract_orders(sql_conn):
    """Extraire les commandes depuis SQL Server"""
    print("📊 Extraction des commandes depuis SQL Server...")
    
    try:
        cursor = sql_conn.cursor()
        query = """
        SELECT TOP 30
            f.SalesOrderNumber,
            f.CustomerKey,
            f.OrderDate,
            SUM(f.SalesAmount) as TotalAmount
        FROM FactInternetSales f
        GROUP BY f.SalesOrderNumber, f.CustomerKey, f.OrderDate
        ORDER BY f.OrderDate DESC
        """
        cursor.execute(query)
        orders = cursor.fetchall()
        print(f"✅ {len(orders)} commandes extraites\n")
        return orders
    except Exception as e:
        print(f"❌ Erreur extraction: {e}\n")
        return []

# ============================================================================
# IMPORT POSTGRESQL
# ============================================================================
def import_clients_to_pg(pg_conn, clients):
    """Importer les clients dans PostgreSQL Odoo"""
    print("📤 Import des clients dans PostgreSQL Odoo...\n")
    
    cursor = pg_conn.cursor()
    imported = 0
    client_mapping = {}
    
    for i, client in enumerate(clients, 1):
        try:
            customer_key = client[0]
            first_name = client[1] or ''
            last_name = client[2] or ''
            email = client[3] or ''
            phone = client[4] or ''
            street = client[5] or ''
            city = client[6] or ''
            zip_code = client[7] or ''
            
            name = f"{first_name} {last_name}".strip()
            
            # Vérifier si le client existe déjà
            cursor.execute(
                "SELECT id FROM res_partner WHERE email = %s",
                (email,)
            )
            existing = cursor.fetchone()
            
            if existing:
                partner_id = existing[0]
                print(f"[{i}/{len(clients)}] {name} - Existe déjà (ID: {partner_id})")
            else:
                # Insérer le nouveau client
                cursor.execute("""
                    INSERT INTO res_partner 
                    (name, email, phone, street, city, zip, customer_rank, is_company, 
                     create_date, write_date, active)
                    VALUES (%s, %s, %s, %s, %s, %s, 1, false, NOW(), NOW(), true)
                    RETURNING id
                """, (name, email, phone, street, city, zip_code))
                
                partner_id = cursor.fetchone()[0]
                pg_conn.commit()
                
                print(f"[{i}/{len(clients)}] {name} - ✅ Importé (ID: {partner_id})")
                imported += 1
            
            client_mapping[customer_key] = partner_id
            
        except Exception as e:
            print(f"[{i}/{len(clients)}] ⚠️  Erreur: {e}")
            pg_conn.rollback()
    
    print(f"\n✅ {imported} nouveaux clients importés\n")
    return client_mapping

def import_orders_to_pg(pg_conn, orders, client_mapping):
    """Importer les commandes comme opportunités dans PostgreSQL Odoo"""
    print("📤 Import des opportunités dans PostgreSQL Odoo...\n")
    
    cursor = pg_conn.cursor()
    imported = 0
    
    # Récupérer l'ID de l'étape "Gagné" (stage_id)
    cursor.execute("""
        SELECT id FROM crm_stage 
        WHERE name ILIKE '%gagn%' OR name ILIKE '%won%'
        LIMIT 1
    """)
    stage_result = cursor.fetchone()
    stage_id = stage_result[0] if stage_result else 1
    
    for i, order in enumerate(orders, 1):
        try:
            order_number = order[0]
            customer_key = order[1]
            order_date = order[2]
            total_amount = float(order[3])
            
            # Trouver le partner_id
            partner_id = client_mapping.get(customer_key)
            
            if not partner_id:
                print(f"[{i}/{len(orders)}] Commande {order_number} - ⚠️  Client non trouvé")
                continue
            
            # Vérifier si l'opportunité existe déjà
            cursor.execute(
                "SELECT id FROM crm_lead WHERE name = %s",
                (f"Commande {order_number}",)
            )
            existing = cursor.fetchone()
            
            if existing:
                print(f"[{i}/{len(orders)}] Commande {order_number} - Existe déjà")
                continue
            
            # Insérer l'opportunité
            cursor.execute("""
                INSERT INTO crm_lead 
                (name, partner_id, type, expected_revenue, probability, stage_id,
                 active, create_date, write_date, date_deadline)
                VALUES (%s, %s, 'opportunity', %s, 100.0, %s, true, NOW(), NOW(), %s)
                RETURNING id
            """, (f"Commande {order_number}", partner_id, total_amount, stage_id, order_date))
            
            lead_id = cursor.fetchone()[0]
            pg_conn.commit()
            
            print(f"[{i}/{len(orders)}] Commande {order_number} - ✅ Importée (ID: {lead_id}, {total_amount:.2f} DT)")
            imported += 1
            
        except Exception as e:
            print(f"[{i}/{len(orders)}] ⚠️  Erreur: {e}")
            pg_conn.rollback()
    
    print(f"\n✅ {imported} nouvelles opportunités importées\n")
    return imported

# ============================================================================
# MAIN
# ============================================================================
def main():
    print("\n" + "="*70)
    print("  🔄 Import SQL Server → PostgreSQL Odoo CRM")
    print("="*70 + "\n")
    
    # Connexions
    sql_conn = connect_sqlserver()
    if not sql_conn:
        sys.exit(1)
    
    pg_conn = connect_postgresql()
    if not pg_conn:
        sys.exit(1)
    
    # Extraction
    print("="*70)
    print("  📥 EXTRACTION DES DONNÉES")
    print("="*70 + "\n")
    
    clients = extract_clients(sql_conn)
    orders = extract_orders(sql_conn)
    
    if not clients:
        print("❌ Aucun client extrait. Arrêt.")
        sys.exit(1)
    
    # Import
    print("="*70)
    print("  📤 IMPORT DANS ODOO")
    print("="*70 + "\n")
    
    client_mapping = import_clients_to_pg(pg_conn, clients)
    imported_opps = import_orders_to_pg(pg_conn, orders, client_mapping)
    
    # Résumé
    print("="*70)
    print("  ✅ RÉSUMÉ")
    print("="*70)
    print(f"\n📊 Clients: {len(client_mapping)} mappés")
    print(f"📊 Opportunités: {imported_opps} importées")
    
    total_revenue = sum(float(order[3]) for order in orders)
    print(f"💰 Revenu total: {total_revenue:,.2f} DT")
    
    print(f"\n🌐 Accédez au CRM: http://localhost:8069/web#action=crm.crm_lead_all_leads\n")
    
    # Fermeture
    sql_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    main()
