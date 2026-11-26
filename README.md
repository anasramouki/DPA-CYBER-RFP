# DPA-CYBER-RFP v4.0 🇲🇦🛡️
> **Plateforme Professionnelle de Veille Stratégique & Soumission des Marchés Publics en Cybersécurité**  
> *Développé pour l'équipe DPA (DataProtech company) — Casablanca, Maroc*

---

## 🌟 Vue d'Ensemble & Nouveautés v4.0

**CyberRFP Maroc v4.0** a été entièrement audité, sécurisé et repensé pour offrir une expérience utilisateur haut de gamme, fluide et ultra-réactive sur tous les supports (Desktop, iPhone, Tablette) :

1. **Top Bar Minimaliste & Épurée** :
   - Design moderne avec icônes Lucide, logo DPA vectoriel et badge de connectivité PMMP direct.
   - Sélecteur de langue trilingue instantané (**Français**, **Anglais**, **Arabe avec bascule RTL native**).
   - Bascule de thème instantanée (**Mode Sombre / Mode Clair**) avec contraste accessible WCAG 2.2 AA.
   - Menu profil **John Doe** (`admin@dpg-cyber.com` / `john.doe@dpg-cyber.com`).

2. **Filtres Compacts en Listes Déroulantes (Zéro Encombrement)** :
   - Finie la barre de filtres encombrante : recherche intelligente par mot-clé avec autocomplétion sécurisée (non polluée par les gestionnaires de mots de passe de navigateur).
   - Menus déroulants ergonomiques : *Acheteurs Publics*, *Échéance & Délais*, *Sources Officielles*, *Tri chronologique et budgétaire*.
   - Puces rapides en 1 clic : *Tous les Marchés*, *Cybersécurité & SSI*, *Acheteurs Prioritaires DPA*, *Mes AO Suivis (Favoris)*.

3. **Tableau & Cartes Ajustés — Zéro Défilement Horizontal (0px Scroll)** :
   - Largeur 100% ajustée sans aucun débordement horizontal (`scrollWidth === clientWidth`) sur desktop, tablette et smartphones (iPhone 14 390px, iPhone SE 320px).
   - Mode tableau riche sur grand écran et bascule automatique en cartes tactiles sur mobile.

4. **Alertes Ciblées & Notifications Intelligentes** :
   - Option exclusive : **⭐ « Uniquement mes AO suivis »** activable directement depuis le panneau des alertes (cloche). Vous ne recevez plus de notifications inutiles pour les marchés de travaux civils ou fournitures de bureau.
   - Notifications visuelles pop-up en direct avec lien direct vers le Dossier et le DCE officiel.
   - Sonnerie d'alerte audio subtile (désactivable en 1 clic).
   - Alertes par Email SMTP intégrées avec formulaire de test en direct dans les paramètres administrateur.

5. **Sources 100% Authentiques et Officielles (Zéro Donnée Factice)** :
   - **Portail Marocain des Marchés Publics (PMMP)** : Flux officiel en temps réel avec caution, estimation budgétaire TTC et téléchargement direct anonyme du DCE.
   - **Al Barid Bank & Jaggaer ESOP** : Ingestion directe des avis officiels et consultations de la banque.
   - **Presse & Journaux d'Annonces Légales** : Scraping en direct de *AO Maroc* et *MarocBiz* pour les consultations bancaires, ministérielles et semi-publiques.

6. **Dossier de Soumission DPA (Hudu) Fluide & Intégré** :
   - Popup et modale d'analyse stratégique sans clipping ni débordement.
   - Check-lists des pièces administratives, techniques et financières conformes au décret des marchés publics marocains.

7. **Accès iPhone & Réseau Local Simplifié** :
   - Script d'ouverture pare-feu en 1 clic (`Activer_Acces_iPhone_Firewall.bat`) avec détection automatique de votre adresse IP locale.
   - Modale avec QR Code instantané : flashez le QR code avec l'appareil photo de votre iPhone pour ouvrir CyberRFP Maroc directement.

---

## 🚀 Démarrage Rapide

### Option A : Exécutable Autonome Windows (Recommandé - Sans installation Python)

1. Double-cliquez sur `Lancer_CyberRFP_Maroc.bat` (ou lancez directement `dist\CyberRFP-Maroc.exe`).
2. Votre navigateur par défaut s'ouvre automatiquement sur : `http://127.0.0.1:8000`.
3. Connectez-vous avec les identifiants par défaut :
   - **Email** : `admin@dpg-cyber.com`
   - **Mot de passe** : `cyberrfp2026`

### Option B : Lancement via Python

```powershell
# 1. Naviguer dans le dossier
cd "C:\Users\Anas Ramouki\Downloads\Anas's Lab\Project One"

# 2. Installer les dépendances
python -m pip install -r requirements.txt

# 3. Lancer l'application
python run.py
```

L'application démarre sur `http://127.0.0.1:8000`.

---

## 📱 Utilisation sur iPhone / Smartphone (Wi-Fi)

1. Connectez votre iPhone au **même réseau Wi-Fi** que votre PC.
2. Faites un clic droit sur `Activer_Acces_iPhone_Firewall.bat` et choisissez **« Exécuter en tant qu'administrateur »** (cela autorise le port 8000 dans le pare-feu Windows).
3. Dans l'application sur votre PC, cliquez sur l'icône de smartphone dans la barre du haut (ou ouvrez le QR Code).
4. Scannez le QR Code affiché avec votre iPhone, ou entrez l'adresse indiquée (ex: `http://192.168.1.XX:8000`).
5. Connectez-vous et profitez de l'interface responsive optimisée mobile.

---

## ⚙️ Configuration & Paramètres (Onglet Admin)

Dans la barre de navigation, cliquez sur l'icône **« Paramètres & Alertes »** :

- **Configuration SMTP / Email** : Configurez votre serveur SMTP (Gmail, Outlook/Office365 ou serveur d'entreprise DPA) et cliquez sur **« Tester la Connexion SMTP »** pour vérifier immédiatement la réception.
- **Clé API Gemini (Google AI Studio)** : Saisissez votre clé API Gemini pour activer la qualification automatique des appels d'offres par IA et la génération de synthèses décisionnelles.
- **Connecteurs Génériques** : Ajoutez ou supprimez à chaud des sources d'achats personnalisées en renseignant simplement leur URL et leurs sélecteurs CSS.

---

## 🔒 Sécurité & Conformité

- Authentification sécurisée par cookies de session HttpOnly avec attributs `SameSite=Lax`.
- Protection CSRF et en-têtes HTTP de sécurité renforcés (`X-Frame-Options`, `Content-Security-Policy`, `X-Content-Type-Options`).
- Aucun stockage de mot de passe en clair (hachage PBKDF2/SHA-256 avec salage).
- Données sensibles masquées et protection contre les attaques d'énumération utilisateur.

---

## 🧪 Tests & Assurance Qualité

L'application est couverte par une suite complète de 51 tests unitaires et d'intégration automatisés :

```powershell
python -m pytest tests/
```

*Résultat : 51/51 tests passés avec succès.*
