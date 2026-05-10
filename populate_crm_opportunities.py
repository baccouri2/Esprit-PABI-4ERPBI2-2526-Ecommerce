#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peupler le CRM Odoo local avec des opportunités de test
Pour avoir un contenu similaire à la version externe
"""

import odoorpc
from datetime import datetime, timedelta
import random

print("========================================")
print("  Peuplement CRM avec Opportunités")
print("========================================")
print()

try:
    print("1. Connexion à Odoo local...")
    odoo = odoorpc.ODOO('localhost', port=8069)
    odoo.login('sougui_crm', 'admin', 'admin')
    print("   ✅ Connexion réussie")
    
    print()
    print("2. Récupération des stages...")
    Stage = odoo.env['crm.stage']
    stages = Stage.search_read([], ['id', 'name'])
    print(f"   ✅ {len(stages)} stages trouvés")
    for stage in stages:
        print(f"      - {stage['name']} (ID: {stage['id']})")
    
    print()
    print("3. Création d'opportunités de test...")
    Lead = odoo.env['crm.lead']
    
    # Liste d'opportunités à créer
    opportunities = [
        {
            'name': 'Opportunité ESPRIT - Formation Data Science',
            'expected_revenue': 25000.0,
            'probability': 75.0,
            'email_from': 'contact@esprit.tn',
            'phone': '+216 71 123 456',
            'description': 'Formation en Data Science pour 20 étudiants',
            'stage_id': stages[0]['id'] if stages else 1,
        },
        {
            'name': 'Projet ERP - Entreprise Tunisienne',
            'expected_revenue': 50000.0,
            'probability': 60.0,
            'email_from': 'direction@entreprise.tn',
            'phone': '+216 71 234 567',
            'description': 'Implémentation système ERP complet',
            'stage_id': stages[1]['id'] if len(stages) > 1 else 1,
        },
        {
            'name': 'Consulting IT - Startup Tech',
            'expected_revenue': 15000.0,
            'probability': 80.0,
            'email_from': 'ceo@startup.tn',
            'phone': '+216 71 345 678',
            'description': 'Conseil en architecture logicielle',
            'stage_id': stages[0]['id'] if stages else 1,
        },
        {
            'name': 'Développement Application Mobile',
            'expected_revenue': 30000.0,
            'probability': 70.0,
            'email_from': 'contact@mobile.tn',
            'phone': '+216 71 456 789',
            'description': 'Application mobile iOS et Android',
            'stage_id': stages[2]['id'] if len(stages) > 2 else 1,
        },
        {
            'name': 'Formation DevOps - Équipe Technique',
            'expected_revenue': 12000.0,
            'probability': 85.0,
            'email_from': 'rh@techcompany.tn',
            'phone': '+216 71 567 890',
            'description': 'Formation DevOps pour 15 développeurs',
            'stage_id': stages[1]['id'] if len(stages) > 1 else 1,
        },
        {
            'name': 'Audit Sécurité Informatique',
            'expected_revenue': 20000.0,
            'probability': 65.0,
            'email_from': 'security@bank.tn',
            'phone': '+216 71 678 901',
            'description': 'Audit complet de sécurité IT',
            'stage_id': stages[0]['id'] if stages else 1,
        },
        {
            'name': 'Migration Cloud AWS',
            'expected_revenue': 45000.0,
            'probability': 55.0,
            'email_from': 'it@corporation.tn',
            'phone': '+216 71 789 012',
            'description': 'Migration infrastructure vers AWS',
            'stage_id': stages[1]['id'] if len(stages) > 1 else 1,
        },
        {
            'name': 'Développement Site E-commerce',
            'expected_revenue': 18000.0,
            'probability': 90.0,
            'email_from': 'commerce@shop.tn',
            'phone': '+216 71 890 123',
            'description': 'Site e-commerce avec paiement en ligne',
            'stage_id': stages[3]['id'] if len(stages) > 3 else 1,
        },
    ]
    
    created_count = 0
    for opp in opportunities:
        try:
            lead_id = Lead.create({
                'name': opp['name'],
                'type': 'opportunity',
                'expected_revenue': opp['expected_revenue'],
                'probability': opp['probability'],
                'email_from': opp['email_from'],
                'phone': opp['phone'],
                'description': opp['description'],
                'stage_id': opp['stage_id'],
            })
            print(f"   ✅ Créé: {opp['name']} (ID: {lead_id})")
            created_count += 1
        except Exception as e:
            print(f"   ⚠️  Erreur: {opp['name']} - {e}")
    
    print()
    print("========================================")
    print(f"  ✅ {created_count} opportunités créées!")
    print("========================================")
    print()
    print("Prochaines étapes:")
    print("  1. Ouvrir http://localhost:3000")
    print("  2. Cliquer sur 'CRM' dans la navbar")
    print("  3. Vous verrez les opportunités dans l'iframe!")
    print()
    print("Ou ouvrir directement:")
    print("  http://localhost:8069/web#model=crm.lead&view_type=kanban")
    print()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    import traceback
    traceback.print_exc()
