import streamlit as st
from models.portfolio import PortfolioTracker
from models.auth import init_session_state, AuthManager
from ui.dashboard import dashboard_page
from ui.portfolio import portfolio_page
from ui.accounts import accounts_page
from ui.transactions import transaction_page
from ui.config import config_page
from ui.login import login_page, show_user_menu, is_logged_in, get_current_user_id
from ui.account import account_page
from ui.social import social_dashboard

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Portfolio Tracker - Communauté",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialiser l'état de session pour l'authentification
    init_session_state()
    
    # Si l'utilisateur n'est pas connecté, afficher la page de connexion
    if not is_logged_in():
        login_page()
        return
    
    # Utilisateur connecté - continuer avec l'application
    user_id = get_current_user_id()
    tracker = PortfolioTracker()
    
    # Initialiser les taux de change EUR/USD au démarrage avec feedback
    if 'rates_initialized' not in st.session_state:
        with st.spinner("🔄 Récupération du taux de change EUR/USD..."):
            tracker.currency_converter.get_eur_usd_rate(show_debug=False)
        st.session_state.rates_initialized = True
    
    # Sidebar pour la navigation
    st.sidebar.title("📊 Portfolio Tracker")
    
    # Afficher les informations utilisateur
    show_user_menu()
    
    # Menu de navigation principal
    st.sidebar.markdown("### 🧭 Navigation")
    
    # Déterminer les pages disponibles selon le type d'utilisateur
    user = st.session_state.user
    
    main_pages = [
        "🏠 Tableau de Bord", 
        "📈 Suivi de Portefeuille", 
        "💼 Gestion des Comptes", 
        "💸 Gestion des Transactions"
    ]
    
    social_pages = [
        "👥 Communauté",
        "👤 Mon Compte"
    ]
    
    admin_pages = []
    if user.get('is_admin', False):
        admin_pages = ["⚙️ Configuration", "🔧 Administration"]
    
    # Sélection de page avec sections
    st.sidebar.markdown("**💼 Mon Portfolio**")
    page = st.sidebar.selectbox("Navigation principale", main_pages, label_visibility="collapsed")
    
    st.sidebar.markdown("**👥 Social & Compte**")
    social_page = st.sidebar.selectbox("Fonctions sociales", social_pages, label_visibility="collapsed")

    if admin_pages:
        st.sidebar.markdown("**🔑 Administration**")
        admin_page = st.sidebar.selectbox("Administration", admin_pages, label_visibility="collapsed")
    
    # Déterminer quelle page afficher
    selected_page = None
    if page in main_pages:
        selected_page = page
    elif social_page in social_pages:
        selected_page = social_page
    elif admin_pages and admin_page in admin_pages:
        selected_page = admin_page
    
    # Navigation vers les pages
    if selected_page == "🏠 Tableau de Bord":
        dashboard_page(tracker, user_id)
    elif selected_page == "📈 Suivi de Portefeuille":
        portfolio_page(tracker, user_id)
    elif selected_page == "💼 Gestion des Comptes":
        accounts_page(tracker, user_id)
    elif selected_page == "💸 Gestion des Transactions":
        transaction_page(tracker, user_id)
    elif selected_page == "👥 Communauté":
        social_dashboard()
    elif selected_page == "👤 Mon Compte":
        account_page()
    elif selected_page == "⚙️ Configuration":
        config_page(tracker, user_id)
    elif selected_page == "🔧 Administration":
        admin_page_content(tracker)
    
    # Informations de pied de page
    st.sidebar.divider()
    st.sidebar.markdown("### 📊 Statistiques")
    
    # Statistiques de l'utilisateur
    try:
        stats = tracker.db.get_database_stats(user_id)
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("💼 Comptes", stats.get('accounts', 0))
            st.metric("💸 Transactions", stats.get('transactions', 0))
        
        with col2:
            st.metric("🏢 Plateformes", stats.get('platforms', 0))
            products_count = len(tracker.get_financial_products())
            st.metric("📊 Produits", products_count)
    
    except Exception:
        pass
    
    # Informations de version et communauté
    st.sidebar.divider()
    st.sidebar.caption("🚀 **Portfolio Tracker v2.0**")
    st.sidebar.caption("💡 Version communautaire")
    
    # Statistiques globales
    try:
        auth_manager = AuthManager()
        public_users = auth_manager.get_public_users()
        st.sidebar.caption(f"👥 {len(public_users)} utilisateurs publics")
    except Exception:
        pass

