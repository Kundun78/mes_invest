import hashlib
import secrets
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Tuple
import sqlite3

class AuthManager:
    """Gestionnaire d'authentification pour l'application multi-utilisateur"""
    
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialise les tables d'authentification et crée l'admin par défaut"""
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
                is_public BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                bio TEXT,
                profile_image_url TEXT
            )
        ''')
        
        # Table des sessions
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
        
        # Ajouter user_id aux tables existantes si pas déjà fait
        self._add_user_id_columns(cursor)
        
        # Créer le compte administrateur par défaut
        self._create_default_admin(cursor)
        
        conn.commit()
        conn.close()
    
    def _add_user_id_columns(self, cursor):
        """Ajoute les colonnes user_id aux tables existantes"""
        tables_to_modify = ['platforms', 'accounts', 'transactions', 'price_history']
        
        for table in tables_to_modify:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN user_id INTEGER')
            except sqlite3.OperationalError:
                pass  # Colonne existe déjà
    
    def _create_default_admin(self, cursor):
        """Crée le compte administrateur par défaut"""
        # Vérifier si l'admin existe déjà
        cursor.execute("SELECT id FROM users WHERE username = 'kundun'")
        if cursor.fetchone():
            return  # Admin existe déjà
        
        # Créer le compte admin
        salt = secrets.token_hex(32)
        password_hash = self._hash_password('changeme', salt)
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt, display_name, is_admin, is_public)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('kundun', password_hash, salt, 'Administrateur', True, True))
        
        admin_id = cursor.lastrowid
        
        # Migrer les données existantes vers le compte admin
        self._migrate_existing_data_to_admin(cursor, admin_id)
    
    def _migrate_existing_data_to_admin(self, cursor, admin_id):
        """Migre toutes les données existantes vers le compte admin"""
        tables_to_migrate = ['platforms', 'accounts', 'transactions', 'price_history']
        
        for table in tables_to_migrate:
            try:
                # Mettre à jour toutes les lignes sans user_id
                cursor.execute(f'UPDATE {table} SET user_id = ? WHERE user_id IS NULL', (admin_id,))
            except sqlite3.OperationalError:
                pass  # La colonne n'existe peut-être pas encore
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hache un mot de passe avec du sel"""
        return hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'), salt.encode('utf-8'), 100000)
    
    def register_user(self, username: str, password: str, email: str = None, display_name: str = None) -> Tuple[bool, str]:
        """Enregistre un nouvel utilisateur"""
        if len(username) < 3:
            return False, "Le nom d'utilisateur doit contenir au moins 3 caractères"
        
        if len(password) < 6:
            return False, "Le mot de passe doit contenir au moins 6 caractères"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                return False, "Ce nom d'utilisateur ou email existe déjà"
            
            # Créer l'utilisateur
            salt = secrets.token_hex(32)
            password_hash = self._hash_password(password, salt)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, display_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, salt, display_name or username))
            
            conn.commit()
            return True, "Compte créé avec succès !"
            
        except sqlite3.IntegrityError:
            return False, "Ce nom d'utilisateur existe déjà"
        except Exception as e:
            return False, f"Erreur lors de la création du compte : {e}"
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[dict]]:
        """Authentifie un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, salt, display_name, is_admin, is_public
            FROM users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return False, None
        
        user_id, username, stored_hash, salt, display_name, is_admin, is_public = user
        calculated_hash = self._hash_password(password, salt)
        
        if calculated_hash == stored_hash:
            # Mettre à jour la date de dernière connexion
            self._update_last_login(user_id)
            
            return True, {
                'id': user_id,
                'username': username,
                'display_name': display_name,
                'is_admin': bool(is_admin),
                'is_public': bool(is_public)
            }
        
        return False, None
    
    def _update_last_login(self, user_id: int):
        """Met à jour la date de dernière connexion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now(), user_id))
        conn.commit()
        conn.close()
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change le mot de passe d'un utilisateur"""
        if len(new_password) < 6:
            return False, "Le nouveau mot de passe doit contenir au moins 6 caractères"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier l'ancien mot de passe
        cursor.execute('SELECT password_hash, salt FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "Utilisateur non trouvé"
        
        stored_hash, salt = result
        if self._hash_password(old_password, salt) != stored_hash:
            conn.close()
            return False, "Ancien mot de passe incorrect"
        
        # Changer le mot de passe
        new_salt = secrets.token_hex(32)
        new_hash = self._hash_password(new_password, new_salt)
        
        cursor.execute('UPDATE users SET password_hash = ?, salt = ? WHERE id = ?', 
                      (new_hash, new_salt, user_id))
        conn.commit()
        conn.close()
        
        return True, "Mot de passe modifié avec succès"
    
    def update_profile(self, user_id: int, display_name: str = None, email: str = None, 
                      bio: str = None, is_public: bool = None) -> Tuple[bool, str]:
        """Met à jour le profil d'un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name)
            
            if email is not None:
                updates.append("email = ?")
                params.append(email)
            
            if bio is not None:
                updates.append("bio = ?")
                params.append(bio)
            
            if is_public is not None:
                updates.append("is_public = ?")
                params.append(is_public)
            
            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
            
            return True, "Profil mis à jour avec succès"
            
        except sqlite3.IntegrityError:
            return False, "Cet email est déjà utilisé par un autre compte"
        except Exception as e:
            return False, f"Erreur lors de la mise à jour : {e}"
        finally:
            conn.close()
    
    def get_user_profile(self, user_id: int) -> Optional[dict]:
        """Récupère le profil d'un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, display_name, bio, is_public, is_admin, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'display_name': result[3],
                'bio': result[4],
                'is_public': bool(result[5]),
                'is_admin': bool(result[6]),
                'created_at': result[7],
                'last_login': result[8]
            }
        
        return None
    
    def get_public_users(self) -> list:
        """Récupère la liste des utilisateurs publics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, display_name, bio, last_login
            FROM users 
            WHERE is_public = TRUE
            ORDER BY last_login DESC
        ''', )
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'username': row[1],
                'display_name': row[2],
                'bio': row[3],
                'last_login': row[4]
            }
            for row in results
        ]
    
    def create_session(self, user_id: int) -> str:
        """Crée une session pour un utilisateur"""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=30)  # Session de 30 jours
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Nettoyer les anciennes sessions expirées
        cursor.execute('DELETE FROM user_sessions WHERE expires_at < ?', (datetime.now(),))
        
        # Créer la nouvelle session
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, session_token, expires_at))
        
        conn.commit()
        conn.close()
        
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[dict]:
        """Valide une session et retourne les informations utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.display_name, u.is_admin, u.is_public
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ? AND s.expires_at > ?
        ''', (session_token, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'display_name': result[2],
                'is_admin': bool(result[3]),
                'is_public': bool(result[4])
            }
        
        return None
    
    def logout_user(self, session_token: str):
        """Déconnecte un utilisateur en supprimant sa session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
        conn.commit()
        conn.close()

def require_auth():
    """Décorateur pour protéger les pages nécessitant une authentification"""
    if 'user' not in st.session_state or not st.session_state.user:
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        st.stop()
    
    return st.session_state.user

def check_admin():
    """Vérifie si l'utilisateur actuel est administrateur"""
    user = require_auth()
    if not user.get('is_admin', False):
        st.error("❌ Accès refusé. Cette fonctionnalité est réservée aux administrateurs.")
        st.stop()
    
    return user

def init_session_state():
    """Initialise l'état de session pour l'authentification"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    
    # Vérifier si l'utilisateur a une session valide
    if 'session_token' in st.session_state and st.session_state.session_token:
        user = st.session_state.auth_manager.validate_session(st.session_state.session_token)
        if user:
            st.session_state.user = user
        else:
            # Session expirée
            st.session_state.user = None
            st.session_state.session_token = None