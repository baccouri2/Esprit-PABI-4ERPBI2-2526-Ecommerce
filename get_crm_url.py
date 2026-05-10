#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtenir l'URL correcte pour accéder au CRM Pipeline
"""

import odoorpc

print("========================================")
print("  Récupération URL CRM Pipeline")
print("========================================")
print()

try:
    print("1. Connexion à Odoo...")
    odoo = odoorpc.ODOO('localhost', port=8069)
    odoo.login('sougui_crm', 'admin', 'admin')
    print("   ✅ Connexion réussie")
    
    print()
    print("2. Recherche de l'action CRM...")
    Action = odoo.env['ir.actions.act_window']
    
    # Chercher l'action CRM pour les leads
    actions = Action.search_read(
        [('res_model', '=', 'crm.lead'), ('name', 'ilike', 'pipeline')],
        ['id', 'name', 'xml_id']
    )
    
    if not actions:
        # Chercher toutes les actions CRM
        actions = Action.search_read(
            [('res_model', '=', 'crm.lead')],
            ['id', 'name', 'xml_id']
        )
    
    print(f"   ✅ {len(actions)} actions trouvées")
    for action in actions:
        print(f"      - {action['name']} (ID: {action['id']})")
    
    print()
    print("3. Recherche du menu CRM...")
    Menu = odoo.env['ir.ui.menu']
    menus = Menu.search_read(
        [('name', 'ilike', 'crm')],
        ['id', 'name', 'action']
    )
    
    print(f"   ✅ {len(menus)} menus trouvés")
    for menu in menus:
        print(f"      - {menu['name']} (ID: {menu['id']})")
    
    print()
    print("========================================")
    print("  URLs à utiliser:")
    print("========================================")
    print()
    
    if actions:
        action_id = actions[0]['id']
        menu_id = menus[0]['id'] if menus else ''
        
        print("URL complète (recommandée):")
        print(f"http://localhost:8069/web#menu_id={menu_id}&action={action_id}&model=crm.lead&view_type=kanban")
        print()
        print("URL simple:")
        print(f"http://localhost:8069/web#action={action_id}&model=crm.lead&view_type=kanban")
        print()
        print("URL directe modèle:")
        print("http://localhost:8069/web#model=crm.lead&view_type=kanban")
    
    print()
    print("========================================")
    print("  Instructions:")
    print("========================================")
    print()
    print("1. Copiez une des URLs ci-dessus")
    print("2. Collez-la dans votre navigateur")
    print("3. Vous verrez directement le pipeline CRM!")
    print()
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    print()
    import traceback
    traceback.print_exc()
