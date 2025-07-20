import streamlit as st
import pandas as pd

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
            
            ✨ **Nouveauté** : La devise, le nom et le type sont maintenant **détectés automatiquement** !
            """)
        
        with st.form("add_product"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                symbol = st.text_input(
                    "Symbole Yahoo Finance *", 
                    placeholder="Ex: AAPL, BTC-EUR, MC.PA, CW8.PA",
                    help="Trouvez le symbole exact sur fr.finance.yahoo.com"
                )
                name = st.text_input(
                    "Nom personnalisé (optionnel)", 
                    placeholder="Laissez vide pour utiliser le nom officiel",
                    help="Le nom sera automatiquement récupéré depuis Yahoo Finance si laissé vide"
                )
            
            with col2:
                st.info("**🤖 Détection automatique :**\n\n✅ Devise\n✅ Nom officiel\n✅ Type de produit\n✅ Prix actuel")
            
            # Message d'information
            st.success("💡 Le produit sera automatiquement analysé et toutes ses informations seront récupérées depuis Yahoo Finance !")
            
            submitted = st.form_submit_button("✅ Ajouter le produit", type="primary")
            
            if submitted:
                if not symbol.strip():
                    st.error("❌ Le symbole est obligatoire !")
                else:
                    with st.spinner(f"🔍 Analyse automatique du produit '{symbol}' sur Yahoo Finance..."):
                        success, message = tracker.add_financial_product(symbol.strip().upper(), name.strip())
                    
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
            # Statistiques rapides avec nouvelles informations
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total produits", len(products))
            with col2:
                with_price = products[products['current_price'].notna()]
                st.metric("💰 Avec prix", len(with_price))
            with col3:
                product_types = products['product_type'].value_counts()
                most_common = product_types.index[0] if not product_types.empty else "N/A"
                st.metric("🏆 Type principal", most_common)
            with col4:
                currencies = products['currency'].value_counts()
                main_currency = currencies.index[0] if not currencies.empty else "N/A"
                st.metric("💱 Devise principale", main_currency)
            
            # Filtre par type
            filter_type = st.selectbox(
                "Filtrer par type :", 
                ["Tous"] + sorted(products['product_type'].unique().tolist()),
                key="product_filter"
            )
            
            if filter_type != "Tous":
                products = products[products['product_type'] == filter_type]
            
            # Affichage des produits avec nouvelles informations
            for idx, product in products.iterrows():
                status_icon = "✅" if pd.notna(product['current_price']) else "⚠️"
                
                # Affichage des prix dans toutes les devises disponibles
                price_info = ""
                if pd.notna(product['current_price']):
                    native_price = f"{product['current_price']:.2f} {product['currency']}"
                    eur_price = f"{product['current_price_eur']:.2f} EUR" if pd.notna(product['current_price_eur']) else ""
                    usd_price = f"{product['current_price_usd']:.2f} USD" if pd.notna(product['current_price_usd']) else ""
                    
                    if product['currency'] == 'EUR':
                        price_info = f" - {native_price}"
                        if usd_price:
                            price_info += f" / {usd_price}"
                    elif product['currency'] == 'USD':
                        price_info = f" - {native_price}"
                        if eur_price:
                            price_info += f" / {eur_price}"
                    else:
                        price_info = f" - {native_price}"
                        if eur_price and usd_price:
                            price_info += f" / {eur_price} / {usd_price}"
                else:
                    price_info = " - Prix non disponible"
                
                # Informations supplémentaires
                extra_info = []
                if pd.notna(product.get('exchange')):
                    extra_info.append(f"📈 {product['exchange']}")
                if pd.notna(product.get('sector')):
                    extra_info.append(f"🏢 {product['sector']}")
                
                extra_str = " | ".join(extra_info)
                if extra_str:
                    extra_str = f" | {extra_str}"
                
                with st.expander(f"{status_icon} {product['symbol']} - {product['name']}{price_info}{extra_str}"):
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
                                                      ["EUR", "USD", "GBP", "CHF", "CAD", "JPY"],
                                                      index=["EUR", "USD", "GBP", "CHF", "CAD", "JPY"].index(product['currency']) if product['currency'] in ["EUR", "USD", "GBP", "CHF", "CAD", "JPY"] else 0,
                                                      key=f"currency_{product['id']}")
                            
                            col_update, col_delete = st.columns(2)
                            with col_update:
                                if st.form_submit_button("✏️ Modifier", type="primary"):
                                    # Si le symbole a changé, revérifier l'existence
                                    if new_symbol.strip().upper() != product['symbol']:
                                        with st.spinner(f"🔍 Vérification du nouveau symbole '{new_symbol}'..."):
                                            valid, message = tracker.yahoo_utils.validate_symbol(new_symbol.strip().upper())
                                            if not valid:
                                                st.error(f"❌ {message}")
                                            else:
                                                # Symbole valide, procéder à la modification
                                                if tracker.update_financial_product(product['id'], new_symbol.strip().upper(), new_name.strip(), new_type, new_currency):
                                                    st.success("✅ Produit modifié avec succès !")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Erreur lors de la modification (symbole déjà existant ?)")
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
                        # Informations détaillées
                        st.write("**Informations :**")
                        st.write(f"**Type :** {product['product_type']}")
                        st.write(f"**Devise native :** {product['currency']}")
                        
                        if pd.notna(product['current_price']):
                            st.write(f"**Prix natif :** {product['current_price']:.2f} {product['currency']}")
                        
                        if pd.notna(product['current_price_eur']):
                            st.write(f"**Prix EUR :** {product['current_price_eur']:.2f} €")
                        
                        if pd.notna(product['current_price_usd']):
                            st.write(f"**Prix USD :** {product['current_price_usd']:.2f} $")
                        
                        # Informations supplémentaires de Yahoo Finance
                        if pd.notna(product.get('exchange')):
                            st.write(f"**Bourse :** {product['exchange']}")
                        
                        if pd.notna(product.get('sector')):
                            st.write(f"**Secteur :** {product['sector']}")
                        
                        if pd.notna(product.get('country')):
                            st.write(f"**Pays :** {product['country']}")
                        
                        if pd.notna(product.get('market_cap')):
                            market_cap_b = product['market_cap'] / 1e9
                            st.write(f"**Cap. boursière :** {market_cap_b:.1f}B {product['currency']}")
                        
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
            st.markdown("4. **Tout le reste se fait automatiquement !** 🤖")