import streamlit as st
from models.portfolio import PortfolioTracker
from ui.dashboard import dashboard_page
from ui.portfolio import portfolio_page
from ui.accounts import accounts_page
from ui.transactions import transaction_page
from ui.config import config_page

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Suivi de Patrimoine",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    tracker = PortfolioTracker()
    
    # Initialiser les taux de change EUR/USD au démarrage avec feedback
    if 'rates_initialized' not in st.session_state:
        with st.spinner("🔄 Récupération du taux de change EUR/USD..."):
            tracker.currency_converter.get_eur_usd_rate(show_debug=True)

        st.session_state.rates_initialized = True
    
    # Sidebar pour la navigation
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox("Choisir une page", 
                               ["🏠 Tableau de Bord", "📈 Suivi de Portefeuille", 
                                "💼 Gestion des Comptes", "💸 Gestion des Transactions", 
                                "⚙️ Configuration"])
    
    if page == "🏠 Tableau de Bord":
        dashboard_page(tracker)
    elif page == "📈 Suivi de Portefeuille":
        portfolio_page(tracker)
    elif page == "💼 Gestion des Comptes":
        accounts_page(tracker)
    elif page == "💸 Gestion des Transactions":
        transaction_page(tracker)
    elif page == "⚙️ Configuration":
        config_page(tracker)

if __name__ == "__main__":
    main()