import sqlite3
import hashlib
import secrets
import streamlit as st
from datetime import datetime
from typing import Optional, Tuple, Dict

class AuthManager:
    """Gestionnaire d'authentification et de comptes utilisateurs"""
    
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_auth_tables()
        self.create_admin_account()
    
    def init_auth_tables(self):
        """Initialise les tables d'authentification"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                display_name TEXT,
                is_public BOOLEAN DEFAULT 0,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                profile_description TEXT
            )
        ''')
        
        # Table des sessions (optionnelle pour Streamlit)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Modifier la table des plateformes pour ajouter user_id
        try:
            cursor.execute('ALTER TABLE platforms ADD COLUMN user_id INTEGER')
            cursor.execute('ALTER TABLE platforms ADD FOREIGN KEY (user_id) REFERENCES users (id)')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        # Modifier la table des comptes pour ajouter user_id
        try:
            cursor.execute('ALTER TABLE accounts ADD COLUMN user_id INTEGER')
            cursor.execute('ALTER TABLE accounts ADD FOREIGN KEY (user_id) REFERENCES users (id)')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        # Modifier la table des transactions pour ajouter user_id
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN user_id INTEGER')
            cursor.execute('ALTER TABLE transactions ADD FOREIGN KEY (user_id) REFERENCES users (id)')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash un mot de passe avec un salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 100,000 iterations
        ).hex()
        
        return password_hash, salt
    
    def create_admin_account(self):
        """Crée le compte administrateur par défaut"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si l'admin existe déjà
        cursor.execute("SELECT id FROM users WHERE username = ?", ("kundun",))
        if cursor.fetchone():
            conn.close()
            return  # Admin existe déjà
        
        # Créer le compte admin
        password_hash, salt = self.hash_password("changeme")
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, display_name, is_public, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("kundun", password_hash, salt, "Administrateur", 1, 1))
        
        admin_user_id = cursor.lastrowid
        
        # Associer les données existantes à l'admin
        cursor.execute("UPDATE platforms SET user_id = ? WHERE user_id IS NULL", (admin_user_id,))
        cursor.execute("UPDATE accounts SET user_id = ? WHERE user_id IS NULL", (admin_user_id,))
        cursor.execute("UPDATE transactions SET user_id = ? WHERE user_id IS NULL", (admin_user_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Compte administrateur 'kundun' créé avec le mot de passe 'changeme'")
    
    def register_user(self, username: str, password: str, email: str = None, 
                     display_name: str = None) -> Tuple[bool, str]:
        """Enregistre un nouvel utilisateur"""
        if len(username) < 3:
            return False, "Le nom d'utilisateur doit contenir au moins 3 caractères"
        
        if len(password) < 6:
            return False, "Le mot de passe doit contenir au moins 6 caractères"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "Ce nom d'utilisateur est déjà pris"
            
            if email:
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    return False, "Cette adresse email est déjà utilisée"
            
            # Créer l'utilisateur
            password_hash, salt = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, display_name, is_public)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, display_name or username, 0))
            
            conn.commit()
            return True, "Compte créé avec succès !"
            
        except Exception as e:
            return False, f"Erreur lors de la création du compte : {str(e)}"
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """Authentifie un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, salt, display_name, is_public, is_admin, email
            FROM users WHERE username = ?
        ''', (username,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            conn.close()
            return False, None
        
        user_id, username, stored_hash, salt, display_name, is_public, is_admin, email = user_data
        
        # Vérifier le mot de passe
        password_hash, _ = self.hash_password(password, salt)
        
        if password_hash == stored_hash:
            # Mettre à jour la dernière connexion
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                          (datetime.now(), user_id))
            conn.commit()
            conn.close()
            
            return True, {
                'id': user_id,
                'username': username,
                'display_name': display_name,
                'is_public': bool(is_public),
                'is_admin': bool(is_admin),
                'email': email
            }
        
        conn.close()
        return False, None
    
    def update_user_profile(self, user_id: int, display_name: str = None, 
                           email: str = None, is_public: bool = None,
                           profile_description: str = None) -> Tuple[bool, str]:
        """Met à jour le profil utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name)
            
            if email is not None:
                # Vérifier si l'email est déjà utilisé
                cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id))
                if cursor.fetchone():
                    return False, "Cette adresse email est déjà utilisée"
                updates.append("email = ?")
                params.append(email)
            
            if is_public is not None:
                updates.append("is_public = ?")
                params.append(1 if is_public else 0)
            
            if profile_description is not None:
                updates.append("profile_description = ?")
                params.append(profile_description)
            
            if updates:
                params.append(user_id)
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
                conn.commit()
            
            return True, "Profil mis à jour avec succès !"
            
        except Exception as e:
            return False, f"Erreur lors de la mise à jour : {str(e)}"
        finally:
            conn.close()
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change le mot de passe d'un utilisateur"""
        if len(new_password) < 6:
            return False, "Le nouveau mot de passe doit contenir au moins 6 caractères"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Vérifier l'ancien mot de passe
            cursor.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False, "Utilisateur non trouvé"
            
            stored_hash, salt = result
            old_password_hash, _ = self.hash_password(old_password, salt)
            
            if old_password_hash != stored_hash:
                return False, "Ancien mot de passe incorrect"
            
            # Créer le nouveau hash
            new_password_hash, new_salt = self.hash_password(new_password)
            
            cursor.execute('''
                UPDATE users SET password_hash = ?, salt = ? WHERE id = ?
            ''', (new_password_hash, new_salt, user_id))
            
            conn.commit()
            return True, "Mot de passe changé avec succès !"
            
        except Exception as e:
            return False, f"Erreur lors du changement de mot de passe : {str(e)}"
        finally:
            conn.close()
    
    def get_public_users(self) -> list:
        """Récupère la liste des utilisateurs publics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, display_name, profile_description, created_at, last_login
            FROM users 
            WHERE is_public = 1 
            ORDER BY last_login DESC, created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'display_name': row[2],
                'profile_description': row[3],
                'created_at': row[4],
                'last_login': row[5]
            })
        
        conn.close()
        return users
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Récupère un utilisateur par son ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, display_name, profile_description, is_public, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'display_name': result[2],
                'profile_description': result[3],
                'is_public': bool(result[4]),
                'created_at': result[5],
                'last_login': result[6]
            }
        
        return None
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Récupère les statistiques d'un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Compter les plateformes
        cursor.execute("SELECT COUNT(*) FROM platforms WHERE user_id = ?", (user_id,))
        platforms_count = cursor.fetchone()[0]
        
        # Compter les comptes
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = ?", (user_id,))
        accounts_count = cursor.fetchone()[0]
        
        # Compter les transactions
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
        transactions_count = cursor.fetchone()[0]
        
        # Première transaction
        cursor.execute("SELECT MIN(transaction_date) FROM transactions WHERE user_id = ?", (user_id,))
        first_transaction = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'platforms_count': platforms_count,
            'accounts_count': accounts_count,
            'transactions_count': transactions_count,
            'first_transaction': first_transaction
        }

# Fonctions utilitaires pour Streamlit
def require_auth():
    """Décorator pour exiger une authentification"""
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("🔒 Vous devez être connecté pour accéder à cette page")
        st.stop()
    
    return st.session_state.user

def is_admin():
    """Vérifie si l'utilisateur actuel est admin"""
    if 'user' not in st.session_state or not st.session_state.user:
        return False
    
    return st.session_state.user.get('is_admin', False)

def get_current_user():
    """Récupère l'utilisateur actuel"""
    return st.session_state.get('user', None)

def logout():
    """Déconnecte l'utilisateur"""
    for key in ['user', 'authenticated']:
        if key in st.session_state:
            del st.session_state[key]