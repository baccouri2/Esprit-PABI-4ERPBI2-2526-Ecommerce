#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple pour vérifier que OdooRPC est correctement installé
"""

print("========================================")
print("  Test Import OdooRPC")
print("========================================")
print()

try:
    print("1. Import du module odoorpc...")
    import odoorpc
    print("   ✅ Import réussi")
    
    print(f"2. Version OdooRPC: {odoorpc.__version__}")
    
    print("3. Test de la classe ODOO...")
    if hasattr(odoorpc, 'ODOO'):
        print("   ✅ Classe ODOO disponible")
        
        # Test de création d'instance (sans connexion)
        print("4. Test création instance ODOO...")
        try:
            # Ne pas se connecter, juste créer l'objet
            api = odoorpc.ODOO('localhost', port=8069)
            print("   ✅ Instance ODOO créée avec succès")
            print(f"   Host: {api.host}")
            print(f"   Port: {api.port}")
        except Exception as e:
            print(f"   ⚠️  Erreur création instance: {e}")
            print("   (Normal si Odoo n'est pas démarré)")
            
    else:
        print("   ❌ Classe ODOO non disponible")
        
    print()
    print("========================================")
    print("  ✅ OdooRPC est correctement installé!")
    print("========================================")
    print()
    print("Prochaines étapes:")
    print("  1. Démarrer Docker Desktop")
    print("  2. Démarrer Odoo: docker-compose -f docker-compose.odoo.yml up -d")
    print("  3. Tester l'API CRM: http://localhost:5000/api/crm/health")
    print()
    
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    print()
    print("Solution:")
    print("  Exécutez: .\\fix_odoorpc.bat")
    print()
    
except Exception as e:
    print(f"❌ Erreur inattendue: {e}")
    print()