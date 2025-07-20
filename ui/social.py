import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from models.auth import AuthManager, require_auth

def social_page(tracker):
    """Page sociale pour voir les portefeuilles publics"""
    
    # Vérifier l'authentification
    user = require_auth()
    auth_manager = AuthManager()
    
    st.title("🌍 Communauté Portfolio Tracker")
    st.caption("Découvrez les portefeuilles publics de vos amis et apprenez de leurs stratégies d'investissement")
    
    # Récupérer les utilisateurs publics
    public_users = auth_manager.get_public_users()
    
    if not public_users:
        st.info("""
        🤷‍♂️ **Aucun portefeuille public pour le moment**
        
        Soyez le premier à partager votre portefeuille avec la communauté !
        Allez dans **Mon Compte** → **Profil** et activez l'option "Rendre mon portefeuille public"
        """)
        return
    
    # Sidebar avec filtres et options
    with st.sidebar:
        st.subheader("🔍 Explorer")
        
        # Filtre par utilisateur
        user_options = ["Tous"] + [u['display_name'] for u in public_users]
        selected_user = st.selectbox("Utilisateur", user_options)
        
        # Options d'affichage
        st.subheader("👁️ Affichage")
        show_descriptions = st.checkbox("Afficher les descriptions", value=True)
        show_stats = st.checkbox("Afficher les statistiques", value=True)
        
        # Tri
        sort_options = ["Dernière activité", "Ancienneté", "Nom"]
        sort_by = st.selectbox("Trier par", sort_options)
    
    # Vue d'ensemble de la communauté
    st.subheader("📊 Vue d'ensemble de la Communauté")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Utilisateurs publics", len(public_users))
    
    with col2:
        # Compter le total des transactions publiques
        total_transactions = 0
        for pub_user in public_users:
            user_stats = auth_manager.get_user_stats(pub_user['id'])
            total_transactions += user_stats['transactions_count']
        st.metric("💸 Transactions publiques", total_transactions)
    
    with col3:
        # Utilisateur le plus actif
        most_active = max(public_users, key=lambda u: auth_manager.get_user_stats(u['id'])['transactions_count'])
        st.metric("🏆 Plus actif", most_active['display_name'])
    
    with col4:
        # Utilisateur le plus ancien
        oldest = min(public_users, key=lambda u: u['created_at'])
        st.metric("🎖️ Premier utilisateur", oldest['display_name'])
    
    st.divider()
    
    # Filtrer les utilisateurs selon la sélection
    if selected_user != "Tous":
        public_users = [u for u in public_users if u['display_name'] == selected_user]
    
    # Trier les utilisateurs
    if sort_by == "Dernière activité":
        public_users.sort(key=lambda u: u['last_login'] or u['created_at'], reverse=True)
    elif sort_by == "Ancienneté":
        public_users.sort(key=lambda u: u['created_at'])
    else:  # Nom
        public_users.sort(key=lambda u: u['display_name'])
    
    # Affichage des portefeuilles publics
    for pub_user in public_users:
        # Créer un conteneur pour chaque utilisateur
        with st.container():
            # En-tête utilisateur
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Nom et statut
                st.markdown(f"### 👤 {pub_user['display_name']}")
                if pub_user['username'] == user['username']:
                    st.markdown("*🔹 C'est vous !*")
            
            with col2:
                # Informations temporelles
                if pub_user['last_login']:
                    last_login = pd.to_datetime(pub_user['last_login'])
                    days_ago = (datetime.now() - last_login).days
                    if days_ago == 0:
                        st.write("🟢 Actif aujourd'hui")
                    elif days_ago == 1:
                        st.write("🟡 Actif hier")
                    else:
                        st.write(f"⚪ Actif il y a {days_ago} jours")
                else:
                    st.write("⚪ Jamais connecté")
            
            with col3:
                # Ancienneté
                created = pd.to_datetime(pub_user['created_at'])
                days_since = (datetime.now() - created).days
                st.write(f"📅 Membre depuis {days_since} jours")
            
            # Description du profil
            if show_descriptions and pub_user['profile_description']:
                st.markdown(f"*💭 {pub_user['profile_description']}*")
            
            # Récupérer les statistiques et le portefeuille de cet utilisateur
            user_stats = auth_manager.get_user_stats(pub_user['id'])
            
            if show_stats:
                # Statistiques de base
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🏢 Plateformes", user_stats['platforms_count'])
                with col2:
                    st.metric("💼 Comptes", user_stats['accounts_count'])
                with col3:
                    st.metric("💸 Transactions", user_stats['transactions_count'])
                with col4:
                    if user_stats['first_transaction']:
                        first_date = pd.to_datetime(user_stats['first_transaction'])
                        experience_days = (datetime.now() - first_date).days
                        st.metric("📈 Expérience", f"{experience_days} jours")
                    else:
                        st.metric("📈 Expérience", "Débutant")
            
            # Obtenir le portefeuille de cet utilisateur (version simplifiée pour la vue publique)
            try:
                # Temporairement changer l'utilisateur actuel pour récupérer son portefeuille
                original_user = st.session_state.user
                st.session_state.user = pub_user
                
                # Créer une instance tracker pour cet utilisateur
                user_portfolio = tracker.get_portfolio_summary()
                
                # Restaurer l'utilisateur original
                st.session_state.user = original_user
                
                if not user_portfolio.empty:
                    # Afficher les graphiques du portefeuille (sans montants exacts)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Répartition par type de produit (sans valeurs)
                        fig_pie = px.pie(
                            user_portfolio, 
                            values='current_value', 
                            names='product_type',
                            title=f"Répartition par type - {pub_user['display_name']}"
                        )
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        fig_pie.update_layout(height=300, showlegend=True)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Top 5 des positions (symboles seulement)
                        top_positions = user_portfolio.nlargest(5, 'current_value')
                        
                        st.write("**🏆 Top 5 des positions :**")
                        for i, (_, position) in enumerate(top_positions.iterrows(), 1):
                            percentage = (position['current_value'] / user_portfolio['current_value'].sum()) * 100
                            gain_color = "🟢" if position['gain_loss_pct'] > 0 else "🔴" if position['gain_loss_pct'] < 0 else "⚪"
                            st.write(f"{i}. **{position['symbol']}** ({percentage:.1f}%) {gain_color}")
                        
                        # Statistiques de performance (sans montants)
                        total_gain_loss_pct = (user_portfolio['gain_loss'].sum() / user_portfolio['total_invested'].sum()) * 100 if user_portfolio['total_invested'].sum() > 0 else 0
                        
                        st.write("**📊 Performance globale :**")
                        if total_gain_loss_pct > 0:
                            st.success(f"📈 +{total_gain_loss_pct:.1f}%")
                        elif total_gain_loss_pct < 0:
                            st.error(f"📉 {total_gain_loss_pct:.1f}%")
                        else:
                            st.info("📊 0.0%")
                        
                        # Diversification
                        nb_positions = len(user_portfolio)
                        st.write(f"**🎯 Diversification :** {nb_positions} positions")
                        
                        if nb_positions <= 3:
                            st.warning("⚠️ Portefeuille peu diversifié")
                        elif nb_positions <= 10:
                            st.info("✅ Diversification modérée")
                        else:
                            st.success("🌟 Très bien diversifié")
                
                else:
                    st.info(f"📭 {pub_user['display_name']} n'a pas encore de positions dans son portefeuille")
                    
            except Exception as e:
                st.error(f"Erreur lors du chargement du portefeuille de {pub_user['display_name']}")
            
            # Actions disponibles
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button(f"📊 Voir le détail", key=f"detail_{pub_user['id']}"):
                    # Rediriger vers une vue détaillée (à implémenter)
                    st.info("🔧 Vue détaillée à venir dans une prochaine version")
            
            with col2:
                if pub_user['username'] != user['username']:
                    if st.button(f"👋 Suivre", key=f"follow_{pub_user['id']}", disabled=True):
                        st.info("🔧 Fonctionnalité de suivi à venir")
            
            with col3:
                if pub_user['username'] == user['username']:
                    st.info("💡 C'est votre portefeuille ! Modifiez-le dans 'Mon Compte'")
            
            st.markdown("---")
    
    # Section d'inspiration et conseils
    st.subheader("💡 Inspirations de la Communauté")
    
    if len(public_users) > 1:
        # Analyser les tendances de la communauté
        all_portfolios = []
        for pub_user in public_users:
            try:
                original_user = st.session_state.user
                st.session_state.user = pub_user
                user_portfolio = tracker.get_portfolio_summary()
                st.session_state.user = original_user
                
                if not user_portfolio.empty:
                    all_portfolios.append(user_portfolio)
            except:
                continue
        
        if all_portfolios:
            # Combiner tous les portefeuilles
            combined_portfolio = pd.concat(all_portfolios, ignore_index=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Actions les plus populaires
                st.write("**🌟 Actions les plus détenues :**")
                symbol_counts = combined_portfolio['symbol'].value_counts().head(5)
                for symbol, count in symbol_counts.items():
                    percentage = (count / len(public_users)) * 100
                    st.write(f"• **{symbol}** - {count} utilisateur(s) ({percentage:.1f}%)")
            
            with col2:
                # Types d'actifs populaires
                st.write("**📊 Types d'actifs populaires :**")
                type_counts = combined_portfolio['product_type'].value_counts()
                fig_community = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Répartition communautaire"
                )
                fig_community.update_layout(height=250, showlegend=True)
                st.plotly_chart(fig_community, use_container_width=True)
    
    # Call-to-action pour partager son portefeuille
    if not user['is_public']:
        st.markdown("---")
        st.info("""
        🌟 **Rejoignez la communauté !**
        
        Partagez votre portefeuille avec les autres utilisateurs et découvrez de nouvelles opportunités d'investissement.
        
        Allez dans **Mon Compte** → **Profil** pour rendre votre portefeuille public.
        """)
        
        if st.button("👤 Aller à Mon Compte", type="primary"):
            st.session_state.page = "account"
            st.rerun()