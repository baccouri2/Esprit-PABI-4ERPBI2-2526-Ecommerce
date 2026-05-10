{
    'name': 'SQL Server Clients Sync',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'Sync B2B and B2C clients from SQL Server to Odoo',
    'description': '''
        This module displays and syncs B2B and B2C clients from SQL Server database.
        Features:
        - View all SQL Server clients (B2B and B2C)
        - Sync clients to Odoo as partners
        - Automatic sync on demand
    ''',
    'author': 'Sougui Analytics',
    'depends': ['base', 'contacts', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/sql_client_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
