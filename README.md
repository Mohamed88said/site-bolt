# E-Commerce Django Site

Un site e-commerce complet développé avec Django, spécialement conçu pour l'Afrique avec un design moderne et des fonctionnalités adaptées aux réalités locales.

## Fonctionnalités

### 🎨 Design Africain Moderne
- Interface inspirée des motifs et couleurs africaines
- Palette de couleurs chaleureuses (or, terre cuite, orange coucher de soleil)
- Motifs géométriques subtils en arrière-plan
- Animations fluides et transitions élégantes
- Responsive design optimisé pour tous les appareils

### Gestion des utilisateurs
- 5 types d'utilisateurs : Acheteurs, Vendeurs, Livreurs, Admins, Super Admins
- Inscription limitée aux rôles Acheteur/Vendeur/Livreur
- Validation obligatoire des profils vendeurs et livreurs
- Upload de documents (pièce d'identité, RCCM, permis)
- Badge "✅ Vendeur certifié" après validation
- Système d'authentification complet
- Profils personnalisés pour chaque type d'utilisateur

### Gestion des produits
- CRUD complet pour les vendeurs
- Choix libre des catégories par les vendeurs
- Catégories et sous-catégories
- Images multiples par produit
- Variantes de produits
- Système de reviews et ratings
- Alertes de rupture de stock
- Produits invisibles tant que vendeur non validé

### Système de commandes
- Panier d'achat
- Processus de checkout complet
- Modes de paiement multiples (carte, mobile money, cash, retrait)
- Codes de confirmation à 6 chiffres
- QR codes pour validation
- Génération automatique de factures PDF
- Gestion des statuts de commande
- Historique des commandes

### Système de livraisons
- Attribution des livraisons aux livreurs
- Demandes de livraison avec propositions de prix
- Validation par l'acheteur
- Suivi des livraisons
- Évaluation des livreurs
- Géolocalisation précise avec instructions d'accès

### Système de retours
- Demandes de retour avec motifs
- Upload de photos des produits
- Gestion des articles retournés
- Suivi des remboursements
- Workflow complet de traitement
- Interface d'administration des retours

### Géolocalisation Guinée
- **Système révolutionnaire adapté à la Guinée**
- Carte interactive avec OpenStreetMap/Leaflet
- Clic sur carte pour définir position GPS exacte
- **Vérification communautaire par les locaux**
- Descriptions personnalisées remplaçant les coordonnées
- Points de repère culturels et géographiques
- Gestion des régions/préfectures/communes
- Instructions d'accès détaillées
- Zones de livraison avec tarification
- Liens cliquables vers Google Maps

### 💳 Paiement Sécurisé
- Carte bancaire, Mobile money, Cash, Retrait boutique
- Paiement en attente jusqu'à réception
- Codes de confirmation uniques
- QR codes pour validation rapide
- Factures PDF automatiques

### 💬 Messagerie Temps Réel
- Chat Acheteur ↔ Vendeur
- Support client intégré
- Basé sur Django Channels (WebSocket)
- Notifications nouveaux messages
- Historique complet

### 👤 Profils Vendeurs Publics
- Page vendeur consultable avec tous ses produits
- Blog intégré pour chaque vendeur
- Statistiques et notes moyennes
- Badge certifié visible
- Bouton contact direct

### 🔔 Notifications Avancées
- Système complet de notifications
- Alertes rupture de stock
- Notifications commandes, livraisons, avis
- Interface de gestion
- Compteur temps réel

### 📊 Analytics & Dashboard
- Tableau de bord vendeur complet
- Statistiques ventes et performances
- Produits populaires
- Taux de conversion
- Graphiques et métriques

### ✏️ Blog Vendeurs
- Système de blog intégré
- Éditeur riche CKEditor
- Catégories d'articles
- Gestion brouillons/publié
- Commentaires et modération

### 🎫 Système de Coupons
- Codes promotionnels
- Remises pourcentage/montant fixe
- Conditions d'utilisation
- Limites et seuils
- Suivi des utilisations
### Autres fonctionnalités
- Liste de favoris
- Recherche avancée
- Filtres multiples
- API REST
- Interface d'administration
- Responsive design
- Pages légales complètes
- FAQ dynamique
- Formulaire de contact fonctionnel

## Installation

### Prérequis
- Python 3.8+
- pip
- virtualenv (recommandé)

### Installation locale

1. Cloner le projet
```bash
git clone <repository-url>
cd ecommerce-site
```

2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Configuration
```bash
cp .env.example .env
# Modifier les variables d'environnement dans .env
```

5. Migrations de base de données
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

7. Collecter les fichiers statiques
```bash
python manage.py collectstatic
```

8. Lancer le serveur de développement
```bash
python manage.py runserver
```

Le site sera accessible à l'adresse `http://127.0.0.1:8000/`

8. Peupler les données de la Guinée
```bash
python manage.py populate_guinea_data
```

## Structure du projet

```
ecommerce/
├── accounts/           # Gestion des utilisateurs
├── products/          # Gestion des produits
├── orders/            # Gestion des commandes
├── deliveries/        # Gestion des livraisons
├── cart/              # Panier d'achat
├── favorites/         # Liste de favoris
├── returns/           # Système de retours
├── geolocation/       # Géolocalisation Guinée
├── notifications/     # Système de notifications
├── analytics/         # Statistiques et analyses
├── coupons/           # Codes promotionnels
├── reviews/           # Système d'avis
├── payments/          # Gestion des paiements
├── messaging/         # Chat temps réel
├── blog/              # Blog vendeurs
├── core/              # Vues générales
├── api/               # API REST
├── templates/         # Templates HTML
├── static/            # Fichiers statiques
├── media/             # Fichiers uploadés
└── management/        # Commandes de gestion
```

## Utilisation

### Types d'utilisateurs

1. **Acheteurs** : Navigation, achat, suivi commandes, géolocalisation, favoris
2. **Vendeurs** : Gestion produits, blog, analytics, validation profil
3. **Livreurs** : Gestion livraisons, demandes, validation documents
4. **Admins** : Gestion administrative du site
5. **Super Admins** : Accès complet à l'administration

### Fonctionnalités principales

- **Page d'accueil** : Design africain, produits mis en avant, catégories
- **Catalogue produits** : Recherche avancée, filtres multiples, pagination
- **Détail produit** : Carousel images, reviews, profil vendeur, géolocalisation
- **Panier** : Gestion quantités, calculs automatiques, modes paiement
- **Checkout** : Processus complet avec géolocalisation et confirmation
- **Profil utilisateur** : Gestion complète selon le type d'utilisateur
- **Dashboard vendeur** : Analytics, blog, gestion produits, statistiques
- **Livraisons** : Géolocalisation précise, demandes, suivi temps réel
- **Messagerie** : Chat temps réel entre utilisateurs
- **Retours** : Système complet avec photos et suivi

## 🌍 Spécificités Guinée

### Géolocalisation adaptée
- Structure administrative guinéenne complète
- 8 régions, préfectures et communes pré-configurées
- Vérification communautaire des adresses
- Points de repère locaux et culturels
- Instructions d'accès détaillées

### Réalités locales
- Adresses informelles avec descriptions personnalisées
- Système évolutif par crowdsourcing
- Tarification par zones géographiques
- Délais adaptés aux distances

## 🎨 Design Africain Moderne

### Palette de couleurs
- **Or africain** (#D4AF37) - Couleur principale
- **Terre cuite** (#8B4513) - Couleur secondaire  
- **Orange coucher de soleil** (#FF6B35) - Accent
- **Vert savane** (#228B22) - Succès
- **Beige sable** (#FFF8DC) - Arrière-plan

### Motifs et textures
- Motifs géométriques africains subtils
- Dégradés inspirés des couchers de soleil
- Animations fluides et naturelles
- Typographie moderne et lisible

## API REST

L'API REST complète est disponible à l'adresse `/api/` et inclut :
- `/api/products/` - Liste des produits
- `/api/categories/` - Liste des catégories
- `/api/orders/` - Commandes de l'utilisateur connecté
- `/api/deliveries/` - Gestion des livraisons
- `/api/notifications/` - Notifications utilisateur

Documentation complète disponible via Django REST Framework à `/api/`.

## Déploiement

### Variables d'environnement de production
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
```

### Serveur de production
```bash
pip install gunicorn
gunicorn ecommerce.wsgi:application
```

## 📱 Technologies utilisées

### Backend
- Django 4.2+ avec toutes les bonnes pratiques
- Django REST Framework pour l'API
- Django Channels pour le WebSocket
- CKEditor pour l'édition riche
- Pillow pour les images
- ReportLab pour les PDF

### Frontend
- Bootstrap 5 pour l'interface responsive
- Font Awesome pour les icônes
- jQuery pour les interactions
- Leaflet pour les cartes interactives
- CSS personnalisé avec design africain

### Base de données
- SQLite pour le développement
- PostgreSQL recommandé pour la production
- Modèles optimisés avec relations appropriées

## Contributions

Les contributions sont les bienvenues ! Ce projet est spécialement conçu pour l'écosystème africain. Veuillez :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📞 Contact

**Mohamed Said Diallo**
- Email : mohamedsaiddiallo88@gmail.com
- Téléphone France : +33 06 28 53 09 45
- Téléphone Guinée : +224 610 267 054
- Localisation : Conakry, Guinée

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Contacter par email : mohamedsaiddiallo88@gmail.com
- Support technique disponible

---

**🌍 Fait avec ❤️ pour l'Afrique**

*Ce projet vise à démocratiser le e-commerce en Afrique en proposant une solution complète, moderne et adaptée aux réalités locales.*