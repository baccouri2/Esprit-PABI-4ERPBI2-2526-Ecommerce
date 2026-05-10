#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifier les bases de données Odoo disponibles
"""

import odoorpc

print("========================================")
print("  Vérification Bases de Données Odoo")
print("========================================")
print()

try:
    print("1. Connexion à Odoo...")
    odoo = odoorpc.ODOO('localhost', port=8069)
    print("   ✅ Connexion réussie")
    
    print()
    print("2. Liste des bases de données:")
    databases = odoo.db.list()
    
    if databases:
        for db in databases:
            print(f"   - {db}")
    else:
        print("   ⚠️  Aucune base de données trouvée")
    
    print()
    print("3. Vérification de 'sougui_crm':")
    if 'sougui_crm' in databases:
        print("   ✅ La base 'sougui_crm' existe")
        
        # Tester la connexion
        print()
        print("4. Test de connexion à 'sougui_crm':")
        try:
            odoo.login('sougui_crm', 'hedir.zraga@esprit.tn', 'Sougui@CEO2024')
            print("   ✅ Connexion réussie avec hedir.zraga@esprit.tn")
            
            # Vérifier les modules installés
            print()
            print("5. Modules CRM installés:")
            Lead = odoo.env['crm.lead']
            print("   ✅ Module crm.lead accessible")
            
        except Exception as e:
            print(f"   ❌ Erreur de connexion: {e}")
            print()
            print("   Solutions:")
            print("   1. Vérifier que l'utilisateur existe dans Odoo")
            print("   2. Vérifier le mot de passe")
            print("   3. Installer le module CRM dans Odoo")
    else:
        print("   ❌ La base 'sougui_crm' n'existe pas")
        print()
        print("   Solutions:")
        print("   1. Créer la base via l'interface Odoo: http://localhost:8069")
        print("   2. Ou exécuter: .\\CREATE_ODOO_DATABASE.bat")
    
    print()
    print("========================================")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    print("Vérifications:")
    print("  1. Odoo est-il démarré? docker ps")
    print("  2. Port 8069 accessible? http://localhost:8069")
    print()
