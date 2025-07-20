import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def transaction_page(tracker):
    st.title("💸 Gestion des Transactions")
    st.caption("💡 Saisissez vos prix dans n'importe quelle devise - La conversion historique est automatique !")
    
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
                    price_display = []
                    
                    if pd.notna(selected_product['current_price']):
                        price_display.append(f"{selected_product['current_price']:.2f} {selected_product['currency']}")
                    
                    if pd.notna(selected_product['current_price_eur']) and selected_product['currency'] != 'EUR':
                        price_display.append(f"{selected_product['current_price_eur']:.2f} EUR")
                    
                    if pd.notna(selected_product['current_price_usd']) and selected_product['currency'] != 'USD':
                        price_display.append(f"{selected_product['current_price_usd']:.2f} USD")
                    
                    if price_display:
                        st.info(f"💰 Prix actuel: {' / '.join(price_display)}")
            
            with col2:
                quantity = st.number_input("Quantité", min_value=0.0, step=0.1)
                
                # Choix de la devise pour le prix - inclure la devise native du produit
                available_currencies = ["EUR", "USD"]
                if product_choice:
                    selected_product = products[products['symbol'] == product_choice].iloc[0]
                    native_currency = selected_product['currency']
                    if native_currency not in available_currencies:
                        available_currencies.insert(0, native_currency)
                    else:
                        # Mettre la devise native en premier
                        available_currencies.remove(native_currency)
                        available_currencies.insert(0, native_currency)
                
                price_currency = st.selectbox("Devise du prix", available_currencies,
                                            help=f"Saisissez le prix dans la devise de votre choix. Conversion automatique avec le taux de change de la date de transaction.")
                
                price = st.number_input(f"Prix unitaire ({price_currency})", min_value=0.0, step=0.01)
                
                fees = st.number_input("Frais (EUR)", min_value=0.0, step=0.01, value=0.0,
                                     help="Les frais sont saisis en EUR par défaut")
                transaction_date = st.date_input("Date de transaction", value=datetime.now().date())
            
            # Affichage des conversions estimées
            if price > 0 and product_choice:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**💱 Conversions estimées :**")
                    # Utiliser les taux actuels pour estimation (pas historiques pour la preview)
                    estimated_eur = tracker.currency_converter.convert_to_eur(price, price_currency)
                    estimated_usd = tracker.currency_converter.eur_to_usd(estimated_eur)
                    
                    if price_currency != 'EUR':
                        st.write(f"Prix en EUR: ~{estimated_eur:.2f} €")
                    if price_currency != 'USD':
                        st.write(f"Prix en USD: ~{estimated_usd:.2f} $")
                
                with col2:
                    total_estimate = estimated_eur * quantity + fees
                    st.write("**💰 Montant total estimé :**")
                    st.write(f"~{total_estimate:.2f} €")
                    
                st.caption("ℹ️ Les montants finaux utiliseront les taux de change historiques de la date de transaction")
            
            if st.form_submit_button("Ajouter la transaction", type="primary"):
                try:
                    tracker.add_transaction(account_choice, product_choice, transaction_type,
                                          quantity, price, price_currency, 
                                          datetime.combine(transaction_date, datetime.min.time()), fees)
                    st.success(f"✅ Transaction ajoutée! Prix: {price:.2f} {price_currency}")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'ajout de la transaction: {str(e)}")
    
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
                
                # Affichage du prix avec conversion plus détaillé
                price_display = f"{transaction['price']:.2f} {transaction['price_currency']}"
                
                # Ajouter les conversions historiques si différentes de la devise de saisie
                conversion_info = []
                if transaction['price_currency'] != 'EUR' and pd.notna(transaction['price_eur']):
                    conversion_info.append(f"{transaction['price_eur']:.2f} €")
                if transaction['price_currency'] != 'USD' and pd.notna(transaction['price_usd']):
                    conversion_info.append(f"{transaction['price_usd']:.2f} $")
                
                if conversion_info:
                    price_display += f" ({' / '.join(conversion_info)})"
                
                # Afficher le taux de change si disponible
                rate_info = ""
                if pd.notna(transaction.get('exchange_rate_eur_usd')):
                    rate_info = f" | Taux: {transaction['exchange_rate_eur_usd']:.4f}"
                
                transaction_title = f"{type_color} {type_label} • {transaction['symbol']} • {transaction['quantity']:.4f} @ {price_display} • {total_amount:,.2f} €{rate_info}"
                
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
                                
                                # Sélecteur de devise pour modifier la transaction
                                available_currencies = ["EUR", "USD", "GBP", "CHF", "CAD", "JPY"]
                                current_currency_idx = 0
                                if transaction['price_currency'] in available_currencies:
                                    current_currency_idx = available_currencies.index(transaction['price_currency'])
                                
                                new_price_currency = st.selectbox("Devise du prix", 
                                                                 available_currencies,
                                                                 index=current_currency_idx,
                                                                 key=f"currency_{transaction['id']}",
                                                                 help="Changez la devise et le prix sera reconverti avec le taux historique")
                                
                                new_price = st.number_input(f"Prix unitaire ({new_price_currency})", 
                                                           min_value=0.0, 
                                                           step=0.01,
                                                           value=float(transaction['price']),
                                                           key=f"price_{transaction['id']}")
                                
                                # Afficher la conversion historique si la devise a changé
                                if new_price_currency != transaction['price_currency'] and new_price > 0:
                                    historical_date = transaction['transaction_date']
                                    est_eur = tracker.currency_converter.convert_with_historical_rate(
                                        new_price, new_price_currency, 'EUR', historical_date
                                    )
                                    est_usd = tracker.currency_converter.convert_with_historical_rate(
                                        new_price, new_price_currency, 'USD', historical_date
                                    )
                                    st.caption(f"💱 À la date du {historical_date.strftime('%d/%m/%Y')} :")
                                    st.caption(f"~{est_eur:.2f} EUR / ~{est_usd:.2f} USD")
                                
                                new_fees = st.number_input("Frais (EUR)", 
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
                                        new_quantity, new_price, new_price_currency,
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
                        # Informations détaillées de la transaction
                        st.write("**Détails :**")
                        st.write(f"**Compte :** {transaction['account_name']}")
                        st.write(f"**Plateforme :** {transaction['platform_name']}")
                        st.write(f"**Produit :** {transaction['product_name']}")
                        st.write(f"**Devise produit :** {transaction['product_currency']}")
                        st.write(f"**Type :** {transaction['transaction_type']}")
                        st.write(f"**Quantité :** {transaction['quantity']:.4f}")
                        
                        st.divider()
                        st.write("**💰 Prix à la date d'achat :**")
                        
                        # Prix saisi
                        st.write(f"**Prix saisi :** {transaction['price']:.2f} {transaction['price_currency']}")
                        
                        # Prix historiques convertis à la date de transaction
                        transaction_date = transaction['transaction_date']
                        st.write(f"**À la date du {transaction_date.strftime('%d/%m/%Y')} :**")
                        
                        if pd.notna(transaction['price_eur']):
                            st.write(f"  📈 **Prix EUR :** {transaction['price_eur']:.2f} €")
                        
                        if pd.notna(transaction['price_usd']):
                            st.write(f"  📈 **Prix USD :** {transaction['price_usd']:.2f} $")
                        
                        # Taux de change utilisé pour cette transaction
                        if pd.notna(transaction.get('exchange_rate_eur_usd')):
                            st.write(f"**Taux EUR/USD utilisé :** {transaction['exchange_rate_eur_usd']:.4f}")
                        
                        st.divider()
                        st.write("**💸 Autres informations :**")
                        st.write(f"**Frais :** {transaction['fees']:.2f} EUR")
                        st.write(f"**Total :** {total_amount:,.2f} EUR")
                        st.write(f"**Date/Heure :** {transaction['transaction_date'].strftime('%d/%m/%Y %H:%M')}")
                        
                        # Comparaison avec les prix actuels si disponible
                        products = tracker.get_financial_products()
                        current_product = products[products['symbol'] == transaction['symbol']]
                        if not current_product.empty:
                            current_price = current_product.iloc[0]
                            if pd.notna(current_price['current_price_eur']):
                                price_change_eur = current_price['current_price_eur'] - transaction['price_eur']
                                price_change_pct = (price_change_eur / transaction['price_eur']) * 100
                                
                                st.divider()
                                st.write("**📊 Évolution depuis l'achat :**")
                                st.write(f"**Prix actuel :** {current_price['current_price_eur']:.2f} €")
                                
                                if price_change_eur >= 0:
                                    st.write(f"**Évolution :** +{price_change_eur:.2f} € (+{price_change_pct:.2f}%) 📈")
                                else:
                                    st.write(f"**Évolution :** {price_change_eur:.2f} € ({price_change_pct:.2f}%) 📉")
        else:
            st.info("🔍 Aucune transaction ne correspond aux filtres sélectionnés.")
            
        # Export des transactions (optionnel)
        if not all_transactions.empty:
            st.divider()
            st.subheader("📤 Export des données")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📊 Télécharger CSV"):
                    csv = filtered_transactions.to_csv(index=False)
                    st.download_button(
                        label="💾 Télécharger",
                        data=csv,
                        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                st.caption("Téléchargez vos transactions filtrées au format CSV pour analyse externe.")