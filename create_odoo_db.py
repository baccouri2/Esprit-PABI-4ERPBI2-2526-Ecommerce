#!/usr/bin/env python3
"""
Script pour créer automatiquement une base de données Odoo
"""

import requests
import time
import sys

# Configuration
ODOO_URL = "http://localhost:8069"
MASTER_PASSWORD = "admin123"
DB_NAME = "sougui_crm"
ADMIN_EMAIL = "admin@sougui.com"
ADMIN_PASSWORD = "Sougui@Admin2024"
LANGUAGE = "fr_FR"
COUNTRY = "TN"
DEMO_DATA = False

def wait_for_odoo():
    """Attendre que Odoo soit prêt"""
    print("⏳ Attente du démarrage d'Odoo...")
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get(f"{ODOO_URL}/web/database/manager", timeout=5)
            if response.status_code == 200:
                print("✅ Odoo est prêt!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"   Tentative {i+1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ Odoo ne répond pas après 60 secondes")
    return False

def check_database_exists():
    """Vérifier si la base de données existe déjà"""
    try:
        response = requests.post(
            f"{ODOO_URL}/web/database/list",
            json={}
        )
        if response.status_code == 200:
            databases = response.json().get('result', [])
            return DB_NAME in databases
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification: {e}")
    return False

def create_database():
    """Créer la base de données Odoo"""
    print("\n" + "="*50)
    print("  Création de la base de données Odoo")
    print("="*50)
    print(f"\n📊 Configuration:")
    print(f"   - Nom de la base: {DB_NAME}")
    print(f"   - Email admin: {ADMIN_EMAIL}")
    print(f"   - Langue: {LANGUAGE}")
    print(f"   - Pays: {COUNTRY}")
    print(f"   - Données de démo: {'Oui' if DEMO_DATA else 'Non'}")
    print()
    
    # Attendre que Odoo soit prêt
    if not wait_for_odoo():
        return False
    
    # Vérifier si la base existe déjà
    if check_database_exists():
        print(f"\n⚠️  La base de données '{DB_NAME}' existe déjà!")
        print(f"   Accédez à: {ODOO_URL}")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Mot de passe: {ADMIN_PASSWORD}")
        return True
    
    print("\n🔨 Création de la base de données en cours...")
    print("   (Cela peut prendre 2-3 minutes)")
    
    try:
        # Créer la base de données
        response = requests.post(
            f"{ODOO_URL}/web/database/create",
            json={
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "master_pwd": MASTER_PASSWORD,
                    "name": DB_NAME,
                    "login": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD,
                    "lang": LANGUAGE,
                    "country_code": COUNTRY,
                    "phone": "",
                    "demo": DEMO_DATA
                },
                "id": 1
            },
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"].get("data", {}).get("message", "Erreur inconnue")
                print(f"\n❌ Erreur lors de la création: {error_msg}")
                
                if "Access Denied" in error_msg or "access denied" in error_msg.lower():
                    print("\n💡 Solutions:")
                    print("   1. Vérifiez que le master password est correct (admin123)")
                    print("   2. Redémarrez Odoo: docker-compose -f docker-compose.odoo.yml restart")
                    print("   3. Créez la base manuellement sur: http://localhost:8069/web/database/manager")
                
                return False
            
            print("\n" + "="*50)
            print("  ✅ Base de données créée avec succès!")
            print("="*50)
            print(f"\n🌐 Accès à Odoo:")
            print(f"   URL: {ODOO_URL}")
            print(f"   Email: {ADMIN_EMAIL}")
            print(f"   Mot de passe: {ADMIN_PASSWORD}")
            print(f"\n📦 Prochaines étapes:")
            print(f"   1. Connectez-vous sur {ODOO_URL}")
            print(f"   2. Allez dans 'Apps' (Applications)")
            print(f"   3. Recherchez et installez 'CRM'")
            print(f"   4. Commencez à utiliser Odoo CRM!")
            print()
            
            return True
        else:
            print(f"\n❌ Erreur HTTP: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏱️  Timeout - La création prend plus de temps que prévu")
        print("   Vérifiez manuellement sur: http://localhost:8069")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("\n🚀 Script de création de base de données Odoo\n")
    
    # Créer la base de données
    success = create_database()
    
    if success:
        print("\n✅ Processus terminé avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Échec de la création de la base de données")
        print("\n💡 Méthode alternative:")
        print("   1. Ouvrez: http://localhost:8069/web/database/manager")
        print("   2. Cliquez sur 'Create Database'")
        print("   3. Utilisez le master password: admin123")
        print("   4. Remplissez le formulaire et créez la base")
        sys.exit(1)

if __name__ == "__main__":
    main()
