import streamlit as st
import pandas as pd
from datetime import datetime
from models.auth import AuthManager, require_auth

def account_page(tracker):
    """Page de gestion du compte utilisateur"""
    
    # Vérifier l'authentification
    user = require_auth()
    auth_manager = AuthManager()
    
    st.title("👤 Mon Compte")
    st.caption(f"Gestion du compte de **{user['display_name']}**")
    
    # Onglets pour différentes sections
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Profil", "🔒 Sécurité", "📊 Statistiques", "⚙️ Paramètres"])
    
    with tab1:
        st.subheader("📋 Informations du Profil")
        
        # Formulaire de mise à jour du profil
        with st.form("update_profile"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**👤 Informations personnelles**")
                
                new_display_name = st.text_input(
                    "Nom d'affichage",
                    value=user['display_name'],
                    help="Comment vous apparaissez aux autres utilisateurs"
                )
                
                new_email = st.text_input(
                    "Adresse email",
                    value=user.get('email', ''),
                    help="Pour les notifications (optionnel)"
                )
                
                # Récupérer la description actuelle
                current_user_data = auth_manager.get_user_by_id(user['id'])
                current_description = current_user_data.get('profile_description', '') if current_user_data else ''
                
                new_description = st.text_area(
                    "Description du profil",
                    value=current_description,
                    placeholder="Parlez de votre stratégie d'investissement, vos objectifs...",
                    help="Visible par les autres utilisateurs si votre profil est public",
                    height=100
                )
            
            with col2:
                st.write("**🌍 Visibilité**")
                
                current_visibility = user['is_public']
                
                new_is_public = st.checkbox(
                    "Rendre mon portefeuille public",
                    value=current_visibility,
                    help="Les autres utilisateurs pourront voir votre tableau de bord"
                )
                
                if new_is_public:
                    st.success("✅ Votre portefeuille sera visible dans la section sociale")
                    st.info("""
                    **🌍 En mode public, les autres verront :**
                    - Votre nom d'affichage
                    - Votre description
                    - Vos graphiques de performance
                    - La répartition de votre portefeuille
                    
                    **🔒 Ils ne verront PAS :**
                    - Vos montants exacts
                    - Vos transactions détaillées
                    - Vos comptes et plateformes
                    """)
                else:
                    st.info("🔒 Votre portefeuille restera privé")
                
                # Informations du compte
                st.write("**ℹ️ Informations du compte**")
                st.write(f"**Nom d'utilisateur :** {user['username']}")
                if user['is_admin']:
                    st.write("**Statut :** 🔧 Administrateur")
                else:
                    st.write("**Statut :** 👤 Utilisateur")
            
            # Bouton de soumission
            if st.form_submit_button("💾 Sauvegarder les modifications", type="primary"):
                success, message = auth_manager.update_user_profile(
                    user['id'],
                    display_name=new_display_name,
                    email=new_email if new_email else None,
                    is_public=new_is_public,
                    profile_description=new_description
                )
                
                if success:
                    st.success(f"✅ {message}")
                    # Mettre à jour la session
                    st.session_state.user['display_name'] = new_display_name
                    st.session_state.user['is_public'] = new_is_public
                    st.session_state.user['email'] = new_email
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with tab2:
        st.subheader("🔒 Sécurité du Compte")
        
        # Changement de mot de passe
        st.write("**🔑 Changer le mot de passe**")
        
        with st.form("change_password"):
            col1, col2 = st.columns(2)
            
            with col1:
                old_password = st.text_input(
                    "Mot de passe actuel",
                    type="password",
                    help="Votre mot de passe actuel"
                )
            
            with col2:
                new_password = st.text_input(
                    "Nouveau mot de passe",
                    type="password",
                    help="Minimum 6 caractères"
                )
                
                confirm_password = st.text_input(
                    "Confirmer le nouveau mot de passe",
                    type="password"
                )
            
            if st.form_submit_button("🔑 Changer le mot de passe"):
                if not all([old_password, new_password, confirm_password]):
                    st.error("❌ Veuillez remplir tous les champs")
                elif new_password != confirm_password:
                    st.error("❌ Les nouveaux mots de passe ne correspondent pas")
                elif len(new_password) < 6:
                    st.error("❌ Le nouveau mot de passe doit contenir au moins 6 caractères")
                else:
                    success, message = auth_manager.change_password(
                        user['id'], old_password, new_password
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
        
        # Informations de sécurité
        st.markdown("---")
        st.write("**🛡️ Conseils de sécurité**")
        st.info("""
        - Utilisez un mot de passe unique et complexe
        - Ne partagez jamais vos identifiants
        - Déconnectez-vous sur les ordinateurs partagés
        - Vérifiez régulièrement l'activité de votre compte
        """)
    
    with tab3:
        st.subheader("📊 Statistiques de votre Portefeuille")
        
        # Récupérer les statistiques
        stats = auth_manager.get_user_stats(user['id'])
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏢 Plateformes", stats['platforms_count'])
        
        with col2:
            st.metric("💼 Comptes", stats['accounts_count'])
        
        with col3:
            st.metric("💸 Transactions", stats['transactions_count'])
        
        with col4:
            if stats['first_transaction']:
                first_date = pd.to_datetime(stats['first_transaction'])
                days_since = (datetime.now() - first_date).days
                st.metric("📅 Depuis", f"{days_since} jours")
            else:
                st.metric("📅 Depuis", "Aucune transaction")
        
        # Informations détaillées
        st.write("**📈 Activité récente**")
        
        # Récupérer les transactions récentes
        user_transactions = tracker.get_all_transactions()
        user_transactions = user_transactions[user_transactions['user_id'] == user['id']] if 'user_id' in user_transactions.columns else user_transactions
        
        if not user_transactions.empty:
            recent_transactions = user_transactions.head(5)
            
            st.write("**🔄 5 dernières transactions :**")
            for _, trans in recent_transactions.iterrows():
                type_emoji = "🟢" if trans['transaction_type'] == 'BUY' else "🔴"
                st.write(f"{type_emoji} {trans['symbol']} - {trans['quantity']:.4f} @ {trans['price']:.2f} {trans['price_currency']} ({trans['transaction_date'].strftime('%d/%m/%Y')})")
            
            # Graphique d'activité par mois
            st.write("**📊 Activité par mois (derniers 12 mois) :**")
            user_transactions['month'] = pd.to_datetime(user_transactions['transaction_date']).dt.to_period('M')
            monthly_activity = user_transactions.groupby('month').size()
            
            if not monthly_activity.empty:
                st.bar_chart(monthly_activity)
            else:
                st.info("Pas encore d'activité à afficher")
        else:
            st.info("🎯 Commencez par ajouter vos premières transactions !")
            
            # Liens vers les autres pages
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🚀 Pour commencer :**")
                st.markdown("1. Ajoutez vos plateformes")
                st.markdown("2. Créez vos comptes")
                st.markdown("3. Ajoutez vos produits financiers")
                st.markdown("4. Saisissez vos transactions")
            
            with col2:
                if st.button("📈 Aller à la Gestion des Comptes", type="primary"):
                    st.session_state.page = "accounts"
                    st.rerun()
    
    with tab4:
        st.subheader("⚙️ Paramètres Avancés")
        
        # Paramètres de notification (pour l'avenir)
        st.write("**🔔 Notifications (à venir)**")
        st.checkbox("Recevoir des notifications par email", disabled=True, help="Fonctionnalité à venir")
        st.checkbox("Notifications de performance hebdomadaire", disabled=True, help="Fonctionnalité à venir")
        st.checkbox("Alertes de nouveaux utilisateurs publics", disabled=True, help="Fonctionnalité à venir")
        
        # Export des données
        st.markdown("---")
        st.write("**📤 Export des Données**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Exporter mes transactions (CSV)"):
                user_transactions = tracker.get_all_transactions()
                if 'user_id' in user_transactions.columns:
                    user_transactions = user_transactions[user_transactions['user_id'] == user['id']]
                
                if not user_transactions.empty:
                    csv = user_transactions.to_csv(index=False)
                    st.download_button(
                        label="💾 Télécharger CSV",
                        data=csv,
                        file_name=f"transactions_{user['username']}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Aucune transaction à exporter")
        
        with col2:
            if st.button("📈 Exporter mon portefeuille (CSV)"):
                portfolio = tracker.get_portfolio_summary()
                if not portfolio.empty:
                    csv = portfolio.to_csv(index=False)
                    st.download_button(
                        label="💾 Télécharger CSV",
                        data=csv,
                        file_name=f"portefeuille_{user['username']}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Aucune position à exporter")
        
        # Actions dangereuses
        st.markdown("---")
        st.write("**⚠️ Zone Dangereuse**")
        
        with st.expander("🗑️ Supprimer mon compte", expanded=False):
            st.error("""
            **⚠️ ATTENTION : Cette action est irréversible !**
            
            La suppression de votre compte entraînera :
            - Suppression de toutes vos transactions
            - Suppression de tous vos comptes et plateformes
            - Perte définitive de votre historique
            
            Cette fonctionnalité sera implémentée dans une future version.
            """)
        
        # Informations sur les données
        st.markdown("---")
        st.write("**ℹ️ À propos de vos données**")
        st.info("""
        - Vos données personnelles sont stockées de manière sécurisée
        - Les mots de passe sont chiffrés et ne peuvent pas être récupérés
        - Les produits financiers sont partagés entre tous les utilisateurs
        - Vous contrôlez entièrement la visibilité de votre portefeuille
        """)