#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Créer la base de données sougui_crm dans Odoo
"""

import odoorpc

print("========================================")
print("  Création Base sougui_crm")
print("========================================")
print()

try:
    print("1. Connexion à Odoo...")
    odoo = odoorpc.ODOO('localhost', port=8069)
    print("   ✅ Connexion réussie")
    
    print()
    print("2. Vérification des bases existantes...")
    databases = odoo.db.list()
    print(f"   Bases existantes: {', '.join(databases)}")
    
    if 'sougui_crm' in databases:
        print("   ⚠️  La base 'sougui_crm' existe déjà!")
        print()
        response = input("   Voulez-vous la supprimer et la recréer? (oui/non): ")
        if response.lower() in ['oui', 'yes', 'o', 'y']:
            print("   Suppression de la base...")
            try:
                odoo.db.drop('admin', 'sougui_crm')
                print("   ✅ Base supprimée")
            except Exception as e:
                print(f"   ❌ Erreur suppression: {e}")
                print("   Continuons avec la base existante...")
        else:
            print("   Utilisation de la base existante")
            print()
            print("========================================")
            print("  ✅ Base sougui_crm disponible")
            print("========================================")
            print()
            print("Prochaines étapes:")
            print("  1. Ouvrir http://localhost:8069")
            print("  2. Se connecter à la base sougui_crm")
            print("  3. Installer le module CRM")
            print("  4. Créer l'utilisateur hedir.zraga@esprit.tn")
            exit(0)
    
    print()
    print("3. Création de la base 'sougui_crm'...")
    print("   (Cela peut prendre 1-2 minutes...)")
    
    try:
        odoo.db.create(
            'admin123',  # Master password from odoo.conf
            'sougui_crm',  # Database name
            False,  # Demo data
            'fr_FR',  # Language
            'admin'  # Admin password
        )
        print("   ✅ Base créée avec succès!")
        
        print()
        print("4. Connexion à la nouvelle base...")
        odoo.login('sougui_crm', 'admin', 'admin')
        print("   ✅ Connexion réussie")
        
        print()
        print("========================================")
        print("  ✅ Base sougui_crm créée!")
        print("========================================")
        print()
        print("Informations de connexion:")
        print("  Base de données: sougui_crm")
        print("  Utilisateur: admin")
        print("  Mot de passe: admin")
        print("  URL: http://localhost:8069")
        print()
        print("Prochaines étapes:")
        print("  1. Ouvrir http://localhost:8069")
        print("  2. Se connecter avec admin/admin")
        print("  3. Installer le module CRM (Apps > CRM)")
        print("  4. Créer l'utilisateur hedir.zraga@esprit.tn:")
        print("     - Settings > Users > Create")
        print("     - Email: hedir.zraga@esprit.tn")
        print("     - Password: Sougui@CEO2024")
        print("     - Access Rights: Sales / Administrator")
        print()
        
    except Exception as e:
        print(f"   ❌ Erreur création: {e}")
        print()
        print("   Note: Si l'erreur mentionne 'master password',")
        print("   le mot de passe master par défaut est 'admin'")
        print("   Vous pouvez le changer dans odoo.conf")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    print("Vérifications:")
    print("  1. Odoo est-il démarré? docker ps")
    print("  2. Port 8069 accessible? http://localhost:8069")
    print()
