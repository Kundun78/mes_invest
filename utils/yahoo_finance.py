import yfinance as yf
import re
from typing import Dict, Optional, Tuple

class YahooFinanceUtils:
    """Utilitaires pour extraire les informations de Yahoo Finance"""
    
    @staticmethod
    def detect_currency_from_symbol(symbol: str) -> str:
        """
        Détecte la devise d'un symbole Yahoo Finance basé sur sa nomenclature
        """
        symbol_upper = symbol.upper()
        
        # Cryptomonnaies avec devise explicite
        if '-EUR' in symbol_upper:
            return 'EUR'
        if '-USD' in symbol_upper:
            return 'USD'
        if '-GBP' in symbol_upper:
            return 'GBP'
        if '-CAD' in symbol_upper:
            return 'CAD'
        if '-CHF' in symbol_upper:
            return 'CHF'
        if '-JPY' in symbol_upper:
            return 'JPY'
        
        # Actions européennes
        if symbol_upper.endswith('.PA'):  # Paris
            return 'EUR'
        if symbol_upper.endswith('.AS'):  # Amsterdam
            return 'EUR'
        if symbol_upper.endswith('.MI'):  # Milan
            return 'EUR'
        if symbol_upper.endswith('.MC'):  # Madrid
            return 'EUR'
        if symbol_upper.endswith('.F'):   # Frankfurt
            return 'EUR'
        if symbol_upper.endswith('.BE'):  # Berlin
            return 'EUR'
        if symbol_upper.endswith('.VI'):  # Vienna
            return 'EUR'
        if symbol_upper.endswith('.BR'):  # Brussels
            return 'EUR'
        if symbol_upper.endswith('.LS'):  # Lisbon
            return 'EUR'
        if symbol_upper.endswith('.HE'):  # Helsinki
            return 'EUR'
        if symbol_upper.endswith('.AT'):  # Athens
            return 'EUR'
        
        # Royaume-Uni
        if symbol_upper.endswith('.L'):   # London
            return 'GBP'
        
        # Suisse
        if symbol_upper.endswith('.SW'):  # Swiss Exchange
            return 'CHF'
        
        # Canada
        if symbol_upper.endswith('.TO') or symbol_upper.endswith('.V'):  # Toronto/Vancouver
            return 'CAD'
        
        # Japon
        if symbol_upper.endswith('.T'):   # Tokyo
            return 'JPY'
        
        # Cryptomonnaies communes (sans suffixe de devise)
        crypto_symbols = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'AVAX', 'MATIC', 'LTC', 'XRP', 'DOGE']
        if any(symbol_upper.startswith(crypto) for crypto in crypto_symbols):
            return 'USD'  # Par défaut crypto en USD
        
        # Par défaut, considérer comme USD (marchés américains)
        return 'USD'
    
    @staticmethod
    def get_product_info(symbol: str) -> Tuple[bool, Dict]:
        """
        Récupère les informations complètes d'un produit financier
        Retourne (success, info_dict)
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Vérifier l'existence en récupérant des données récentes
            hist = ticker.history(period="5d")
            if hist.empty:
                return False, {"error": f"Aucune donnée de prix trouvée pour '{symbol}'"}
            
            # Récupérer les informations détaillées
            info = ticker.info
            
            # Prix actuel
            current_price = hist['Close'].iloc[-1]
            
            # Détecter la devise
            detected_currency = None
            
            # 1. Essayer d'abord via les métadonnées Yahoo
            if 'currency' in info and info['currency']:
                detected_currency = info['currency'].upper()
            elif 'financialCurrency' in info and info['financialCurrency']:
                detected_currency = info['financialCurrency'].upper()
            
            # 2. Si pas trouvé, utiliser la détection par symbole
            if not detected_currency or detected_currency == 'None':
                detected_currency = YahooFinanceUtils.detect_currency_from_symbol(symbol)
            
            # Nom du produit
            product_name = (info.get('longName') or 
                          info.get('shortName') or 
                          info.get('displayName') or 
                          symbol)
            
            # Type de produit
            product_type = YahooFinanceUtils.determine_product_type(symbol, info)
            
            result = {
                'symbol': symbol.upper(),
                'name': product_name,
                'currency': detected_currency,
                'current_price': current_price,
                'product_type': product_type,
                'market_cap': info.get('marketCap'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'exchange': info.get('exchange'),
                'country': info.get('country'),
                'raw_info': info  # Pour debug si nécessaire
            }
            
            return True, result
            
        except Exception as e:
            return False, {"error": f"Erreur lors de la récupération des informations pour '{symbol}': {str(e)}"}
    
    @staticmethod
    def determine_product_type(symbol: str, info: Dict) -> str:
        """
        Détermine le type de produit financier
        """
        symbol_upper = symbol.upper()
        
        # Cryptomonnaies
        if ('-EUR' in symbol_upper or '-USD' in symbol_upper or 
            any(symbol_upper.startswith(crypto) for crypto in ['BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'AVAX', 'MATIC', 'LTC', 'XRP', 'DOGE'])):
            return 'Crypto'
        
        # ETF basé sur le nom
        name = str(info.get('longName', '') + ' ' + info.get('shortName', '')).upper()
        if any(keyword in name for keyword in ['ETF', 'FUND', 'INDEX', 'TRACKER', 'ISHARES', 'VANGUARD', 'SPDR']):
            return 'ETF'
        
        # Type via Yahoo Finance
        quote_type = info.get('quoteType', '').upper()
        if quote_type == 'ETF':
            return 'ETF'
        elif quote_type == 'EQUITY':
            return 'Action'
        elif quote_type == 'MUTUALFUND':
            return 'Fonds'
        elif quote_type == 'BOND':
            return 'Obligation'
        elif quote_type == 'CRYPTOCURRENCY':
            return 'Crypto'
        
        # Par défaut, considérer comme une action
        return 'Action'
    
    @staticmethod
    def validate_symbol(symbol: str) -> Tuple[bool, str]:
        """
        Valide qu'un symbole existe sur Yahoo Finance
        Retourne (is_valid, message)
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            
            if hist.empty:
                return False, f"Le symbole '{symbol}' n'existe pas ou n'a pas de données récentes sur Yahoo Finance."
            
            return True, f"Symbole '{symbol}' validé avec succès."
            
        except Exception as e:
            return False, f"Erreur lors de la validation du symbole '{symbol}': {str(e)}"
    
    @staticmethod
    def search_suggestions(query: str) -> list:
        """
        Suggère des symboles basés sur une recherche (fonctionnalité future)
        Pour l'instant, retourne une liste vide car Yahoo Finance n'a pas d'API de recherche simple
        """
        # Cette fonctionnalité pourrait être implémentée avec d'autres APIs
        # comme Alpha Vantage, IEX Cloud, etc.
        return []
    
    @staticmethod
    def get_currency_symbol(currency_code: str) -> str:
        """Retourne le symbole de la devise"""
        currency_symbols = {
            'EUR': '€',
            'USD': '$',
            'GBP': '£',
            'CHF': 'CHF',
            'CAD': 'C$',
            'JPY': '¥'
        }
        return currency_symbols.get(currency_code, currency_code)