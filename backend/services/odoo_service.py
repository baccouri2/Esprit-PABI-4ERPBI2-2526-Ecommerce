"""
Service Odoo pour l'intégration CRM
Gère la connexion et les opérations CRUD sur Odoo via OdooRPC
"""

import odoorpc
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class OdooClient:
    """Client Odoo pour gérer les opérations CRM"""
    
    def __init__(self, host: str = 'localhost', port: int = 8069, 
                 db: str = 'sougui_crm', user: str = 'admin', 
                 password: str = 'admin'):
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password
        self.api = None
        
    def login(self):
        """Se connecter à Odoo"""
        try:
            if not self.api:
                # IMPORTANT: Utiliser ODOO (majuscules) au lieu de Odoo
                self.api = odoorpc.ODOO(self.host, port=self.port)
                self.api.login(self.db, self.user, self.password)
                logger.info(f"✅ Connexion Odoo réussie: {self.user}@{self.db}")
            return self.api
        except Exception as e:
            logger.error(f"❌ Erreur connexion Odoo: {e}")
            raise
    
    def ensure_connection(self):
        """S'assurer que la connexion est active"""
        if not self.api:
            self.login()
        return self.api
    
    # ========================================================================
    # LEADS / OPPORTUNITIES (crm.lead)
    # ========================================================================
    
    def get_leads(self, domain: Optional[List] = None, 
                  fields: Optional[List] = None, 
                  limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Récupérer les leads/opportunités
        
        Args:
            domain: Filtre Odoo (ex: [('type', '=', 'opportunity')])
            fields: Champs à récupérer
            limit: Nombre max de résultats
            offset: Décalage pour pagination
        """
        try:
            self.ensure_connection()
            Lead = self.api.env['crm.lead']
            
            if domain is None:
                domain = [('type', '=', 'opportunity')]
            
            if fields is None:
                fields = ['id', 'name', 'partner_id', 'expected_revenue', 
                         'probability', 'stage_id', 'user_id', 'date_deadline',
                         'email_from', 'phone', 'description', 'create_date']
            
            leads = Lead.search_read(domain, fields, limit=limit, offset=offset)
            return leads
        except Exception as e:
            logger.error(f"❌ Erreur get_leads: {e}")
            return []
    
    def get_lead_by_id(self, lead_id: int) -> Optional[Dict]:
        """Récupérer un lead par son ID"""
        try:
            self.ensure_connection()
            Lead = self.api.env['crm.lead']
            lead = Lead.browse(lead_id)
            
            if lead.exists():
                return {
                    'id': lead.id,
                    'name': lead.name,
                    'partner_id': [lead.partner_id.id, lead.partner_id.name] if lead.partner_id else False,
                    'expected_revenue': lead.expected_revenue,
                    'probability': lead.probability,
                    'stage_id': [lead.stage_id.id, lead.stage_id.name] if lead.stage_id else False,
                    'user_id': [lead.user_id.id, lead.user_id.name] if lead.user_id else False,
                    'email_from': lead.email_from,
                    'phone': lead.phone,
                    'description': lead.description,
                    'date_deadline': str(lead.date_deadline) if lead.date_deadline else None,
                    'create_date': str(lead.create_date),
                }
            return None
        except Exception as e:
            logger.error(f"❌ Erreur get_lead_by_id: {e}")
            return None
    
    def create_lead(self, data: Dict) -> Optional[int]:
        """
        Créer un nouveau lead/opportunité
        
        Args:
            data: Données du lead (name, partner_id, expected_revenue, etc.)
        """
        try:
            self.ensure_connection()
            Lead = self.api.env['crm.lead']
            
            lead_data = {
                'name': data.get('name'),
                'type': 'opportunity',  # Type: opportunité
                'partner_id': data.get('partner_id'),
                'expected_revenue': data.get('expected_revenue', 0.0),
                'probability': data.get('probability', 50.0),
                'email_from': data.get('email_from'),
                'phone': data.get('phone'),
                'description': data.get('description'),
                'date_deadline': data.get('date_deadline'),
            }
            
            # Supprimer les valeurs None
            lead_data = {k: v for k, v in lead_data.items() if v is not None}
            
            lead_id = Lead.create(lead_data)
            logger.info(f"✅ Lead créé: ID {lead_id}")
            return lead_id
        except Exception as e:
            logger.error(f"❌ Erreur create_lead: {e}")
            return None
    
    def update_lead(self, lead_id: int, data: Dict) -> bool:
        """Mettre à jour un lead"""
        try:
            self.ensure_connection()
            Lead = self.api.env['crm.lead']
            lead = Lead.browse(lead_id)
            
            if lead.exists():
                # Supprimer les valeurs None
                update_data = {k: v for k, v in data.items() if v is not None}
                lead.write(update_data)
                logger.info(f"✅ Lead {lead_id} mis à jour")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erreur update_lead: {e}")
            return False
    
    def delete_lead(self, lead_id: int) -> bool:
        """Supprimer un lead"""
        try:
            self.ensure_connection()
            Lead = self.api.env['crm.lead']
            lead = Lead.browse(lead_id)
            
            if lead.exists():
                lead.unlink()
                logger.info(f"✅ Lead {lead_id} supprimé")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erreur delete_lead: {e}")
            return False
    
    # ========================================================================
    # STAGES (crm.stage)
    # ========================================================================
    
    def get_stages(self) -> List[Dict]:
        """Récupérer les étapes du pipeline CRM"""
        try:
            self.ensure_connection()
            Stage = self.api.env['crm.stage']
            stages = Stage.search_read([], ['id', 'name', 'sequence', 'fold'])
            return stages
        except Exception as e:
            logger.error(f"❌ Erreur get_stages: {e}")
            return []
    
    # ========================================================================
    # PARTNERS (res.partner) - Clients/Fournisseurs
    # ========================================================================
    
    def get_partners(self, domain: Optional[List] = None, 
                     fields: Optional[List] = None, 
                     limit: int = 100) -> List[Dict]:
        """Récupérer les partenaires (clients/fournisseurs)"""
        try:
            self.ensure_connection()
            Partner = self.api.env['res.partner']
            
            if fields is None:
                fields = ['id', 'name', 'email', 'phone', 'mobile', 
                         'street', 'city', 'zip', 'customer_rank', 'supplier_rank']
            
            partners = Partner.search_read(domain or [], fields, limit=limit)
            return partners
        except Exception as e:
            logger.error(f"❌ Erreur get_partners: {e}")
            return []
    
    def get_customers(self, limit: int = 100) -> List[Dict]:
        """Récupérer uniquement les clients"""
        return self.get_partners(domain=[('customer_rank', '>', 0)], limit=limit)
    
    def get_suppliers(self, limit: int = 100) -> List[Dict]:
        """Récupérer uniquement les fournisseurs"""
        return self.get_partners(domain=[('supplier_rank', '>', 0)], limit=limit)
    
    def create_partner(self, data: Dict) -> Optional[int]:
        """Créer un nouveau partenaire"""
        try:
            self.ensure_connection()
            Partner = self.api.env['res.partner']
            
            partner_data = {
                'name': data.get('name'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'mobile': data.get('mobile'),
                'street': data.get('street'),
                'city': data.get('city'),
                'zip': data.get('zip'),
                'customer_rank': data.get('customer_rank', 1),
                'supplier_rank': data.get('supplier_rank', 0),
                'is_company': data.get('is_company', False),
            }
            
            partner_data = {k: v for k, v in partner_data.items() if v is not None}
            partner_id = Partner.create(partner_data)
            logger.info(f"✅ Partenaire créé: ID {partner_id}")
            return partner_id
        except Exception as e:
            logger.error(f"❌ Erreur create_partner: {e}")
            return None
    
    # ========================================================================
    # USERS (res.users) - Vendeurs
    # ========================================================================
    
    def get_users(self) -> List[Dict]:
        """Récupérer les utilisateurs (vendeurs)"""
        try:
            self.ensure_connection()
            User = self.api.env['res.users']
            users = User.search_read([], ['id', 'name', 'email'])
            return users
        except Exception as e:
            logger.error(f"❌ Erreur get_users: {e}")
            return []
    
    # ========================================================================
    # ACTIVITIES (mail.activity)
    # ========================================================================
    
    def get_activities(self, lead_id: int) -> List[Dict]:
        """Récupérer les activités d'un lead"""
        try:
            self.ensure_connection()
            Activity = self.api.env['mail.activity']
            activities = Activity.search_read(
                [('res_model', '=', 'crm.lead'), ('res_id', '=', lead_id)],
                ['id', 'activity_type_id', 'summary', 'date_deadline', 'user_id']
            )
            return activities
        except Exception as e:
            logger.error(f"❌ Erreur get_activities: {e}")
            return []
    
    def create_activity(self, lead_id: int, data: Dict) -> Optional[int]:
        """Créer une activité pour un lead"""
        try:
            self.ensure_connection()
            Activity = self.api.env['mail.activity']
            
            activity_data = {
                'res_model': 'crm.lead',
                'res_id': lead_id,
                'activity_type_id': data.get('activity_type_id', 1),  # 1 = Call
                'summary': data.get('summary'),
                'date_deadline': data.get('date_deadline'),
                'user_id': data.get('user_id'),
            }
            
            activity_id = Activity.create(activity_data)
            logger.info(f"✅ Activité créée: ID {activity_id}")
            return activity_id
        except Exception as e:
            logger.error(f"❌ Erreur create_activity: {e}")
            return None


# Instance globale du client Odoo
odoo_client = OdooClient()
