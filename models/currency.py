import streamlit as st
import requests
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import time

class CurrencyConverter:
    """Gestionnaire de conversion de devises avec support taux historiques"""
    
    def __init__(self):
        self.eur_usd_rate = None  # Combien d'USD pour 1 EUR
        self.last_update = None
        # Cache pour les taux historiques
        self.historical_rates_cache = {}
        # Taux fixes pour les autres devises (vers EUR)
        self.other_rates = {
            'GBP': 1.15,  # 1 GBP = 1.15 EUR
            'CHF': 0.95,  # 1 CHF = 0.95 EUR
            'CAD': 0.65,  # 1 CAD = 0.65 EUR
            'JPY': 0.0067, # 1 JPY = 0.0067 EUR
        }
    
    def get_eur_usd_rate_alternative(self, show_debug=False) -> bool:
        """Méthode alternative pour récupérer le taux EUR/USD via une API gratuite"""
        try:
            if show_debug:
                st.write("🔄 Tentative avec API alternative...")
            
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

    def get_historical_eur_usd_rate(self, date: datetime) -> Optional[float]:
        """Récupère le taux EUR/USD historique pour une date donnée"""
        date_key = date.strftime('%Y-%m-%d')
        
        # Vérifier le cache
        if date_key in self.historical_rates_cache:
            return self.historical_rates_cache[date_key]
        
        try:
            # Récupérer via Yahoo Finance
            ticker = yf.Ticker('EURUSD=X')
            
            # Récupérer une semaine autour de la date pour avoir plus de chances
            start_date = date - timedelta(days=7)
            end_date = date + timedelta(days=7)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                # Chercher la date la plus proche
                hist.index = hist.index.date
                target_date = date.date()
                
                if target_date in hist.index:
                    rate = hist.loc[target_date, 'Close']
                else:
                    # Trouver la date la plus proche
                    closest_date = min(hist.index, key=lambda x: abs((x - target_date).days))
                    rate = hist.loc[closest_date, 'Close']
                
                # Mettre en cache
                self.historical_rates_cache[date_key] = rate
                return rate
            
        except Exception as e:
            print(f"Erreur lors de la récupération du taux historique EUR/USD pour {date}: {e}")
        
        # Fallback : utiliser le taux actuel
        if not self.eur_usd_rate:
            self.get_eur_usd_rate()
        
        return self.eur_usd_rate if self.eur_usd_rate else 1.08

    def convert_with_historical_rate(self, amount: float, from_currency: str, 
                                   to_currency: str, date: datetime) -> float:
        """Convertit un montant entre devises en utilisant le taux historique"""
        
        if from_currency == to_currency:
            return amount
        
        # Gestion EUR <-> USD avec taux historique
        if from_currency == 'EUR' and to_currency == 'USD':
            historical_rate = self.get_historical_eur_usd_rate(date)
            return amount * historical_rate
        
        elif from_currency == 'USD' and to_currency == 'EUR':
            historical_rate = self.get_historical_eur_usd_rate(date)
            return amount / historical_rate
        
        # Pour les autres devises, utiliser les taux fixes (amélioration possible)
        elif to_currency == 'EUR' and from_currency in self.other_rates:
            return amount * self.other_rates[from_currency]
        
        elif from_currency == 'EUR' and to_currency in self.other_rates:
            return amount / self.other_rates[to_currency]
        
        # Conversion via EUR pour autres devises
        elif from_currency in self.other_rates and to_currency in self.other_rates:
            # Convertir d'abord vers EUR, puis vers la devise cible
            amount_eur = amount * self.other_rates[from_currency]
            return amount_eur / self.other_rates[to_currency]
        
        # Si pas supporté, retourner le montant original
        return amount

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