#!/usr/bin/env python3
"""
Script de test pour l'intégration Odoo CRM
Teste la connexion et les opérations CRUD
"""

import sys
import os

# Ajouter le dossier backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.odoo_service import odoo_client

def test_connection():
    """Test 1: Connexion à Odoo"""
    print("\n" + "="*60)
    print("  TEST 1: Connexion à Odoo")
    print("="*60)
    
    try:
        odoo_client.login()
        print("✅ Connexion réussie!")
        print(f"   Host: {odoo_client.host}:{odoo_client.port}")
        print(f"   Database: {odoo_client.db}")
        print(f"   User: {odoo_client.user}")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_get_leads():
    """Test 2: Récupérer les leads"""
    print("\n" + "="*60)
    print("  TEST 2: Récupération des Leads")
    print("="*60)
    
    try:
        leads = odoo_client.get_leads(limit=5)
        print(f"✅ {len(leads)} leads récupérés")
        
        for lead in leads:
            print(f"\n   Lead #{lead['id']}: {lead['name']}")
            print(f"   - Client: {lead['partner_id'][1] if lead['partner_id'] else 'N/A'}")
            print(f"   - Revenu: {lead['expected_revenue']} DT")
            print(f"   - Probabilité: {lead['probability']}%")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_get_stages():
    """Test 3: Récupérer les étapes"""
    print("\n" + "="*60)
    print("  TEST 3: Récupération des Étapes")
    print("="*60)
    
    try:
        stages = odoo_client.get_stages()
        print(f"✅ {len(stages)} étapes récupérées")
        
        for stage in stages:
            print(f"   - {stage['name']} (ID: {stage['id']})")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_get_partners():
    """Test 4: Récupérer les partenaires"""
    print("\n" + "="*60)
    print("  TEST 4: Récupération des Partenaires")
    print("="*60)
    
    try:
        customers = odoo_client.get_customers(limit=5)
        print(f"✅ {len(customers)} clients récupérés")
        
        for customer in customers:
            print(f"   - {customer['name']} ({customer['email'] or 'Pas d'email'})")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_create_lead():
    """Test 5: Créer un lead de test"""
    print("\n" + "="*60)
    print("  TEST 5: Création d'un Lead de Test")
    print("="*60)
    
    try:
        lead_data = {
            'name': 'Test Opportunité - Script Python',
            'expected_revenue': 5000.0,
            'probability': 50.0,
            'email_from': 'test@example.com',
            'phone': '+216 12 345 678',
            'description': 'Lead créé automatiquement par le script de test'
        }
        
        lead_id = odoo_client.create_lead(lead_data)
        
        if lead_id:
            print(f"✅ Lead créé avec succès!")
            print(f"   ID: {lead_id}")
            print(f"   Nom: {lead_data['name']}")
            print(f"   Revenu: {lead_data['expected_revenue']} DT")
            return lead_id
        else:
            print("❌ Échec de la création")
            return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_update_lead(lead_id):
    """Test 6: Mettre à jour un lead"""
    print("\n" + "="*60)
    print("  TEST 6: Mise à Jour du Lead")
    print("="*60)
    
    try:
        update_data = {
            'probability': 75.0,
            'description': 'Lead mis à jour par le script de test'
        }
        
        success = odoo_client.update_lead(lead_id, update_data)
        
        if success:
            print(f"✅ Lead #{lead_id} mis à jour")
            print(f"   Nouvelle probabilité: 75%")
            return True
        else:
            print("❌ Échec de la mise à jour")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_delete_lead(lead_id):
    """Test 7: Supprimer un lead"""
    print("\n" + "="*60)
    print("  TEST 7: Suppression du Lead de Test")
    print("="*60)
    
    try:
        success = odoo_client.delete_lead(lead_id)
        
        if success:
            print(f"✅ Lead #{lead_id} supprimé")
            return True
        else:
            print("❌ Échec de la suppression")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Exécuter tous les tests"""
    print("\n" + "="*60)
    print("  🧪 TESTS D'INTÉGRATION ODOO CRM")
    print("="*60)
    
    results = []
    
    # Test 1: Connexion
    if not test_connection():
        print("\n❌ Échec de la connexion. Arrêt des tests.")
        print("\n💡 Vérifiez:")
        print("   1. Que Odoo est démarré (START_ODOO.bat)")
        print("   2. Que la base 'sougui_crm' existe")
        print("   3. Que les identifiants sont corrects")
        return
    
    results.append(("Connexion", True))
    
    # Test 2: Récupérer les leads
    results.append(("Récupération leads", test_get_leads()))
    
    # Test 3: Récupérer les étapes
    results.append(("Récupération étapes", test_get_stages()))
    
    # Test 4: Récupérer les partenaires
    results.append(("Récupération partenaires", test_get_partners()))
    
    # Test 5: Créer un lead
    lead_id = test_create_lead()
    results.append(("Création lead", lead_id is not None))
    
    if lead_id:
        # Test 6: Mettre à jour le lead
        results.append(("Mise à jour lead", test_update_lead(lead_id)))
        
        # Test 7: Supprimer le lead
        results.append(("Suppression lead", test_delete_lead(lead_id)))
    
    # Résumé
    print("\n" + "="*60)
    print("  📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"  Résultat: {passed}/{total} tests réussis")
    print("="*60)
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés ! L'intégration fonctionne parfaitement.")
        print("\n🚀 Prochaines étapes:")
        print("   1. Démarrer Flask: cd backend && python app.py")
        print("   2. Tester l'API: curl http://localhost:5000/api/crm/health")
        print("   3. Développer l'interface Angular")
    else:
        print(f"\n⚠️  {total - passed} test(s) échoué(s). Vérifiez les erreurs ci-dessus.")
    
    print()

if __name__ == "__main__":
    main()
