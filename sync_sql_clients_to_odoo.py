#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync SQL Server Clients to Odoo
Fetches B2B and B2C clients from SQL Server and creates them as partners in Odoo
"""

import pyodbc
import xmlrpc.client
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SQL_SERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'HEDIRE\\MSSQLSERVER05',
    'database': 'dw_pi',
    'trusted_connection': True,
}

ODOO_CONFIG = {
    'url': 'http://localhost:8069',
    'db': 'sougui_crm',
    'username': 'admin',
    'password': 'admin',
}


class SQLClientSyncer:
    def __init__(self):
        self.sql_conn = None
        self.odoo_uid = None
        self.odoo_models = None
        self.common = None
        
    def connect_sql_server(self):
        """Connect to SQL Server"""
        try:
            conn_str = (
                f"DRIVER={SQL_SERVER_CONFIG['driver']};"
                f"SERVER={SQL_SERVER_CONFIG['server']};"
                f"DATABASE={SQL_SERVER_CONFIG['database']};"
                f"Trusted_Connection={'yes' if SQL_SERVER_CONFIG['trusted_connection'] else 'no'};"
            )
            self.sql_conn = pyodbc.connect(conn_str, timeout=15)
            logger.info('✓ Connected to SQL Server')
            return True
        except Exception as e:
            logger.error(f'✗ Failed to connect to SQL Server: {str(e)}')
            return False
    
    def connect_odoo(self):
        """Connect to Odoo"""
        try:
            self.common = xmlrpc.client.ServerProxy(f'{ODOO_CONFIG["url"]}/xmlrpc/2/common')
            self.odoo_uid = self.common.authenticate(
                ODOO_CONFIG['db'],
                ODOO_CONFIG['username'],
                ODOO_CONFIG['password'],
                {}
            )
            
            if not self.odoo_uid:
                logger.error('✗ Odoo authentication failed')
                return False
            
            self.odoo_models = xmlrpc.client.ServerProxy(f'{ODOO_CONFIG["url"]}/xmlrpc/2/object')
            logger.info(f'✓ Connected to Odoo (UID: {self.odoo_uid})')
            return True
        except Exception as e:
            logger.error(f'✗ Failed to connect to Odoo: {str(e)}')
            return False
    
    def fetch_sql_clients(self):
        """Fetch all clients from SQL Server"""
        try:
            cursor = self.sql_conn.cursor()
            clients = []
            
            # Fetch B2B clients
            logger.info('Fetching B2B clients from SQL Server...')
            cursor.execute("""
                SELECT
                    b.pk_id_client,
                    b.MF,
                    b.company,
                    b.date_participation,
                    COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2b b
                LEFT JOIN fact_sale s ON s.fk_clientB2B = b.pk_id_client
                GROUP BY b.pk_id_client, b.MF, b.company, b.date_participation
                ORDER BY b.pk_id_client
            """)
            
            for row in cursor.fetchall():
                clients.append({
                    'type': 'b2b',
                    'sql_id': row[0],
                    'mf': row[1],
                    'company': row[2],
                    'date_participation': row[3],
                    'order_count': row[4],
                })
            
            logger.info(f'  Found {len([c for c in clients if c["type"] == "b2b"])} B2B clients')
            
            # Fetch B2C clients
            logger.info('Fetching B2C clients from SQL Server...')
            cursor.execute("""
                SELECT
                    b.pk_id_client,
                    b.first_name,
                    b.last_name,
                    b.date_participation,
                    COUNT(s.pk_id_sale) AS order_count
                FROM dim_clientb2c b
                LEFT JOIN fact_sale s ON s.fk_clientB2C = b.pk_id_client
                GROUP BY b.pk_id_client, b.first_name, b.last_name, b.date_participation
                ORDER BY b.pk_id_client
            """)
            
            for row in cursor.fetchall():
                clients.append({
                    'type': 'b2c',
                    'sql_id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'date_participation': row[3],
                    'order_count': row[4],
                })
            
            logger.info(f'  Found {len([c for c in clients if c["type"] == "b2c"])} B2C clients')
            logger.info(f'✓ Total: {len(clients)} clients')
            
            return clients
        except Exception as e:
            logger.error(f'✗ Error fetching SQL clients: {str(e)}')
            return []
    
    def sync_to_odoo(self, clients):
        """Sync clients to Odoo as partners"""
        synced = 0
        failed = 0
        
        for client in clients:
            try:
                # Prepare partner data
                partner_data = {}
                
                if client['type'] == 'b2b':
                    partner_data = {
                        'name': client['company'],
                        'is_company': True,
                        'vat': client['mf'],
                        'type': 'contact',
                    }
                else:
                    partner_data = {
                        'name': f"{client['first_name']} {client['last_name']}",
                        'is_company': False,
                        'type': 'contact',
                    }
                
                # Check if partner already exists
                existing = self.odoo_models.execute_kw(
                    ODOO_CONFIG['db'],
                    self.odoo_uid,
                    ODOO_CONFIG['password'],
                    'res.partner',
                    'search',
                    [[('name', '=', partner_data['name'])]]
                )
                
                if existing:
                    logger.info(f'  ⊘ Partner "{partner_data["name"]}" already exists (ID: {existing[0]})')
                    continue
                
                # Create partner
                partner_id = self.odoo_models.execute_kw(
                    ODOO_CONFIG['db'],
                    self.odoo_uid,
                    ODOO_CONFIG['password'],
                    'res.partner',
                    'create',
                    [partner_data]
                )
                
                logger.info(f'  ✓ Created partner "{partner_data["name"]}" (ID: {partner_id})')
                synced += 1
                
            except Exception as e:
                logger.error(f'  ✗ Failed to sync "{client.get("company", client.get("first_name", "Unknown"))}": {str(e)}')
                failed += 1
        
        return synced, failed
    
    def run(self):
        """Run the sync process"""
        logger.info('=' * 60)
        logger.info('SQL Server Clients → Odoo Sync')
        logger.info('=' * 60)
        
        # Connect to SQL Server
        if not self.connect_sql_server():
            return False
        
        # Connect to Odoo
        if not self.connect_odoo():
            return False
        
        # Fetch clients
        clients = self.fetch_sql_clients()
        if not clients:
            logger.warning('No clients found to sync')
            return False
        
        # Sync to Odoo
        logger.info('\nSyncing clients to Odoo...')
        synced, failed = self.sync_to_odoo(clients)
        
        # Summary
        logger.info('\n' + '=' * 60)
        logger.info('Sync Summary')
        logger.info('=' * 60)
        logger.info(f'Total clients: {len(clients)}')
        logger.info(f'Successfully synced: {synced}')
        logger.info(f'Failed: {failed}')
        logger.info(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        logger.info('=' * 60)
        
        # Close connections
        if self.sql_conn:
            self.sql_conn.close()
        
        return True


if __name__ == '__main__':
    syncer = SQLClientSyncer()
    success = syncer.run()
    exit(0 if success else 1)
