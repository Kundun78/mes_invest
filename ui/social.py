import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from models.auth import require_auth, AuthManager
from models.portfolio import PortfolioTracker

def social_page():
    """Page sociale pour voir les portefeuilles publics"""
    user = require_auth()
    auth_manager = AuthManager()
    
    st.title("👥 Communauté Portfolio Tracker")
    st.caption("Découvrez les stratégies d'investissement et transactions de la communauté")
    
    # Récupérer la liste des utilisateurs publics
    public_users = auth_manager.get_public_users()
    
    if not public_users:
        st.info("""
        🌱 **La communauté grandit !**
        
        Aucun utilisateur n'a encore rendu son profil public.
        
        **💡 Soyez le premier !**
        - Allez dans votre compte
        - Activez la visibilité publique
        - Partagez votre stratégie et vos transactions avec la communauté
        """)
        return
    
    # Sidebar avec filtres
    with st.sidebar:
        st.subheader("🔍 Filtres de recherche")
        
        # Filtre par nom
        search_term = st.text_input("🔎 Rechercher un utilisateur", placeholder="Nom ou pseudo...")
        
        # Filtre par activité
        activity_filter = st.selectbox("📅 Activité", 
                                     ["Tous", "Actifs (7 derniers jours)", "Récents (30 derniers jours)"])
        
        st.divider()
        st.info("💡 **Conseil :** Cliquez sur un profil pour voir ses transactions détaillées")
        st.warning("👁️ **Transparence :** Tous les profils publics partagent leurs transactions complètes")
    
    # Appliquer les filtres
    filtered_users = public_users.copy()
    
    if search_term:
        filtered_users = [
            u for u in filtered_users 
            if search_term.lower() in u['username'].lower() or 
               search_term.lower() in (u['display_name'] or '').lower()
        ]
    
    if activity_filter == "Actifs (7 derniers jours)":
        week_ago = datetime.now() - timedelta(days=7)
        filtered_users = [
            u for u in filtered_users 
            if u['last_login'] and datetime.fromisoformat(u['last_login']) > week_ago
        ]
    elif activity_filter == "Récents (30 derniers jours)":
        month_ago = datetime.now() - timedelta(days=30)
        filtered_users = [
            u for u in filtered_users 
            if u['last_login'] and datetime.fromisoformat(u['last_login']) > month_ago
        ]
    
    # Affichage des statistiques de la communauté
    st.subheader("📊 Statistiques de la communauté")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Utilisateurs publics", len(public_users))
    
    with col2:
        active_users = len([u for u in public_users if u['last_login'] and 
                          datetime.fromisoformat(u['last_login']) > datetime.now() - timedelta(days=7)])
        st.metric("🔥 Actifs (7j)", active_users)
    
    with col3:
        users_with_bio = len([u for u in public_users if u['bio']])
        st.metric("📝 Avec biographie", users_with_bio)
    
    with col4:
        # Calculer le nombre total de portefeuilles avec des données
        tracker = PortfolioTracker()
        portfolios_with_data = 0
        for u in public_users:
            try:
                portfolio = tracker.get_portfolio_summary(user_id=u['id'])
                if not portfolio.empty:
                    portfolios_with_data += 1
            except:
                pass
        st.metric("💼 Avec portefeuille", portfolios_with_data)
    
    st.divider()
    
    # Affichage des profils utilisateur
    st.subheader(f"👤 Profils de la communauté ({len(filtered_users)})")
    
    if not filtered_users:
        st.warning("🔍 Aucun utilisateur ne correspond à vos critères de recherche.")
        return
    
    # Afficher les utilisateurs par groupes de 2
    for i in range(0, len(filtered_users), 2):
        col1, col2 = st.columns(2)
        
        users_batch = filtered_users[i:i+2]
        
        for j, profile_user in enumerate(users_batch):
            with col1 if j == 0 else col2:
                show_user_profile_card(profile_user, tracker, user['id'])

