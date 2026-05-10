#!/usr/bin/env python3
"""
Script pour importer les données depuis SQL Server vers Odoo CRM
Importe : Clients, Contacts, Opportunités
"""

import pyodbc
import xmlrpc.client
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION SQL SERVER
# ============================================================================
SQL_SERVER = 'localhost'  # ou l'adresse de votre serveur
SQL_DATABASE = 'dw_pi'  # Nom de votre base de données
SQL_USERNAME = 'sa'  # Votre username SQL Server
SQL_PASSWORD = 'votre_mot_de_passe'  # Votre mot de passe SQL Server

# ============================================================================
# CONFIGURATION ODOO
# ============================================================================
ODOO_URL = "http://localhost:8069"
ODOO_DB = "sougui_crm"
ODOO_USERNAME = "hedir.zraga@esprit.tn"
ODOO_PASSWORD = "Sougui@CEO2024"

# ============================================================================
# CONNEXION SQL SERVER
# ============================================================================
def connect_sqlserver():
    """Se connecter à SQL Server"""
    print("🔌 Connexion à SQL Server...")
    print(f"   Serveur: {SQL_SERVER}")
    print(f"   Base de données: {SQL_DATABASE}")
    print()
    
    try:
        # Chaîne de connexion SQL Server
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SQL_SERVER};'
            f'DATABASE={SQL_DATABASE};'
            f'UID={SQL_USERNAME};'
            f'PWD={SQL_PASSWORD}'
        )
        
        conn = pyodbc.connect(conn_str)
        print("✅ Connexion SQL Server réussie!")
        return conn
        
    except Exception as e:
        print(f"❌ Erreur de connexion SQL Server: {e}")
        print("\n💡 Vérifiez:")
        print("   1. Que SQL Server est démarré")
        print("   2. Que les identifiants sont corrects")
        print("   3. Que le driver ODBC est installé")
        return None

# ============================================================================
# CONNEXION ODOO
# ============================================================================
def connect_odoo():
    """Se connecter à Odoo"""
    print("\n🔌 Connexion à Odoo...")
    print(f"   URL: {ODOO_URL}")
    print(f"   Database: {ODOO_DB}")
    print(f"   User: {ODOO_USERNAME}")
    print()
    
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if uid:
            print(f"✅ Connexion Odoo réussie! UID: {uid}")
            models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
            return uid, models
        else:
            print("❌ Échec de l'authentification Odoo")
            return None, None
            
    except Exception as e:
        print(f"❌ Erreur de connexion Odoo: {e}")
        return None, None

# ============================================================================
# EXTRACTION DES DONNÉES SQL SERVER
# ============================================================================
def extract_clients(conn):
    """Extraire les clients depuis SQL Server"""
    print("\n📊 Extraction des clients depuis SQL Server...")
    
    try:
        cursor = conn.cursor()
        
        # Requête pour extraire les clients
        query = """
        SELECT DISTINCT
            CustomerKey,
            FirstName,
            LastName,
            EmailAddress,
            Phone,
            AddressLine1,
            City,
            StateProvinceName,
            PostalCode,
            CountryRegionName
        FROM DimCustomer
        WHERE EmailAddress IS NOT NULL
        ORDER BY CustomerKey
        """
        
        cursor.execute(query)
        clients = cursor.fetchall()
        
        print(f"✅ {len(clients)} clients extraits")
        return clients
        
    except Exception as e:
        print(f"❌ Erreur extraction clients: {e}")
        return []

def extract_orders(conn):
    """Extraire les commandes depuis SQL Server"""
    print("\n📊 Extraction des commandes depuis SQL Server...")
    
    try:
        cursor = conn.cursor()
        
        # Requête pour extraire les commandes récentes
        query = """
        SELECT TOP 100
            f.SalesOrderNumber,
            f.CustomerKey,
            f.OrderDate,
            SUM(f.SalesAmount) as TotalAmount,
            COUNT(DISTINCT f.ProductKey) as ProductCount
        FROM FactInternetSales f
        GROUP BY f.SalesOrderNumber, f.CustomerKey, f.OrderDate
        ORDER BY f.OrderDate DESC
        """
        
        cursor.execute(query)
        orders = cursor.fetchall()
        
        print(f"✅ {len(orders)} commandes extraites")
        return orders
        
    except Exception as e:
        print(f"❌ Erreur extraction commandes: {e}")
        return []

# ============================================================================
# IMPORT DANS ODOO
# ============================================================================
def import_client_to_odoo(models, uid, client_data):
    """Importer un client dans Odoo"""
    try:
        # Vérifier si le client existe déjà (par email)
        email = client_data[3] if client_data[3] else ''
        
        if email:
            existing = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.partner', 'search',
                [[['email', '=', email]]]
            )
            
            if existing:
                return existing[0]  # Retourner l'ID existant
        
        # Préparer les données du contact
        partner_data = {
            'name': f"{client_data[1]} {client_data[2]}".strip(),
            'email': email,
            'phone': client_data[4] if client_data[4] else '',
            'street': client_data[5] if client_data[5] else '',
            'city': client_data[6] if client_data[6] else '',
            'state_id': False,  # À mapper si nécessaire
            'zip': client_data[8] if client_data[8] else '',
            'country_id': False,  # À mapper si nécessaire
            'customer_rank': 1,  # Marquer comme client
            'is_company': False,
        }
        
        # Créer le contact
        partner_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'create',
            [partner_data]
        )
        
        return partner_id
        
    except Exception as e:
        print(f"   ⚠️  Erreur import client: {e}")
        return None

