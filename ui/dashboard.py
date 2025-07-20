import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

def dashboard_page(tracker):
    st.title("🏠 Tableau de Bord")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.caption("💱 Tous les prix sont automatiquement détectés et stockés en EUR et USD")
    
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
        stats = tracker.db.get_database_stats()
        history_count = stats.get('price_history', 0)
        
        if history_count > 0:
            # Évolution sur 1 an par défaut
            st.subheader("📈 Évolution (1 an)")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
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
                st.info("📊 Pas assez de données pour afficher l'évolution sur 1 an. Vérifiez que vous avez des transactions et de l'historique de prix.")
        else:
            st.info("🔧 Pour voir les courbes d'évolution, initialisez l'historique des prix dans la Configuration.")
        
        # Graphiques de répartition
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Répartition par produit")
            fig_pie = px.pie(portfolio, values='current_value', names='name')
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("🏢 Répartition par plateforme")
            platform_summary = portfolio.groupby('platform_name')['current_value'].sum().reset_index()
            fig_platform = px.bar(platform_summary, x='platform_name', y='current_value')
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
                
                col1, col2, col3, col4 = st.columns([1, 2, 3, 2])
                with col1:
                    st.write(f"{type_color} {type_label}")
                with col2:
                    st.write(f"**{transaction['symbol']}**")
                with col3:
                    # Affichage amélioré du prix avec conversions
                    price_display = f"{transaction['price']:.2f} {transaction['price_currency']}"
                    
                    # Ajouter les conversions si disponibles et différentes
                    conversions = []
                    if transaction['price_currency'] != 'EUR' and pd.notna(transaction.get('price_eur')):
                        conversions.append(f"{transaction['price_eur']:.2f} €")
                    if transaction['price_currency'] != 'USD' and pd.notna(transaction.get('price_usd')):
                        conversions.append(f"{transaction['price_usd']:.2f} $")
                    
                    if conversions:
                        price_display += f" ({'/'.join(conversions)})"
                    
                    st.write(f"{transaction['quantity']:.4f} @ {price_display}")
                with col4:
                    date_str = transaction['transaction_date'].strftime('%d/%m/%Y')
                    # Ajouter un indicateur si c'est une conversion historique
                    if pd.notna(transaction.get('exchange_rate_eur_usd')) and transaction['price_currency'] != 'EUR':
                        date_str += " 💱"
                    st.write(date_str)
            
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
            st.write("*Les devises sont détectées automatiquement !*")
        
        with col3:
            st.write("**3. Saisissez vos transactions**")
            st.write("Achats/ventes dans n'importe quelle devise")
            st.write("*Conversion automatique !*")
        
        st.info("💡 Utilisez la navigation de gauche pour accéder aux différentes sections.")