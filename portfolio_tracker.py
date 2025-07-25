# portfolio_tracker.py
import streamlit as st
import pandas as pd
import sqlite3
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, List, Optional
import time

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Suivi de Patrimoine",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CurrencyConverter:
    """Gestionnaire de conversion de devises EUR/USD + support autres devises"""
    
    def __init__(self):
        self.eur_usd_rate = None  # Combien d'USD pour 1 EUR
        self.last_update = None
        # Taux fixes pour les autres devises (vers EUR)
        self.other_rates = {
            'GBP': 1.15,  # 1 GBP = 1.15 EUR
            'CHF': 0.95,  # 1 CHF = 0.95 EUR
            'CAD': 0.65   # 1 CAD = 0.65 EUR
        }
    
    def get_eur_usd_rate_alternative(self, show_debug=False) -> bool:
        """Méthode alternative pour récupérer le taux EUR/USD via une API gratuite"""
        try:
            if show_debug:
                st.write("🔄 Tentative avec API alternative...")
            
            import requests
            
            # API gratuite pour les taux de change
            url = "https://api.exchangerate-api.com/v4/latest/EUR"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'USD' in data['rates']:
                    self.eur_usd_rate = data['rates']['USD']
                    self.last_update = datetime.now()
                    
                    if show_debug:
                        st.success(f"✅ Taux EUR/USD récupéré via API: 1 EUR = {self.eur_usd_rate:.4f} USD")
                    
                    return True
            
            return False
            
        except Exception as e:
            if show_debug:
                st.write(f"❌ Erreur API alternative: {str(e)}")
            return False
    def get_eur_usd_rate(self, show_debug=False) -> bool:
        """Récupère le taux de change EUR/USD via yfinance puis API de secours"""
        try:
            # Mise à jour toutes les 6 heures seulement
            if (self.last_update and 
                datetime.now() - self.last_update < timedelta(hours=6)):
                return True
            
            # Essayer d'abord Yahoo Finance avec plusieurs symboles
            symbols_to_try = ['EURUSD=X', 'EUR=X', 'USDEUR=X']
            
            for symbol in symbols_to_try:
                try:
                    if show_debug:
                        st.write(f"🔍 Tentative de récupération du taux avec {symbol}...")
                    
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")  # 2 jours pour plus de chances
                    
                    if not hist.empty:
                        rate = hist['Close'].iloc[-1]
                        
                        if show_debug:
                            st.write(f"✅ Taux trouvé avec {symbol}: {rate}")
                        
                        # Si c'est USDEUR=X, on inverse le taux
                        if symbol == 'USDEUR=X':
                            self.eur_usd_rate = 1.0 / rate
                        else:
                            self.eur_usd_rate = rate
                        
                        self.last_update = datetime.now()
                        
                        if show_debug:
                            st.success(f"✅ Taux EUR/USD récupéré: 1 EUR = {self.eur_usd_rate:.4f} USD")
                        
                        return True
                    else:
                        if show_debug:
                            st.write(f"⚠️ Pas de données pour {symbol}")
                        
                except Exception as e:
                    if show_debug:
                        st.write(f"❌ Erreur avec {symbol}: {str(e)}")
                    continue
            
            # Si Yahoo Finance ne fonctionne pas, essayer l'API alternative
            if show_debug:
                st.write("🔄 Yahoo Finance indisponible, tentative avec API alternative...")
            
            if self.get_eur_usd_rate_alternative():
                return True
            
            # Si rien ne fonctionne, utiliser un taux de secours
            if show_debug:
                st.warning("⚠️ Impossible de récupérer le taux EUR/USD en temps réel, utilisation d'un taux de secours")
            
            self.eur_usd_rate = 1.08  # Approximatif EUR/USD
            self.last_update = datetime.now()
            return False
                
        except Exception as e:
            if show_debug:
                st.error(f"Erreur générale lors de la récupération du taux EUR/USD: {e}")
            
            # Utiliser un taux de secours
            self.eur_usd_rate = 1.08  # Approximatif : 1 EUR = 1.08 USD
            self.last_update = datetime.now()
            return False
    
    def eur_to_usd(self, eur_amount: float) -> float:
        """Convertit EUR vers USD"""
        if not self.eur_usd_rate:
            self.get_eur_usd_rate()
        
        if not self.eur_usd_rate:
            st.warning("⚠️ Taux EUR/USD non disponible, pas de conversion appliquée")
            return eur_amount
        
        return eur_amount * self.eur_usd_rate
    
    def usd_to_eur(self, usd_amount: float) -> float:
        """Convertit USD vers EUR"""
        if not self.eur_usd_rate:
            self.get_eur_usd_rate()
        
        if not self.eur_usd_rate:
            st.warning("⚠️ Taux EUR/USD non disponible, pas de conversion appliquée")
            return usd_amount
        
        return usd_amount / self.eur_usd_rate
    
    def convert_to_eur(self, amount: float, from_currency: str) -> float:
        """Convertit un montant vers EUR (méthode de compatibilité)"""
        if from_currency == 'EUR':
            return amount
        elif from_currency == 'USD':
            return self.usd_to_eur(amount)
        elif from_currency in self.other_rates:
            return amount * self.other_rates[from_currency]
        else:
            st.warning(f"⚠️ Devise {from_currency} non supportée, pas de conversion appliquée")
            return amount
    
    def convert_price_to_both(self, price: float, original_currency: str) -> tuple:
        """Convertit un prix vers EUR et USD"""
        if not self.eur_usd_rate:
            self.get_eur_usd_rate()
        
        if original_currency == 'EUR':
            price_eur = price
            price_usd = self.eur_to_usd(price)
        elif original_currency == 'USD':
            price_eur = self.usd_to_eur(price)
            price_usd = price
        else:
            # Pour d'autres devises, convertir d'abord en EUR puis en USD
            if original_currency in self.other_rates:
                price_eur = price * self.other_rates[original_currency]
                price_usd = self.eur_to_usd(price_eur)
            else:
                # Par défaut, considérer comme EUR
                price_eur = price
                price_usd = self.eur_to_usd(price)
        
        return price_eur, price_usd
    
    def get_rate_info(self) -> str:
        """Retourne les informations sur le taux actuel"""
        if not self.eur_usd_rate:
            # Essayer de récupérer le taux sans les messages de debug
            self._get_eur_usd_rate_silent()
        
        if not self.eur_usd_rate:
            return "Taux de change EUR/USD non disponible\nUtilisation d'un taux de secours sera appliquée lors des conversions."
        
        rates_text = f"Taux de change actuel:\n"
        rates_text += f"1 EUR = {self.eur_usd_rate:.4f} USD\n"
        rates_text += f"1 USD = {(1/self.eur_usd_rate):.4f} EUR\n"
        
        rates_text += f"\nAutres devises (taux fixes):\n"
        for currency, rate in self.other_rates.items():
            rates_text += f"1 {currency} = {rate:.4f} EUR\n"
        
        if self.last_update:
            rates_text += f"\nDernière mise à jour EUR/USD: {self.last_update.strftime('%d/%m/%Y %H:%M')}"
        
        return rates_text
    
    def _get_eur_usd_rate_silent(self) -> bool:
        """Version silencieuse de get_eur_usd_rate pour les vérifications internes"""
        try:
            # Essayer rapidement Yahoo Finance
            ticker = yf.Ticker('EURUSD=X')
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                self.eur_usd_rate = hist['Close'].iloc[-1]
                self.last_update = datetime.now()
                return True
            
            # Essayer l'API alternative
            import requests
            url = "https://api.exchangerate-api.com/v4/latest/EUR"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'USD' in data['rates']:
                    self.eur_usd_rate = data['rates']['USD']
                    self.last_update = datetime.now()
                    return True
            
            # Utiliser le taux de secours
            self.eur_usd_rate = 1.08
            self.last_update = datetime.now()
            return False
            
        except:
            self.eur_usd_rate = 1.08
            self.last_update = datetime.now()
            return False

