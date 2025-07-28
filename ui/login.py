import streamlit as st
from models.auth import AuthManager

def login_page():
    """Page de connexion et d'inscription"""
    st.title("🔐 Connexion - Portfolio Tracker")
    
    auth_manager = AuthManager()
    
    # Onglets pour connexion et inscription
    tab1, tab2 = st.tabs(["🔑 Connexion", "📝 Inscription"])
    
    with tab1:
        st.subheader("Connexion à votre compte")
        
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", placeholder="Votre nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                login_button = st.form_submit_button("🔑 Se connecter", type="primary", use_container_width=True)
            with col2:
                st.caption("Mot de passe oublié ?")
        
        if login_button:
            if not username or not password:
                st.error("❌ Veuillez remplir tous les champs")
            else:
                success, user_data = auth_manager.authenticate_user(username, password)
                
                if success:
                    # Créer une session
                    session_token = auth_manager.create_session(user_data['id'])
                    
                    # Stocker dans la session Streamlit
                    st.session_state.user = user_data
                    st.session_state.session_token = session_token
                    
                    st.success(f"🎉 Bienvenue {user_data['display_name']} !")
                    st.balloons()
                    
                    # Redirection automatique
                    st.rerun()
                else:
                    st.error("❌ Nom d'utilisateur ou mot de passe incorrect")
        
        # Informations pour les nouveaux utilisateurs
        st.divider()
        st.info("""
        **🆕 Nouveau sur Portfolio Tracker ?**
        
        Créez un compte pour :
        - 📊 Suivre votre portefeuille financier
        - 💱 Gérer vos transactions multi-devises  
        - 📈 Visualiser l'évolution de vos investissements
        - 👥 Partager votre performance avec la communauté (optionnel)
        """)
    
    with tab2:
        st.subheader("Créer un nouveau compte")
        
        with st.form("register_form"):
            new_username = st.text_input("Nom d'utilisateur *", 
                                        placeholder="Au moins 3 caractères",
                                        help="Ce nom sera visible par les autres utilisateurs")
            new_email = st.text_input("Email", 
                                     placeholder="votre@email.com (optionnel)",
                                     help="Pour la récupération de compte (optionnel)")
            new_display_name = st.text_input("Nom d'affichage", 
                                            placeholder="Votre nom ou pseudonyme",
                                            help="Nom affiché publiquement (optionnel)")
            new_password = st.text_input("Mot de passe *", 
                                        type="password", 
                                        placeholder="Au moins 6 caractères")
            confirm_password = st.text_input("Confirmer le mot de passe *", 
                                           type="password", 
                                           placeholder="Retapez votre mot de passe")
            
            # Options de confidentialité
            st.divider()
            st.write("**🔒 Paramètres de confidentialité**")
            make_public = st.checkbox("Rendre mon profil public", 
                                    help="Les autres utilisateurs pourront voir votre portefeuille ET vos transactions (vous pourrez changer cela plus tard)")
            
            if make_public:
                st.warning("👥 **Profil public activé :**\n"
                          "- Votre tableau de bord sera visible\n"
                          "- **Vos transactions seront visibles** (symboles, prix, quantités, dates)\n"
                          "- Vos performances d'investissement seront publiques")
            else:
                st.info("🔒 Votre portefeuille et vos transactions resteront privés")
            
            register_button = st.form_submit_button("📝 Créer mon compte", type="primary", use_container_width=True)
        
        if register_button:
            # Validation côté client
            if not new_username or not new_password:
                st.error("❌ Les champs marqués d'une * sont obligatoires")
            elif len(new_username) < 3:
                st.error("❌ Le nom d'utilisateur doit contenir au moins 3 caractères")
            elif len(new_password) < 6:
                st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
            elif new_password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas")
            else:
                # Tentative de création du compte
                success, message = auth_manager.register_user(
                    username=new_username,
                    password=new_password,
                    email=new_email if new_email else None,
                    display_name=new_display_name if new_display_name else None
                )
                
                if success:
                    st.success("✅ " + message)
                    
                    # Configurer la visibilité publique si demandée
                    if make_public:
                        # Se connecter automatiquement pour mettre à jour le profil
                        auth_success, user_data = auth_manager.authenticate_user(new_username, new_password)
                        if auth_success:
                            auth_manager.update_profile(user_data['id'], is_public=True)
                    
                    st.info("🔑 Vous pouvez maintenant vous connecter avec vos identifiants dans l'onglet 'Connexion'")
                    st.balloons()
                else:
                    st.error("❌ " + message)
        
        # Conditions d'utilisation
        st.divider()
        st.caption("""
        **📋 En créant un compte, vous acceptez :**
        - De fournir des informations exactes
        - De garder vos identifiants confidentiels
        - D'utiliser l'application de manière responsable
        - Que les données des produits financiers sont partagées entre tous les utilisateurs
        - **Qu'en mode public, vos transactions d'investissement seront visibles par la communauté**
        """)

def show_user_menu():
    """Affiche le menu utilisateur dans la sidebar"""
    if 'user' in st.session_state and st.session_state.user:
        user = st.session_state.user
        
        st.sidebar.divider()
        st.sidebar.markdown(f"### 👤 {user['display_name']}")
        
        if user.get('is_admin', False):
            st.sidebar.markdown("🔑 **Administrateur**")
        
        if user.get('is_public', False):
            st.sidebar.markdown("👥 **Profil public**")
        else:
            st.sidebar.markdown("🔒 **Profil privé**")
        
        # Bouton de déconnexion
        if st.sidebar.button("🚪 Se déconnecter", use_container_width=True):
            # Supprimer la session côté serveur
            if 'session_token' in st.session_state:
                auth_manager = AuthManager()
                auth_manager.logout_user(st.session_state.session_token)
            
            # Nettoyer la session Streamlit
            st.session_state.user = None
            st.session_state.session_token = None
            
            st.rerun()

def is_logged_in() -> bool:
    """Vérifie si un utilisateur est connecté"""
    return 'user' in st.session_state and st.session_state.user is not None

def get_current_user():
    """Retourne l'utilisateur actuel ou None"""
    return st.session_state.get('user', None)

def get_current_user_id():
    """Retourne l'ID de l'utilisateur actuel ou None"""
    user = get_current_user()
    return user['id'] if user else None