def show_user_profile_card(profile_user, tracker, current_user_id):
    """Affiche une carte de profil utilisateur"""
    
    # Container pour la carte
    with st.container():
        # En-tête du profil
        col_info, col_stats = st.columns([2, 1])
        
        with col_info:
            # Nom et statut
            st.markdown(f"### 👤 {profile_user['display_name']}")
            st.caption(f"@{profile_user['username']}")
            
            # Dernière activité
            if profile_user['last_login']:
                last_seen = datetime.fromisoformat(profile_user['last_login'])
                days_ago = (datetime.now() - last_seen).days
                
                if days_ago == 0:
                    activity_text = "🟢 Actif aujourd'hui"
                elif days_ago == 1:
                    activity_text = "🟡 Actif hier"
                elif days_ago < 7:
                    activity_text = f"🟡 Actif il y a {days_ago} jours"
                elif days_ago < 30:
                    activity_text = f"🟠 Actif il y a {days_ago} jours"
                else:
                    activity_text = f"🔴 Actif il y a {days_ago} jours"
                
                st.caption(activity_text)
        
        with col_stats:
            # Bouton pour voir le profil détaillé
            if st.button(f"👁️ Voir le profil", key=f"view_{profile_user['id']}", use_container_width=True):
                st.session_state.viewing_user_id = profile_user['id']
                st.rerun()
        
        # Biographie
        if profile_user['bio']:
            st.write(profile_user['bio'])
        else:
            st.caption("_Aucune biographie renseignée_")
        
        # Statistiques du portefeuille
        try:
            portfolio = tracker.get_portfolio_summary(user_id=profile_user['id'])
            
            if not portfolio.empty:
                total_value = portfolio['current_value'].sum()
                total_invested = portfolio['total_invested'].sum()
                total_gain_loss = total_value - total_invested
                total_gain_loss_pct = (total_gain_loss / total_invested) * 100 if total_invested > 0 else 0
                
                st.divider()
                
                # Métriques du portefeuille
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("💰 Valeur", f"{total_value:,.0f}€", label_visibility="collapsed")
                    st.caption("Valeur actuelle")
                
                with col2:
                    st.metric("📈 Performance", f"{total_gain_loss_pct:+.1f}%", 
                             delta=f"{total_gain_loss:+,.0f}€", label_visibility="collapsed")
                    st.caption("Plus/Moins value")
                
                with col3:
                    st.metric("📊 Positions", len(portfolio), label_visibility="collapsed")
                    st.caption("Nombre d'actifs")
                
                # Mini graphique de répartition
                if len(portfolio) > 1:
                    st.divider()
                    fig_mini = px.pie(portfolio, values='current_value', names='name', 
                                    title="Répartition du portefeuille")
                    fig_mini.update_traces(textposition='inside', textinfo='percent')
                    fig_mini.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0),
                                         showlegend=False)
                    st.plotly_chart(fig_mini, use_container_width=True)
            else:
                st.info("📈 Portefeuille en cours de construction")
                
        except Exception as e:
            st.caption("⚠️ Erreur lors du chargement du portefeuille")
        
        st.divider()

