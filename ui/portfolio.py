import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

def portfolio_page(tracker, user_id):
    st.title("📈 Suivi de Portefeuille Avancé")
    st.caption("💱 Analyse multi-devises avec conversion automatique en temps réel")
    
    # Sidebar pour les filtres
    with st.sidebar:
        st.subheader("🔍 Filtres")
        
        # Sélection de la période
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
        
        # Options d'affichage des courbes
        st.write("**📈 Options d'affichage**")
        chart_type = st.radio("Type de graphique", 
                             ["🌈 Répartition cumulative", "📊 Valeur totale", "💰 Investissement vs Plus/Moins Value"],
                             index=0,
                             help="Répartition cumulative: courbe empilée par catégorie | Valeur totale: courbe simple | Investissement vs +/- Value: évolution des montants investis et gains/pertes")
        
        if chart_type == "🌈 Répartition cumulative":
            breakdown_by = st.selectbox("Répartition par", 
                                      ["💼 Comptes", "🏷️ Classes d'actifs", "🏢 Plateformes", "📊 Produits Financiers", "💱 Devises"],
                                      help="Choisissez comment diviser la courbe cumulative")
        else:
            breakdown_by = "💼 Comptes"
        
        st.divider()
        
        # Récupérer les options de filtrage - filtré par user_id
        filters = tracker.get_available_filters(user_id)
        
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
    portfolio = tracker.get_portfolio_summary(user_id)
    
    if portfolio.empty:
        st.info("📝 Aucune position dans le portefeuille. Ajoutez des transactions pour commencer l'analyse!")
        return
    
    # Applique les filtres au portefeuille actuel
    filtered_portfolio = portfolio.copy()
    
    if account_filter:
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
    
    # Récupérer l'évolution - filtré par user_id
    evolution_data = tracker.get_portfolio_evolution(
        start_date, end_date, user_id, account_filter, product_filter, asset_filter
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
                "📊 Produits Financiers": 'breakdown_product',
                "💱 Devises": 'breakdown_currency'
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
        
        # Métriques d'évolution
        col1, col2, col3, col4 = st.columns(4)
        
        first_value = evolution_data['total_value'].iloc[0]
        last_value = evolution_data['total_value'].iloc[-1]
        variation = last_value - first_value
        variation_pct = (variation / first_value) * 100 if first_value > 0 else 0
        
        with col1:
            st.metric("📊 Variation de période", 
                     f"{variation:,.2f} €",
                     delta=f"{variation_pct:.2f}%")
        
        with col2:
            max_value = evolution_data['total_value'].max()
            st.metric("📈 Valeur maximale", f"{max_value:,.2f} €")
        
        with col3:
            min_value = evolution_data['total_value'].min()
            st.metric("📉 Valeur minimale", f"{min_value:,.2f} €")
        
        with col4:
            volatility = evolution_data['total_value'].std()
            st.metric("📊 Volatilité", f"{volatility:,.2f} €")
            
    else:
        # Vérifier s'il y a des données d'historique pour cet utilisateur
        stats = tracker.db.get_database_stats(user_id)
        history_count = stats.get('price_history', 0)
        
        if history_count == 0:
            st.info("📊 Pour voir les graphiques d'évolution, initialisez d'abord l'historique des prix dans la Configuration.")
            st.info("💡 Allez dans **Configuration** → **Initialisation de l'historique des prix** → **Initialiser l'historique complet**")
        else:
            st.warning("📊 Pas assez de données pour la période sélectionnée. Essayez une période plus large ou vérifiez que vous avez des transactions dans cette période.")
            st.info("💡 Pour diagnostiquer le problème, allez dans **Configuration** → **Diagnostic des Graphiques d'Évolution**")
    
    # Graphiques de répartition actuels
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Répartition par produit")
        if not filtered_portfolio.empty:
            fig_pie = px.pie(filtered_portfolio, values='current_value', names='name',
                            title="")
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("🏢 Répartition par plateforme")
        if not filtered_portfolio.empty:
            platform_summary = filtered_portfolio.groupby('platform_name')['current_value'].sum().reset_index()
            fig_platform = px.bar(platform_summary, x='platform_name', y='current_value',
                                 title="")
            fig_platform.update_layout(
                height=400, 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_tickangle=-45,
                showlegend=False
            )
            st.plotly_chart(fig_platform, use_container_width=True)
    
    # Répartition par devise
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💱 Répartition par devise native")
        if not filtered_portfolio.empty:
            currency_summary = filtered_portfolio.groupby('currency')['current_value'].sum().reset_index()
            fig_currency = px.pie(currency_summary, values='current_value', names='currency',
                                title="")
            fig_currency.update_traces(textposition='inside', textinfo='percent+label')
            fig_currency.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_currency, use_container_width=True)
    
    with col2:
        st.subheader("🏷️ Répartition par classe d'actifs")
        if not filtered_portfolio.empty:
            asset_summary = filtered_portfolio.groupby('product_type')['current_value'].sum().reset_index()
            fig_asset = px.bar(asset_summary, x='product_type', y='current_value',
                             title="")
            fig_asset.update_layout(
                height=400, 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_tickangle=-45,
                showlegend=False
            )
            st.plotly_chart(fig_asset, use_container_width=True)
    
    st.divider()
    
    # Tableau détaillé organisé par compte
    st.subheader("📋 Détail des Positions par Compte")
    
    if not filtered_portfolio.empty:
        # Organiser le portfolio par compte
        portfolio_by_account = filtered_portfolio.sort_values(['account_name', 'symbol'])
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
                
                # Créer le DataFrame pour ce compte avec informations de devise
                account_df = account_positions[[
                    'symbol', 'name', 'product_type', 'currency', 'total_quantity', 
                    'avg_buy_price_eur', 'current_price_eur', 'current_value', 
                    'total_invested', 'gain_loss', 'gain_loss_pct'
                ]].copy()
                
                # Ajouter des emojis selon le type de produit et la devise
                def add_emoji_to_symbol(row):
                    symbol = row['symbol']
                    product_type = row['product_type']
                    currency = row['currency']
                    
                    # Emoji pour le type
                    if product_type == 'Crypto':
                        type_emoji = "🪙"
                    elif product_type == 'ETF':
                        type_emoji = "📊"
                    elif product_type == 'Action':
                        type_emoji = "📈"
                    else:
                        type_emoji = "💰"
                    
                    # Emoji pour la devise
                    if currency == 'EUR':
                        currency_emoji = "🇪🇺"
                    elif currency == 'USD':
                        currency_emoji = "🇺🇸"
                    elif currency == 'GBP':
                        currency_emoji = "🇬🇧"
                    else:
                        currency_emoji = "🌍"
                    
                    return f"{type_emoji}{currency_emoji} {symbol}"
                
                account_df['symbol_with_emoji'] = account_df.apply(add_emoji_to_symbol, axis=1)
                
                # Renommer les colonnes pour l'affichage
                display_df = account_df[[
                    'symbol_with_emoji', 'name', 'product_type', 'currency', 'total_quantity', 
                    'avg_buy_price_eur', 'current_price_eur', 'current_value', 
                    'total_invested', 'gain_loss', 'gain_loss_pct'
                ]].copy()
                
                display_df.columns = [
                    'Symbole', 'Nom', 'Type', 'Devise', 'Quantité', 
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
    
    # Section d'analyse avancée
    st.divider()
    st.subheader("📊 Analyse Avancée")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🎯 Top Performers**")
        if not filtered_portfolio.empty:
            top_performers = filtered_portfolio.nlargest(5, 'gain_loss_pct')[['symbol', 'name', 'gain_loss_pct']]
            for _, perf in top_performers.iterrows():
                st.write(f"📈 **{perf['symbol']}**: +{perf['gain_loss_pct']:.2f}%")
    
    with col2:
        st.write("**📉 Positions en perte**")
        if not filtered_portfolio.empty:
            worst_performers = filtered_portfolio[filtered_portfolio['gain_loss_pct'] < 0].nsmallest(5, 'gain_loss_pct')[['symbol', 'name', 'gain_loss_pct']]
            if not worst_performers.empty:
                for _, perf in worst_performers.iterrows():
                    st.write(f"📉 **{perf['symbol']}**: {perf['gain_loss_pct']:.2f}%")
            else:
                st.write("🎉 Aucune position en perte !")
    
    # Informations sur les devises
    st.subheader("💱 Informations de Change")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Taux EUR/USD actuel :**")
        rate_info = tracker.currency_converter.get_rate_info()
        st.text(rate_info)
    
    with col2:
        if st.button("🔄 Actualiser les taux"):
            tracker.currency_converter.last_update = None
            success = tracker.currency_converter.get_eur_usd_rate(show_debug=True)
            if success:
                st.success("✅ Taux mis à jour!")
            st.rerun()