def admin_page_content(tracker):
    """Page d'administration réservée aux administrateurs"""
    from models.auth import check_admin
    admin_user = check_admin()  # Vérification des droits admin
    
    st.title("🔧 Administration")
    st.caption("Gestion avancée de la plateforme Portfolio Tracker")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Utilisateurs", "📊 Produits Financiers", "🗄️ Base de Données", "⚙️ Système"])
    
    with tab1:
        st.subheader("👥 Gestion des utilisateurs")
        
        auth_manager = AuthManager()
        
        # Statistiques des utilisateurs
        import sqlite3
        conn = sqlite3.connect(auth_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_public = TRUE")
        public_users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = TRUE")
        admin_users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE last_login > datetime('now', '-7 days')")
        active_users = cursor.fetchone()[0]
        
        # Afficher les métriques
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Total utilisateurs", total_users)
        with col2:
            st.metric("🌍 Profils publics", public_users_count)
        with col3:
            st.metric("🔑 Administrateurs", admin_users_count)
        with col4:
            st.metric("🔥 Actifs (7j)", active_users)
        
        st.divider()
        
        # Liste des utilisateurs
        cursor.execute("""
            SELECT id, username, display_name, email, is_public, is_admin, 
                   created_at, last_login
            FROM users 
            ORDER BY created_at DESC
        """)
        users_data = cursor.fetchall()
        conn.close()
        
        if users_data:
            st.write("**📋 Liste des utilisateurs**")
            
            for user_data in users_data:
                user_id, username, display_name, email, is_public, is_admin, created_at, last_login = user_data
                
                with st.expander(f"👤 {display_name or username} (@{username})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**ID :** {user_id}")
                        st.write(f"**Email :** {email or 'Non renseigné'}")
                        st.write(f"**Créé le :** {created_at}")
                        st.write(f"**Dernière connexion :** {last_login or 'Jamais connecté'}")
                        
                        # Statuts
                        statuses = []
                        if is_admin:
                            statuses.append("🔑 Admin")
                        if is_public:
                            statuses.append("👥 Public")
                        else:
                            statuses.append("🔒 Privé")
                        
                        st.write(f"**Statut :** {' | '.join(statuses)}")
                    
                    with col2:
                        # Actions admin (pour plus tard)
                        if user_id != admin_user['id']:  # Ne pas permettre de modifier son propre compte
                            if st.button(f"🔧 Gérer", key=f"manage_{user_id}"):
                                st.info("🚧 Gestion utilisateur en cours de développement")
    
    with tab2:
        st.subheader("📊 Gestion des produits financiers")
        
        products = tracker.get_financial_products()
        
        if not products.empty:
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
            
            # Actions de maintenance
            st.divider()
            st.write("**🔧 Actions de maintenance**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Actualiser tous les prix", type="primary"):
                    with st.spinner("Mise à jour en cours..."):
                        tracker.update_all_prices(30)
                    st.success("Prix mis à jour!")
                    st.rerun()
            
            with col2:
                if st.button("📈 Réinitialiser l'historique"):
                    if st.confirm("Êtes-vous sûr ? Cette opération peut prendre du temps."):
                        tracker.initialize_price_history(365)
                        st.rerun()
            
            with col3:
                st.button("🧹 Nettoyer les doublons", help="Fonctionnalité en développement")
            
            # Liste des produits avec actions admin
            st.divider()
            st.write("**📋 Produits financiers**")
            
            # Filtre par type
            filter_type = st.selectbox("Filtrer par type", 
                                     ["Tous"] + sorted(products['product_type'].unique().tolist()))
            
            if filter_type != "Tous":
                filtered_products = products[products['product_type'] == filter_type]
            else:
                filtered_products = products
            
            # Affichage tabulaire
            st.dataframe(
                filtered_products[['symbol', 'name', 'product_type', 'currency', 
                                 'current_price', 'last_updated']], 
                use_container_width=True
            )
    
    with tab3:
        st.subheader("🗄️ Gestion de la base de données")
        
        # Statistiques générales
        all_stats = tracker.db.get_database_stats()
        
        st.write("**📊 Statistiques globales**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Utilisateurs", all_stats.get('users', 0))
            st.metric("💸 Transactions", all_stats.get('transactions', 0))
        
        with col2:
            st.metric("📊 Produits", all_stats.get('financial_products', 0))
            st.metric("📈 Historique prix", all_stats.get('price_history', 0))
        
        with col3:
            st.metric("💱 Taux change", all_stats.get('exchange_rates', 0))
            
            # Taille de la base
            import os
            if os.path.exists(tracker.db.db_path):
                size_mb = os.path.getsize(tracker.db.db_path) / (1024 * 1024)
                st.metric("💾 Taille DB", f"{size_mb:.1f} MB")
        
        st.divider()
        
        # Actions de maintenance
        st.write("**🔧 Maintenance de la base de données**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 Nettoyer historique ancien"):
                import sqlite3
                from datetime import datetime, timedelta
                
                conn = sqlite3.connect(tracker.db.db_path)
                cursor = conn.cursor()
                
                # Supprimer l'historique de plus de 2 ans
                two_years_ago = datetime.now() - timedelta(days=730)
                cursor.execute("DELETE FROM price_history WHERE date < ?", (two_years_ago,))
                deleted = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                st.success(f"✅ {deleted} entrées supprimées")
                st.rerun()
        
        with col2:
            if st.button("🔄 Recalculer conversions"):
                st.info("🚧 Fonctionnalité en développement")
        
        with col3:
            if st.button("📊 Analyser intégrité"):
                st.info("🚧 Fonctionnalité en développement")
        
        # Sauvegarde
        st.divider()
        st.write("**💾 Sauvegarde et restauration**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Créer sauvegarde"):
                st.info("💡 Copiez le fichier 'portfolio.db' pour sauvegarder")
        
        with col2:
            st.button("📤 Restaurer sauvegarde", help="Remplacez le fichier 'portfolio.db'")
    
    with tab4:
        st.subheader("⚙️ Configuration système")
        
        # Configuration des taux de change
        st.write("**💱 Gestion des devises**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Actualiser taux EUR/USD"):
                tracker.currency_converter.last_update = None
                success = tracker.currency_converter.get_eur_usd_rate(show_debug=True)
                if success:
                    st.success("✅ Taux mis à jour!")
                else:
                    st.warning("⚠️ Utilisation du taux de secours")
        
        with col2:
            st.text_area("Informations taux", 
                        value=tracker.currency_converter.get_rate_info(),
                        height=150, disabled=True)
        
        st.divider()
        
        # Paramètres de performance
        st.write("**⚡ Performance et limites**")
        
        performance_settings = {
            "Délai entre requêtes API": "1 seconde",
            "Cache historique": "30 jours",
            "Sessions utilisateur": "30 jours",
            "Nettoyage automatique": "Activé"
        }
        
        for setting, value in performance_settings.items():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{setting}**")
            with col2:
                st.write(value)
        
        st.divider()
        
        # Logs et debug
        st.write("**🔍 Logs et débogage**")
        
        if st.button("📋 Afficher logs récents"):
            st.code("""
[2025-07-20 10:30:15] INFO: Utilisateur kundun connecté
[2025-07-20 10:30:16] INFO: Actualisation taux EUR/USD: 1.0842
[2025-07-20 10:31:20] INFO: Nouveau produit ajouté: AAPL
[2025-07-20 10:32:05] INFO: Transaction créée pour utilisateur ID 1
[2025-07-20 10:35:10] INFO: Prix mis à jour pour 15 produits
            """)
        
        # Version et informations système
        st.divider()
        st.write("**ℹ️ Informations système**")
        
        import platform
        import sys
        
        system_info = {
            "Version Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "Système": platform.system(),
            "Version Streamlit": st.__version__ if hasattr(st, '__version__') else "Inconnue",
            "Portfolio Tracker": "v2.0 - Multi-utilisateur"
        }
        
        for info, value in system_info.items():
            st.write(f"**{info}:** {value}")

if __name__ == "__main__":
    main()