def show_detailed_profile():
    """Affiche le profil détaillé d'un utilisateur avec ses transactions publiques"""
    if 'viewing_user_id' not in st.session_state:
        return
    
    viewing_user_id = st.session_state.viewing_user_id
    auth_manager = AuthManager()
    tracker = PortfolioTracker()
    
    # Récupérer les informations de l'utilisateur visualisé
    viewed_profile = auth_manager.get_user_profile(viewing_user_id)
    
    if not viewed_profile or not viewed_profile['is_public']:
        st.error("❌ Profil non trouvé ou privé")
        return
    
    # Bouton de retour
    if st.button("← Retour à la communauté"):
        del st.session_state.viewing_user_id
        st.rerun()
    
    st.title(f"👤 Profil de {viewed_profile['display_name']}")
    st.caption(f"@{viewed_profile['username']}")
    
    # Informations du profil
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if viewed_profile['bio']:
            st.write("**💬 À propos**")
            st.write(viewed_profile['bio'])
        
        # Activité
        if viewed_profile['last_login']:
            last_seen = datetime.fromisoformat(viewed_profile['last_login'])
            st.write(f"**🕒 Dernière activité :** {last_seen.strftime('%d/%m/%Y à %H:%M')}")
        
        if viewed_profile['created_at']:
            created = datetime.fromisoformat(viewed_profile['created_at'])
            st.write(f"**📅 Membre depuis :** {created.strftime('%d/%m/%Y')}")
    
    with col2:
        # Statistiques rapides
        try:
            import sqlite3
            conn = sqlite3.connect(tracker.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (viewing_user_id,))
            transactions_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT MIN(transaction_date), MAX(transaction_date) 
                FROM transactions WHERE user_id = ?
            """, (viewing_user_id,))
            date_range = cursor.fetchone()
            
            cursor.execute("""
                SELECT SUM(CASE WHEN transaction_type = 'BUY' THEN quantity * price_eur 
                               ELSE 0 END) as total_invested
                FROM transactions WHERE user_id = ?
            """, (viewing_user_id,))
            total_invested = cursor.fetchone()[0] or 0
            
            conn.close()
            
            st.metric("💸 Transactions", transactions_count)
            st.metric("💰 Total investi", f"{total_invested:,.0f} €")
            
            if date_range[0]:
                first_transaction = datetime.fromisoformat(date_range[0])
                experience_days = (datetime.now() - first_transaction).days
                st.metric("📈 Expérience", f"{experience_days} jours")
            
        except Exception:
            pass
    
    st.divider()
    
    # Tableau de bord du portefeuille (version publique)
    st.subheader("📊 Tableau de bord public")
    
    try:
        portfolio = tracker.get_portfolio_summary(user_id=viewing_user_id)
        
        if portfolio.empty:
            st.info("📈 Cet utilisateur n'a pas encore de positions dans son portefeuille.")
            return
        
        # Métriques principales
        total_invested = portfolio['total_invested'].sum()
        total_current = portfolio['current_value'].sum()
        total_gain_loss = total_current - total_invested
        total_gain_loss_pct = (total_gain_loss / total_invested) * 100 if total_invested > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Valeur totale", f"{total_current:,.0f} €")
        with col2:
            st.metric("💸 Montant investi", f"{total_invested:,.0f} €")
        with col3:
            st.metric("📈 Plus/Moins value", f"{total_gain_loss:+,.0f} €", 
                     delta=f"{total_gain_loss_pct:+.1f}%")
        with col4:
            st.metric("📊 Positions", len(portfolio))
        
        # Graphiques de répartition
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Répartition par produit")
            fig_pie = px.pie(portfolio, values='current_value', names='name')
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("🏷️ Répartition par type")
            type_summary = portfolio.groupby('product_type')['current_value'].sum().reset_index()
            fig_type = px.bar(type_summary, x='product_type', y='current_value')
            fig_type.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_type, use_container_width=True)
        
        # Top positions avec détails
        st.subheader("🎯 Top positions")
        top_positions = portfolio.nlargest(5, 'current_value')[['symbol', 'name', 'product_type', 'total_quantity', 'current_value', 'gain_loss_pct']]
        
        for _, position in top_positions.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**{position['symbol']}**")
            with col2:
                st.write(position['name'])
            with col3:
                st.write(f"{position['total_quantity']:.2f}")
            with col4:
                color = "🟢" if position['gain_loss_pct'] >= 0 else "🔴"
                st.write(f"{color} {position['gain_loss_pct']:+.1f}%")
        
        st.divider()
        
        # ✨ NOUVELLES SECTIONS - TRANSACTIONS PUBLIQUES
        st.subheader("💸 Historique des Transactions")
        
        # Récupérer toutes les transactions de cet utilisateur
        all_transactions = tracker.get_all_transactions(viewing_user_id)
        
        if not all_transactions.empty:
            # Filtre par période pour les transactions
            transaction_period = st.selectbox(
                "Afficher les transactions des :", 
                ["7 derniers jours", "30 derniers jours", "3 derniers mois", "6 derniers mois", "Toutes"],
                index=1
            )
            
            # Filtrer les transactions selon la période
            end_date = datetime.now()
            if transaction_period == "7 derniers jours":
                start_date = end_date - timedelta(days=7)
                filtered_transactions = all_transactions[all_transactions['transaction_date'] >= start_date]
            elif transaction_period == "30 derniers jours":
                start_date = end_date - timedelta(days=30)
                filtered_transactions = all_transactions[all_transactions['transaction_date'] >= start_date]
            elif transaction_period == "3 derniers mois":
                start_date = end_date - timedelta(days=90)
                filtered_transactions = all_transactions[all_transactions['transaction_date'] >= start_date]
            elif transaction_period == "6 derniers mois":
                start_date = end_date - timedelta(days=180)
                filtered_transactions = all_transactions[all_transactions['transaction_date'] >= start_date]
            else:
                filtered_transactions = all_transactions.head(50)  # Limiter à 50 pour la performance
            
            if not filtered_transactions.empty:
                st.write(f"**📋 {len(filtered_transactions)} transactions trouvées**")
                
                # Affichage des transactions par groupes de date
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
                        type_bg_color = "#d4edda"
                    else:
                        type_color = "🔴"
                        type_label = "VENTE"
                        type_bg_color = "#f8d7da"
                    
                    # Affichage du prix avec conversions
                    price_display = f"{transaction['price']:.2f} {transaction['price_currency']}"
                    
                    # Ajouter les conversions si différentes de la devise de saisie
                    conversion_info = []
                    if transaction['price_currency'] != 'EUR' and pd.notna(transaction['price_eur']):
                        conversion_info.append(f"{transaction['price_eur']:.2f} €")
                    if transaction['price_currency'] != 'USD' and pd.notna(transaction['price_usd']):
                        conversion_info.append(f"{transaction['price_usd']:.2f} $")
                    
                    if conversion_info:
                        price_display += f" ({'/'.join(conversion_info)})"
                    
                    # Container pour chaque transaction
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
                        
                        with col1:
                            st.markdown(f"<div style='background-color: {type_bg_color}; padding: 5px; border-radius: 5px; text-align: center;'>{type_color}<br><small>{type_label}</small></div>", unsafe_allow_html=True)
                        
                        with col2:
                            st.write(f"**{transaction['symbol']}**")
                            st.caption(transaction['product_name'])
                        
                        with col3:
                            st.write(f"**Quantité :** {transaction['quantity']:.4f}")
                            st.caption(f"Compte: {transaction['account_name']}")
                        
                        with col4:
                            st.write(f"**Prix :** {price_display}")
                            if transaction['fees'] > 0:
                                st.caption(f"Frais: {transaction['fees']:.2f} €")
                        
                        with col5:
                            total_amount = transaction['total_amount']
                            st.write(f"**Total :** {total_amount:,.2f} €")
                            # Afficher le taux de change si disponible
                            if pd.notna(transaction.get('exchange_rate_eur_usd')):
                                st.caption(f"Taux: {transaction['exchange_rate_eur_usd']:.4f}")
                        
                        st.divider()
            else:
                st.info(f"Aucune transaction trouvée pour la période sélectionnée.")
        else:
            st.info("Cet utilisateur n'a pas encore effectué de transactions.")
        
        # Statistiques des transactions
        if not all_transactions.empty:
            st.subheader("📊 Analyse des Transactions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Répartition par type
                transaction_types = all_transactions['transaction_type'].value_counts()
                fig_trans_type = px.pie(
                    values=transaction_types.values, 
                    names=transaction_types.index,
                    title="Répartition Achats/Ventes"
                )
                fig_trans_type.update_layout(height=300)
                st.plotly_chart(fig_trans_type, use_container_width=True)
            
            with col2:
                # Évolution du volume des transactions par mois
                all_transactions['month'] = pd.to_datetime(all_transactions['transaction_date']).dt.to_period('M')
                monthly_volume = all_transactions.groupby('month')['total_amount'].sum().reset_index()
                monthly_volume['month_str'] = monthly_volume['month'].astype(str)
                
                fig_monthly = px.bar(
                    monthly_volume, 
                    x='month_str', 
                    y='total_amount',
                    title="Volume Mensuel (€)"
                )
                fig_monthly.update_layout(height=300, showlegend=False)
                fig_monthly.update_xaxes(title="Mois")
                fig_monthly.update_yaxes(title="Volume (€)")
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            with col3:
                # Produits les plus tradés
                product_trades = all_transactions['symbol'].value_counts().head(5)
                fig_products = px.bar(
                    x=product_trades.index,
                    y=product_trades.values,
                    title="Top 5 Produits Tradés"
                )
                fig_products.update_layout(height=300, showlegend=False)
                fig_products.update_xaxes(title="Symbole")
                fig_products.update_yaxes(title="Nombre de transactions")
                st.plotly_chart(fig_products, use_container_width=True)
            
            # Tableau récapitulatif par produit
            st.subheader("📈 Récapitulatif par Produit")
            
            product_summary = all_transactions.groupby('symbol').agg({
                'quantity': lambda x: (all_transactions[all_transactions['symbol']==x.name]['quantity'] * 
                                     (all_transactions[all_transactions['symbol']==x.name]['transaction_type'] == 'BUY').astype(int) - 
                                     all_transactions[all_transactions['symbol']==x.name]['quantity'] * 
                                     (all_transactions[all_transactions['symbol']==x.name]['transaction_type'] == 'SELL').astype(int)).sum(),
                'total_amount': 'sum',
                'transaction_date': 'count'
            }).reset_index()
            
            product_summary.columns = ['Symbole', 'Quantité Nette', 'Volume Total (€)', 'Nb Transactions']
            product_summary = product_summary[product_summary['Quantité Nette'] > 0]  # Afficher seulement les positions actuelles
            
            if not product_summary.empty:
                st.dataframe(
                    product_summary.style.format({
                        'Quantité Nette': '{:.4f}',
                        'Volume Total (€)': '{:,.2f}',
                        'Nb Transactions': '{:.0f}'
                    }),
                    use_container_width=True
                )
            else:
                st.info("Aucune position actuelle trouvée.")
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du portefeuille : {e}")

def social_dashboard():
    """Page principale sociale"""
    # Vérifier si on visualise un profil spécifique
    if 'viewing_user_id' in st.session_state:
        show_detailed_profile()
    else:
        social_page()