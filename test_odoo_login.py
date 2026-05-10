#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tester différentes combinaisons de login Odoo
"""

import odoorpc

print("========================================")
print("  Test Connexion Odoo")
print("========================================")
print()

# Configurations à tester
configs = [
    {'db': 'odoo_db', 'user': 'admin', 'password': 'admin'},
    {'db': 'odoo_db', 'user': 'admin', 'password': 'Sougui@CEO2024'},
    {'db': 'odoo_db', 'user': 'hedir.zraga@esprit.tn', 'password': 'Sougui@CEO2024'},
]

odoo = odoorpc.ODOO('localhost', port=8069)

for i, config in enumerate(configs, 1):
    print(f"{i}. Test: db={config['db']}, user={config['user']}")
    try:
        odoo.login(config['db'], config['user'], config['password'])
        print(f"   ✅ SUCCÈS!")
        print(f"   User ID: {odoo.env.uid}")
        print(f"   Context: {odoo.env.context}")
        print()
        print("   ✅ Cette configuration fonctionne!")
        print(f"   Utilisez: db='{config['db']}', user='{config['user']}', password='{config['password']}'")
        break
    except Exception as e:
        print(f"   ❌ Échec: {e}")
        print()
else:
    print("❌ Aucune configuration ne fonctionne")
    print()
    print("Solutions:")
    print("  1. Créer un nouvel utilisateur dans Odoo")
    print("  2. Réinitialiser le mot de passe admin")
    print("  3. Créer une nouvelle base de données")
