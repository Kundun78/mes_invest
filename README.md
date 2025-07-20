# Portfolio Tracker 🚀

Une application Streamlit moderne pour le suivi de portefeuille financier multi-devises avec détection automatique et conversion historique.

## ✨ Nouvelles Fonctionnalités

### 🤖 Détection Automatique des Produits Financiers
- **Devise automatique** : Plus besoin de spécifier la devise, elle est détectée depuis Yahoo Finance
- **Métadonnées complètes** : Nom officiel, type de produit, secteur, bourse, capitalisation
- **Validation en temps réel** : Vérification automatique de l'existence sur Yahoo Finance

### 💱 Gestion Multi-Devises Avancée
- **Conversion historique** : Utilise les taux de change de la date de transaction
- **Support étendu** : EUR, USD, GBP, CHF, CAD, JPY
- **Stockage dual** : Tous les prix stockés en EUR et USD
- **Cache intelligent** : Mise en cache des taux historiques

### 🏗️ Architecture Modulaire
Le code a été complètement restructuré pour une meilleure maintenabilité :

```
portfolio_tracker/
├── main.py                 # Point d'entrée principal
├── models/
│   ├── currency.py         # Gestion des devises et conversions
│   ├── database.py         # Gestion de la base de données SQLite
│   └── portfolio.py        # Logique métier du portefeuille
├── ui/
│   ├── dashboard.py        # Interface tableau de bord
│   ├── accounts.py         # Interface gestion des comptes
│   ├── transactions.py     # Interface gestion des transactions
│   ├── portfolio.py        # Interface suivi de portefeuille
│   └── config.py           # Interface de configuration
├── utils/
│   └── yahoo_finance.py    # Utilitaires Yahoo Finance
├── requirements.txt        # Dépendances Python
└── README.md              # Cette documentation
```

## 🚀 Installation et Lancement

### Prérequis
- Python 3.8+
- pip

### Installation
```bash
# Cloner ou télécharger le projet
cd portfolio_tracker

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run main.py
```

## 📋 Guide d'Utilisation

### 1. Premier Démarrage
1. **Créer une plateforme** : Ajoutez vos courtiers/banques dans "Gestion des Comptes" > "Plateformes"
2. **Créer des comptes** : Associez vos comptes (PEA, CTO, etc.) aux plateformes
3. **Ajouter des produits** : Utilisez la détection automatique avec les symboles Yahoo Finance

### 2. Ajouter un Produit Financier
```
✅ Ancien système : Vous deviez spécifier manuellement la devise, le nom, le type
🚀 Nouveau système : Il suffit du symbole Yahoo Finance !

Exemples :
- Actions françaises : MC.PA (LVMH), OR.PA (L'Oréal)
- Actions américaines : AAPL (Apple), MSFT (Microsoft)
- ETF : CW8.PA (MSCI World), EWLD.PA (iShares)
- Crypto : BTC-EUR (Bitcoin), ETH-EUR (Ethereum)
```

### 3. Saisir des Transactions
```
🚀 Nouveauté : Saisissez le prix dans n'importe quelle devise !

Exemple :
- Achat d'Apple (AAPL) coté en USD
- Vous pouvez saisir le prix en EUR, USD, ou même GBP
- La conversion utilise automatiquement le taux historique de la date de transaction
```

## 🔧 Fonctionnalités Techniques

### Détection Automatique des Devises
L'application détecte automatiquement la devise native d'un produit basé sur :
- Les suffixes de symboles (`.PA` = EUR, `.L` = GBP, etc.)
- Les préfixes crypto (`BTC-EUR`, `ETH-USD`, etc.)
- Les métadonnées Yahoo Finance
- Des règles de fallback intelligentes

### Conversion Historique
- Récupération des taux EUR/USD historiques via Yahoo Finance
- Cache local pour éviter les appels API répétés
- Fallback vers des APIs alternatives si Yahoo Finance est indisponible
- Stockage des taux utilisés dans la base de données

### Base de Données Évolutive
- Schema SQLite avec support des migrations automatiques
- Stockage des prix en devises multiples
- Historique des taux de change utilisés
- Métadonnées enrichies des produits financiers

## 🔍 Symboles Yahoo Finance Supportés

### Actions
- **France** : `MC.PA`, `OR.PA`, `AI.PA`, `SAN.PA`
- **USA** : `AAPL`, `MSFT`, `GOOGL`, `TSLA`
- **UK** : `LLOY.L`, `BP.L`, `SHEL.L`
- **Allemagne** : `SAP.DE`, `SIE.DE`

### ETF
- **Européens** : `CW8.PA`, `EWLD.PA`, `PAEEM.PA`
- **Américains** : `SPY`, `QQQ`, `VTI`

### Cryptomonnaies
- **En EUR** : `BTC-EUR`, `ETH-EUR`, `ADA-EUR`
- **En USD** : `BTC-USD`, `ETH-USD`, `DOGE-USD`

## 📊 Interface Utilisateur

### Tableau de Bord
- Vue d'ensemble du portefeuille en temps réel
- Graphiques de répartition par devise, type, plateforme
- Transactions récentes avec conversion automatique

### Suivi de Portefeuille
- Analyse avancée avec filtres multiples
- Graphiques d'évolution temporelle
- Breakdown par compte avec informations de devise
- Top/Flop performers

### Gestion des Transactions
- Saisie dans n'importe quelle devise
- Conversion automatique avec taux historiques
- Preview des conversions avant validation
- Export CSV des transactions

## 🛠️ Configuration

### Initialisation de l'Historique
Pour utiliser les graphiques d'évolution :
1. Allez dans "Configuration"
2. Cliquez sur "Initialiser l'historique complet"
3. Attendez que tous les produits soient traités

### Gestion des Taux de Change
- Mise à jour automatique toutes les 6 heures
- Bouton de mise à jour manuelle disponible
- Test de connectivité aux APIs
- Cache des taux historiques

## 🐛 Résolution de Problèmes

### Symbole Non Trouvé
```
❌ Erreur : Symbole 'XYZ' non trouvé
✅ Solution : Vérifiez sur fr.finance.yahoo.com
- Recherchez votre produit
- Copiez le symbole exact depuis l'URL
- Ajoutez les suffixes appropriés (.PA, .L, etc.)
```

### Problème de Conversion
```
⚠️ Taux de change non disponible
✅ Solutions :
- Vérifiez votre connexion internet
- Actualisez les taux dans Configuration
- Vérifiez si Yahoo Finance est accessible
```

### Base de Données
```
🔧 Maintenance :
- La base portfolio.db est créée automatiquement
- Sauvegardez ce fichier pour conserver vos données
- Les migrations de schema sont automatiques
```

## 🎯 Améliorations Futures

### Prochaines Fonctionnalités
- [ ] Support d'autres sources de données (Alpha Vantage, IEX)
- [ ] Alertes de prix personnalisées
- [ ] Import de transactions via CSV
- [ ] Calcul des dividendes automatique
- [ ] Support des fractions d'actions
- [ ] Interface mobile optimisée

### Optimisations
- [ ] Cache Redis pour les données fréquentes
- [ ] API rate limiting intelligent
- [ ] Compression de l'historique ancien
- [ ] Export vers Excel avec formatage

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :
1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation dans l'interface
- Utilisez les outils de debug dans Configuration

---

