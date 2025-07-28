import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple, List, Dict

class DatabaseManager:
    """Gestionnaire de la base de données SQLite multi-utilisateur"""
    
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données SQLite multi-utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tables utilisateurs (gérées par AuthManager)
        # Nous ajoutons seulement les colonnes user_id aux tables existantes
        
        # Table des plateformes (par utilisateur)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(name, user_id)
            )
        ''')
        
        # Table des comptes (par utilisateur)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_id INTEGER,
                name TEXT NOT NULL,
                account_type TEXT,
                user_id INTEGER,
                FOREIGN KEY (platform_id) REFERENCES platforms (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des produits financiers (COMMUNE à tous les utilisateurs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                product_type TEXT NOT NULL,
                currency TEXT NOT NULL,
                current_price REAL,
                current_price_eur REAL,
                current_price_usd REAL,
                market_cap REAL,
                sector TEXT,
                industry TEXT,
                exchange TEXT,
                country TEXT,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des transactions (par utilisateur)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                product_id INTEGER,
                transaction_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                price_currency TEXT NOT NULL,
                price_eur REAL NOT NULL,
                price_usd REAL NOT NULL,
                transaction_date TIMESTAMP NOT NULL,
                fees REAL DEFAULT 0,
                fees_currency TEXT DEFAULT 'EUR',
                exchange_rate_eur_usd REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (product_id) REFERENCES financial_products (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table des prix historiques (COMMUNE mais peut être par utilisateur pour les historiques personnalisés)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL NOT NULL,
                price_eur REAL NOT NULL,
                price_usd REAL NOT NULL,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER DEFAULT NULL,
                FOREIGN KEY (product_id) REFERENCES financial_products (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(product_id, date, user_id)
            )
        ''')
        
        # Table pour stocker les taux de change historiques (COMMUNE)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_currency, to_currency, date)
            )
        ''')
        
        # Mise à jour des tables existantes pour ajouter les colonnes user_id
        self._update_existing_tables(cursor)
        
        conn.commit()
        conn.close()
    
    def _update_existing_tables(self, cursor):
        """Met à jour les tables existantes pour ajouter les colonnes user_id"""
        
        # Tables nécessitant user_id
        tables_needing_user_id = ['platforms', 'accounts', 'transactions']
        
        for table in tables_needing_user_id:
            try:
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN user_id INTEGER')
            except sqlite3.OperationalError:
                pass  # Colonne existe déjà
        
        # Ajouter user_id optionnel à price_history pour l'historique personnalisé
        try:
            cursor.execute('ALTER TABLE price_history ADD COLUMN user_id INTEGER DEFAULT NULL')
        except sqlite3.OperationalError:
            pass
        
        # Autres colonnes existantes...
        new_columns_products = [
            ('current_price_eur', 'REAL'),
            ('current_price_usd', 'REAL'),
            ('market_cap', 'REAL'),
            ('sector', 'TEXT'),
            ('industry', 'TEXT'),
            ('exchange', 'TEXT'),
            ('country', 'TEXT'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for column_name, column_type in new_columns_products:
            try:
                cursor.execute(f'ALTER TABLE financial_products ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                pass
        
        new_columns_transactions = [
            ('price_currency', 'TEXT DEFAULT "EUR"'),
            ('price_eur', 'REAL'),
            ('price_usd', 'REAL'),
            ('fees_currency', 'TEXT DEFAULT "EUR"'),
            ('exchange_rate_eur_usd', 'REAL'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for column_name, column_type in new_columns_transactions:
            try:
                cursor.execute(f'ALTER TABLE transactions ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                pass
        
        new_columns_history = [
            ('price_eur', 'REAL'),
            ('price_usd', 'REAL'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ]
        
        for column_name, column_type in new_columns_history:
            try:
                cursor.execute(f'ALTER TABLE price_history ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                pass
    
    # Méthodes pour les plateformes (avec user_id)
    def add_platform(self, name: str, user_id: int, description: str = "") -> bool:
        """Ajoute une nouvelle plateforme pour un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO platforms (name, description, user_id) VALUES (?, ?, ?)", 
                         (name, description, user_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_platform(self, platform_id: int, name: str, user_id: int, description: str = "") -> bool:
        """Met à jour une plateforme d'un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE platforms SET name = ?, description = ? WHERE id = ? AND user_id = ?",
                         (name, description, platform_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def delete_platform(self, platform_id: int, user_id: int) -> Tuple[bool, str]:
        """Supprime une plateforme d'un utilisateur (si aucun compte associé)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si la plateforme appartient à l'utilisateur et a des comptes
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE platform_id = ? AND user_id = ?", 
                      (platform_id, user_id))
        account_count = cursor.fetchone()[0]
        
        if account_count > 0:
            conn.close()
            return False, f"Impossible de supprimer : {account_count} compte(s) utilisent cette plateforme"
        
        try:
            cursor.execute("DELETE FROM platforms WHERE id = ? AND user_id = ?", (platform_id, user_id))
            if cursor.rowcount == 0:
                conn.close()
                return False, "Plateforme non trouvée ou vous n'avez pas les droits"
            conn.commit()
            conn.close()
            return True, "Plateforme supprimée avec succès"
        except Exception as e:
            conn.close()
            return False, f"Erreur lors de la suppression : {e}"
    
    def get_platforms(self, user_id: int) -> pd.DataFrame:
        """Récupère toutes les plateformes d'un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM platforms WHERE user_id = ? ORDER BY name", 
                              conn, params=(user_id,))
        conn.close()
        return df
    
    # Méthodes pour les comptes (avec user_id)
    def add_account(self, platform_id: int, name: str, account_type: str, user_id: int) -> bool:
        """Ajoute un nouveau compte pour un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier que la plateforme appartient à l'utilisateur
        cursor.execute("SELECT id FROM platforms WHERE id = ? AND user_id = ?", (platform_id, user_id))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute("INSERT INTO accounts (platform_id, name, account_type, user_id) VALUES (?, ?, ?, ?)",
                      (platform_id, name, account_type, user_id))
        conn.commit()
        conn.close()
        return True
    
    def update_account(self, account_id: int, platform_id: int, name: str, account_type: str, user_id: int) -> bool:
        """Met à jour un compte d'un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier que la plateforme appartient à l'utilisateur
        cursor.execute("SELECT id FROM platforms WHERE id = ? AND user_id = ?", (platform_id, user_id))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute("UPDATE accounts SET platform_id = ?, name = ?, account_type = ? WHERE id = ? AND user_id = ?",
                      (platform_id, name, account_type, account_id, user_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def delete_account(self, account_id: int, user_id: int) -> Tuple[bool, str]:
        """Supprime un compte d'un utilisateur (si aucune transaction associée)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si le compte a des transactions
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE account_id = ? AND user_id = ?", 
                      (account_id, user_id))
        transaction_count = cursor.fetchone()[0]
        
        if transaction_count > 0:
            conn.close()
            return False, f"Impossible de supprimer : {transaction_count} transaction(s) utilisent ce compte"
        
        try:
            cursor.execute("DELETE FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
            if cursor.rowcount == 0:
                conn.close()
                return False, "Compte non trouvé ou vous n'avez pas les droits"
            conn.commit()
            conn.close()
            return True, "Compte supprimé avec succès"
        except Exception as e:
            conn.close()
            return False, f"Erreur lors de la suppression : {e}"
    
    def get_accounts(self, user_id: int) -> pd.DataFrame:
        """Récupère tous les comptes d'un utilisateur avec les plateformes"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT a.id, a.name, a.account_type, a.platform_id, p.name as platform_name
            FROM accounts a
            JOIN platforms p ON a.platform_id = p.id
            WHERE a.user_id = ?
            ORDER BY p.name, a.name
        '''
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df
    
    # Méthodes pour les produits financiers (COMMUNS - pas de user_id)
    def add_financial_product(self, product_info: Dict) -> Tuple[bool, str]:
        """Ajoute un nouveau produit financier (commun à tous les utilisateurs)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO financial_products 
                            (symbol, name, product_type, currency, current_price, 
                             current_price_eur, current_price_usd, market_cap, sector, 
                             industry, exchange, country, last_updated) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (product_info['symbol'], product_info['name'], 
                           product_info['product_type'], product_info['currency'],
                           product_info['current_price'], product_info['current_price_eur'],
                           product_info['current_price_usd'], product_info.get('market_cap'),
                           product_info.get('sector'), product_info.get('industry'),
                           product_info.get('exchange'), product_info.get('country'),
                           datetime.now()))
            
            product_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return True, f"Produit '{product_info['symbol']}' ajouté avec succès ! Prix actuel: {product_info['current_price']:.2f} {product_info['currency']}"
        except sqlite3.IntegrityError:
            conn.close()
            return False, f"Le symbole '{product_info['symbol']}' existe déjà."
        except Exception as e:
            conn.close()
            return False, f"Erreur lors de l'ajout du produit: {str(e)}"
    
    def get_financial_products(self) -> pd.DataFrame:
        """Récupère tous les produits financiers (communs)"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM financial_products ORDER BY symbol", conn)
        conn.close()
        return df
    
    def get_financial_product_by_symbol(self, symbol: str) -> Optional[pd.Series]:
        """Récupère un produit financier par son symbole"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM financial_products WHERE symbol = ?", (symbol,))
        result = cursor.fetchone()
        
        if result:
            # Récupérer les noms des colonnes
            columns = [description[0] for description in cursor.description]
            conn.close()
            return pd.Series(result, index=columns)
        
        conn.close()
        return None
    
    def update_product_price(self, symbol: str, current_price: float, 
                           price_eur: float, price_usd: float) -> bool:
        """Met à jour le prix d'un produit (commun)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''UPDATE financial_products 
                        SET current_price = ?, current_price_eur = ?, current_price_usd = ?, last_updated = ?
                        WHERE symbol = ?''',
                      (current_price, price_eur, price_usd, datetime.now(), symbol))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # Méthodes pour les transactions (avec user_id)
    def add_transaction(self, account_id: int, product_id: int, transaction_type: str,
                       quantity: float, price: float, price_currency: str, 
                       price_eur: float, price_usd: float, transaction_date: datetime, 
                       fees: float = 0, fees_currency: str = "EUR", 
                       exchange_rate: float = None, user_id: int = None) -> bool:
        """Ajoute une nouvelle transaction pour un utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''INSERT INTO transactions 
                        (account_id, product_id, transaction_type, quantity, price, price_currency,
                         price_eur, price_usd, transaction_date, fees, fees_currency, 
                         exchange_rate_eur_usd, user_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (account_id, product_id, transaction_type, quantity, price, price_currency,
                       price_eur, price_usd, transaction_date, fees, fees_currency, 
                       exchange_rate, user_id))
        conn.commit()
        conn.close()
        return True
    
    def get_all_transactions(self, user_id: int) -> pd.DataFrame:
        """Récupère toutes les transactions d'un utilisateur avec détails"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT 
                t.id,
                t.account_id,
                t.transaction_type,
                t.quantity,
                t.price,
                t.price_currency,
                t.price_eur,
                t.price_usd,
                t.transaction_date,
                t.fees,
                t.fees_currency,
                t.exchange_rate_eur_usd,
                fp.symbol,
                fp.name as product_name,
                fp.currency as product_currency,
                a.name as account_name,
                p.name as platform_name
            FROM transactions t
            JOIN financial_products fp ON t.product_id = fp.id
            JOIN accounts a ON t.account_id = a.id
            JOIN platforms p ON a.platform_id = p.id
            WHERE t.user_id = ?
            ORDER BY t.transaction_date DESC
        '''
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        
        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            # Calculer le montant total en EUR
            df['total_amount'] = df['quantity'] * df['price_eur'] + df['fees']
        
        return df
    
    # Méthodes pour les taux de change historiques (communs)
    def save_exchange_rate(self, from_currency: str, to_currency: str, 
                          rate: float, date: datetime) -> bool:
        """Sauvegarde un taux de change historique"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT OR REPLACE INTO exchange_rates 
                            (from_currency, to_currency, rate, date)
                            VALUES (?, ?, ?, ?)''',
                          (from_currency, to_currency, rate, date.date()))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_exchange_rate(self, from_currency: str, to_currency: str, 
                         date: datetime) -> Optional[float]:
        """Récupère un taux de change historique"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT rate FROM exchange_rates 
                        WHERE from_currency = ? AND to_currency = ? AND date = ?''',
                      (from_currency, to_currency, date.date()))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    # Méthodes utilitaires
    def get_database_stats(self, user_id: int = None) -> Dict:
        """Retourne des statistiques sur la base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        if user_id:
            # Stats spécifiques à l'utilisateur
            user_tables = [
                ('platforms', 'SELECT COUNT(*) FROM platforms WHERE user_id = ?'),
                ('accounts', 'SELECT COUNT(*) FROM accounts WHERE user_id = ?'),
                ('transactions', 'SELECT COUNT(*) FROM transactions WHERE user_id = ?'),
            ]
            
            for table, query in user_tables:
                cursor.execute(query, (user_id,))
                stats[table] = cursor.fetchone()[0]
        
        # Stats communes
        common_tables = ['financial_products', 'price_history', 'exchange_rates']
        for table in common_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        # Stats globales
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['users'] = cursor.fetchone()[0]
        
        conn.close()
        return stats