import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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
    st.write("L'application détecte automatiquement les devises et stocke tous les prix en EUR et USD.")
    
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
        with st.expander("📊 Taux de change actuels", expanded=False):
            st.text(tracker.currency_converter.get_rate_info())
    
    st.divider()
    
    st.subheader("🔍 Test de détection automatique")
    st.write("Testez la détection automatique des informations d'un produit financier :")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        test_symbol = st.text_input("Symbole à tester", placeholder="Ex: AAPL, BTC-EUR, MC.PA")
        
        if st.button("🔍 Analyser ce symbole"):
            if test_symbol:
                with st.spinner(f"Analyse de {test_symbol}..."):
                    success, info = tracker.yahoo_utils.get_product_info(test_symbol)
                
                if success:
                    st.success("✅ Produit trouvé et analysé!")
                    
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.write(f"**Nom détecté :** {info['name']}")
                        st.write(f"**Type détecté :** {info['product_type']}")
                        st.write(f"**Devise détectée :** {info['currency']}")
                        st.write(f"**Prix actuel :** {info['current_price']:.2f} {info['currency']}")
                    
                    with col_info2:
                        if info.get('exchange'):
                            st.write(f"**Bourse :** {info['exchange']}")
                        if info.get('sector'):
                            st.write(f"**Secteur :** {info['sector']}")
                        if info.get('country'):
                            st.write(f"**Pays :** {info['country']}")
                        if info.get('market_cap'):
                            market_cap_b = info['market_cap'] / 1e9
                            st.write(f"**Capitalisation :** {market_cap_b:.1f}B {info['currency']}")
                    
                    # Afficher les conversions
                    price_eur, price_usd = tracker.currency_converter.convert_price_to_both(
                        info['current_price'], info['currency']
                    )
                    
                    st.write("**💱 Conversions automatiques :**")
                    st.write(f"Prix en EUR: {price_eur:.2f} €")
                    st.write(f"Prix en USD: {price_usd:.2f} $")
                    
                else:
                    st.error(f"❌ {info.get('error', 'Erreur inconnue')}")
            else:
                st.warning("Veuillez saisir un symbole à tester")
    
    with col2:
        st.info("**💡 Détection automatique :**\n\n✅ Devise native\n✅ Nom officiel\n✅ Type de produit\n✅ Prix actuel\n✅ Métadonnées\n✅ Conversion EUR/USD")
    
    st.divider()
    
    st.subheader("📈 Initialisation de l'historique des prix")
    st.write("""
    **Important :** Pour utiliser les courbes d'évolution, vous devez d'abord initialiser l'historique des prix.
    Cette opération récupère les données historiques pour tous vos produits financiers avec conversion EUR/USD.
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
        # Statistiques sur l'historique actuel
        if not products.empty:
            with st.expander("📊 État de l'historique actuel", expanded=False):
                stats = tracker.db.get_database_stats()
                history_count = stats.get('price_history', 0)
                
                st.write(f"**Total points d'historique :** {history_count}")
                
                if history_count > 0:
                    st.write("**Détail par produit :**")
                    
                    import sqlite3
                    conn = sqlite3.connect(tracker.db.db_path)
                    cursor = conn.cursor()
                    
                    for _, product in products.iterrows():
                        cursor.execute('''SELECT COUNT(*), MIN(date), MAX(date) 
                                        FROM price_history WHERE product_id = ?''', (product['id'],))
                        result = cursor.fetchone()
                        count, min_date, max_date = result
                        
                        if count > 0:
                            st.write(f"**{product['symbol']}** : {count} points")
                            st.write(f"   📅 Du {min_date} au {max_date}")
                        else:
                            st.write(f"**{product['symbol']}** : ❌ Aucun historique")
                    
                    conn.close()
                else:
                    st.write("❌ Aucun historique disponible")
    
    st.divider()
    
    st.subheader("📊 Informations sur la base de données")
    
    # Statistiques générales
    platforms = tracker.get_platforms()
    accounts = tracker.get_accounts()
    stats = tracker.db.get_database_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏢 Plateformes", len(platforms))
    with col2:
        st.metric("💼 Comptes", len(accounts))
    with col3:
        st.metric("📈 Produits", len(products))
    with col4:
        st.metric("💸 Transactions", stats.get('transactions', 0))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📈 Points d'historique", stats.get('price_history', 0))
    with col2:
        st.metric("💱 Taux de change", stats.get('exchange_rates', 0))
    with col3:
        st.metric("🗄️ Taille de la DB", "Calculé...")
    with col4:
        if st.button("🔄 Actualiser stats"):
            st.rerun()
    
    # Affichage de l'état des prix avec nouvelles informations
    if not products.empty:
        st.subheader("💰 État des prix et devises")
        
        # Séparer les produits avec et sans prix
        with_price = products[products['current_price'].notna()]
        without_price = products[products['current_price'].isna()]
        
        if not with_price.empty:
            st.write("**✅ Produits avec prix à jour :**")
            
            # Affichage plus détaillé avec devises
            display_products = with_price[['symbol', 'name', 'product_type', 'currency', 
                                         'current_price', 'current_price_eur', 'current_price_usd', 
                                         'exchange', 'last_updated']].copy()
            
            # Formater les prix
            display_products['Prix natif'] = display_products.apply(
                lambda row: f"{row['current_price']:.2f} {row['currency']}" 
                if pd.notna(row['current_price']) else "N/A", axis=1
            )
            
            display_products['Prix EUR'] = display_products.apply(
                lambda row: f"{row['current_price_eur']:.2f} €" 
                if pd.notna(row['current_price_eur']) else "N/A", axis=1
            )
            
            display_products['Prix USD'] = display_products.apply(
                lambda row: f"{row['current_price_usd']:.2f} $" 
                if pd.notna(row['current_price_usd']) else "N/A", axis=1
            )
            
            # Afficher le tableau
            st.dataframe(display_products[['symbol', 'name', 'product_type', 'currency', 
                                        'Prix natif', 'Prix EUR', 'Prix USD', 'exchange', 'last_updated']], 
                        use_container_width=True, hide_index=True)
        
        if not without_price.empty:
            st.write("**⚠️ Produits sans prix (à actualiser) :**")
            st.dataframe(without_price[['symbol', 'name', 'product_type', 'currency']], 
                        use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Section de maintenance
    st.subheader("🛠️ Maintenance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**🧹 Nettoyage**")
        if st.button("Nettoyer l'historique (>1 an)"):
            import sqlite3
            conn = sqlite3.connect(tracker.db.db_path)
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
    
    # Section de debug avancé
    with st.expander("🔧 Debug Avancé", expanded=False):
        st.write("**Informations techniques :**")
        
        # Test des connexions API
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Yahoo Finance"):
                with st.spinner("Test en cours..."):
                    success, msg = tracker.yahoo_utils.validate_symbol("AAPL")
                    if success:
                        st.success("✅ Yahoo Finance accessible")
                    else:
                        st.error(f"❌ {msg}")
        
        with col2:
            if st.button("🧪 Test API de change"):
                with st.spinner("Test en cours..."):
                    success = tracker.currency_converter.get_eur_usd_rate_alternative()
                    if success:
                        st.success("✅ API de change accessible")
                    else:
                        st.error("❌ API de change inaccessible")
        
        # Informations sur les taux de change en cache
        st.write("**Cache des taux de change :**")
        cache_info = tracker.currency_converter.historical_rates_cache
        if cache_info:
            st.write(f"Entrées en cache : {len(cache_info)}")
            for date, rate in list(cache_info.items())[:5]:  # Afficher les 5 premiers
                st.write(f"  {date}: {rate:.4f}")
        else:
            st.write("Aucun taux en cache")
        
        # Historique des taux de change stockés
        st.write("**Taux de change utilisés dans les transactions :**")
        import sqlite3
        conn = sqlite3.connect(tracker.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT date, rate, COUNT(*) as usage_count 
                        FROM exchange_rates 
                        WHERE from_currency = 'EUR' AND to_currency = 'USD'
                        GROUP BY date, rate 
                        ORDER BY date DESC LIMIT 10''')
        historical_rates = cursor.fetchall()
        conn.close()
        
        if historical_rates:
            st.write("**10 derniers taux EUR/USD utilisés :**")
            for date, rate, count in historical_rates:
                st.write(f"  📅 {date}: {rate:.4f} (utilisé {count} fois)")
        else:
            st.write("Aucun taux historique stocké")
    
    # Nouvel outil de test de conversion historique
    st.divider()
    st.subheader("🕰️ Test de Conversion Historique")
    st.write("Testez les conversions avec les taux historiques :")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        test_amount = st.number_input("Montant", min_value=0.0, value=100.0, step=10.0)
        test_from_currency = st.selectbox("De", ["EUR", "USD", "GBP", "CHF", "CAD"], index=1)
        test_to_currency = st.selectbox("Vers", ["EUR", "USD", "GBP", "CHF", "CAD"], index=0)
    
    with col2:
        test_date = st.date_input("Date historique", value=datetime.now().date() - timedelta(days=30))
        
        if st.button("🔄 Convertir"):
            if test_amount > 0:
                converted_amount = tracker.currency_converter.convert_with_historical_rate(
                    test_amount, test_from_currency, test_to_currency, datetime.combine(test_date, datetime.min.time())
                )
                st.success(f"✅ {test_amount:.2f} {test_from_currency} = {converted_amount:.2f} {test_to_currency}")
                
                # Afficher le taux utilisé
                if test_from_currency == 'EUR' and test_to_currency == 'USD':
                    rate = tracker.currency_converter.get_historical_eur_usd_rate(datetime.combine(test_date, datetime.min.time()))
                    st.info(f"📊 Taux EUR/USD du {test_date}: {rate:.4f}")
                elif test_from_currency == 'USD' and test_to_currency == 'EUR':
                    rate = tracker.currency_converter.get_historical_eur_usd_rate(datetime.combine(test_date, datetime.min.time()))
                    st.info(f"📊 Taux USD/EUR du {test_date}: {(1/rate):.4f}")
    
    with col3:
        st.info("**💡 Utilisation :**\n\nCet outil utilise les mêmes taux historiques que vos transactions pour vérifier la cohérence des conversions.")