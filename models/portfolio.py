import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

from models.database import DatabaseManager
from models.currency import CurrencyConverter
from utils.yahoo_finance import YahooFinanceUtils

class PortfolioTracker:
    """Gestionnaire principal du portefeuille financier"""
    
    def __init__(self, db_path: str = "portfolio.db"):
        self.db = DatabaseManager(db_path)
        self.currency_converter = CurrencyConverter()
        self.yahoo_utils = YahooFinanceUtils()
    
    # Méthodes pour les plateformes (delegation vers database)
    def add_platform(self, name: str, description: str = "") -> bool:
        return self.db.add_platform(name, description)
    
    def update_platform(self, platform_id: int, name: str, description: str = "") -> bool:
        return self.db.update_platform(platform_id, name, description)
    
    def delete_platform(self, platform_id: int) -> Tuple[bool, str]:
        return self.db.delete_platform(platform_id)
    
    def get_platforms(self) -> pd.DataFrame:
        return self.db.get_platforms()
    
    # Méthodes pour les comptes
    def add_account(self, platform_id: int, name: str, account_type: str) -> bool:
        return self.db.add_account(platform_id, name, account_type)
    
    def update_account(self, account_id: int, platform_id: int, name: str, account_type: str) -> bool:
        return self.db.update_account(account_id, platform_id, name, account_type)
    
    def delete_account(self, account_id: int) -> Tuple[bool, str]:
        return self.db.delete_account(account_id)
    
    def get_accounts(self) -> pd.DataFrame:
        return self.db.get_accounts()
    
    # Méthodes pour les produits financiers avec détection automatique
    def add_financial_product(self, symbol: str, manual_name: str = "") -> Tuple[bool, str]:
        """
        Ajoute un nouveau produit financier avec détection automatique de la devise et des informations
        """
        try:
            # Récupérer les informations complètes via Yahoo Finance
            success, product_info = self.yahoo_utils.get_product_info(symbol)
            
            if not success:
                return False, product_info.get('error', 'Erreur inconnue')
            
            # Utiliser le nom manuel si fourni, sinon celui de Yahoo Finance
            if manual_name.strip():
                product_info['name'] = manual_name.strip()
            
            # Convertir le prix actuel dans toutes les devises
            current_price = product_info['current_price']
            currency = product_info['currency']
            
            price_eur, price_usd = self.currency_converter.convert_price_to_both(current_price, currency)
            
            product_info['current_price_eur'] = price_eur
            product_info['current_price_usd'] = price_usd
            
            # Ajouter à la base de données
            success, message = self.db.add_financial_product(product_info)
            
            if success:
                # Ajouter quelques points d'historique récent
                self._add_recent_price_history(symbol, currency)
            
            return success, message
            
        except Exception as e:
            return False, f"Erreur lors de l'ajout du produit '{symbol}': {str(e)}"
    
    def _add_recent_price_history(self, symbol: str, currency: str, days: int = 30):
        """Ajoute l'historique récent des prix pour un nouveau produit"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            
            if not hist.empty:
                product = self.db.get_financial_product_by_symbol(symbol)
                if product is not None:
                    product_id = product['id']
                    
                    # Ajouter l'historique avec conversion EUR/USD
                    for date, row in hist.iterrows():
                        price_eur, price_usd = self.currency_converter.convert_price_to_both(
                            row['Close'], currency
                        )
                        
                        # Insérer dans price_history
                        import sqlite3
                        conn = sqlite3.connect(self.db.db_path)
                        cursor = conn.cursor()
                        cursor.execute('''INSERT OR REPLACE INTO price_history 
                                        (product_id, price, price_eur, price_usd, date)
                                        VALUES (?, ?, ?, ?, ?)''',
                                      (product_id, row['Close'], price_eur, price_usd, date.date()))
                        conn.commit()
                        conn.close()
                        
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'historique pour {symbol}: {e}")
    
    def update_financial_product(self, product_id: int, symbol: str, name: str, 
                               product_type: str, currency: str) -> bool:
        return self.db.update_financial_product(product_id, symbol, name, product_type, currency)
    
    def delete_financial_product(self, product_id: int) -> Tuple[bool, str]:
        return self.db.delete_financial_product(product_id)
    
    def get_financial_products(self) -> pd.DataFrame:
        return self.db.get_financial_products()
    
    def get_financial_product_by_id(self, product_id: int) -> Optional[pd.Series]:
        """Récupère un produit financier par son ID"""
        products = self.get_financial_products()
        if not products.empty:
            result = products[products['id'] == product_id]
            if not result.empty:
                return result.iloc[0]
        return None
    
    # Méthodes pour les transactions avec conversion automatique
    def add_transaction(self, account_id: int, product_symbol: str, transaction_type: str,
                       quantity: float, price: float, price_currency: str, 
                       transaction_date: datetime, fees: float = 0, fees_currency: str = "EUR"):
        """
        Ajoute une nouvelle transaction avec conversion automatique des devises
        en utilisant les taux de change de la date de transaction
        """
        # Récupérer l'ID du produit
        product = self.db.get_financial_product_by_symbol(product_symbol)
        if product is None:
            raise ValueError(f"Produit avec le symbole '{product_symbol}' non trouvé")
        
        product_id = product['id']
        
        # Convertir le prix dans les deux devises avec le taux historique
        price_eur = self.currency_converter.convert_with_historical_rate(
            price, price_currency, 'EUR', transaction_date
        )
        price_usd = self.currency_converter.convert_with_historical_rate(
            price, price_currency, 'USD', transaction_date
        )
        
        # Récupérer le taux EUR/USD de la date de transaction pour l'enregistrer
        exchange_rate_eur_usd = self.currency_converter.get_historical_eur_usd_rate(transaction_date)
        
        # Convertir les frais en EUR
        if fees_currency != 'EUR':
            fees_eur = self.currency_converter.convert_with_historical_rate(
                fees, fees_currency, 'EUR', transaction_date
            )
        else:
            fees_eur = fees
        
        # Sauvegarder le taux de change utilisé
        self.db.save_exchange_rate('EUR', 'USD', exchange_rate_eur_usd, transaction_date)
        
        # Ajouter la transaction
        return self.db.add_transaction(
            account_id, product_id, transaction_type, quantity, price, price_currency,
            price_eur, price_usd, transaction_date, fees_eur, fees_currency, exchange_rate_eur_usd
        )
    
    def get_all_transactions(self) -> pd.DataFrame:
        return self.db.get_all_transactions()
    
    def update_transaction(self, transaction_id: int, account_id: int, product_symbol: str, 
                          transaction_type: str, quantity: float, price: float, price_currency: str,
                          transaction_date: datetime, fees: float = 0) -> Tuple[bool, str]:
        """Met à jour une transaction avec support du changement de devise"""
        try:
            # Récupérer l'ID du produit
            product = self.db.get_financial_product_by_symbol(product_symbol)
            if product is None:
                return False, f"Produit avec le symbole '{product_symbol}' non trouvé"
            
            product_id = product['id']
            
            # Convertir le prix dans les deux devises avec le taux historique de la nouvelle date
            price_eur = self.currency_converter.convert_with_historical_rate(
                price, price_currency, 'EUR', transaction_date
            )
            price_usd = self.currency_converter.convert_with_historical_rate(
                price, price_currency, 'USD', transaction_date
            )
            
            # Récupérer le taux EUR/USD de la date de transaction
            exchange_rate_eur_usd = self.currency_converter.get_historical_eur_usd_rate(transaction_date)
            
            # Convertir les frais en EUR (on suppose qu'ils sont déjà en EUR)
            fees_eur = fees
            
            # Sauvegarder le taux de change utilisé
            self.db.save_exchange_rate('EUR', 'USD', exchange_rate_eur_usd, transaction_date)
            
            # Mettre à jour la transaction
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''UPDATE transactions 
                            SET account_id = ?, product_id = ?, transaction_type = ?, 
                                quantity = ?, price = ?, price_currency = ?,
                                price_eur = ?, price_usd = ?, transaction_date = ?, 
                                fees = ?, exchange_rate_eur_usd = ?
                            WHERE id = ?''',
                          (account_id, product_id, transaction_type, quantity, price, price_currency,
                           price_eur, price_usd, transaction_date, fees_eur, exchange_rate_eur_usd, transaction_id))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                return True, f"Transaction mise à jour avec succès! Prix: {price:.2f} {price_currency} (converti: {price_eur:.2f} EUR / {price_usd:.2f} USD)"
            else:
                return False, "Transaction non trouvée"
            
        except Exception as e:
            return False, f"Erreur lors de la mise à jour: {str(e)}"
    
    def delete_transaction(self, transaction_id: int) -> Tuple[bool, str]:
        """Supprime une transaction"""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success, "Transaction supprimée avec succès" if success else "Transaction non trouvée"
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[dict]:
        """Récupère une transaction spécifique par son ID"""
        transactions = self.get_all_transactions()
        if not transactions.empty:
            transaction = transactions[transactions['id'] == transaction_id]
            if not transaction.empty:
                return transaction.iloc[0].to_dict()
        return None
    
    # Méthodes pour la mise à jour des prix
    def update_price(self, symbol: str, days_history: int = 30) -> bool:
        """Met à jour le prix d'un produit avec historique"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days_history}d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                
                # Récupérer la devise du produit
                product = self.db.get_financial_product_by_symbol(symbol)
                if product is None:
                    return False
                
                product_currency = product['currency']
                
                # Convertir le prix actuel dans les deux devises
                price_eur, price_usd = self.currency_converter.convert_price_to_both(
                    current_price, product_currency
                )
                
                # Mettre à jour le prix actuel
                self.db.update_product_price(symbol, current_price, price_eur, price_usd)
                
                # Ajouter l'historique récent
                product_id = product['id']
                import sqlite3
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()
                
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
        """Initialise l'historique des prix pour tous les produits"""
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
                    import sqlite3
                    conn = sqlite3.connect(self.db.db_path)
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
                    
                    # Mettre à jour le prix actuel
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
            time.sleep(1)  # Délai pour éviter les limitations d'API
        
        progress_bar.empty()
        status_text.empty()
        st.success("🎉 Initialisation de l'historique terminée!")
    
    # Méthodes d'analyse du portefeuille
    def get_portfolio_summary(self) -> pd.DataFrame:
        """Calcule le résumé du portefeuille en utilisant les prix EUR stockés"""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        
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
                AVG(CASE WHEN t.transaction_type = 'BUY' THEN t.price_eur ELSE NULL END) as avg_buy_price_eur,
                SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * t.price_eur + COALESCE(t.fees, 0)
                         WHEN t.transaction_type = 'SELL' THEN -t.quantity * t.price_eur - COALESCE(t.fees, 0)
                         ELSE 0 END) as total_invested_eur
            FROM transactions t
            JOIN financial_products fp ON t.product_id = fp.id
            JOIN accounts a ON t.account_id = a.id
            JOIN platforms p ON a.platform_id = p.id
            GROUP BY fp.symbol, a.id
            HAVING total_quantity > 0
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            # Utiliser les prix EUR stockés
            df['current_price_eur'] = df['current_price_eur'].fillna(0)
            df['avg_buy_price_eur'] = df['avg_buy_price_eur'].fillna(0)
            df['total_invested_eur'] = df['total_invested_eur'].fillna(0)
            
            df['current_value'] = df['total_quantity'] * df['current_price_eur']
            df['gain_loss'] = df['current_value'] - df['total_invested_eur']
            df['gain_loss_pct'] = df.apply(
                lambda row: (row['gain_loss'] / row['total_invested_eur']) * 100 
                if row['total_invested_eur'] > 0 else 0, 
                axis=1
            )
            
            # Colonnes pour compatibilité
            df['total_invested'] = df['total_invested_eur']
            df['avg_buy_price'] = df['avg_buy_price_eur']
        
        return df
    
    def get_price_history(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Récupère l'historique des prix pour un produit sur une période"""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        
        query = '''
            SELECT ph.date, ph.price, ph.price_eur, ph.price_usd
            FROM price_history ph
            JOIN financial_products fp ON ph.product_id = fp.id
            WHERE fp.symbol = ? AND ph.date BETWEEN ? AND ?
            ORDER BY ph.date
        '''
        df = pd.read_sql_query(query, conn, params=(symbol, start_date.date(), end_date.date()))
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def get_portfolio_evolution(self, start_date: datetime, end_date: datetime, 
                               account_filter: list = None, product_filter: list = None, 
                               asset_class_filter: list = None) -> pd.DataFrame:
        """Calcule l'évolution de la valeur du portefeuille dans le temps avec les nouveaux prix EUR/USD"""
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        
        # Base query pour récupérer les transactions
        base_query = '''
            SELECT 
                t.transaction_date,
                t.transaction_type,
                t.quantity,
                t.price_eur,
                t.fees,
                fp.symbol,
                fp.name,
                fp.product_type,
                fp.currency,
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
        
        # Générer les dates pour l'évolution
        total_days = (end_date - start_date).days
        
        if total_days <= 7:
            freq = '1D'   # Quotidien pour 7 jours ou moins
        elif total_days <= 30:
            freq = '2D'   # Tous les 2 jours pour 1 mois
        elif total_days <= 90:
            freq = 'W'    # Hebdomadaire pour 3 mois
        else:
            freq = 'W'    # Hebdomadaire pour plus de 3 mois
            
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        evolution_data = []
        
        for current_date in date_range:
            daily_breakdown = {
                'account': {},
                'platform': {},
                'asset_class': {},
                'product': {},
                'currency': {}
            }
            daily_value = 0
            total_invested_to_date = 0
            
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
                    'breakdown_product': {},
                    'breakdown_currency': {}
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
                        'currency': trans['currency'],
                        'account_name': trans['account_name'],
                        'platform_name': trans['platform_name'],
                        'invested_amount': 0
                    }
                
                if trans['transaction_type'] == 'BUY':
                    positions[symbol]['quantity'] += trans['quantity']
                    # Utiliser le prix EUR déjà converti historiquement
                    invested_eur = trans['quantity'] * trans['price_eur'] + (trans['fees'] if pd.notna(trans['fees']) else 0)
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
                    # Chercher le prix EUR le plus proche de cette date dans l'historique
                    price_history = self.get_price_history(symbol, current_date - timedelta(days=7), current_date)
                    closest_price_eur = None
                    
                    if not price_history.empty:
                        # Utiliser le prix EUR de l'historique
                        if 'price_eur' in price_history.columns and pd.notna(price_history.iloc[-1]['price_eur']):
                            closest_price_eur = price_history.iloc[-1]['price_eur']
                        else:
                            # Fallback au prix original avec conversion
                            closest_price = price_history.iloc[-1]['price']
                            if pd.notna(closest_price):
                                closest_price_eur = self.currency_converter.convert_to_eur(closest_price, position['currency'])
                    else:
                        # Si pas d'historique, utiliser le prix EUR actuel du produit
                        products = self.get_financial_products()
                        product_row = products[products['symbol'] == symbol]
                        if not product_row.empty:
                            product = product_row.iloc[0]
                            if pd.notna(product.get('current_price_eur')):
                                closest_price_eur = product['current_price_eur']
                            elif pd.notna(product.get('current_price')):
                                closest_price_eur = self.currency_converter.convert_to_eur(
                                    product['current_price'], product['currency']
                                )
                    
                    if closest_price_eur and closest_price_eur > 0:
                        value = position['quantity'] * closest_price_eur
                        daily_value += value
                        
                        # Breakdown par catégorie
                        account_name = position['account_name']
                        platform_name = position['platform_name']
                        asset_class = position['product_type']
                        product_name = position['name']
                        currency = position['currency']
                        
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
                        
                        if currency not in daily_breakdown['currency']:
                            daily_breakdown['currency'][currency] = 0
                        daily_breakdown['currency'][currency] += value
            
            evolution_data.append({
                'date': current_date,
                'total_value': daily_value,
                'total_invested': total_invested_to_date,
                'gain_loss': daily_value - total_invested_to_date,
                'breakdown_account': daily_breakdown['account'],
                'breakdown_platform': daily_breakdown['platform'],
                'breakdown_asset_class': daily_breakdown['asset_class'],
                'breakdown_product': daily_breakdown['product'],
                'breakdown_currency': daily_breakdown['currency']
            })
        
        return pd.DataFrame(evolution_data)
    
    def get_available_filters(self):
        """Récupère les options disponibles pour les filtres"""
        accounts = self.get_accounts()
        products = self.get_financial_products()
        
        asset_classes = []
        if not products.empty:
            asset_classes = products['product_type'].unique().tolist()
        
        return {
            'accounts': accounts,
            'products': products[['symbol', 'name']] if not products.empty else pd.DataFrame(),
            'asset_classes': asset_classes
        }