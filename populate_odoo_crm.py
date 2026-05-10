#!/usr/bin/env python3
"""
Script pour peupler Odoo CRM avec des données de test
Crée des clients et des opportunités pour tester l'intégration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.odoo_service import odoo_client

# Données de test
CLIENTS = [
    {
        'name': 'Entreprise Alpha SA',
        'email': 'contact@alpha.tn',
        'phone': '+216 71 123 456',
        'city': 'Tunis',
        'customer_rank': 1
    },
    {
        'name': 'Beta Solutions SARL',
        'email': 'info@beta.tn',
        'phone': '+216 98 765 432',
        'city': 'Sfax',
        'customer_rank': 1
    },
    {
        'name': 'Gamma Technologies',
        'email': 'contact@gamma.tn',
        'phone': '+216 22 345 678',
        'city': 'Sousse',
        'customer_rank': 1
    },
]

OPPORTUNITES = [
    {
        'name': 'Vente Logiciel CRM',
        'expected_revenue': 25000,
        'probability': 75,
        'description': 'Vente de solution CRM complète'
    },
    {
        'name': 'Formation Équipe Commerciale',
        'expected_revenue': 8000,
        'probability': 90,
        'description': 'Formation de 5 jours pour l\'équipe'
    },
    {
        'name': 'Maintenance Annuelle',
        'expected_revenue': 12000,
        'probability': 60,
        'description': 'Contrat de maintenance 12 mois'
    },
    {
        'name': 'Intégration Power BI',
        'expected_revenue': 15000,
        'probability': 50,
        'description': 'Intégration dashboards Power BI'
    },
    {
        'name': 'Développement Module Custom',
        'expected_revenue': 30000,
        'probability': 40,
        'description': 'Développement module spécifique'
    },
]

def main():
    print("\n" + "="*60)
    print("  🚀 Peuplement Odoo CRM avec Données de Test")
    print("="*60 + "\n")
    
    # Connexion
    try:
        odoo_client.login()
        print("✅ Connexion Odoo réussie\n")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        print("\n💡 Vérifiez que Odoo est démarré (START_ODOO.bat)")
        return
    
    # Créer les clients
    print("="*60)
    print("  📤 Création des Clients")
    print("="*60 + "\n")
    
    partner_ids = []
    for i, client in enumerate(CLIENTS, 1):
        print(f"[{i}/{len(CLIENTS)}] {client['name']}")
        partner_id = odoo_client.create_partner(client)
        if partner_id:
            partner_ids.append(partner_id)
            print(f"   ✅ Client créé (ID: {partner_id})\n")
        else:
            print(f"   ⚠️  Échec\n")
    
    # Créer les opportunités
    print("="*60)
    print("  📤 Création des Opportunités")
    print("="*60 + "\n")
    
    lead_ids = []
    for i, opp in enumerate(OPPORTUNITES, 1):
        # Assigner un client aléatoire
        if partner_ids:
            opp['partner_id'] = partner_ids[i % len(partner_ids)]
        
        print(f"[{i}/{len(OPPORTUNITES)}] {opp['name']}")
        print(f"   💰 Revenu: {opp['expected_revenue']} DT")
        print(f"   📈 Probabilité: {opp['probability']}%")
        
        lead_id = odoo_client.create_lead(opp)
        if lead_id:
            lead_ids.append(lead_id)
            print(f"   ✅ Opportunité créée (ID: {lead_id})\n")
        else:
            print(f"   ⚠️  Échec\n")
    
    # Résumé
    print("="*60)
    print("  ✅ RÉSUMÉ")
    print("="*60)
    print(f"\n📊 Clients créés: {len(partner_ids)}")
    print(f"📊 Opportunités créées: {len(lead_ids)}")
    
    total_revenue = sum(opp['expected_revenue'] for opp in OPPORTUNITES)
    print(f"💰 Revenu total potentiel: {total_revenue:,} DT")
    
    print(f"\n🌐 Accédez au CRM:")
    print(f"   - Odoo: http://localhost:8069/web#action=crm.crm_lead_all_leads")
    print(f"   - API: http://localhost:5000/api/crm/leads")
    print(f"   - Angular: Cliquez sur 'CRM Odoo' dans le menu\n")

if __name__ == "__main__":
    main()
