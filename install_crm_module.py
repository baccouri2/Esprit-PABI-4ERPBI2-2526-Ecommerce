#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installer le module CRM dans Odoo
"""

import odoorpc
import time

print("========================================")
print("  Installation Module CRM")
print("========================================")
print()

try:
    print("1. Connexion à Odoo...")
    odoo = odoorpc.ODOO('localhost', port=8069)
    odoo.login('sougui_crm', 'admin', 'admin')
    print("   ✅ Connexion réussie")
    
    print()
    print("2. Recherche du module CRM...")
    Module = odoo.env['ir.module.module']
    
    # Chercher le module CRM
    crm_module_ids = Module.search([('name', '=', 'crm')])
    
    if not crm_module_ids:
        print("   ❌ Module CRM non trouvé")
        print()
        print("   Le module CRM devrait être disponible par défaut.")
        print("   Vérifiez l'installation d'Odoo.")
        exit(1)
    
    crm_module = Module.browse(crm_module_ids[0])
    print(f"   ✅ Module trouvé: {crm_module.name}")
    print(f"   État: {crm_module.state}")
    
    if crm_module.state == 'installed':
        print("   ✅ Le module CRM est déjà installé!")
    else:
        print()
        print("3. Installation du module CRM...")
        print("   (Cela peut prendre 30-60 secondes...)")
        
        crm_module.button_immediate_install()
        
        print("   ✅ Installation lancée!")
        print("   Attente de la fin de l'installation...")
        
        # Attendre que l'installation soit terminée
        for i in range(30):
            time.sleep(2)
            crm_module = Module.browse(crm_module_ids[0])
            if crm_module.state == 'installed':
                print("   ✅ Module CRM installé avec succès!")
                break
            print(f"   ... en cours ({i*2}s)")
        else:
            print("   ⚠️  L'installation prend plus de temps que prévu")
            print("   Vérifiez manuellement dans Odoo")
    
    print()
    print("4. Vérification de l'accès au module...")
    try:
        Lead = odoo.env['crm.lead']
        print("   ✅ Module crm.lead accessible")
        
        # Tester la création d'un lead
        print()
        print("5. Test de création d'opportunité...")
        lead_id = Lead.create({
            'name': 'Test Installation CRM',
            'type': 'opportunity',
            'expected_revenue': 5000.0,
            'probability': 50.0
        })
        print(f"   ✅ Opportunité créée: ID {lead_id}")
        
        # Supprimer le lead de test
        lead = Lead.browse(lead_id)
        lead.unlink()
        print("   ✅ Lead de test supprimé")
        
    except Exception as e:
        print(f"   ❌ Erreur d'accès: {e}")
        print()
        print("   Le module CRM n'est peut-être pas complètement installé.")
        print("   Essayez de vous connecter à Odoo et d'installer manuellement:")
        print("   1. Ouvrir http://localhost:8069")
        print("   2. Apps > Rechercher 'CRM'")
        print("   3. Cliquer sur 'Install'")
        exit(1)
    
    print()
    print("========================================")
    print("  ✅ Module CRM opérationnel!")
    print("========================================")
    print()
    print("Vous pouvez maintenant:")
    print("  1. Tester l'API: .\\CREATE_TEST_OPPORTUNITY.ps1")
    print("  2. Ouvrir l'interface: http://localhost:8069")
    print("  3. Utiliser l'application Angular")
    print()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    import traceback
    traceback.print_exc()
