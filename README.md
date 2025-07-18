💰 Outil de Suivi de Patrimoine Financier
Un outil complet développé en Python avec Streamlit pour suivre votre patrimoine financier avec des courbes d'évolution avancées et des analyses détaillées.
🚀 Fonctionnalités
📊 Suivi Avancé

Courbes d'évolution temporelles : Visualisez l'évolution de votre portefeuille dans le temps
Filtres sophistiqués : Par compte, produit financier, classe d'actifs, et période personnalisable
Analyses multi-dimensionnelles : Répartition par plateforme, compte, produit, classe d'actifs
Historique des prix complet : Données historiques jusqu'à 2 ans en arrière

💼 Gestion Complète (CRUD)

Multi-plateformes : Gérez vos comptes sur différentes plateformes (brokers, banques, etc.)
Produits financiers variés : Actions, ETF, crypto-monnaies, obligations, etc.
CRUD complet : Créer, Lire, Modifier, Supprimer tous vos éléments
Contrôles de sécurité : Vérifications avant suppression des éléments liés

💸 Gestion Complète des Transactions

Ajout simplifié : Formulaire intuitif pour nouvelles transactions
Modification complète : Édition de tous les champs d'une transaction
Suppression sécurisée : Suppression avec confirmations
Filtrage avancé : Par compte, type, période
Organisation intelligente : Transactions groupées par date
Statistiques temps réel : Achats, ventes, frais totaux

🔄 Données en Temps Réel

Mise à jour automatique des prix : Via l'API Yahoo Finance
Historique automatique : Récupération et stockage de l'historique des prix
Calcul automatique des performances : Plus/moins-values, pourcentages de gain
Métriques en temps réel : Valeur totale, variation, top/flop performers

🎨 Interface Moderne

Tableaux de bord interactifs : Graphiques Plotly avec zoom et filtres
Navigation intuitive : Sidebar avec filtres avancés
Design responsive : Compatible mobile et desktop
Visualisations riches : Courbes, secteurs, barres, métriques

📋 Prérequis

Python 3.8 ou plus récent
Connexion Internet (pour la mise à jour des prix)

🛠 Installation

Télécharger les fichiers :

portfolio_tracker.py
requirements.txt
sample_data.py (optionnel)


Installer les dépendances :
bashpip install -r requirements.txt

Lancer l'application :
bashstreamlit run portfolio_tracker.py

Ouvrir votre navigateur :
L'application s'ouvrira automatiquement à l'adresse http://localhost:8501

🎯 Guide d'utilisation
1. Configuration initiale
a) Ajouter des plateformes :

Allez dans "💼 Gestion des Comptes" → onglet "Plateformes"
Ajoutez vos plateformes d'investissement (ex: Boursorama, Degiro, Binance, etc.)
Modifiez ou supprimez selon vos besoins

b) Créer des comptes :

Dans l'onglet "Comptes", associez vos comptes à leurs plateformes
Types de comptes supportés : CTO, PEA, Assurance Vie, Livret, Portefeuille Crypto, etc.
Interface de modification complète

c) Ajouter des produits financiers :

Dans l'onglet "Produits Financiers", ajoutez les actifs que vous détenez
Utilisez les symboles Yahoo Finance (ex: AAPL, BTC-EUR, MC.PA)
Modification et suppression avec vérifications de sécurité

2. Initialisation de l'historique des prix ⚡
IMPORTANT : Pour utiliser les courbes d'évolution, vous devez initialiser l'historique :

Allez dans "⚙️ Configuration"
Section "📈 Initialisation de l'historique des prix"
Choisissez le nombre de jours (recommandé : 365 jours)
Cliquez "🚀 Initialiser l'historique complet"
Attendez la fin du processus (peut prendre plusieurs minutes)

3. Gestion des transactions
Nouvelle transaction :

Allez dans "💸 Gestion des Transactions" → onglet "Nouvelle Transaction"
Saisissez : compte, produit, type (BUY/SELL), quantité, prix, frais, date

Modifier/Supprimer :

Onglet "Gérer les Transactions" → filtrez et trouvez votre transaction
Modifiez tous les champs ou supprimez si nécessaire
Filtres disponibles : compte, type, période

Filtrage intelligent :

Par compte : analysez l'activité d'un compte spécifique
Par type : voir tous les achats ou toutes les ventes
Par période : focus sur 7 jours, 30 jours, 3 mois

4. Suivi avancé du portefeuille 📈
Filtres avancés (sidebar) :

Période : Prédéfinie (1 mois à 2 ans) ou personnalisée
Comptes : Sélection multiple de vos comptes
Produits : Filtrage par produits financiers spécifiques
Classes d'actifs : Actions, ETF, Crypto, etc.

Analyses disponibles :

Courbe d'évolution principale : Valeur totale dans le temps
Par Plateforme : Répartition et évolution par broker/banque
Par Compte : Performance de chaque compte
Par Produit : Analyse détaillée par position
Par Classe d'Actifs : Vue macro de votre allocation

Métriques calculées :

Valeur actuelle vs montant investi
Plus/moins-values en € et %
Performance relative par position
Top/Flop performers

5. Tableau de bord

Vue d'ensemble : Métriques clés de votre patrimoine
Évolution récente : Graphique 30 derniers jours
Répartitions : Par produit et plateforme
Performances : Meilleures et pires positions

📊 Symboles supportés
Actions françaises

MC.PA (LVMH)
OR.PA (L'Oréal)
AIR.PA (Airbus)
BNP.PA (BNP Paribas)
SAN.PA (Sanofi)

Actions américaines

AAPL (Apple)
MSFT (Microsoft)
GOOGL (Alphabet)
TSLA (Tesla)
NVDA (Nvidia)

ETF populaires

CW8.PA (MSCI World)
EWLD.PA (EWLD)
PAEEM.PA (Emerging Markets)
LYXOR.PA (CAC 40)

Crypto-monnaies populaires

BTC-EUR (Bitcoin)
ETH-EUR (Ethereum)
ADA-EUR (Cardano)
SOL-EUR (Solana)
MATIC-EUR (Polygon)
AVAX-EUR (Avalanche)
LINK-EUR (Chainlink)
DOT-EUR (Polkadot)

Plateformes crypto

Binance : Plateforme leader mondial
Coinbase : Interface simple, régulée US
Kraken : Sécurisée, basée en Europe
Crypto.com : Avec carte de crédit crypto
Bitpanda : Interface française

🔧 Fonctionnalités avancées
Historique et évolution

Stockage local : Historique complet dans SQLite
Calculs temporels : Évolution de la valeur du portefeuille jour par jour
Gestion des dividendes : Prêt pour futures implémentations
Optimisation des performances : Requêtes SQL optimisées

Filtrage et analyse

Filtres combinables : Comptes + Produits + Classes + Période
Visualisations interactives : Zoom, hover, légendes
Exports de données : Tableaux complets avec formatage
Breakdown détaillé : Répartition multi-niveaux