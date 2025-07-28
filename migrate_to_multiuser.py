#!/usr/bin/env python3
"""
Script de migration pour transformer l'application Portfolio Tracker
en version multi-utilisateur et migrer les données existantes vers le compte admin.

Ce script doit être exécuté une seule fois lors de la mise à jour.
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime

def migrate_to_multiuser(db_path="portfolio.db"):
    """
    Migre la base de données vers le système multi-utilisateur
    """
    print("🔄 Début de la migration vers le système multi-utilisateur...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Créer les nouvelles tables d'authentification
        print("📋 Création des tables d'authentification...")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                display_name TEXT,
                is_public BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                bio TEXT,
                profile_image_url TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 2. Ajouter les colonnes user_id aux tables existantes
        print("🔧 Ajout des colonnes user_id...")
        
        tables_to_modify = [
            'platforms',
            'accounts', 
            'transactions'
        ]
        
        for table in tables_to_modify:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN user_id INTEGER')
                print(f"   ✅ Colonne user_id ajoutée à {table}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"   ℹ️ Colonne user_id existe déjà dans {table}")
                else:
                    print(f"   ❌ Erreur lors de l'ajout de user_id à {table}: {e}")
        
        # Ajouter user_id optionnel à price_history
        try:
            cursor.execute('ALTER TABLE price_history ADD COLUMN user_id INTEGER DEFAULT NULL')
            print("   ✅ Colonne user_id ajoutée à price_history")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   ℹ️ Colonne user_id existe déjà dans price_history")
            else:
                print(f"   ❌ Erreur: {e}")
        
        # 3. Créer le compte administrateur par défaut
        print("👑 Création du compte administrateur...")
        
        # Vérifier si l'admin existe déjà
        cursor.execute("SELECT id FROM users WHERE username = 'kundun'")
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            # Créer le compte admin
            salt = secrets.token_hex(32)
            password_hash = hashlib.pbkdf2_hmac('sha256','changeme'.encode('utf-8'), salt.encode('utf-8'), 100000)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, display_name, is_admin, is_public)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('kundun', password_hash, salt, 'Administrateur', True, True))
            
            admin_id = cursor.lastrowid
            print(f"   ✅ Compte admin créé avec l'ID {admin_id}")
        else:
            admin_id = admin_exists[0]
            print(f"   ℹ️ Compte admin existe déjà avec l'ID {admin_id}")
        
        # 4. Migrer toutes les données existantes vers le compte admin
        print("📦 Migration des données existantes vers le compte admin...")
        
        # Compter les données à migrer
        data_counts = {}
        for table in tables_to_modify:
            cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE user_id IS NULL')
            count = cursor.fetchone()[0]
            data_counts[table] = count
        
        print(f"   📊 Données à migrer:")
        for table, count in data_counts.items():
            print(f"      - {table}: {count} enregistrements")
        
        # Effectuer la migration
        for table in tables_to_modify:
            cursor.execute(f'UPDATE {table} SET user_id = ? WHERE user_id IS NULL', (admin_id,))
            updated = cursor.rowcount
            print(f"   ✅ {table}: {updated} enregistrements migrés")
        
        # 5. Ajouter des contraintes de clés étrangères (optionnel - peut poser problème avec SQLite)
        print("🔗 Vérification de l'intégrité des données...")
        
        # Vérifier que toutes les données ont un user_id valide
        for table in tables_to_modify:
            cursor.execute(f'''
                SELECT COUNT(*) FROM {table} t
                LEFT JOIN users u ON t.user_id = u.id
                WHERE t.user_id IS NOT NULL AND u.id IS NULL
            ''')
            orphaned = cursor.fetchone()[0]
            if orphaned > 0:
                print(f"   ⚠️ {table}: {orphaned} enregistrements avec user_id invalide")
            else:
                print(f"   ✅ {table}: Intégrité OK")
        
        # 6. Ajouter des index pour améliorer les performances
        print("⚡ Création des index pour les performances...")
        
        indexes = [
            ('idx_platforms_user', 'CREATE INDEX IF NOT EXISTS idx_platforms_user ON platforms(user_id)'),
            ('idx_accounts_user', 'CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id)'),
            ('idx_transactions_user', 'CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)'),
            ('idx_transactions_date', 'CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)'),
            ('idx_users_username', 'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)'),
            ('idx_sessions_token', 'CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)'),
        ]
        
        for index_name, index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"   ✅ Index {index_name} créé")
            except sqlite3.OperationalError as e:
                print(f"   ℹ️ Index {index_name}: {e}")
        
        # 7. Mettre à jour les contraintes UNIQUE pour inclure user_id (pour les plateformes)
        print("🔒 Mise à jour des contraintes...")
        
        # Note: SQLite ne permet pas de modifier facilement les contraintes
        # Cette partie pourrait nécessiter une recréation de table si nécessaire
        
        # Valider la migration
        print("✅ Validation de la migration...")
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
        admin_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM platforms WHERE user_id = ?", (admin_id,))
        platforms_migrated = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ?", (admin_id,))
        accounts_migrated = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (admin_id,))
        transactions_migrated = cursor.fetchone()[0]
        
        print(f"""
