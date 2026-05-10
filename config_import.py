# ============================================================================
# CONFIGURATION IMPORT SQL SERVER → ODOO CRM
# ============================================================================

# ────────────────────────────────────────────────────────────────────────────
# SQL SERVER CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────
SQL_CONFIG = {
    'server': 'localhost',  # Adresse du serveur SQL
    'database': 'dw_pi',  # Nom de la base de données
    'username': 'sa',  # Username SQL Server
    'password': 'VotreMotDePasse',  # Mot de passe SQL Server
    'driver': 'ODBC Driver 17 for SQL Server',  # Driver ODBC
}

# ────────────────────────────────────────────────────────────────────────────
# ODOO CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────
ODOO_CONFIG = {
    'url': 'http://localhost:8069',
    'database': 'sougui_crm',
    'username': 'hedir.zraga@esprit.tn',
    'password': 'Sougui@CEO2024',
}

# ────────────────────────────────────────────────────────────────────────────
# IMPORT LIMITS (pour les tests)
# ────────────────────────────────────────────────────────────────────────────
IMPORT_LIMITS = {
    'max_clients': 50,  # Nombre maximum de clients à importer (0 = illimité)
    'max_orders': 30,  # Nombre maximum de commandes à importer (0 = illimité)
}

# ────────────────────────────────────────────────────────────────────────────
# SQL QUERIES
# ────────────────────────────────────────────────────────────────────────────

# Requête pour extraire les clients
QUERY_CLIENTS = """
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

# Requête pour extraire les commandes
QUERY_ORDERS = """
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

# ────────────────────────────────────────────────────────────────────────────
# FIELD MAPPING
# ────────────────────────────────────────────────────────────────────────────

# Mapping des champs clients SQL Server → Odoo
CLIENT_FIELD_MAPPING = {
    'CustomerKey': 0,  # Index dans le résultat SQL
    'FirstName': 1,
    'LastName': 2,
    'EmailAddress': 3,
    'Phone': 4,
    'AddressLine1': 5,
    'City': 6,
    'StateProvinceName': 7,
    'PostalCode': 8,
    'CountryRegionName': 9,
}

# Mapping des champs commandes SQL Server → Odoo
ORDER_FIELD_MAPPING = {
    'SalesOrderNumber': 0,
    'CustomerKey': 1,
    'OrderDate': 2,
    'TotalAmount': 3,
    'ProductCount': 4,
}

# ────────────────────────────────────────────────────────────────────────────
# ODOO SETTINGS
# ────────────────────────────────────────────────────────────────────────────

# ID de l'étape "Gagné" dans le CRM (à ajuster selon votre configuration)
ODOO_STAGE_WON_ID = 4

# Probabilité par défaut pour les opportunités importées
DEFAULT_PROBABILITY = 100.0

# Tags à ajouter aux opportunités importées (IDs des tags Odoo)
DEFAULT_TAGS = []  # Ex: [1, 2, 3]

# ID de l'équipe de vente par défaut
DEFAULT_TEAM_ID = False  # False = pas d'équipe assignée

# ────────────────────────────────────────────────────────────────────────────
# ADVANCED OPTIONS
# ────────────────────────────────────────────────────────────────────────────

# Activer le mode verbose (affichage détaillé)
VERBOSE = True

# Activer le mode dry-run (simulation sans import réel)
DRY_RUN = False

# Ignorer les erreurs et continuer l'import
IGNORE_ERRORS = True

# Créer un log des imports
CREATE_LOG_FILE = True
LOG_FILE_PATH = 'import_log.txt'
