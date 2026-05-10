"""
Routes Flask pour l'API CRM Odoo
Endpoints pour gérer les leads, opportunités, clients, etc.
"""

from flask import Blueprint, request, jsonify
from services.odoo_service import odoo_client
import logging

logger = logging.getLogger(__name__)

crm_bp = Blueprint('crm', __name__, url_prefix='/api/crm')


# ============================================================================
# LEADS / OPPORTUNITIES
# ============================================================================

@crm_bp.route('/leads', methods=['GET'])
def get_leads():
    """
    GET /api/crm/leads
    Récupérer la liste des leads/opportunités
    
    Query params:
        - limit: nombre max de résultats (défaut: 100)
        - offset: décalage pour pagination (défaut: 0)
        - stage_id: filtrer par étape
        - user_id: filtrer par vendeur
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        stage_id = request.args.get('stage_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        # Construire le domaine de recherche
        domain = [('type', '=', 'opportunity')]
        
        if stage_id:
            domain.append(('stage_id', '=', stage_id))
        if user_id:
            domain.append(('user_id', '=', user_id))
        
        leads = odoo_client.get_leads(domain=domain, limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'data': leads,
            'count': len(leads)
        })
    except Exception as e:
        logger.error(f"❌ Erreur get_leads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    """
    GET /api/crm/leads/:id
    Récupérer un lead spécifique
    """
    try:
        lead = odoo_client.get_lead_by_id(lead_id)
        
        if lead:
            return jsonify({'success': True, 'data': lead})
        else:
            return jsonify({'success': False, 'error': 'Lead not found'}), 404
    except Exception as e:
        logger.error(f"❌ Erreur get_lead: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/leads', methods=['POST'])
def create_lead():
    """
    POST /api/crm/leads
    Créer un nouveau lead/opportunité
    
    Body JSON:
    {
        "name": "Opportunité Test",
        "partner_id": 15,
        "expected_revenue": 10000,
        "probability": 75,
        "email_from": "client@example.com",
        "phone": "+216 12 345 678",
        "description": "Description de l'opportunité",
        "date_deadline": "2024-12-31"
    }
    """
    try:
        data = request.json
        
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        lead_id = odoo_client.create_lead(data)
        
        if lead_id:
            return jsonify({
                'success': True,
                'data': {'id': lead_id},
                'message': 'Lead created successfully'
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create lead'}), 500
    except Exception as e:
        logger.error(f"❌ Erreur create_lead: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/leads/<int:lead_id>', methods=['PUT'])
def update_lead(lead_id):
    """
    PUT /api/crm/leads/:id
    Mettre à jour un lead
    
    Body JSON: champs à mettre à jour
    """
    try:
        data = request.json
        success = odoo_client.update_lead(lead_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Lead not found'}), 404
    except Exception as e:
        logger.error(f"❌ Erreur update_lead: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    """
    DELETE /api/crm/leads/:id
    Supprimer un lead
    """
    try:
        success = odoo_client.delete_lead(lead_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Lead deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Lead not found'}), 404
    except Exception as e:
        logger.error(f"❌ Erreur delete_lead: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# STAGES
# ============================================================================

@crm_bp.route('/stages', methods=['GET'])
def get_stages():
    """
    GET /api/crm/stages
    Récupérer les étapes du pipeline CRM
    """
    try:
        stages = odoo_client.get_stages()
        return jsonify({'success': True, 'data': stages})
    except Exception as e:
        logger.error(f"❌ Erreur get_stages: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PARTNERS (Clients/Fournisseurs)
# ============================================================================

@crm_bp.route('/partners', methods=['GET'])
def get_partners():
    """
    GET /api/crm/partners
    Récupérer les partenaires
    
    Query params:
        - type: 'customer' ou 'supplier'
        - limit: nombre max de résultats
    """
    try:
        partner_type = request.args.get('type')
        limit = request.args.get('limit', 100, type=int)
        
        if partner_type == 'customer':
            partners = odoo_client.get_customers(limit=limit)
        elif partner_type == 'supplier':
            partners = odoo_client.get_suppliers(limit=limit)
        else:
            partners = odoo_client.get_partners(limit=limit)
        
        return jsonify({'success': True, 'data': partners})
    except Exception as e:
        logger.error(f"❌ Erreur get_partners: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/partners', methods=['POST'])
def create_partner():
    """
    POST /api/crm/partners
    Créer un nouveau partenaire (client/fournisseur)
    """
    try:
        data = request.json
        
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        partner_id = odoo_client.create_partner(data)
        
        if partner_id:
            return jsonify({
                'success': True,
                'data': {'id': partner_id},
                'message': 'Partner created successfully'
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create partner'}), 500
    except Exception as e:
        logger.error(f"❌ Erreur create_partner: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# USERS (Vendeurs)
# ============================================================================

@crm_bp.route('/users', methods=['GET'])
def get_users():
    """
    GET /api/crm/users
    Récupérer les utilisateurs (vendeurs)
    """
    try:
        users = odoo_client.get_users()
        return jsonify({'success': True, 'data': users})
    except Exception as e:
        logger.error(f"❌ Erreur get_users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ACTIVITIES
# ============================================================================

@crm_bp.route('/leads/<int:lead_id>/activities', methods=['GET'])
def get_activities(lead_id):
    """
    GET /api/crm/leads/:id/activities
    Récupérer les activités d'un lead
    """
    try:
        activities = odoo_client.get_activities(lead_id)
        return jsonify({'success': True, 'data': activities})
    except Exception as e:
        logger.error(f"❌ Erreur get_activities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crm_bp.route('/leads/<int:lead_id>/activities', methods=['POST'])
def create_activity(lead_id):
    """
    POST /api/crm/leads/:id/activities
    Créer une activité pour un lead
    """
    try:
        data = request.json
        activity_id = odoo_client.create_activity(lead_id, data)
        
        if activity_id:
            return jsonify({
                'success': True,
                'data': {'id': activity_id},
                'message': 'Activity created successfully'
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create activity'}), 500
    except Exception as e:
        logger.error(f"❌ Erreur create_activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@crm_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /api/crm/health
    Vérifier la connexion à Odoo
    """
    try:
        odoo_client.ensure_connection()
        return jsonify({
            'success': True,
            'message': 'Odoo connection OK',
            'odoo_host': odoo_client.host,
            'odoo_db': odoo_client.db
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
