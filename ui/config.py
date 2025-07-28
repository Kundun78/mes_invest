import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def config_page(tracker, user_id):
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
        products = tracker.get_financial_products(user_id)
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
    
    st.subheader("🔍 Diagnostic des Graphiques d'Évolution")
    st.write("Vérifiez pourquoi les graphiques d'évolution ne s'affichent pas :")
    
    if st.button("🧪 Diagnostic Complet"):
        with st.spinner("Diagnostic en cours..."):
            # 1. Vérifier les données de base
            st.write("**📊 1. Vérification des données de base :**")
            
            transactions = tracker.get_all_transactions(user_id)
            if transactions.empty:
                st.error("❌ Aucune transaction trouvée ! Ajoutez des transactions d'abord.")
                return
            else:
                st.success(f"✅ {len(transactions)} transactions trouvées")
                oldest_transaction = transactions['transaction_date'].min()
                newest_transaction = transactions['transaction_date'].max()
                st.info(f"📅 Période : du {oldest_transaction.strftime('%d/%m/%Y')} au {newest_transaction.strftime('%d/%m/%Y')}")
            
            # 2. Vérifier l'historique des prix
            st.write("**📈 2. Vérification de l'historique des prix :**")
            
            stats = tracker.db.get_database_stats(user_id)
            history_count = stats.get('price_history', 0)
            
            if history_count == 0:
                st.error("❌ Aucun historique de prix ! Initialisez l'historique dans la section ci-dessus.")
                return
            else:
                st.success(f"✅ {history_count} points d'historique de prix trouvés")
            
            # 3. Tester le calcul d'évolution
            st.write("**⚙️ 3. Test du calcul d'évolution :**")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Test sur 30 jours
            
            try:
                evolution_data = tracker.get_portfolio_evolution(start_date, end_date, user_id)
                
                if evolution_data.empty:
                    st.warning("⚠️ Aucune donnée d'évolution générée. Vérifiez que vos transactions sont dans la période testée.")
                    
                    # Diagnostic plus poussé
                    st.write("**🔍 Diagnostic détaillé :**")
                    
                    # Vérifier les transactions dans la période
                    transactions_in_period = transactions[
                        (transactions['transaction_date'] >= start_date) & 
                        (transactions['transaction_date'] <= end_date)
                    ]
                    
                    if transactions_in_period.empty:
                        st.info(f"💡 Aucune transaction dans les 30 derniers jours. Essayez une période plus large.")
                        
                        # Test avec une période plus large
                        start_date_large = oldest_transaction
                        evolution_data_large = tracker.get_portfolio_evolution(start_date_large, end_date, user_id)
                        
                        if not evolution_data_large.empty:
                            st.success(f"✅ {len(evolution_data_large)} points d'évolution générés avec la période complète")
                            st.info("💡 Les graphiques devraient maintenant fonctionner dans l'interface principale !")
                        else:
                            st.error("❌ Problème dans le calcul d'évolution même avec la période complète")
                    else:
                        st.info(f"📊 {len(transactions_in_period)} transactions trouvées dans la période")
                        
                else:
                    st.success(f"✅ {len(evolution_data)} points d'évolution générés avec succès !")
                    
                    # Afficher un aperçu
                    if len(evolution_data) > 0:
                        first_value = evolution_data['total_value'].iloc[0]
                        last_value = evolution_data['total_value'].iloc[-1]
                        st.info(f"📈 Valeur de départ : {first_value:,.2f} €")
                        st.info(f"📈 Valeur actuelle : {last_value:,.2f} €")
                        st.success("🎉 Les graphiques d'évolution devraient maintenant fonctionner !")
                        
            except Exception as e:
                st.error(f"❌ Erreur lors du calcul d'évolution : {str(e)}")
                st.write("**Stack trace pour debug :**")
                import traceback
                st.code(traceback.format_exc())
            
            # 4. Vérifier les conversions EUR/USD
            st.write("**💱 4. Vérification des conversions EUR/USD :**")
            
            transactions_with_conversion = transactions[transactions['price_currency'] != 'EUR']
            if not transactions_with_conversion.empty:
                st.info(f"📊 {len(transactions_with_conversion)} transactions avec conversion de devise trouvées")
                
                # Vérifier si les prix EUR sont bien renseignés
                missing_eur_conversion = transactions_with_conversion[
                    transactions_with_conversion['price_eur'].isna()
                ]
                
                if not missing_eur_conversion.empty:
                    st.warning(f"⚠️ {len(missing_eur_conversion)} transactions sans conversion EUR détectées")
                    st.info("💡 Cela peut affecter les calculs d'évolution")
                else:
                    st.success("✅ Toutes les conversions EUR sont correctes")
            else:
                st.info("📊 Toutes les transactions sont en EUR, pas de conversion nécessaire")
    
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
                tracker.initialize_price_history(history_days, user_id)
                st.success("🎉 Historique initialisé ! Vous pouvez maintenant utiliser les courbes d'évolution.")
                st.rerun()
            else:
                st.error("Aucun produit financier trouvé. Ajoutez d'abord des produits.")
    
    with col2:
        # Statistiques sur l'historique actuel
        if not products.empty:
            with st.expander("📊 État de l'historique actuel", expanded=False):
                stats = tracker.db.get_database_stats(user_id)
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
    
    # Statistiques générales - filtrer par user_id
    platforms = tracker.get_platforms(user_id)
    accounts = tracker.get_accounts(user_id)
    stats = tracker.db.get_database_stats(user_id)
    
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
            # Filtrer par user_id en joignant avec la table products
            cursor.execute("""DELETE FROM price_history 
                            WHERE date < ? 
                            AND product_id IN (
                                SELECT id FROM financial_products WHERE user_id = ?
                            )""", (one_year_ago, user_id))
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
        
        # Historique des taux de change stockés - filtrer par user_id
        st.write("**Taux de change utilisés dans vos transactions :**")
        import sqlite3
        conn = sqlite3.connect(tracker.db.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT er.date, er.rate, COUNT(*) as usage_count 
                        FROM exchange_rates er
                        JOIN transactions t ON t.transaction_date::date = er.date
                        WHERE er.from_currency = 'EUR' AND er.to_currency = 'USD'
                        AND t.user_id = ?
                        GROUP BY er.date, er.rate 
                        ORDER BY er.date DESC LIMIT 10''', (user_id,))
        historical_rates = cursor.fetchall()
        conn.close()
        
        if historical_rates:
            st.write("**10 derniers taux EUR/USD utilisés :**")
            for date, rate, count in historical_rates:
                st.write(f"  📅 {date}: {rate:.4f} (utilisé {count} fois)")
        else:
            st.write("Aucun taux historique stocké pour vos transactions")
    
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