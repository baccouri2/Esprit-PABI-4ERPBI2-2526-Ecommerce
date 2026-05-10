#!/usr/bin/env python3
"""
Script pour créer automatiquement des opportunités dans Odoo CRM
"""

import xmlrpc.client
import sys

# Configuration Odoo
ODOO_URL = "http://localhost:8069"
ODOO_DB = "sougui_crm"  # Changez selon votre base de données
ODOO_USERNAME = "hedir.zraga@esprit.tn"
ODOO_PASSWORD = "Sougui@CEO2024"

# Données d'exemple pour les opportunités
SAMPLE_OPPORTUNITIES = [
    {
        'name': 'Vente Produit Sougui Premium',
        'partner_name': 'Entreprise Test SA',
        'email_from': 'contact@entreprise-test.tn',
        'phone': '+216 71 123 456',
        'expected_revenue': 15000.0,
        'probability': 60.0,
        'description': 'Client intéressé par nos produits premium',
    },
    {
        'name': 'Opportunité E-commerce',
        'partner_name': 'Digital Solutions SARL',
        'email_from': 'info@digitalsolutions.tn',
        'phone': '+216 98 765 432',
        'expected_revenue': 25000.0,
        'probability': 75.0,
        'description': 'Projet de plateforme e-commerce complète',
    },
    {
        'name': 'Contrat Maintenance Annuel',
        'partner_name': 'TechCorp Tunisia',
        'email_from': 'contact@techcorp.tn',
        'phone': '+216 71 987 654',
        'expected_revenue': 8000.0,
        'probability': 90.0,
        'description': 'Renouvellement contrat maintenance',
    },
    {
        'name': 'Formation CRM Odoo',
        'partner_name': 'Formation Plus',
        'email_from': 'formation@formationplus.tn',
        'phone': '+216 22 345 678',
        'expected_revenue': 5000.0,
        'probability': 50.0,
        'description': 'Formation équipe commerciale sur Odoo CRM',
    },
    {
        'name': 'Intégration Power BI',
        'partner_name': 'Analytics Pro',
        'email_from': 'contact@analyticspro.tn',
        'phone': '+216 55 123 789',
        'expected_revenue': 12000.0,
        'probability': 65.0,
        'description': 'Intégration dashboards Power BI avec système existant',
    },
]

def connect_odoo():
    """Se connecter à Odoo et retourner l'UID"""
    print("🔌 Connexion à Odoo...")
    print(f"   URL: {ODOO_URL}")
    print(f"   Database: {ODOO_DB}")
    print(f"   User: {ODOO_USERNAME}")
    print()
    
    try:
        # Connexion à l'API commune
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        
        # Authentification
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if uid:
            print(f"✅ Connexion réussie! UID: {uid}")
            return uid
        else:
            print("❌ Échec de l'authentification")
            print("\n💡 Vérifiez:")
            print("   1. Que Odoo est démarré (START_ODOO.bat)")
            print("   2. Que la base de données existe")
            print("   3. Que les identifiants sont corrects")
            return None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Assurez-vous que:")
        print("   1. Odoo est démarré: START_ODOO.bat")
        print("   2. L'URL est correcte: http://localhost:8069")
        return None

def create_partner(models, uid, partner_data):
    """Créer ou trouver un contact/partenaire"""
    try:
        # Chercher si le partenaire existe déjà
        partner_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search',
            [[['email', '=', partner_data['email']]]]
        )
        
        if partner_ids:
            print(f"   📋 Contact existant trouvé: {partner_data['name']}")
            return partner_ids[0]
        
        # Créer le partenaire
        partner_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'create',
            [{
                'name': partner_data['name'],
                'email': partner_data['email'],
                'phone': partner_data.get('phone', ''),
                'is_company': True,
            }]
        )
        
        print(f"   ✅ Contact créé: {partner_data['name']}")
        return partner_id
        
    except Exception as e:
        print(f"   ⚠️  Erreur création contact: {e}")
        return None

def create_opportunity(models, uid, opp_data):
    """Créer une opportunité dans le CRM"""
    try:
        # Créer ou trouver le partenaire
        partner_id = None
        if opp_data.get('partner_name'):
            partner_id = create_partner(models, uid, {
                'name': opp_data['partner_name'],
                'email': opp_data.get('email_from', ''),
                'phone': opp_data.get('phone', ''),
            })
        
        # Préparer les données de l'opportunité
        lead_data = {
            'name': opp_data['name'],
            'type': 'opportunity',  # Type: opportunité (pas lead)
            'email_from': opp_data.get('email_from', ''),
            'phone': opp_data.get('phone', ''),
            'expected_revenue': opp_data.get('expected_revenue', 0.0),
            'probability': opp_data.get('probability', 50.0),
            'description': opp_data.get('description', ''),
        }
        
        # Ajouter le partenaire si créé
        if partner_id:
            lead_data['partner_id'] = partner_id
        
        # Créer l'opportunité
        lead_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'crm.lead', 'create',
            [lead_data]
        )
        
        return lead_id
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("  🚀 Création d'Opportunités Odoo CRM")
    print("="*60 + "\n")
    
    # Connexion à Odoo
    uid = connect_odoo()
    if not uid:
        sys.exit(1)
    
    # Connexion au modèle d'objets
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    
    print("\n" + "="*60)
    print(f"  📊 Création de {len(SAMPLE_OPPORTUNITIES)} opportunités")
    print("="*60 + "\n")
    
    created_count = 0
    
    for i, opp in enumerate(SAMPLE_OPPORTUNITIES, 1):
        print(f"[{i}/{len(SAMPLE_OPPORTUNITIES)}] {opp['name']}")
        
        lead_id = create_opportunity(models, uid, opp)
        
        if lead_id:
            print(f"   ✅ Opportunité créée (ID: {lead_id})")
            print(f"   💰 Revenu attendu: {opp['expected_revenue']} DT")
            print(f"   📈 Probabilité: {opp['probability']}%")
            created_count += 1
        
        print()
    
    # Résumé
    print("="*60)
    print(f"  ✅ Résumé: {created_count}/{len(SAMPLE_OPPORTUNITIES)} opportunités créées")
    print("="*60)
    
    if created_count > 0:
        print(f"\n🌐 Accédez au CRM sur: {ODOO_URL}/web#action=crm.crm_lead_all_leads")
        print(f"\n📊 Vous pouvez maintenant:")
        print(f"   1. Voir les opportunités dans le pipeline")
        print(f"   2. Glisser-déposer entre les étapes")
        print(f"   3. Ajouter des activités (appels, réunions)")
        print(f"   4. Suivre les revenus et conversions")
    
    print()

if __name__ == "__main__":
    main()