class PortfolioTracker:
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.currency_converter = CurrencyConverter()
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des plateformes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')
        
        # Table des comptes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_id INTEGER,
                name TEXT NOT NULL,
                account_type TEXT,
                FOREIGN KEY (platform_id) REFERENCES platforms (id)
            )
        ''')
        
        # Table des produits financiers avec prix EUR et USD
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                product_type TEXT NOT NULL,
                currency TEXT DEFAULT 'EUR',
                current_price REAL,
                current_price_eur REAL,
                current_price_usd REAL,
                last_updated TIMESTAMP
            )
        ''')
        
        # Table des transactions avec devise de saisie
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                product_id INTEGER,
                transaction_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                price_currency TEXT DEFAULT 'EUR',
                price_eur REAL,
                price_usd REAL,
                transaction_date TIMESTAMP NOT NULL,
                fees REAL DEFAULT 0,
                fees_currency TEXT DEFAULT 'EUR',
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (product_id) REFERENCES financial_products (id)
            )
        ''')
        
        # Table des prix historiques avec EUR et USD
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                price REAL NOT NULL,
                price_eur REAL,
                price_usd REAL,
                date DATE NOT NULL,
                FOREIGN KEY (product_id) REFERENCES financial_products (id),
                UNIQUE(product_id, date)
            )
        ''')
        
        # Mise à jour des tables existantes pour ajouter les nouvelles colonnes
        try:
            cursor.execute('ALTER TABLE financial_products ADD COLUMN current_price_eur REAL')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        try:
            cursor.execute('ALTER TABLE financial_products ADD COLUMN current_price_usd REAL')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN price_currency TEXT DEFAULT "EUR"')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN price_eur REAL')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN price_usd REAL')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        try:
            cursor.execute('ALTER TABLE transactions ADD COLUMN fees_currency TEXT DEFAULT "EUR"')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        try:
            cursor.execute('ALTER TABLE price_history ADD COLUMN price_eur REAL')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        try:
            cursor.execute('ALTER TABLE price_history ADD COLUMN price_usd REAL')
        except sqlite3.OperationalError:
            pass  # Colonne existe déjà
        
        conn.commit()
        conn.close()
    
    def add_platform(self, name: str, description: str = ""):
        """Ajoute une nouvelle plateforme"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO platforms (name, description) VALUES (?, ?)", 
                         (name, description))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_platform(self, platform_id: int, name: str, description: str = ""):
        """Met à jour une plateforme"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE platforms SET name = ?, description = ? WHERE id = ?",
                         (name, description, platform_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def delete_platform(self, platform_id: int):
        """Supprime une plateforme (si aucun compte associé)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si la plateforme a des comptes
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE platform_id = ?", (platform_id,))
        account_count = cursor.fetchone()[0]
        
        if account_count > 0:
            conn.close()
            return False, f"Impossible de supprimer : {account_count} compte(s) utilisent cette plateforme"
        
        try:
            cursor.execute("DELETE FROM platforms WHERE id = ?", (platform_id,))
            conn.commit()
            conn.close()
            return True, "Plateforme supprimée avec succès"
        except Exception as e:
            conn.close()
            return False, f"Erreur lors de la suppression : {e}"
    
    def add_account(self, platform_id: int, name: str, account_type: str):
        """Ajoute un nouveau compte"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts (platform_id, name, account_type) VALUES (?, ?, ?)",
                      (platform_id, name, account_type))
        conn.commit()
        conn.close()
    
    def update_account(self, account_id: int, platform_id: int, name: str, account_type: str):
        """Met à jour un compte"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET platform_id = ?, name = ?, account_type = ? WHERE id = ?",
                      (platform_id, name, account_type, account_id))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def delete_account(self, account_id: int):
        """Supprime un compte (si aucune transaction associée)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si le compte a des transactions
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE account_id = ?", (account_id,))
        transaction_count = cursor.fetchone()[0]
        
        if transaction_count > 0:
            conn.close()
            return False, f"Impossible de supprimer : {transaction_count} transaction(s) utilisent ce compte"
        
        try:
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            conn.commit()
            conn.close()
            return True, "Compte supprimé avec succès"
        except Exception as e:
            conn.close()
            return False, f"Erreur lors de la suppression : {e}"
    
    def add_financial_product(self, symbol: str, name: str, product_type: str, currency: str = "EUR"):
        """Ajoute un nouveau produit financier après vérification de l'existence"""
        # D'abord vérifier que le symbole existe sur Yahoo Finance
        try:
            ticker = yf.Ticker(symbol)
            # Essayer de récupérer des données récentes pour valider l'existence
            hist = ticker.history(period="5d")
            info = ticker.info
            
            if hist.empty:
                return False, f"Aucune donnée de prix trouvée pour le symbole '{symbol}'. Vérifiez le symbole sur Yahoo Finance."
            
            # Récupérer le prix actuel et des informations
            current_price = hist['Close'].iloc[-1]
            
            # Convertir le prix en EUR et USD
            price_eur, price_usd = self.currency_converter.convert_price_to_both(current_price, currency)
            
            # Essayer de récupérer le nom réel du produit si disponible
            real_name = info.get('longName') or info.get('shortName') or name
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute('''INSERT INTO financial_products 
                                (symbol, name, product_type, currency, current_price, 
                                 current_price_eur, current_price_usd, last_updated) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                              (symbol, real_name, product_type, currency, current_price, 
                               price_eur, price_usd, datetime.now()))
                
                # Ajouter quelques points d'historique récent avec conversion
                product_id = cursor.lastrowid
                for date, row in hist.iterrows():
                    hist_price_eur, hist_price_usd = self.currency_converter.convert_price_to_both(
                        row['Close'], currency
                    )
                    cursor.execute('''INSERT OR REPLACE INTO price_history 
                                    (product_id, price, price_eur, price_usd, date)
                                    VALUES (?, ?, ?, ?, ?)''',
                                  (product_id, row['Close'], hist_price_eur, hist_price_usd, date.date()))
                
                conn.commit()
                return True, f"Produit '{symbol}' ajouté avec succès ! Prix actuel: {current_price:.2f} {currency} ({price_eur:.2f} EUR / {price_usd:.2f} USD)"
            except sqlite3.IntegrityError:
                return False, f"Le symbole '{symbol}' existe déjà dans votre portefeuille."
            finally:
                conn.close()
                
        except Exception as e:
            return False, f"Erreur lors de la vérification du symbole '{symbol}': {str(e)}. Vérifiez que le symbole est correct sur Yahoo Finance."
    
    def update_financial_product(self, product_id: int, symbol: str, name: str, product_type: str, currency: str):
        """Met à jour un produit financier"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''UPDATE financial_products 
                            SET symbol = ?, name = ?, product_type = ?, currency = ?
                            WHERE id = ?''',
                          (symbol, name, product_type, currency, product_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def delete_financial_product(self, product_id: int):
        """Supprime un produit financier (si pas utilisé dans des transactions)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier si le produit est utilisé dans des transactions
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE product_id = ?", (product_id,))
        transaction_count = cursor.fetchone()[0]
        
        if transaction_count > 0:
            conn.close()
            return False, f"Impossible de supprimer : {transaction_count} transaction(s) utilisent ce produit"
        
        try:
            # Supprimer l'historique des prix
            cursor.execute("DELETE FROM price_history WHERE product_id = ?", (product_id,))
            # Supprimer le produit
            cursor.execute("DELETE FROM financial_products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            return True, "Produit supprimé avec succès"
        except Exception as e:
            conn.close()
            return False, f"Erreur lors de la suppression : {e}"
    
    def add_transaction(self, account_id: int, product_symbol: str, transaction_type: str,
                       quantity: float, price: float, price_currency: str, transaction_date: datetime, 
                       fees: float = 0, fees_currency: str = "EUR"):
        """Ajoute une nouvelle transaction avec devise de saisie"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Récupère l'ID du produit
        cursor.execute("SELECT id FROM financial_products WHERE symbol = ?", (product_symbol,))
        product_id = cursor.fetchone()[0]
        
        # Convertir le prix dans les deux devises
        price_eur, price_usd = self.currency_converter.convert_price_to_both(price, price_currency)
        
        # Convertir les frais en EUR (devise de référence pour les frais)
        if fees_currency == "EUR":
            fees_eur = fees
        elif fees_currency == "USD":
            fees_eur = self.currency_converter.usd_to_eur(fees)
        else:
            fees_eur = fees  # Par défaut
        
        cursor.execute('''INSERT INTO transactions 
                        (account_id, product_id, transaction_type, quantity, price, price_currency,
                         price_eur, price_usd, transaction_date, fees, fees_currency)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (account_id, product_id, transaction_type, quantity, price, price_currency,
                       price_eur, price_usd, transaction_date, fees_eur, fees_currency))
        conn.commit()
        conn.close()
    
    def get_all_transactions(self) -> pd.DataFrame:
        """Récupère toutes les transactions avec détails et devises"""
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
                fp.symbol,
                fp.name as product_name,
                a.name as account_name,
                p.name as platform_name
            FROM transactions t
            JOIN financial_products fp ON t.product_id = fp.id
            JOIN accounts a ON t.account_id = a.id
            JOIN platforms p ON a.platform_id = p.id
            ORDER BY t.transaction_date DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            # Utiliser le prix EUR pour calculer le montant total
            df['total_amount'] = df['quantity'] * df['price_eur'] + df['fees']
        
        return df
    
    def update_transaction(self, transaction_id: int, account_id: int, product_symbol: str, 
                          transaction_type: str, quantity: float, price: float, 
                          transaction_date: datetime, fees: float = 0):
        """Met à jour une transaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Récupère l'ID du produit
        cursor.execute("SELECT id FROM financial_products WHERE symbol = ?", (product_symbol,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False, f"Produit avec le symbole '{product_symbol}' non trouvé"
        
        product_id = result[0]
        
        cursor.execute('''UPDATE transactions 
                        SET account_id = ?, product_id = ?, transaction_type = ?, 
                            quantity = ?, price = ?, transaction_date = ?, fees = ?
                        WHERE id = ?''',
                      (account_id, product_id, transaction_type, quantity, price, 
                       transaction_date, fees, transaction_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success, "Transaction mise à jour avec succès" if success else "Erreur lors de la mise à jour"
    
    def delete_transaction(self, transaction_id: int):
        """Supprime une transaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success, "Transaction supprimée avec succès" if success else "Transaction non trouvée"
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[dict]:
        """Récupère une transaction spécifique par son ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                t.id, t.account_id, t.transaction_type, t.quantity, 
                t.price, t.transaction_date, t.fees,
                fp.symbol, fp.name as product_name,
                a.name as account_name, p.name as platform_name
            FROM transactions t
            JOIN financial_products fp ON t.product_id = fp.id
            JOIN accounts a ON t.account_id = a.id
            JOIN platforms p ON a.platform_id = p.id
            WHERE t.id = ?
        ''', (transaction_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'account_id': result[1],
                'transaction_type': result[2],
                'quantity': result[3],
                'price': result[4],
                'transaction_date': result[5],
                'fees': result[6],
                'symbol': result[7],
                'product_name': result[8],
                'account_name': result[9],
                'platform_name': result[10]
            }
        return None
    
    def get_platforms(self) -> pd.DataFrame:
        """Récupère toutes les plateformes"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM platforms", conn)
        conn.close()
        return df
    
    def get_accounts(self) -> pd.DataFrame:
        """Récupère tous les comptes avec les plateformes"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT a.id, a.name, a.account_type, p.name as platform_name
            FROM accounts a
            JOIN platforms p ON a.platform_id = p.id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_financial_products(self) -> pd.DataFrame:
        """Récupère tous les produits financiers"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM financial_products ORDER BY symbol", conn)
        conn.close()
        return df
    
    def get_financial_product_by_id(self, product_id: int) -> Optional[pd.Series]:
        """Récupère un produit financier spécifique par son ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM financial_products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'symbol', 'name', 'product_type', 'currency', 'current_price', 'last_updated']
            return pd.Series(result, index=columns)
        return None
    
    def update_price(self, symbol: str, days_history: int = 30) -> bool:
        """Met à jour le prix d'un produit avec historique via yfinance et conversion EUR/USD"""
        try:
            ticker = yf.Ticker(symbol)
            # Récupérer l'historique sur la période demandée
            hist = ticker.history(period=f"{days_history}d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Récupérer la devise du produit
                cursor.execute("SELECT currency FROM financial_products WHERE symbol = ?", (symbol,))
                result = cursor.fetchone()
                product_currency = result[0] if result else 'EUR'
                
                # Convertir le prix actuel dans les deux devises
                price_eur, price_usd = self.currency_converter.convert_price_to_both(current_price, product_currency)
                
                # Met à jour le prix actuel
                cursor.execute('''UPDATE financial_products 
                                SET current_price = ?, current_price_eur = ?, current_price_usd = ?, last_updated = ?
                                WHERE symbol = ?''',
                              (current_price, price_eur, price_usd, datetime.now(), symbol))
                
                # Récupère l'ID du produit
                cursor.execute("SELECT id FROM financial_products WHERE symbol = ?", (symbol,))
                product_id = cursor.fetchone()[0]
                
                # Ajoute tout l'historique à la base avec conversion
                for date, row in hist.iterrows():
                    hist_price_eur, hist_price_usd = self.currency_converter.convert_price_to_both(
                        row['Close'], product_currency
                    )
                    cursor.execute('''INSERT OR REPLACE INTO price_history 
                                    (product_id, price, price_eur, price_usd, date)
                                    VALUES (?, ?, ?, ?, ?)''',
                                  (product_id, row['Close'], hist_price_eur, hist_price_usd, date.date()))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            st.error(f"Erreur lors de la mise à jour du prix pour {symbol}: {e}")
            return False
    
    def get_price_history(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Récupère l'historique des prix pour un produit sur une période avec EUR et USD"""
        conn = sqlite3.connect(self.db_path)
        
        # D'abord essayer avec les nouvelles colonnes
        try:
            query = '''
                SELECT ph.date, ph.price, ph.price_eur, ph.price_usd
                FROM price_history ph
                JOIN financial_products fp ON ph.product_id = fp.id
                WHERE fp.symbol = ? AND ph.date BETWEEN ? AND ?
                ORDER BY ph.date
            '''
            df = pd.read_sql_query(query, conn, params=(symbol, start_date.date(), end_date.date()))
        except sqlite3.OperationalError:
            # Fallback vers l'ancienne structure si les nouvelles colonnes n'existent pas
            query = '''
                SELECT ph.date, ph.price
                FROM price_history ph
                JOIN financial_products fp ON ph.product_id = fp.id
                WHERE fp.symbol = ? AND ph.date BETWEEN ? AND ?
                ORDER BY ph.date
            '''
            df = pd.read_sql_query(query, conn, params=(symbol, start_date.date(), end_date.date()))
            # Ajouter des colonnes vides pour la compatibilité
            if not df.empty:
                df['price_eur'] = None
                df['price_usd'] = None
        
        conn.close()
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df
    
    def get_portfolio_evolution(self, start_date: datetime, end_date: datetime, 
                               account_filter: list = None, product_filter: list = None, 
                               asset_class_filter: list = None) -> pd.DataFrame:
        """Calcule l'évolution de la valeur du portefeuille dans le temps avec breakdown détaillé"""
        conn = sqlite3.connect(self.db_path)
        
        # Base query pour récupérer les transactions
        base_query = '''
            SELECT 
                t.transaction_date,
                t.transaction_type,
                t.quantity,
                t.price,
                t.price_eur,
                t.price_usd,
                t.fees,
                fp.symbol,
                fp.name,
                fp.product_type,
                a.id as account_id,
                a.name as account_name,
                p.name as platform_name
            FROM transactions t
            JOIN financial_products fp ON t.product_id = fp.id
            JOIN accounts a ON t.account_id = a.id
            JOIN platforms p ON a.platform_id = p.id
            WHERE t.transaction_date <= ?
        '''
        
        params = [end_date]
        
        # Ajouter les filtres
        if account_filter:
            placeholders = ','.join(['?' for _ in account_filter])
            base_query += f' AND a.id IN ({placeholders})'
            params.extend(account_filter)
        
        if product_filter:
            placeholders = ','.join(['?' for _ in product_filter])
            base_query += f' AND fp.symbol IN ({placeholders})'
            params.extend(product_filter)
        
        if asset_class_filter:
            placeholders = ','.join(['?' for _ in asset_class_filter])
            base_query += f' AND fp.product_type IN ({placeholders})'
            params.extend(asset_class_filter)
        
        base_query += ' ORDER BY t.transaction_date'
        
        transactions = pd.read_sql_query(base_query, conn, params=params)
        conn.close()
        
        if transactions.empty:
            return pd.DataFrame()
        
        # Récupérer les devises de tous les produits d'un coup
        products_info = {}
        unique_symbols = transactions['symbol'].unique()
        for symbol in unique_symbols:
            product_row = transactions[transactions['symbol'] == symbol].iloc[0]
            # Récupérer la devise depuis la base
            conn_temp = sqlite3.connect(self.db_path)
            cursor_temp = conn_temp.cursor()
            cursor_temp.execute("SELECT currency FROM financial_products WHERE symbol = ?", (symbol,))
            currency_result = cursor_temp.fetchone()
            conn_temp.close()
            
            products_info[symbol] = {
                'currency': currency_result[0] if currency_result else 'EUR',
                'name': product_row['name'],
                'product_type': product_row['product_type']
            }
        
        # Générer les dates pour l'évolution (fréquence adaptée à la période)
        total_days = (end_date - start_date).days
        total_hours = (end_date - start_date).total_seconds() / 3600
        
        if total_hours <= 24:  # 1 jour ou moins
            freq = '1H'  # Horaire pour 1 jour
        elif total_days <= 7:
            freq = '2H'  # Toutes les 2h pour 7 jours
        elif total_days <= 30:
            freq = 'D'   # Quotidien pour 1 mois
        else:
            freq = 'W'   # Hebdomadaire pour plus de 30 jours (meilleur scaling)
            
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        evolution_data = []
        
        for current_date in date_range:
            daily_breakdown = {
                'account': {},
                'platform': {},
                'asset_class': {},
                'product': {}
            }
            daily_value = 0
            
            # Transactions jusqu'à cette date
            trans_to_date = transactions[
                pd.to_datetime(transactions['transaction_date']) <= current_date
            ]
            
            if trans_to_date.empty:
                evolution_data.append({
                    'date': current_date,
                    'total_value': 0,
                    'total_invested': 0,
                    'gain_loss': 0,
                    'breakdown_account': {},
                    'breakdown_platform': {},
                    'breakdown_asset_class': {},
                    'breakdown_product': {}
                })
                continue
            
            # Calculer les positions à cette date
            positions = {}
            
            for _, trans in trans_to_date.iterrows():
                symbol = trans['symbol']
                if symbol not in positions:
                    positions[symbol] = {
                        'quantity': 0,
                        'symbol': symbol,
                        'name': trans['name'],
                        'product_type': trans['product_type'],
                        'account_name': trans['account_name'],
                        'platform_name': trans['platform_name'],
                        'invested_amount': 0
                    }
                
                # Récupérer la devise du produit
                product_currency = products_info.get(symbol, {}).get('currency', 'EUR')
                
                if trans['transaction_type'] == 'BUY':
                    positions[symbol]['quantity'] += trans['quantity']
                    # Ajouter le montant investi (prix + frais, convertis en EUR)
                    
                    # Utiliser price_eur si disponible, sinon convertir
                    if 'price_eur' in trans and pd.notna(trans['price_eur']):
                        price_eur = trans['price_eur']
                    else:
                        # Conversion du prix original
                        product_currency = products_info.get(symbol, {}).get('currency', 'EUR')
                        price_eur = self.currency_converter.convert_to_eur(trans['price'], product_currency)
                    
                    invested_eur = trans['quantity'] * price_eur + (trans['fees'] if pd.notna(trans.get('fees')) else 0)
                    positions[symbol]['invested_amount'] += invested_eur
                else:  # SELL
                    # Calculer le ratio vendu
                    if positions[symbol]['quantity'] > 0:
                        ratio_sold = trans['quantity'] / positions[symbol]['quantity']
                        # Réduire proportionnellement le montant investi
                        positions[symbol]['invested_amount'] *= (1 - ratio_sold)
                    
                    positions[symbol]['quantity'] -= trans['quantity']
                    
                    # Si la quantité devient négative, remettre à 0
                    if positions[symbol]['quantity'] < 0:
                        positions[symbol]['quantity'] = 0
                        positions[symbol]['invested_amount'] = 0
            
            # Calculer le montant total investi à cette date
            total_invested_to_date = sum(pos['invested_amount'] for pos in positions.values() if pos['quantity'] > 0)
            
            # Récupérer les prix pour cette date
            for symbol, position in positions.items():
                if position['quantity'] > 0:
                    # Chercher le prix EUR le plus proche de cette date
                    price_history = self.get_price_history(symbol, current_date - timedelta(days=7), current_date)
                    closest_price_eur = None
                    
                    if not price_history.empty:
                        # Utiliser directement le prix EUR de l'historique si disponible
                        if 'price_eur' in price_history.columns and pd.notna(price_history.iloc[-1]['price_eur']):
                            closest_price_eur = price_history.iloc[-1]['price_eur']
                        else:
                            # Fallback au prix original avec conversion
                            closest_price = price_history.iloc[-1]['price']
                            if pd.notna(closest_price):
                                product_currency = products_info.get(symbol, {}).get('currency', 'EUR')
                                closest_price_eur = self.currency_converter.convert_to_eur(closest_price, product_currency)
                    else:
                        # Si pas d'historique, utiliser le prix EUR actuel du produit
                        conn_temp = sqlite3.connect(self.db_path)
                        cursor_temp = conn_temp.cursor()
                        cursor_temp.execute("SELECT current_price_eur, current_price, currency FROM financial_products WHERE symbol = ?", (symbol,))
                        result = cursor_temp.fetchone()
                        conn_temp.close()
                        
                        if result:
                            current_price_eur, current_price, currency = result
                            if current_price_eur and pd.notna(current_price_eur):
                                closest_price_eur = current_price_eur
                            elif current_price and pd.notna(current_price):
                                # Conversion du prix original
                                product_currency = currency or 'EUR'
                                closest_price_eur = self.currency_converter.convert_to_eur(current_price, product_currency)
                    
                    if closest_price_eur and closest_price_eur > 0:
                        value = position['quantity'] * closest_price_eur
                        daily_value += value
                        
                        # Breakdown par catégorie
                        account_name = position['account_name']
                        platform_name = position['platform_name']
                        asset_class = position['product_type']
                        product_name = position['name']  # Utiliser le nom au lieu du symbole
                        
                        if account_name not in daily_breakdown['account']:
                            daily_breakdown['account'][account_name] = 0
                        daily_breakdown['account'][account_name] += value
                        
                        if platform_name not in daily_breakdown['platform']:
                            daily_breakdown['platform'][platform_name] = 0
                        daily_breakdown['platform'][platform_name] += value
                        
                        if asset_class not in daily_breakdown['asset_class']:
                            daily_breakdown['asset_class'][asset_class] = 0
                        daily_breakdown['asset_class'][asset_class] += value
                        
                        if product_name not in daily_breakdown['product']:
                            daily_breakdown['product'][product_name] = 0
                        daily_breakdown['product'][product_name] += value
            
            evolution_data.append({
                'date': current_date,
                'total_value': daily_value,
                'total_invested': total_invested_to_date,
                'gain_loss': daily_value - total_invested_to_date,
                'breakdown_account': daily_breakdown['account'],
                'breakdown_platform': daily_breakdown['platform'],
                'breakdown_asset_class': daily_breakdown['asset_class'],
                'breakdown_product': daily_breakdown['product']
            })
        
        return pd.DataFrame(evolution_data)
    
    def get_available_filters(self):
        """Récupère les options disponibles pour les filtres"""
        conn = sqlite3.connect(self.db_path)
        
        # Comptes
        accounts = pd.read_sql_query('''
            SELECT a.id, a.name, p.name as platform_name
            FROM accounts a
            JOIN platforms p ON a.platform_id = p.id
        ''', conn)
        
        # Produits
        products = pd.read_sql_query('SELECT DISTINCT symbol, name FROM financial_products', conn)
        
        # Classes d'actifs
        asset_classes = pd.read_sql_query('SELECT DISTINCT product_type FROM financial_products', conn)
        
        conn.close()
        
        return {
            'accounts': accounts,
            'products': products,
            'asset_classes': asset_classes['product_type'].tolist()
        }
    
    def update_all_prices(self, days_history: int = 30):
        """Met à jour tous les prix avec historique"""
        products = self.get_financial_products()
        if products.empty:
            return
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, row in products.iterrows():
            status_text.text(f"Mise à jour de {row['symbol']} ({i+1}/{len(products)})")
            success = self.update_price(row['symbol'], days_history)
            if success:
                st.success(f"✅ {row['symbol']} mis à jour")
            else:
                st.error(f"❌ Erreur pour {row['symbol']}")
            progress_bar.progress((i + 1) / len(products))
            time.sleep(0.5)  # Éviter de surcharger l'API
        
        progress_bar.empty()
        status_text.empty()
    
    def initialize_price_history(self, days: int = 365):
        """Initialise l'historique des prix pour tous les produits avec conversion EUR/USD"""
        products = self.get_financial_products()
        if products.empty:
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, row in products.iterrows():
            status_text.text(f"Initialisation de l'historique pour {row['symbol']} ({i+1}/{len(products)})")
            
            try:
                ticker = yf.Ticker(row['symbol'])
                hist = ticker.history(period=f"{days}d")
                
                if not hist.empty:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    # Nettoyer l'ancien historique
                    cursor.execute("DELETE FROM price_history WHERE product_id = ?", (row['id'],))
                    
                    # Ajouter le nouvel historique avec conversion
                    for date, row_data in hist.iterrows():
                        price_eur, price_usd = self.currency_converter.convert_price_to_both(
                            row_data['Close'], row['currency']
                        )
                        cursor.execute('''INSERT INTO price_history (product_id, price, price_eur, price_usd, date)
                                        VALUES (?, ?, ?, ?, ?)''',
                                      (row['id'], row_data['Close'], price_eur, price_usd, date.date()))
                    
                    # Mettre à jour le prix actuel avec conversion
                    current_price = hist['Close'].iloc[-1]
                    current_price_eur, current_price_usd = self.currency_converter.convert_price_to_both(
                        current_price, row['currency']
                    )
                    cursor.execute('''UPDATE financial_products 
                                    SET current_price = ?, current_price_eur = ?, current_price_usd = ?, last_updated = ?
                                    WHERE id = ?''',
                                  (current_price, current_price_eur, current_price_usd, datetime.now(), row['id']))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Historique de {row['symbol']} initialisé ({len(hist)} jours)")
                else:
                    st.warning(f"⚠️ Aucune donnée trouvée pour {row['symbol']}")
                    
            except Exception as e:
                st.error(f"❌ Erreur pour {row['symbol']}: {e}")
            
            progress_bar.progress((i + 1) / len(products))
            time.sleep(1)  # Délai plus long pour éviter les limitations d'API
        
        progress_bar.empty()
        status_text.empty()
        st.success("🎉 Initialisation de l'historique terminée!")
    
    def get_portfolio_summary(self) -> pd.DataFrame:
        """Calcule le résumé du portefeuille en utilisant les prix EUR stockés"""
        conn = sqlite3.connect(self.db_path)
        
        # Essayer d'abord avec les nouvelles colonnes
        try:
            query = '''
                SELECT 
                    fp.symbol,
                    fp.name,
                    fp.current_price,
                    fp.current_price_eur,
                    fp.current_price_usd,
                    fp.currency,
                    fp.product_type,
                    a.name as account_name,
                    p.name as platform_name,
                    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity 
                             WHEN t.transaction_type = 'SELL' THEN -t.quantity 
                             ELSE 0 END) as total_quantity,
                    AVG(CASE WHEN t.transaction_type = 'BUY' THEN COALESCE(t.price_eur, t.price) ELSE NULL END) as avg_buy_price_eur,
                    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * COALESCE(t.price_eur, t.price) + COALESCE(t.fees, 0)
                             WHEN t.transaction_type = 'SELL' THEN -t.quantity * COALESCE(t.price_eur, t.price) - COALESCE(t.fees, 0)
                             ELSE 0 END) as total_invested_eur
                FROM transactions t
                JOIN financial_products fp ON t.product_id = fp.id
                JOIN accounts a ON t.account_id = a.id
                JOIN platforms p ON a.platform_id = p.id
                GROUP BY fp.symbol, a.id
                HAVING total_quantity > 0
            '''
            df = pd.read_sql_query(query, conn)
            
        except sqlite3.OperationalError:
            # Fallback vers l'ancienne structure
            query = '''
                SELECT 
                    fp.symbol,
                    fp.name,
                    fp.current_price,
                    fp.currency,
                    fp.product_type,
                    a.name as account_name,
                    p.name as platform_name,
                    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity 
                             WHEN t.transaction_type = 'SELL' THEN -t.quantity 
                             ELSE 0 END) as total_quantity,
                    AVG(CASE WHEN t.transaction_type = 'BUY' THEN t.price ELSE NULL END) as avg_buy_price,
                    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * t.price + COALESCE(t.fees, 0)
                             WHEN t.transaction_type = 'SELL' THEN -t.quantity * t.price - COALESCE(t.fees, 0)
                             ELSE 0 END) as total_invested
                FROM transactions t
                JOIN financial_products fp ON t.product_id = fp.id
                JOIN accounts a ON t.account_id = a.id
                JOIN platforms p ON a.platform_id = p.id
                GROUP BY fp.symbol, a.id
                HAVING total_quantity > 0
            '''
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                # Pas de nouvelles colonnes, utiliser l'ancien système entièrement
                self.currency_converter.get_eur_usd_rate()
                
                df['current_price_eur'] = df.apply(
                    lambda row: self.currency_converter.convert_to_eur(row['current_price'], row['currency']),
                    axis=1
                )
                df['avg_buy_price_eur'] = df.apply(
                    lambda row: self.currency_converter.convert_to_eur(row['avg_buy_price'], row['currency']),
                    axis=1
                )
                df['total_invested_eur'] = df.apply(
                    lambda row: self.currency_converter.convert_to_eur(row['total_invested'], row['currency']),
                    axis=1
                )
        
        conn.close()
        
        if not df.empty:
            # Utiliser les prix EUR stockés (ou convertis)
            if 'current_price_eur' in df.columns and df['current_price_eur'].notna().any():
                # Remplacer les None par une conversion à la volée
                df['current_price_eur'] = df.apply(
                    lambda row: row['current_price_eur'] if pd.notna(row['current_price_eur']) 
                    else self.currency_converter.convert_to_eur(row['current_price'], row['currency']),
                    axis=1
                )
                df['current_value'] = df['total_quantity'] * df['current_price_eur']
            else:
                # Fallback pour l'ancienne structure - conversion à la volée
                df['current_price_eur'] = df.apply(
                    lambda row: self.currency_converter.convert_to_eur(row['current_price'], row['currency']),
                    axis=1
                )
                df['current_value'] = df['total_quantity'] * df['current_price_eur']
            
            # Gérer les montants investis
            if 'total_invested_eur' in df.columns:
                # Remplacer les None par une conversion
                df['total_invested_eur'] = df.apply(
                    lambda row: row['total_invested_eur'] if pd.notna(row['total_invested_eur'])
                    else self.currency_converter.convert_to_eur(row.get('total_invested', 0), row['currency']),
                    axis=1
                )
            else:
                # Utiliser l'ancien système
                df['total_invested_eur'] = df.apply(
                    lambda row: self.currency_converter.convert_to_eur(row.get('total_invested', 0), row['currency']),
                    axis=1
                )
            
            # Gérer les prix d'achat moyens
            if 'avg_buy_price_eur' in df.columns:
                df['avg_buy_price_eur'] = df.apply(
                    lambda row: row['avg_buy_price_eur'] if pd.notna(row['avg_buy_price_eur'])
                    else self.currency_converter.convert_to_eur(row.get('avg_buy_price', 0), row['currency']),
                    axis=1
                )
            else:
                df['avg_buy_price_eur'] = df.apply(
                    lambda row: self.currency_converter.convert_to_eur(row.get('avg_buy_price', 0), row['currency']),
                    axis=1
                )
            
            # Calculs finaux
            df['gain_loss'] = df['current_value'] - df['total_invested_eur']
            df['gain_loss_pct'] = df.apply(
                lambda row: (row['gain_loss'] / row['total_invested_eur']) * 100 
                if row['total_invested_eur'] > 0 else 0, 
                axis=1
            )
            
            # Colonnes pour compatibilité
            df['total_invested'] = df['total_invested_eur']
            df['avg_buy_price'] = df['avg_buy_price_eur']
            
            # Remplacer tous les None par 0 pour éviter les erreurs d'affichage
            df = df.fillna(0)
        
        return df

# Interface Streamlit
def main():
    tracker = PortfolioTracker()
    
    # Initialiser les taux de change EUR/USD au démarrage avec feedback
    if 'rates_initialized' not in st.session_state:
        with st.spinner("🔄 Récupération du taux de change EUR/USD..."):
            success = tracker.currency_converter.get_eur_usd_rate(show_debug=True)
            if success:
                st.success(f"✅ Taux EUR/USD récupéré: 1 EUR = {tracker.currency_converter.eur_usd_rate:.4f} USD")
            else:
                st.warning("⚠️ Utilisation d'un taux de secours EUR/USD")
        st.session_state.rates_initialized = True
    
    # Sidebar pour la navigation
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox("Choisir une page", 
                               ["🏠 Tableau de Bord", "📈 Suivi de Portefeuille", 
                                "💼 Gestion des Comptes", "💸 Gestion des Transactions", 
                                "⚙️ Configuration"])
    
    if page == "🏠 Tableau de Bord":
        dashboard_page(tracker)
    elif page == "📈 Suivi de Portefeuille":
        portfolio_page(tracker)
    elif page == "💼 Gestion des Comptes":
        accounts_page(tracker)
    elif page == "💸 Gestion des Transactions":
        transaction_page(tracker)
    elif page == "⚙️ Configuration":
        config_page(tracker)

def dashboard_page(tracker):
    st.title("🏠 Tableau de Bord")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.caption("💱 Tous les prix sont stockés en EUR et USD - Calculs en EUR")
    
    with col2:
        if st.button("🔄 Actualiser tous les prix"):
            with st.spinner("Mise à jour des prix..."):
                tracker.update_all_prices(30)
            st.success("Prix mis à jour!")
            st.rerun()
    
    # Résumé du portefeuille
    portfolio = tracker.get_portfolio_summary()
    
    if not portfolio.empty:
        # Métriques principales
        total_invested = portfolio['total_invested'].sum()
        total_current = portfolio['current_value'].sum()
        total_gain_loss = total_current - total_invested
        total_gain_loss_pct = (total_gain_loss / total_invested) * 100 if total_invested > 0 else 0
        
        st.subheader("📊 Vue d'ensemble")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Valeur totale", f"{total_current:,.2f} €")
        with col2:
            st.metric("💸 Investi", f"{total_invested:,.2f} €")
        with col3:
            st.metric("📈 Plus/Moins value", f"{total_gain_loss:,.2f} €", 
                     delta=f"{total_gain_loss_pct:.2f}%")
        with col4:
            st.metric("📊 Nombre de positions", len(portfolio))
        
        # Vérifier s'il y a des données d'historique
        conn = sqlite3.connect(tracker.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM price_history")
        history_count = cursor.fetchone()[0]
        conn.close()
        
        if history_count > 0:
            # Évolution sur 1 an par défaut
            st.subheader("📈 Évolution (1 an)")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # 1 an par défaut
            
            evolution_data = tracker.get_portfolio_evolution(start_date, end_date)
            
            if not evolution_data.empty and len(evolution_data) > 1:
                # Calculer la variation
                first_value = evolution_data['total_value'].iloc[0]
                last_value = evolution_data['total_value'].iloc[-1]
                variation = last_value - first_value
                variation_pct = (variation / first_value) * 100 if first_value > 0 else 0
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Graphique simple et épuré
                    fig_quick = go.Figure()
                    fig_quick.add_trace(go.Scatter(
                        x=evolution_data['date'],
                        y=evolution_data['total_value'],
                        mode='lines',
                        name='Valeur du portefeuille',
                        line=dict(color='#1f77b4', width=3),
                        fill='tonexty',
                        hovertemplate='<b>%{x}</b><br>Valeur: %{y:,.2f} €<extra></extra>'
                    ))
                    
                    fig_quick.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Valeur (€)",
                        height=400,
                        showlegend=False,
                        margin=dict(l=0, r=0, t=20, b=0),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    # Améliorer la lisibilité des axes
                    fig_quick.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                    fig_quick.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
                    
                    st.plotly_chart(fig_quick, use_container_width=True)
                
                with col2:
                    st.metric("📊 Variation 1 an", 
                             f"{variation:,.2f} €",
                             delta=f"{variation_pct:.2f}%")
            else:
                st.info("📊 Pas assez de données pour afficher l'évolution sur 1 an.")
        else:
            st.info("🔧 Pour voir les courbes d'évolution, initialisez l'historique des prix dans la Configuration.")
        
        # Graphiques de répartition
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Répartition par produit")
            fig_pie = px.pie(portfolio, values='current_value', names='name',
                            title="")
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("🏢 Répartition par plateforme")
            platform_summary = portfolio.groupby('platform_name')['current_value'].sum().reset_index()
            fig_platform = px.bar(platform_summary, x='platform_name', y='current_value',
                                 title="")
            fig_platform.update_layout(
                height=400, 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_tickangle=-45,
                showlegend=False
            )
            st.plotly_chart(fig_platform, use_container_width=True)
        
        # Affichage des transactions récentes
        st.subheader("📋 Transactions récentes")
        all_transactions = tracker.get_all_transactions()
        recent_transactions = all_transactions.head(5) if not all_transactions.empty else pd.DataFrame()
        
        if not recent_transactions.empty:
            for _, transaction in recent_transactions.iterrows():
                type_color = "🟢" if transaction['transaction_type'] == 'BUY' else "🔴"
                type_label = "ACHAT" if transaction['transaction_type'] == 'BUY' else "VENTE"
                
                col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                with col1:
                    st.write(f"{type_color} {type_label}")
                with col2:
                    st.write(f"**{transaction['symbol']}**")
                with col3:
                    st.write(f"{transaction['quantity']:.4f} @ {transaction['price']:.2f}€")
                with col4:
                    st.write(f"{transaction['transaction_date'].strftime('%d/%m/%Y')}")
            
            # Statistique rapide
            total_transactions = len(all_transactions)
            if total_transactions > 5:
                st.caption(f"💡 Affichage des 5 dernières transactions sur {total_transactions} au total. Allez dans 'Gestion des Transactions' pour tout voir.")
            else:
                st.caption("💡 Allez dans 'Gestion des Transactions' pour modifier vos transactions.")
        else:
            st.info("💡 Aucune transaction enregistrée. Commencez par ajouter vos premières transactions dans 'Gestion des Transactions'.")
    else:
        st.info("Aucune position dans le portefeuille. Ajoutez des transactions pour commencer!")
        
        # Liens rapides pour démarrer
        st.subheader("🚀 Pour commencer")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**1. Configurez vos plateformes**")
            st.write("Ajoutez vos courtiers, banques, exchanges crypto...")
        
        with col2:
            st.write("**2. Ajoutez vos produits**")
            st.write("Actions, ETF, crypto-monnaies, obligations...")
        
        with col3:
            st.write("**3. Saisissez vos transactions**")
            st.write("Achats/ventes sur toutes plateformes")
        
        st.info("💡 Utilisez la navigation de gauche pour accéder aux différentes sections.")

def portfolio_page(tracker):
    st.title("📈 Suivi de Portefeuille Avancé")
    st.caption("💱 Tous les prix sont stockés en EUR et USD - Vous pouvez saisir vos transactions dans l'une ou l'autre devise")
    
    # Sidebar pour les filtres
    with st.sidebar:
        st.subheader("🔍 Filtres")
        
        # Sélection de la période (suppression de l'option personnalisée)
        st.write("**📅 Période d'analyse**")
        period = st.selectbox("Période", 
                            ["1 jour", "7 jours", "1 mois", "3 mois", "6 mois", "1 an", "2 ans"],
                            index=5)  # Par défaut : 1 an
        
        end_date = datetime.now()
        if period == "1 jour":
            start_date = end_date - timedelta(days=1)
        elif period == "7 jours":
            start_date = end_date - timedelta(days=7)
        elif period == "1 mois":
            start_date = end_date - timedelta(days=30)
        elif period == "3 mois":
            start_date = end_date - timedelta(days=90)
        elif period == "6 mois":
            start_date = end_date - timedelta(days=180)
        elif period == "1 an":
            start_date = end_date - timedelta(days=365)
        else:  # 2 ans
            start_date = end_date - timedelta(days=730)
        
        st.divider()
        
        # Options d'affichage des courbes (répartition cumulative par défaut)
        st.write("**📈 Options d'affichage**")
        chart_type = st.radio("Type de graphique", 
                             ["🌈 Répartition cumulative", "📊 Valeur totale", "💰 Investissement vs Plus/Moins Value"],
                             index=0,  # Répartition cumulative par défaut
                             help="Répartition cumulative: courbe empilée par catégorie | Valeur totale: courbe simple | Investissement vs +/- Value: évolution des montants investis et gains/pertes")
        
        if chart_type == "🌈 Répartition cumulative":
            breakdown_by = st.selectbox("Répartition par", 
                                      ["💼 Comptes", "🏷️ Classes d'actifs", "🏢 Plateformes", "📊 Produits Financiers"],
                                      help="Choisissez comment diviser la courbe cumulative")
        else:
            breakdown_by = "💼 Comptes"  # Valeur par défaut
        
        st.divider()
        
        # Récupérer les options de filtrage
        filters = tracker.get_available_filters()
        
        # Filtres par compte
        st.write("**💼 Comptes**")
        if not filters['accounts'].empty:
            account_options = ["Tous"] + [f"{row['name']} ({row['platform_name']})" 
                                        for _, row in filters['accounts'].iterrows()]
            selected_accounts = st.multiselect("Sélectionner les comptes", 
                                             account_options,
                                             default=["Tous"])
            
            if "Tous" in selected_accounts:
                account_filter = None
            else:
                account_indices = [i for i, opt in enumerate(account_options[1:]) 
                                 if opt in selected_accounts]
                account_filter = [filters['accounts'].iloc[i]['id'] for i in account_indices]
        else:
            account_filter = None
            st.info("Aucun compte disponible")
        
        # Filtres par produit
        st.write("**📊 Produits financiers**")
        if not filters['products'].empty:
            product_options = ["Tous"] + [f"{row['symbol']} - {row['name']}" 
                                        for _, row in filters['products'].iterrows()]
            selected_products = st.multiselect("Sélectionner les produits", 
                                             product_options,
                                             default=["Tous"])
            
            if "Tous" in selected_products:
                product_filter = None
            else:
                product_symbols = []
                for prod_opt in selected_products:
                    symbol = prod_opt.split(" - ")[0]
                    product_symbols.append(symbol)
                product_filter = product_symbols
        else:
            product_filter = None
            st.info("Aucun produit disponible")
        
        # Filtres par classe d'actifs
        st.write("**🏷️ Classes d'actifs**")
        if filters['asset_classes']:
            asset_options = ["Toutes"] + filters['asset_classes']
            selected_assets = st.multiselect("Sélectionner les classes", 
                                           asset_options,
                                           default=["Toutes"])
            
            if "Toutes" in selected_assets:
                asset_filter = None
            else:
                asset_filter = [asset for asset in selected_assets if asset != "Toutes"]
        else:
            asset_filter = None
            st.info("Aucune classe d'actifs disponible")
        
        # Bouton de mise à jour
        if st.button("🔄 Actualiser l'analyse"):
            st.rerun()
    
    # Contenu principal
    portfolio = tracker.get_portfolio_summary()
    
    if portfolio.empty:
        st.info("📝 Aucune position dans le portefeuille. Ajoutez des transactions pour commencer l'analyse!")
        return
    
    # Applique les filtres au portefeuille actuel
    filtered_portfolio = portfolio.copy()
    
    if account_filter:
        # Récupérer les noms des comptes filtrés
        account_names = [filters['accounts'][filters['accounts']['id'] == aid]['name'].iloc[0] 
                        for aid in account_filter]
        filtered_portfolio = filtered_portfolio[filtered_portfolio['account_name'].isin(account_names)]
    
    if product_filter:
        filtered_portfolio = filtered_portfolio[filtered_portfolio['symbol'].isin(product_filter)]
    
    if asset_filter:
        filtered_portfolio = filtered_portfolio[filtered_portfolio['product_type'].isin(asset_filter)]
    
    if filtered_portfolio.empty:
        st.warning("🔍 Aucune donnée ne correspond aux filtres sélectionnés.")
        return
    
    # Métriques du portefeuille filtré
    st.subheader("📊 Vue d'ensemble (filtrée)")
    
    total_invested = filtered_portfolio['total_invested'].sum()
    total_current = filtered_portfolio['current_value'].sum()
    total_gain_loss = total_current - total_invested
    total_gain_loss_pct = (total_gain_loss / total_invested) * 100 if total_invested > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Valeur actuelle", f"{total_current:,.2f} €")
    with col2:
        st.metric("💸 Montant investi", f"{total_invested:,.2f} €")
    with col3:
        st.metric("📈 Plus/Moins value", f"{total_gain_loss:,.2f} €", 
                 delta=f"{total_gain_loss_pct:.2f}%")
    with col4:
        st.metric("🎯 Positions", len(filtered_portfolio))
    
    # Évolution temporelle
    st.subheader("📈 Évolution de la valeur du portefeuille")
    
    # Récupérer l'évolution
    evolution_data = tracker.get_portfolio_evolution(
        start_date, end_date, account_filter, product_filter, asset_filter
    )
    
    if not evolution_data.empty and len(evolution_data) > 1:
        # Palette de couleurs cohérente et étendue
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
            '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
            '#c49c94', '#f7b6d3', '#c7c7c7', '#dbdb8d', '#9edae5',
            '#ad494a', '#d6616b', '#e7969c', '#7b4173', '#a55194',
            '#ce6dbd', '#de9ed6', '#3182bd', '#6baed6', '#9ecae1'
        ]
        category_colors = {}  # Pour stocker les couleurs utilisées
        
        # Graphique d'évolution
        if chart_type == "📊 Valeur totale":
            # Graphique simple
            fig_evolution = go.Figure()
            
            fig_evolution.add_trace(go.Scatter(
                x=evolution_data['date'],
                y=evolution_data['total_value'],
                mode='lines',
                name='Valeur totale',
                line=dict(color='#1f77b4', width=3),
                hovertemplate='<b>%{x}</b><br>Valeur: %{y:,.2f} €<extra></extra>',
                fill='tonexty' if len(evolution_data) > 2 else None
            ))
            
            fig_evolution.update_layout(
                title="Évolution de la valeur du portefeuille",
                xaxis_title="Date",
                yaxis_title="Valeur (€)",
                hovermode='x unified',
                showlegend=False,
                height=500
            )
            
            # Variables pour la section drill-down
            all_categories = []
            
        elif chart_type == "💰 Investissement vs Plus/Moins Value":
            # Graphique avec montant investi et plus/moins value
            fig_evolution = go.Figure()
            
            # Courbe du montant investi
            fig_evolution.add_trace(go.Scatter(
                x=evolution_data['date'],
                y=evolution_data['total_invested'],
                mode='lines',
                name='Montant investi',
                line=dict(color='#2E86AB', width=3),
                hovertemplate='<b>%{x}</b><br>Investi: %{y:,.2f} €<extra></extra>',
                fill='tonexty'
            ))
            
            # Courbe de la valeur actuelle
            fig_evolution.add_trace(go.Scatter(
                x=evolution_data['date'],
                y=evolution_data['total_value'],
                mode='lines',
                name='Valeur actuelle',
                line=dict(color='#A23B72', width=3),
                hovertemplate='<b>%{x}</b><br>Valeur: %{y:,.2f} €<extra></extra>'
            ))
            
            # Zone de gain/perte (remplissage entre les courbes)
            fig_evolution.add_trace(go.Scatter(
                x=evolution_data['date'],
                y=evolution_data['total_value'],
                mode='lines',
                line=dict(color='rgba(0,0,0,0)'),
                fill='tonexty',
                fillcolor='rgba(76, 175, 80, 0.3)',  # Vert transparent pour les gains
                showlegend=False,
                hoverinfo='skip'
            ))
            
            # Ligne de la plus/moins value (optionnel, pour plus de clarté)
            fig_evolution.add_trace(go.Scatter(
                x=evolution_data['date'],
                y=evolution_data['gain_loss'],
                mode='lines',
                name='Plus/Moins Value',
                line=dict(color='#F18F01', width=2, dash='dash'),
                hovertemplate='<b>%{x}</b><br>+/- Value: %{y:,.2f} €<extra></extra>',
                yaxis='y2'  # Axe secondaire pour la plus/moins value
            ))
            
            fig_evolution.update_layout(
                title="Évolution : Investissement vs Valeur Actuelle",
                xaxis_title="Date",
                yaxis_title="Montant (€)",
                yaxis2=dict(
                    title="Plus/Moins Value (€)",
                    overlaying='y',
                    side='right',
                    zeroline=True,
                    zerolinewidth=2,
                    zerolinecolor='gray'
                ),
                hovermode='x unified',
                showlegend=True,
                height=600,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Variables pour la section drill-down
            all_categories = []
            
        else:  # Répartition cumulative
            # Préparer les données pour le graphique empilé
            breakdown_key = {
                "💼 Comptes": 'breakdown_account',
                "🏷️ Classes d'actifs": 'breakdown_asset_class',
                "🏢 Plateformes": 'breakdown_platform',
                "📊 Produits Financiers": 'breakdown_product'
            }[breakdown_by]
            
            # Collecter toutes les catégories uniques
            all_categories = set()
            for _, row in evolution_data.iterrows():
                if isinstance(row[breakdown_key], dict):
                    all_categories.update(row[breakdown_key].keys())
            
            all_categories = sorted(list(all_categories))
            
            if not all_categories:
                st.warning("Aucune donnée de répartition disponible pour cette période.")
                return
            
            # Préparer les données pour chaque catégorie
            category_data = {}
            for category in all_categories:
                category_data[category] = []
                for _, row in evolution_data.iterrows():
                    breakdown = row[breakdown_key] if isinstance(row[breakdown_key], dict) else {}
                    category_data[category].append(breakdown.get(category, 0))
            
            # Créer le graphique empilé
            fig_evolution = go.Figure()
            
            # Stocker les couleurs utilisées pour cohérence
            for i, category in enumerate(all_categories):
                color = colors[i % len(colors)]
                category_colors[category] = color
                
                fig_evolution.add_trace(go.Scatter(
                    x=evolution_data['date'],
                    y=category_data[category],
                    mode='lines',
                    name=category,
                    stackgroup='one',
                    line=dict(width=0.5),
                    fillcolor=color,
                    hovertemplate=f'<b>{category}</b><br>' + 
                                '%{x}<br>Valeur: %{y:,.2f} €<extra></extra>'
                ))
            
            # Calculer le total pour chaque point
            total_values = []
            for _, row in evolution_data.iterrows():
                breakdown = row[breakdown_key] if isinstance(row[breakdown_key], dict) else {}
                total_values.append(sum(breakdown.values()))
            
            # Ajouter une ligne pour la valeur totale
            fig_evolution.add_trace(go.Scatter(
                x=evolution_data['date'],
                y=total_values,
                mode='lines',
                name='Total',
                line=dict(color='black', width=2, dash='dash'),
                hovertemplate='<b>Total</b><br>%{x}<br>Valeur: %{y:,.2f} €<extra></extra>'
            ))
            
            fig_evolution.update_layout(
                title=f"Évolution cumulative - {breakdown_by}",
                xaxis_title="Date",
                yaxis_title="Valeur (€)",
                hovermode='x unified',
                showlegend=True,
                height=600,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
        
        st.plotly_chart(fig_evolution, use_container_width=True)
        
        st.divider()
        
        # Section de répartition avec camembert unique
        st.subheader("🥧 Répartition du Portefeuille")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Sélecteur pour le type de répartition du camembert
            pie_breakdown = st.selectbox(
                "Afficher la répartition par :",
                ["🏢 Plateformes", "💼 Comptes", "🏷️ Classes d'actifs", "📊 Produits Financiers"],
                help="Choisissez le niveau de détail pour le camembert"
            )
        
        with col2:
            # Calcul des données pour le camembert
            if pie_breakdown == "🏢 Plateformes":
                pie_data = filtered_portfolio.groupby('platform_name')['current_value'].sum().reset_index()
                pie_data.columns = ['category', 'value']
                pie_title = "Répartition par Plateforme"
            elif pie_breakdown == "💼 Comptes":
                pie_data = filtered_portfolio.groupby('account_name')['current_value'].sum().reset_index()
                pie_data.columns = ['category', 'value']
                pie_title = "Répartition par Compte"
            elif pie_breakdown == "🏷️ Classes d'actifs":
                pie_data = filtered_portfolio.groupby('product_type')['current_value'].sum().reset_index()
                pie_data.columns = ['category', 'value']
                pie_title = "Répartition par Classe d'Actifs"
            else:  # Produits Financiers
                # Utiliser le nom au lieu du symbole pour les produits financiers
                pie_data = filtered_portfolio[['name', 'current_value']].copy()
                pie_data.columns = ['category', 'value']
                pie_title = "Répartition par Produit Financier"
            
            # Créer le camembert avec couleurs cohérentes
            fig_pie = go.Figure(data=[go.Pie(
                labels=pie_data['category'],
                values=pie_data['value'],
                hole=0.4,  # Donut chart pour un look moderne
                hovertemplate='<b>%{label}</b><br>Valeur: %{value:,.2f} €<br>Part: %{percent}<extra></extra>',
                textinfo='label+percent',
                textposition='auto',
                marker=dict(
                    colors=[colors[i % len(colors)] for i in range(len(pie_data))],
                    line=dict(color='white', width=2)
                )
            )])
            
            fig_pie.update_layout(
                title=pie_title,
                showlegend=True,
                height=400,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                ),
                margin=dict(t=50, b=50, l=50, r=150)
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.divider()
        
        # Tableau détaillé organisé par compte
        st.subheader("📋 Détail des Positions par Compte")
        
        # Organiser le portfolio par compte
        portfolio_by_account = filtered_portfolio.sort_values(['account_name', 'symbol'])
        
        if not portfolio_by_account.empty:
            current_account = None
            
            for _, position in portfolio_by_account.iterrows():
                # Afficher l'en-tête du compte si c'est un nouveau compte
                if current_account != position['account_name']:
                    current_account = position['account_name']
                    
                    # Calculer les totaux pour ce compte
                    account_positions = portfolio_by_account[portfolio_by_account['account_name'] == current_account]
                    account_total_value = account_positions['current_value'].sum()
                    account_total_invested = account_positions['total_invested'].sum()
                    account_total_gain_loss = account_total_value - account_total_invested
                    account_gain_loss_pct = (account_total_gain_loss / account_total_invested) * 100 if account_total_invested > 0 else 0
                    
                    # Couleur pour l'en-tête du compte
                    account_color = "green" if account_total_gain_loss >= 0 else "red"
                    
                    # Emoji selon le type de compte
                    account_type = account_positions.iloc[0]['account_name']
                    if "crypto" in account_type.lower() or "wallet" in account_type.lower():
                        account_emoji = "🪙"
                    elif "pea" in account_type.lower():
                        account_emoji = "🇫🇷"
                    elif "cto" in account_type.lower():
                        account_emoji = "💼"
                    elif "assurance" in account_type.lower():
                        account_emoji = "🛡️"
                    else:
                        account_emoji = "💰"
                    
                    st.markdown(f"### {account_emoji} {current_account} ({position['platform_name']})")
                    
                    # Métriques du compte
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("💰 Valeur", f"{account_total_value:,.2f} €")
                    with col2:
                        st.metric("💸 Investi", f"{account_total_invested:,.2f} €")
                    with col3:
                        st.metric("📈 +/- Value", f"{account_total_gain_loss:,.2f} €", 
                                delta=f"{account_gain_loss_pct:.2f}%")
                    with col4:
                        st.metric("🎯 Positions", len(account_positions))
                    
                    # Créer le DataFrame pour ce compte
                    account_df = account_positions[[
                        'symbol', 'name', 'product_type', 'total_quantity', 
                        'avg_buy_price_eur', 'current_price_eur', 'current_value', 
                        'total_invested', 'gain_loss', 'gain_loss_pct'
                    ]].copy()
                    
                    # Remplacer les None par 0 pour éviter les erreurs de formatage
                    account_df = account_df.fillna(0)
                    
                    # Ajouter des emojis selon le type de produit
                    def add_emoji_to_symbol(row):
                        symbol = row['symbol']
                        product_type = row['product_type']
                        if product_type == 'Crypto':
                            return f"🪙 {symbol}"
                        elif product_type == 'ETF':
                            return f"📊 {symbol}"
                        elif product_type == 'Action':
                            return f"📈 {symbol}"
                        else:
                            return f"💰 {symbol}"
                    
                    account_df['symbol_with_emoji'] = account_df.apply(add_emoji_to_symbol, axis=1)
                    
                    # Renommer les colonnes pour l'affichage
                    display_df = account_df[[
                        'symbol_with_emoji', 'name', 'product_type', 'total_quantity', 
                        'avg_buy_price_eur', 'current_price_eur', 'current_value', 
                        'total_invested', 'gain_loss', 'gain_loss_pct'
                    ]].copy()
                    
                    display_df.columns = [
                        'Symbole', 'Nom', 'Type', 'Quantité', 
                        'Prix Achat Moy.', 'Prix Actuel', 'Valeur Actuelle',
                        'Montant Investi', '+/- Value €', '+/- Value %'
                    ]
                    
                    # Fonction pour colorer les cellules selon les gains/pertes
                    def color_gains_losses(val):
                        if pd.isna(val):
                            return ''
                        try:
                            num_val = float(str(val).replace(',', '').replace('€', '').replace('%', '').strip())
                            if num_val > 0:
                                return 'background-color: #d4edda; color: #155724'  # Vert
                            elif num_val < 0:
                                return 'background-color: #f8d7da; color: #721c24'  # Rouge
                            else:
                                return 'background-color: #e2e3e5; color: #383d41'  # Gris
                        except:
                            return ''
                    
                    # Appliquer le style avec couleurs
                    styled_df = display_df.style.format({
                        'Quantité': '{:.4f}',
                        'Prix Achat Moy.': '{:.2f} €',
                        'Prix Actuel': '{:.2f} €',
                        'Valeur Actuelle': '{:,.2f} €',
                        'Montant Investi': '{:,.2f} €',
                        '+/- Value €': '{:,.2f} €',
                        '+/- Value %': '{:.2f}%'
                    }).applymap(color_gains_losses, subset=['+/- Value €', '+/- Value %'])
                    
                    # Afficher le tableau stylé
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")  # Séparateur entre comptes
        
    else:
        st.warning("📊 Pas suffisamment de données historiques pour générer les graphiques d'évolution. Actualisez l'historique des prix dans la configuration.")
        
        # Afficher quand même le tableau actuel
        st.subheader("📋 Positions actuelles")
        st.dataframe(
            filtered_portfolio[['symbol', 'name', 'platform_name', 'account_name', 
                              'total_quantity', 'avg_buy_price', 'current_price_eur', 
                              'current_value', 'gain_loss', 'gain_loss_pct']].style.format({
                'avg_buy_price': '{:.2f} €',
                'current_price_eur': '{:.2f} €',
                'current_value': '{:.2f} €',
                'gain_loss': '{:.2f} €',
                'gain_loss_pct': '{:.2f}%'
            }),
            use_container_width=True
        )

def accounts_page(tracker):
    st.title("💼 Gestion des Comptes")
    
    tab1, tab2, tab3 = st.tabs(["Plateformes", "Comptes", "Produits Financiers"])
    
    with tab1:
        st.subheader("Ajouter une plateforme")
        with st.form("add_platform"):
            platform_name = st.text_input("Nom de la plateforme")
            platform_desc = st.text_area("Description")
            if st.form_submit_button("Ajouter"):
                if tracker.add_platform(platform_name, platform_desc):
                    st.success("Plateforme ajoutée!")
                    st.rerun()
                else:
                    st.error("Cette plateforme existe déjà!")
        
        st.subheader("Plateformes existantes")
        platforms = tracker.get_platforms()
        
        if not platforms.empty:
            for idx, platform in platforms.iterrows():
                with st.expander(f"🏢 {platform['name']}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        with st.form(f"edit_platform_{platform['id']}"):
                            st.write("**Modifier cette plateforme :**")
                            new_name = st.text_input("Nom", value=platform['name'], key=f"pname_{platform['id']}")
                            new_desc = st.text_area("Description", value=platform['description'] or "", key=f"pdesc_{platform['id']}")
                            
                            col_update, col_delete = st.columns(2)
                            with col_update:
                                if st.form_submit_button("✏️ Modifier", type="primary"):
                                    if tracker.update_platform(platform['id'], new_name, new_desc):
                                        st.success("Plateforme modifiée!")
                                        st.rerun()
                                    else:
                                        st.error("Erreur lors de la modification")
                            
                            with col_delete:
                                if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                                    success, message = tracker.delete_platform(platform['id'])
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                    
                    with col2:
                        st.write("**Informations :**")
                        st.write(f"**ID :** {platform['id']}")
                        if platform['description']:
                            st.write(f"**Description :** {platform['description']}")
        else:
            st.info("Aucune plateforme ajoutée.")
    
    with tab2:
        st.subheader("Ajouter un compte")
        platforms = tracker.get_platforms()
        if not platforms.empty:
            with st.form("add_account"):
                platform_choice = st.selectbox("Plateforme", 
                                              options=platforms['id'].tolist(),
                                              format_func=lambda x: platforms[platforms['id']==x]['name'].iloc[0])
                account_name = st.text_input("Nom du compte")
                account_type = st.selectbox("Type de compte", 
                                          ["CTO", "PEA", "Assurance Vie", "Livret", "Portefeuille Crypto", "Autre"])
                if st.form_submit_button("Ajouter"):
                    tracker.add_account(platform_choice, account_name, account_type)
                    st.success("Compte ajouté!")
                    st.rerun()
        else:
            st.warning("Ajoutez d'abord une plateforme pour créer des comptes.")
        
        st.subheader("Comptes existants")
        accounts = tracker.get_accounts()
        
        if not accounts.empty:
            for idx, account in accounts.iterrows():
                with st.expander(f"💼 {account['name']} ({account['platform_name']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        with st.form(f"edit_account_{account['id']}"):
                            st.write("**Modifier ce compte :**")
                            
                            # Sélection de la plateforme
                            platform_ids = platforms['id'].tolist()
                            platform_names = [platforms[platforms['id']==pid]['name'].iloc[0] for pid in platform_ids]
                            current_platform_name = account['platform_name']
                            current_platform_idx = platform_names.index(current_platform_name)
                            
                            new_platform = st.selectbox("Plateforme", 
                                                       options=platform_ids,
                                                       index=int(current_platform_idx),
                                                       format_func=lambda x: platforms[platforms['id']==x]['name'].iloc[0],
                                                       key=f"platform_{account['id']}")
                            
                            new_account_name = st.text_input("Nom du compte", value=account['name'], key=f"aname_{account['id']}")
                            
                            account_types = ["CTO", "PEA", "Assurance Vie", "Livret", "Portefeuille Crypto", "Autre"]
                            current_type_idx = account_types.index(account['account_type']) if account['account_type'] in account_types else 0
                            new_account_type = st.selectbox("Type de compte", 
                                                          account_types,
                                                          index=current_type_idx,
                                                          key=f"atype_{account['id']}")
                            
                            col_update, col_delete = st.columns(2)
                            with col_update:
                                if st.form_submit_button("✏️ Modifier", type="primary"):
                                    if tracker.update_account(account['id'], new_platform, new_account_name, new_account_type):
                                        st.success("Compte modifié!")
                                        st.rerun()
                                    else:
                                        st.error("Erreur lors de la modification")
                            
                            with col_delete:
                                if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                                    success, message = tracker.delete_account(account['id'])
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                    
                    with col2:
                        st.write("**Informations :**")
                        st.write(f"**ID :** {account['id']}")
                        st.write(f"**Type :** {account['account_type']}")
                        st.write(f"**Plateforme :** {account['platform_name']}")
        else:
            st.info("Aucun compte ajouté.")
    
    with tab3:
        st.subheader("Ajouter un produit financier")
        
        # Aide pour trouver les symboles
        with st.expander("🔍 Comment trouver le bon symbole Yahoo Finance ?", expanded=False):
            st.markdown("""
            **🌐 Recherchez votre produit sur [Yahoo Finance France](https://fr.finance.yahoo.com/)**
            
            **📋 Exemples de symboles par type :**
            - **Actions françaises** : Ajoutez `.PA` → `MC.PA` (LVMH), `OR.PA` (L'Oréal)
            - **Actions américaines** : Symbole direct → `AAPL` (Apple), `MSFT` (Microsoft)
            - **ETF européens** : Avec `.PA` → `CW8.PA` (MSCI World), `EWLD.PA` (iShares)
            - **Crypto-monnaies** : Avec `-EUR` → `BTC-EUR` (Bitcoin), `ETH-EUR` (Ethereum)
            
            **🔍 Méthode de recherche :**
            1. Allez sur [fr.finance.yahoo.com](https://fr.finance.yahoo.com/)
            2. Tapez le nom de votre produit (ex: "Apple", "Bitcoin", "LVMH")
            3. Cliquez sur le bon résultat
            4. **Copiez le symbole affiché dans l'URL** (ex: `AAPL`, `BTC-EUR`, `MC.PA`)
            
            ⚠️ **Important** : Le produit sera vérifié automatiquement avant ajout !
            """)
        
        with st.form("add_product"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                symbol = st.text_input(
                    "Symbole Yahoo Finance *", 
                    placeholder="Ex: AAPL, BTC-EUR, MC.PA, CW8.PA",
                    help="Trouvez le symbole exact sur fr.finance.yahoo.com"
                )
                name = st.text_input(
                    "Nom du produit", 
                    placeholder="Ex: Apple Inc., Bitcoin, LVMH",
                    help="Nom descriptif (sera mis à jour automatiquement si trouvé sur Yahoo Finance)"
                )
            
            with col2:
                product_type = st.selectbox("Type", ["Action", "ETF", "Crypto", "Obligation", "Autre"])
                currency = st.selectbox("Devise", ["EUR", "USD", "GBP", "CHF", "CAD"])
            
            # Message d'information
            st.info("💡 Le produit sera automatiquement vérifié sur Yahoo Finance avant d'être ajouté à votre portefeuille.")
            
            submitted = st.form_submit_button("✅ Ajouter le produit", type="primary")
            
            if submitted:
                if not symbol.strip():
                    st.error("❌ Le symbole est obligatoire !")
                elif not name.strip():
                    st.error("❌ Le nom du produit est obligatoire !")
                else:
                    with st.spinner(f"🔍 Vérification du produit '{symbol}' sur Yahoo Finance..."):
                        success, message = tracker.add_financial_product(symbol.strip().upper(), name.strip(), product_type, currency)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                        st.markdown("**💡 Conseils :**")
                        st.markdown("- Vérifiez l'orthographe du symbole")
                        st.markdown("- Allez sur [Yahoo Finance](https://fr.finance.yahoo.com/) pour confirmer le symbole")
                        st.markdown("- Pour les actions françaises, ajoutez `.PA` (ex: `MC.PA` pour LVMH)")
                        st.markdown("- Pour les cryptos en euros, ajoutez `-EUR` (ex: `BTC-EUR`)")
        
        st.divider()
        
        st.subheader("Produits financiers")
        products = tracker.get_financial_products()
        
        if not products.empty:
            # Statistiques rapides
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total produits", len(products))
            with col2:
                with_price = products[products['current_price'].notna()]
                st.metric("💰 Avec prix", len(with_price))
            with col3:
                product_types = products['product_type'].value_counts()
                most_common = product_types.index[0] if not product_types.empty else "N/A"
                st.metric("🏆 Type principal", most_common)
            
            # Filtre par type
            filter_type = st.selectbox(
                "Filtrer par type :", 
                ["Tous"] + sorted(products['product_type'].unique().tolist()),
                key="product_filter"
            )
            
            if filter_type != "Tous":
                products = products[products['product_type'] == filter_type]
            
            # Affichage des produits avec options de modification
            for idx, product in products.iterrows():
                status_icon = "✅" if pd.notna(product['current_price']) else "⚠️"
                
                # Affichage des prix EUR et USD
                price_info = ""
                if pd.notna(product['current_price_eur']) and pd.notna(product['current_price_usd']):
                    price_info = f" - {product['current_price_eur']:.2f} EUR / {product['current_price_usd']:.2f} USD"
                elif pd.notna(product['current_price']):
                    price_info = f" - {product['current_price']:.2f} {product['currency']}"
                else:
                    price_info = " - Prix non disponible"
                
                with st.expander(f"{status_icon} {product['symbol']} - {product['name']}{price_info}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Formulaire de modification
                        with st.form(f"edit_product_{product['id']}"):
                            st.write("**Modifier ce produit :**")
                            st.caption("⚠️ Attention : Modifier le symbole vérifiera à nouveau l'existence sur Yahoo Finance")
                            
                            new_symbol = st.text_input("Symbole", value=product['symbol'], key=f"symbol_{product['id']}")
                            new_name = st.text_input("Nom", value=product['name'], key=f"name_{product['id']}")
                            new_type = st.selectbox("Type", 
                                                  ["Action", "ETF", "Crypto", "Obligation", "Autre"],
                                                  index=["Action", "ETF", "Crypto", "Obligation", "Autre"].index(product['product_type']) if product['product_type'] in ["Action", "ETF", "Crypto", "Obligation", "Autre"] else 0,
                                                  key=f"type_{product['id']}")
                            new_currency = st.selectbox("Devise", 
                                                      ["EUR", "USD", "GBP", "CHF", "CAD"],
                                                      index=["EUR", "USD", "GBP", "CHF", "CAD"].index(product['currency']) if product['currency'] in ["EUR", "USD", "GBP", "CHF", "CAD"] else 0,
                                                      key=f"currency_{product['id']}")
                            
                            col_update, col_delete = st.columns(2)
                            with col_update:
                                if st.form_submit_button("✏️ Modifier", type="primary"):
                                    # Si le symbole a changé, revérifier l'existence
                                    if new_symbol.strip().upper() != product['symbol']:
                                        with st.spinner(f"🔍 Vérification du nouveau symbole '{new_symbol}'..."):
                                            try:
                                                ticker = yf.Ticker(new_symbol.strip().upper())
                                                hist = ticker.history(period="1d")
                                                if hist.empty:
                                                    st.error(f"❌ Le symbole '{new_symbol}' n'existe pas sur Yahoo Finance !")
                                                else:
                                                    # Symbole valide, procéder à la modification
                                                    if tracker.update_financial_product(product['id'], new_symbol.strip().upper(), new_name.strip(), new_type, new_currency):
                                                        st.success("✅ Produit modifié avec succès !")
                                                        st.rerun()
                                                    else:
                                                        st.error("❌ Erreur lors de la modification (symbole déjà existant ?)")
                                            except Exception as e:
                                                st.error(f"❌ Erreur lors de la vérification du symbole '{new_symbol}' : {str(e)}")
                                    else:
                                        # Symbole inchangé, modification directe
                                        if tracker.update_financial_product(product['id'], new_symbol.strip().upper(), new_name.strip(), new_type, new_currency):
                                            st.success("✅ Produit modifié avec succès !")
                                            st.rerun()
                                        else:
                                            st.error("❌ Erreur lors de la modification")
                            
                            with col_delete:
                                if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                                    success, message = tracker.delete_financial_product(product['id'])
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                    
                    with col2:
                        # Informations actuelles
                        st.write("**Informations actuelles :**")
                        st.write(f"**Type :** {product['product_type']}")
                        st.write(f"**Devise native :** {product['currency']}")
                        
                        if pd.notna(product['current_price']):
                            st.write(f"**Prix natif :** {product['current_price']:.2f} {product['currency']}")
                        
                        if pd.notna(product['current_price_eur']):
                            st.write(f"**Prix EUR :** {product['current_price_eur']:.2f} EUR")
                        
                        if pd.notna(product['current_price_usd']):
                            st.write(f"**Prix USD :** {product['current_price_usd']:.2f} USD")
                        
                        if pd.notna(product['last_updated']):
                            update_date = pd.to_datetime(product['last_updated'])
                            st.write(f"**Dernière MAJ :** {update_date.strftime('%d/%m/%Y %H:%M')}")
                        
                        if pd.isna(product['current_price']):
                            st.warning("⚠️ Prix non disponible")
                        
                        # Bouton de mise à jour du prix
                        if st.button(f"🔄 Actualiser prix", key=f"update_price_{product['id']}"):
                            with st.spinner(f"Mise à jour de {product['symbol']}..."):
                                if tracker.update_price(product['symbol']):
                                    st.success("✅ Prix mis à jour !")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la mise à jour")
        else:
            st.info("📝 Aucun produit financier ajouté.")
            st.markdown("**🚀 Pour commencer :**")
            st.markdown("1. Trouvez votre produit sur [Yahoo Finance](https://fr.finance.yahoo.com/)")
            st.markdown("2. Copiez le symbole exact (ex: `AAPL`, `MC.PA`, `BTC-EUR`)")
            st.markdown("3. Ajoutez-le avec le formulaire ci-dessus")

def transaction_page(tracker):
    st.title("💸 Gestion des Transactions")
    st.caption("💡 Vous pouvez maintenant saisir vos prix d'achat en EUR ou USD - La conversion est automatique")
    
    # Onglets pour séparer nouvelle transaction et gestion
    tab1, tab2 = st.tabs(["🛒 Nouvelle Transaction", "📋 Gérer les Transactions"])
    
    accounts = tracker.get_accounts()
    products = tracker.get_financial_products()
    
    if accounts.empty or products.empty:
        st.warning("Vous devez d'abord créer des comptes et des produits financiers.")
        return
    
    with tab1:
        st.subheader("Ajouter une nouvelle transaction")
        
        with st.form("add_transaction"):
            col1, col2 = st.columns(2)
            
            with col1:
                account_choice = st.selectbox("Compte", 
                                            options=accounts['id'].tolist(),
                                            format_func=lambda x: f"{accounts[accounts['id']==x]['name'].iloc[0]} ({accounts[accounts['id']==x]['platform_name'].iloc[0]})")
                
                product_choice = st.selectbox("Produit", 
                                            options=products['symbol'].tolist(),
                                            format_func=lambda x: f"{x} - {products[products['symbol']==x]['name'].iloc[0]}")
                
                transaction_type = st.selectbox("Type", ["BUY", "SELL"])
                
                # Afficher les prix actuels du produit sélectionné
                if product_choice:
                    selected_product = products[products['symbol'] == product_choice].iloc[0]
                    if pd.notna(selected_product['current_price_eur']) and pd.notna(selected_product['current_price_usd']):
                        st.info(f"💰 Prix actuel: {selected_product['current_price_eur']:.2f} EUR / {selected_product['current_price_usd']:.2f} USD")
            
            with col2:
                quantity = st.number_input("Quantité", min_value=0.0, step=0.1)
                
                # Choix de la devise pour le prix
                price_currency = st.selectbox("Devise du prix d'achat", ["EUR", "USD"], 
                                            help="Choisissez la devise dans laquelle vous voulez saisir le prix")
                
                price = st.number_input(f"Prix unitaire ({price_currency})", min_value=0.0, step=0.01)
                
                fees = st.number_input("Frais (EUR)", min_value=0.0, step=0.01, value=0.0,
                                     help="Les frais sont toujours saisis en EUR")
                transaction_date = st.date_input("Date de transaction", value=datetime.now().date())
            
            if st.form_submit_button("Ajouter la transaction", type="primary"):
                tracker.add_transaction(account_choice, product_choice, transaction_type,
                                      quantity, price, price_currency, 
                                      datetime.combine(transaction_date, datetime.min.time()), fees)
                st.success(f"Transaction ajoutée! Prix: {price:.2f} {price_currency}")
                st.rerun()
    
    with tab2:
        st.subheader("Gérer les transactions existantes")
        
        # Récupérer toutes les transactions
        all_transactions = tracker.get_all_transactions()
        
        if all_transactions.empty:
            st.info("📝 Aucune transaction enregistrée.")
            return
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre par compte
            account_options = ["Tous"] + all_transactions['account_name'].unique().tolist()
            selected_account = st.selectbox("Filtrer par compte", account_options)
        
        with col2:
            # Filtre par type
            type_options = ["Tous", "BUY", "SELL"]
            selected_type = st.selectbox("Filtrer par type", type_options)
        
        with col3:
            # Filtre par période
            period_options = ["Toutes", "7 derniers jours", "30 derniers jours", "3 derniers mois"]
            selected_period = st.selectbox("Filtrer par période", period_options)
        
        # Appliquer les filtres
        filtered_transactions = all_transactions.copy()
        
        if selected_account != "Tous":
            filtered_transactions = filtered_transactions[filtered_transactions['account_name'] == selected_account]
        
        if selected_type != "Tous":
            filtered_transactions = filtered_transactions[filtered_transactions['transaction_type'] == selected_type]
        
        if selected_period != "Toutes":
            end_date = datetime.now()
            if selected_period == "7 derniers jours":
                start_date = end_date - timedelta(days=7)
            elif selected_period == "30 derniers jours":
                start_date = end_date - timedelta(days=30)
            else:  # 3 derniers mois
                start_date = end_date - timedelta(days=90)
            
            filtered_transactions = filtered_transactions[
                filtered_transactions['transaction_date'] >= start_date
            ]
        
        # Statistiques rapides
        if not filtered_transactions.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Transactions", len(filtered_transactions))
            with col2:
                buy_count = len(filtered_transactions[filtered_transactions['transaction_type'] == 'BUY'])
                st.metric("🛒 Achats", buy_count)
            with col3:
                sell_count = len(filtered_transactions[filtered_transactions['transaction_type'] == 'SELL'])
                st.metric("💰 Ventes", sell_count)
            with col4:
                total_fees = filtered_transactions['fees'].sum()
                st.metric("💸 Frais totaux", f"{total_fees:.2f} €")
            
            st.divider()
            
            # Affichage des transactions par groupe
            current_date = None
            
            for _, transaction in filtered_transactions.iterrows():
                transaction_date = transaction['transaction_date'].date()
                
                # Afficher l'en-tête de date si c'est une nouvelle date
                if current_date != transaction_date:
                    current_date = transaction_date
                    st.markdown(f"### 📅 {transaction_date.strftime('%d/%m/%Y')}")
                
                # Couleur selon le type de transaction
                if transaction['transaction_type'] == 'BUY':
                    type_color = "🟢"
                    type_label = "ACHAT"
                else:
                    type_color = "🔴"
                    type_label = "VENTE"
                
                # Afficher la transaction dans un expander
                total_amount = transaction['total_amount']
                transaction_title = f"{type_color} {type_label} • {transaction['symbol']} • {transaction['quantity']:.4f} • {total_amount:,.2f} €"
                
                with st.expander(transaction_title):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Formulaire de modification
                        with st.form(f"edit_transaction_{transaction['id']}"):
                            st.write("**Modifier cette transaction :**")
                            
                            # Champs modifiables
                            edit_col1, edit_col2 = st.columns(2)
                            
                            with edit_col1:
                                # Compte
                                accounts_list = accounts['id'].tolist()
                                current_account_idx = 0
                                for idx, acc_id in enumerate(accounts_list):
                                    if acc_id == transaction['account_id']:
                                        current_account_idx = idx
                                        break
                                
                                new_account = st.selectbox("Compte", 
                                                         options=accounts_list,
                                                         index=current_account_idx,
                                                         format_func=lambda x: f"{accounts[accounts['id']==x]['name'].iloc[0]} ({accounts[accounts['id']==x]['platform_name'].iloc[0]})",
                                                         key=f"account_{transaction['id']}")
                                
                                # Produit
                                products_list = products['symbol'].tolist()
                                current_product_idx = 0
                                for idx, symbol in enumerate(products_list):
                                    if symbol == transaction['symbol']:
                                        current_product_idx = idx
                                        break
                                
                                new_product = st.selectbox("Produit", 
                                                         options=products_list,
                                                         index=current_product_idx,
                                                         format_func=lambda x: f"{x} - {products[products['symbol']==x]['name'].iloc[0]}",
                                                         key=f"product_{transaction['id']}")
                                
                                new_type = st.selectbox("Type", 
                                                       ["BUY", "SELL"],
                                                       index=0 if transaction['transaction_type'] == 'BUY' else 1,
                                                       key=f"type_{transaction['id']}")
                            
                            with edit_col2:
                                new_quantity = st.number_input("Quantité", 
                                                             min_value=0.0, 
                                                             step=0.0001,
                                                             value=float(transaction['quantity']),
                                                             key=f"quantity_{transaction['id']}")
                                
                                new_price = st.number_input("Prix unitaire", 
                                                           min_value=0.0, 
                                                           step=0.01,
                                                           value=float(transaction['price']),
                                                           key=f"price_{transaction['id']}")
                                
                                new_fees = st.number_input("Frais", 
                                                          min_value=0.0, 
                                                          step=0.01,
                                                          value=float(transaction['fees']),
                                                          key=f"fees_{transaction['id']}")
                                
                                new_date = st.date_input("Date", 
                                                        value=transaction['transaction_date'].date(),
                                                        key=f"date_{transaction['id']}")
                            
                            # Boutons d'action
                            col_update, col_delete = st.columns(2)
                            
                            with col_update:
                                if st.form_submit_button("✏️ Modifier", type="primary"):
                                    success, message = tracker.update_transaction(
                                        transaction['id'], new_account, new_product, new_type,
                                        new_quantity, new_price, 
                                        datetime.combine(new_date, datetime.min.time()), new_fees
                                    )
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                            
                            with col_delete:
                                if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                                    success, message = tracker.delete_transaction(transaction['id'])
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                    
                    with col2:
                        # Informations de la transaction
                        st.write("**Détails :**")
                        st.write(f"**Compte :** {transaction['account_name']}")
                        st.write(f"**Plateforme :** {transaction['platform_name']}")
                        st.write(f"**Produit :** {transaction['product_name']}")
                        st.write(f"**Type :** {transaction['transaction_type']}")
                        st.write(f"**Quantité :** {transaction['quantity']:.4f}")
                        
                        # Afficher le prix dans la devise de saisie et en EUR
                        if pd.notna(transaction.get('price_currency')):
                            st.write(f"**Prix saisi :** {transaction['price']:.2f} {transaction['price_currency']}")
                            if transaction['price_currency'] != 'EUR' and pd.notna(transaction.get('price_eur')):
                                st.write(f"**Prix EUR :** {transaction['price_eur']:.2f} EUR")
                        else:
                            st.write(f"**Prix unitaire :** {transaction['price']:.2f} EUR")
                        
                        st.write(f"**Frais :** {transaction['fees']:.2f} EUR")
                        st.write(f"**Total :** {total_amount:,.2f} EUR")
                        st.write(f"**Date :** {transaction['transaction_date'].strftime('%d/%m/%Y %H:%M')}")
        else:
            st.info("🔍 Aucune transaction ne correspond aux filtres sélectionnés.")

def config_page(tracker):
    st.title("⚙️ Configuration")
    
    st.subheader("🔄 Gestion des prix")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Mise à jour des prix actuels**")
        update_days = st.number_input("Jours d'historique à récupérer", 
                                    min_value=1, max_value=365, value=30)
        if st.button("🔄 Actualiser tous les prix"):
            with st.spinner("Mise à jour en cours..."):
                tracker.update_all_prices(update_days)
            st.success("Tous les prix ont été mis à jour!")
            st.rerun()
    
    with col2:
        st.write("**Mise à jour d'un produit spécifique**")
        products = tracker.get_financial_products()
        if not products.empty:
            product_to_update = st.selectbox("Produit à actualiser", 
                                           products['symbol'].tolist(),
                                           format_func=lambda x: f"{x} - {products[products['symbol']==x]['name'].iloc[0]}")
            if st.button("🔄 Actualiser ce produit"):
                if tracker.update_price(product_to_update, update_days):
                    st.success(f"Prix de {product_to_update} mis à jour!")
                    st.rerun()
                else:
                    st.error(f"Erreur lors de la mise à jour de {product_to_update}")
    
    st.divider()
    
    st.subheader("💱 Gestion des devises")
    st.write("L'application stocke automatiquement tous les prix en EUR et USD.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Actualiser le taux EUR/USD"):
            with st.spinner("Mise à jour du taux de change EUR/USD..."):
                # Forcer la mise à jour en réinitialisant la date
                tracker.currency_converter.last_update = None
                success = tracker.currency_converter.get_eur_usd_rate(show_debug=True)
                if success:
                    st.success("✅ Taux EUR/USD mis à jour!")
                else:
                    st.warning("⚠️ Taux de secours utilisé")
            st.rerun()
    
    with col2:
        with st.expander("📊 Taux de change EUR/USD actuel", expanded=False):
            st.text(tracker.currency_converter.get_rate_info())
    
    st.divider()
    
    st.subheader("📈 Initialisation de l'historique des prix")
    st.write("""
    **Important :** Pour utiliser les courbes d'évolution, vous devez d'abord initialiser l'historique des prix.
    Cette opération récupère les données historiques pour tous vos produits financiers.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        history_days = st.number_input("Nombre de jours d'historique", 
                                     min_value=30, max_value=2000, value=365,
                                     help="Plus vous prenez de jours, plus l'opération sera longue")
        
        estimated_time = len(products) * 2 if not products.empty else 0
        st.info(f"⏱️ Temps estimé : ~{estimated_time} secondes pour {len(products) if not products.empty else 0} produits")
        
        if st.button("🚀 Initialiser l'historique complet", type="primary"):
            if not products.empty:
                st.warning("⚠️ Cette opération peut prendre plusieurs minutes. Ne fermez pas la page.")
                tracker.initialize_price_history(history_days)
                st.success("🎉 Historique initialisé ! Vous pouvez maintenant utiliser les courbes d'évolution.")
                st.rerun()
            else:
                st.error("Aucun produit financier trouvé. Ajoutez d'abord des produits.")
    
    with col2:
        # Statistiques sur l'historique actuel - maintenant dans un expander
        if not products.empty:
            with st.expander("📊 État de l'historique actuel", expanded=False):
                conn = sqlite3.connect(tracker.db_path)
                cursor = conn.cursor()
                
                st.write("**Détail par produit :**")
                
                for _, product in products.iterrows():
                    cursor.execute('''SELECT COUNT(*), MIN(date), MAX(date) 
                                    FROM price_history WHERE product_id = ?''', (product['id'],))
                    result = cursor.fetchone()
                    count, min_date, max_date = result
                    
                    if count > 0:
                        st.write(f"**{product['symbol']}** : {count} points de données")
                        st.write(f"   📅 Du {min_date} au {max_date}")
                    else:
                        st.write(f"**{product['symbol']}** : ❌ Aucun historique")
                
                conn.close()
    
    st.divider()
    
    st.subheader("📊 Informations sur la base de données")
    
    # Statistiques générales
    platforms = tracker.get_platforms()
    accounts = tracker.get_accounts()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏢 Plateformes", len(platforms))
    with col2:
        st.metric("💼 Comptes", len(accounts))
    with col3:
        st.metric("📈 Produits", len(products))
    with col4:
        # Calculer le nombre de transactions
        conn = sqlite3.connect(tracker.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        transaction_count = cursor.fetchone()[0]
        
        # Calculer le nombre total de points d'historique
        cursor.execute("SELECT COUNT(*) FROM price_history")
        history_count = cursor.fetchone()[0]
        conn.close()
        
        st.metric("💸 Transactions", transaction_count)
    
    # Affichage de l'état des prix
    if not products.empty:
        st.subheader("💰 État des prix")
        
        # Séparer les produits avec et sans prix
        with_price = products[products['current_price'].notna()]
        without_price = products[products['current_price'].isna()]
        
        if not with_price.empty:
            st.write("**✅ Produits avec prix à jour :**")
            price_display = with_price[['symbol', 'name', 'current_price', 'currency', 'last_updated']].copy()
            price_display['Prix'] = price_display.apply(
                lambda row: f"{row['current_price']:.2f} {row['currency']}" 
                if pd.notna(row['current_price']) else "N/A", axis=1
            )
            st.dataframe(price_display[['symbol', 'name', 'Prix', 'last_updated']], 
                        use_container_width=True)
        
        if not without_price.empty:
            st.write("**⚠️ Produits sans prix (à actualiser) :**")
            st.dataframe(without_price[['symbol', 'name', 'product_type']], 
                        use_container_width=True)
    
    st.metric("📈 Points d'historique", history_count)
    
    st.divider()
    
    # Section de maintenance
    st.subheader("🛠️ Maintenance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**🧹 Nettoyage**")
        if st.button("Nettoyer l'historique (>1 an)"):
            conn = sqlite3.connect(tracker.db_path)
            cursor = conn.cursor()
            one_year_ago = datetime.now() - timedelta(days=365)
            cursor.execute("DELETE FROM price_history WHERE date < ?", (one_year_ago,))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            st.success(f"✅ {deleted_count} entrées supprimées")
            st.rerun()
    
    with col2:
        st.write("**📥 Sauvegarde**")
        if st.button("Info sauvegarde"):
            st.info("💡 Pour sauvegarder : copiez le fichier 'portfolio.db' depuis le répertoire de l'application")
    
    with col3:
        st.write("**🔄 Rechargement**")
        if st.button("Recharger l'application"):
            st.rerun()

if __name__ == "__main__":
    main()