📊 Résultats de la migration:
   👑 Administrateurs: {admin_count}
   🏢 Plateformes migrées: {platforms_migrated}
   💼 Comptes migrés: {accounts_migrated}
   💸 Transactions migrées: {transactions_migrated}
        """)
        
        # Confirmer les changements
        conn.commit()
        print("💾 Migration sauvegardée avec succès!")
        
        return True, admin_id, {
            'platforms': platforms_migrated,
            'accounts': accounts_migrated, 
            'transactions': transactions_migrated
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
        return False, None, None
        
    finally:
        conn.close()

def verify_migration(db_path="portfolio.db"):
    """
    Vérifie que la migration s'est bien déroulée
    """
    print("\n🔍 Vérification de la migration...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier les tables
        tables_required = ['users', 'user_sessions']
        for table in tables_required:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                print(f"   ✅ Table {table} existe")
            else:
                print(f"   ❌ Table {table} manquante")
        
        # Vérifier les colonnes user_id
        tables_with_user_id = ['platforms', 'accounts', 'transactions']
        for table in tables_with_user_id:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            if 'user_id' in columns:
                print(f"   ✅ Colonne user_id existe dans {table}")
            else:
                print(f"   ❌ Colonne user_id manquante dans {table}")
        
        # Vérifier l'admin
        cursor.execute("SELECT username, is_admin FROM users WHERE username = 'kundun'")
        admin = cursor.fetchone()
        if admin and admin[1]:
            print("   ✅ Compte administrateur 'kundun' existe et est admin")
        else:
            print("   ❌ Problème avec le compte administrateur")
        
        # Vérifier que les données ont des user_id
        for table in tables_with_user_id:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL")
            null_count = cursor.fetchone()[0]
            if null_count == 0:
                print(f"   ✅ Tous les enregistrements de {table} ont un user_id")
            else:
                print(f"   ⚠️ {table} a {null_count} enregistrements sans user_id")
        
        print("✅ Vérification terminée!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    finally:
        conn.close()

def main():
    """
    Fonction principale du script de migration
    """
    print("🚀 Portfolio Tracker - Migration vers Multi-utilisateur")
    print("=" * 60)
    
    # Demander confirmation
    response = input("⚠️ Cette opération va modifier votre base de données. Avez-vous fait une sauvegarde ? (oui/non): ")
    if response.lower() not in ['oui', 'yes', 'y', 'o']:
        print("❌ Migration annulée. Veuillez d'abord sauvegarder votre fichier portfolio.db")
        return
    
    # Effectuer la migration
    success, admin_id, stats = migrate_to_multiuser()
    
    if success:
        print("\n🎉 Migration réussie!")
        print(f"""
📋 Prochaines étapes:
   1. Lancez l'application: streamlit run main.py
   2. Connectez-vous avec:
      - Nom d'utilisateur: kundun
      - Mot de passe: changeme
   3. Changez immédiatement le mot de passe admin
   4. Invitez d'autres utilisateurs à créer leurs comptes
   
🔒 Sécurité:
   - Vos données existantes sont maintenant associées au compte 'kundun'
   - Changez le mot de passe par défaut dès la première connexion
   - Les produits financiers restent communs à tous les utilisateurs
        """)
        
        # Vérification finale
        verify_migration()
        
    else:
        print("\n❌ Migration échouée. Vérifiez les erreurs ci-dessus.")
        print("💡 Vous pouvez restaurer votre sauvegarde et réessayer.")

if __name__ == "__main__":
    main()