def import_order_as_opportunity(models, uid, order_data, partner_id):
    """Importer une commande comme opportunité dans le CRM"""
    try:
        # Vérifier si l'opportunité existe déjà
        order_number = order_data[0]
        
        existing = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'crm.lead', 'search',
            [[['name', '=', f"Commande {order_number}"]]]
        )
        
        if existing:
            return existing[0]
        
        # Préparer les données de l'opportunité
        lead_data = {
            'name': f"Commande {order_number}",
            'partner_id': partner_id,
            'type': 'opportunity',
            'expected_revenue': float(order_data[3]),  # TotalAmount
            'probability': 100.0,  # Commande déjà passée = 100%
            'stage_id': 4,  # Étape "Gagné" (à ajuster selon votre config)
            'description': f"Commande importée depuis SQL Server\n"
                          f"Nombre de produits: {order_data[4]}\n"
                          f"Date: {order_data[2]}",
            'date_deadline': order_data[2] if order_data[2] else False,
        }
        
        # Créer l'opportunité
        lead_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'crm.lead', 'create',
            [lead_data]
        )
        
        return lead_id
        
    except Exception as e:
        print(f"   ⚠️  Erreur import opportunité: {e}")
        return None

# ============================================================================
# PROCESSUS PRINCIPAL
# ============================================================================
def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print("  🔄 Import SQL Server → Odoo CRM")
    print("="*70 + "\n")
    
    # Connexion SQL Server
    sql_conn = connect_sqlserver()
    if not sql_conn:
        sys.exit(1)
    
    # Connexion Odoo
    uid, models = connect_odoo()
    if not uid or not models:
        sys.exit(1)
    
    # Extraction des données
    print("\n" + "="*70)
    print("  📥 EXTRACTION DES DONNÉES")
    print("="*70)
    
    clients = extract_clients(sql_conn)
    orders = extract_orders(sql_conn)
    
    # Import des clients
    print("\n" + "="*70)
    print("  📤 IMPORT DES CLIENTS DANS ODOO")
    print("="*70 + "\n")
    
    client_mapping = {}  # Mapping CustomerKey → partner_id
    imported_clients = 0
    
    for i, client in enumerate(clients, 1):
        customer_key = client[0]
        name = f"{client[1]} {client[2]}".strip()
        
        print(f"[{i}/{len(clients)}] {name}")
        
        partner_id = import_client_to_odoo(models, uid, client)
        
        if partner_id:
            client_mapping[customer_key] = partner_id
            print(f"   ✅ Client importé (ID: {partner_id})")
            imported_clients += 1
        
        # Limiter à 50 clients pour le test
        if i >= 50:
            print(f"\n⚠️  Limite de 50 clients atteinte (test)")
            break
    
    # Import des commandes comme opportunités
    print("\n" + "="*70)
    print("  📤 IMPORT DES COMMANDES COMME OPPORTUNITÉS")
    print("="*70 + "\n")
    
    imported_opportunities = 0
    
    for i, order in enumerate(orders, 1):
        order_number = order[0]
        customer_key = order[1]
        amount = order[3]
        
        print(f"[{i}/{len(orders)}] Commande {order_number} - {amount:.2f} DT")
        
        # Trouver le partner_id correspondant
        partner_id = client_mapping.get(customer_key)
        
        if not partner_id:
            print(f"   ⚠️  Client non trouvé (CustomerKey: {customer_key})")
            continue
        
        lead_id = import_order_as_opportunity(models, uid, order, partner_id)
        
        if lead_id:
            print(f"   ✅ Opportunité créée (ID: {lead_id})")
            imported_opportunities += 1
        
        # Limiter à 30 opportunités pour le test
        if i >= 30:
            print(f"\n⚠️  Limite de 30 opportunités atteinte (test)")
            break
    
    # Résumé
    print("\n" + "="*70)
    print("  ✅ RÉSUMÉ DE L'IMPORT")
    print("="*70)
    print(f"\n📊 Clients:")
    print(f"   - Extraits: {len(clients)}")
    print(f"   - Importés: {imported_clients}")
    
    print(f"\n📊 Opportunités:")
    print(f"   - Commandes extraites: {len(orders)}")
    print(f"   - Opportunités créées: {imported_opportunities}")
    
    total_revenue = sum(order[3] for order in orders[:30])
    print(f"\n💰 Revenu total importé: {total_revenue:,.2f} DT")
    
    print(f"\n🌐 Accédez au CRM: {ODOO_URL}/web#action=crm.crm_lead_all_leads")
    print()
    
    # Fermer la connexion SQL Server
    sql_conn.close()

if __name__ == "__main__":
    main()
