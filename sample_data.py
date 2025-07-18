# sample_data.py
# Script pour peupler la base de données avec des données d'exemple

from portfolio_tracker import PortfolioTracker
from datetime import datetime, timedelta
import random

def populate_sample_data():
    """Peuple la base de données avec des données d'exemple"""
    tracker = PortfolioTracker()
    
    print("🏗️ Création des données d'exemple...")
    
    # 1. Ajouter des plateformes
    platforms = [
        ("Boursorama", "Banque en ligne avec courtage"),
        ("Degiro", "Courtier européen low-cost"),
        ("Binance", "Plateforme de crypto-monnaies"),
        ("Assurance Vie AXA", "Contrat d'assurance vie")
    ]
    
    for name, desc in platforms:
        tracker.add_platform(name, desc)
        print(f"✅ Plateforme ajoutée: {name}")
    
    # 2. Ajouter des comptes
    accounts = [
        (1, "CTO Principal", "CTO"),
        (1, "PEA", "PEA"),
        (2, "Compte Degiro", "CTO"),
        (3, "Wallet Crypto", "Crypto"),
        (4, "AV Multisupport", "Assurance Vie")
    ]
    
    for platform_id, name, account_type in accounts:
        tracker.add_account(platform_id, name, account_type)
        print(f"✅ Compte ajouté: {name}")
    
    # 3. Ajouter des produits financiers
    products = [
        # Actions françaises
        ("MC.PA", "LVMH", "Action", "EUR"),
        ("OR.PA", "L'Oréal", "Action", "EUR"),
        ("AIR.PA", "Airbus", "Action", "EUR"),
        
        # Actions américaines
        ("AAPL", "Apple Inc.", "Action", "USD"),
        ("MSFT", "Microsoft", "Action", "USD"),
        ("GOOGL", "Alphabet", "Action", "USD"),
        
        # ETF
        ("CW8.PA", "MSCI World UCITS ETF", "ETF", "EUR"),
        ("EWLD.PA", "Xtrackers MSCI World", "ETF", "EUR"),
        
        # Crypto
        ("BTC-EUR", "Bitcoin", "Crypto", "EUR"),
        ("ETH-EUR", "Ethereum", "Crypto", "EUR"),
    ]
    
    for symbol, name, product_type, currency in products:
        tracker.add_financial_product(symbol, name, product_type, currency)
        print(f"✅ Produit ajouté: {symbol} - {name}")
    
    # 4. Ajouter des transactions d'exemple
    base_date = datetime.now() - timedelta(days=365)  # Il y a un an
    
    transactions = [
        # CTO Principal (account_id=1)
        (1, "MC.PA", "BUY", 5, 650.0, base_date + timedelta(days=30), 9.95),
        (1, "OR.PA", "BUY", 3, 380.0, base_date + timedelta(days=45), 9.95),
        (1, "CW8.PA", "BUY", 50, 75.0, base_date + timedelta(days=60), 9.95),
        
        # PEA (account_id=2)
        (2, "AIR.PA", "BUY", 8, 110.0, base_date + timedelta(days=90), 4.95),
        (2, "EWLD.PA", "BUY", 30, 80.0, base_date + timedelta(days=120), 4.95),
        
        # Degiro (account_id=3)
        (3, "AAPL", "BUY", 10, 150.0, base_date + timedelta(days=150), 2.0),
        (3, "MSFT", "BUY", 7, 300.0, base_date + timedelta(days=180), 2.0),
        (3, "GOOGL", "BUY", 2, 2500.0, base_date + timedelta(days=200), 2.0),
        
        # Crypto (account_id=4)
        (4, "BTC-EUR", "BUY", 0.1, 35000.0, base_date + timedelta(days=220), 10.0),
        (4, "ETH-EUR", "BUY", 2, 2000.0, base_date + timedelta(days=240), 5.0),
        
        # Quelques transactions plus récentes
        (1, "MC.PA", "BUY", 2, 700.0, base_date + timedelta(days=300), 9.95),
        (2, "CW8.PA", "BUY", 25, 82.0, base_date + timedelta(days=320), 4.95),
        (3, "AAPL", "SELL", 3, 180.0, base_date + timedelta(days=340), 2.0),  # Prise de bénéfice
    ]
    
    for account_id, symbol, trans_type, quantity, price, date, fees in transactions:
        tracker.add_transaction(account_id, symbol, trans_type, quantity, price, date, fees)
        print(f"✅ Transaction ajoutée: {trans_type} {quantity} {symbol} à {price}€")
    
    print("\n🎉 Données d'exemple créées avec succès!")
    print("\n📊 Récapitulatif:")
    print(f"- {len(platforms)} plateformes")
    print(f"- {len(accounts)} comptes") 
    print(f"- {len(products)} produits financiers")
    print(f"- {len(transactions)} transactions")
    
    # Proposer d'initialiser l'historique des prix
    print("\n🔄 Initialisation de l'historique des prix...")
    response = input("Voulez-vous initialiser l'historique des prix maintenant ? (o/N): ")
    
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        print("📈 Initialisation de l'historique des prix (365 jours)...")
        print("⚠️ Cette opération peut prendre plusieurs minutes...")
        
        import yfinance as yf
        import time
        
        for symbol, name, product_type, currency in products:
            print(f"  📊 {symbol} - {name}...")
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="365d")
                
                if not hist.empty:
                    import sqlite3
                    conn = sqlite3.connect("portfolio.db")
                    cursor = conn.cursor()
                    
                    # Récupérer l'ID du produit
                    cursor.execute("SELECT id FROM financial_products WHERE symbol = ?", (symbol,))
                    product_id = cursor.fetchone()[0]
                    
                    # Ajouter l'historique
                    for date, row_data in hist.iterrows():
                        cursor.execute('''INSERT OR REPLACE INTO price_history (product_id, price, date)
                                        VALUES (?, ?, ?)''',
                                      (product_id, row_data['Close'], date.date()))
                    
                    # Mettre à jour le prix actuel
                    current_price = hist['Close'].iloc[-1]
                    cursor.execute('''UPDATE financial_products 
                                    SET current_price = ?, last_updated = ?
                                    WHERE id = ?''',
                                  (current_price, datetime.now(), product_id))
                    
                    conn.commit()
                    conn.close()
                    
                    print(f"    ✅ {len(hist)} points d'historique ajoutés")
                else:
                    print(f"    ⚠️ Aucune donnée trouvée")
                    
            except Exception as e:
                print(f"    ❌ Erreur: {e}")
            
            time.sleep(1)  # Éviter de surcharger l'API
        
        print("\n🎉 Historique des prix initialisé!")
    else:
        print("\n💡 Vous pourrez initialiser l'historique plus tard dans l'onglet Configuration.")
    
    print("\n🚀 Vous pouvez maintenant lancer l'application:")
    print("streamlit run portfolio_tracker.py")
    
    print("\n📈 Fonctionnalités disponibles:")
    print("- 🏠 Tableau de bord avec métriques")
    print("- 📈 Courbes d'évolution (si historique initialisé)")
    print("- 💼 Gestion complète des comptes et produits")
    print("- 🛒 Ajout de nouvelles transactions")
    print("- ⚙️ Configuration et maintenance")

if __name__ == "__main__":
    populate_sample_data()