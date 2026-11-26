# Source Inspection & Technical Findings: Moroccan Procurement Portals

This document details the live inspection, HTTP behaviors, DOM structures, authentication requirements, and exact selectors of Moroccan public procurement platforms probed on November 20, 2026 for **CyberRFP Maroc**.

---

## 1. Portail Marocain des Marchés Publics (PMMP)
- **URL**: `https://www.marchespublics.gov.ma` (Redirects to `/pmmp/`)
- **Operator**: Trésorerie Générale du Royaume (TGR) / Ministère de l'Économie et des Finances
- **Underlying Engine**: PHP Prado Framework (`PRADO_PAGESTATE`, `ctl0$...` control IDs)
- **Authentication**: **None required** for search, viewing consultation details, or downloading public DCE. Anonymity is guaranteed by Moroccan procurement decree (Décret n° 2-22-431 relatif aux marchés publics).
- **Access Controls & Anti-Bot**: No CAPTCHA on consultation search and details. WAF rate-limiting requires respectful crawling cadence (1 request every ~2-3 seconds, exponential backoff). Cookies (`SERVERID`, `ocs_uid`, `dcookie`) must be initialized by visiting `/pmmp/`.

### Live Network Endpoints
1. **Session Init**: `GET https://www.marchespublics.gov.ma/pmmp/`
2. **Consultation Search List**: `GET https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours`
3. **Advanced Search Form**: `POST https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons`
   - Form name: `main_form`, id: `ctl0_ctl2`
   - Buyer input: `ctl0$CONTENU_PAGE$AdvancedSearch$orgName` (e.g. `OFPPT`, `SOREC`, `DGSSI`)
   - Reference input: `ctl0$CONTENU_PAGE$AdvancedSearch$reference`
   - Procedure type: `ctl0$CONTENU_PAGE$AdvancedSearch$procedureType` (e.g. `AOO`, `AOP`)
   - Category: `ctl0$CONTENU_PAGE$AdvancedSearch$categorie` (`Travaux`, `Fournitures`, `Services`)
   - Publication date range: `ctl0$CONTENU_PAGE$AdvancedSearch$dateMiseEnLigneStart` / `End`
   - Submit action: `ctl0$CONTENU_PAGE$AdvancedSearch$lancerRecherche`
4. **Consultation Detail**: `GET https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation={refConsultation}&orgAcronyme={orgAcronyme}`
5. **DCE Anonymous Download**: `POST https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={refConsultation}&orgAcronyme={orgAcronyme}`
   - Radio anonymous: `ctl0$CONTENU_PAGE$EntrepriseFormulaireDemande$RadioGroup` = `ctl0$CONTENU_PAGE$EntrepriseFormulaireDemande$choixAnonyme`
   - Terms acceptance: `ctl0$CONTENU_PAGE$EntrepriseFormulaireDemande$accepterConditions` = `on`
   - Submit: `ctl0$CONTENU_PAGE$validateButton` = `Valider`

### DOM Selectors (Verified on Live HTML)
- **Tender Card Container**: `div.generalBox` (`hidden-xs.col-xs-10.generalBox.watched`)
- **Procedure Type Badge**: `span.hotTender span` (e.g. `AOO`, `AOP`)
- **Reference Number**: `span[id*="_referencem"]` (e.g. `43/2026`)
- **Objet / Title**: `div.p-objet` (cleaned text after `Objet :`)
- **Estimated Budget (DH)**: `span.estim-mad` or `span[id*="_estimationLabel"]` (e.g. `40 931 655,07`)
- **Buyer Name**: `div.title.p-card div` (text following `Acheteur public :`)
- **Submission Deadline**:
  - Date: `.limita.p-card .fa-calendar-o + span` (e.g. `Mar 09 Fév 2027`)
  - Time: `.limita.p-card .fa-clock-o + span` (e.g. `10:30`)
- **Detail Link**: `a[href*="EntrepriseDetailsConsultation"]` (contains `refConsultation` and `orgAcronyme`)
- **Detail Page Fields**:
  - Provisional Guarantee: Extracted from table/row labeled `Caution provisoire :` (e.g. `800 000,00 MAD`)
  - Opening of Bids: Extracted from `Lieu d'ouverture des plis :`
  - Execution Place: Extracted from `Lieu d'exécution :`
  - Required Qualifications: Extracted from `Qualifications :`
  - Required Agréments: Extracted from `Agréments :`
  - Contact Details: Extracted from `Contact Administratif :`

---

## 2. Al Barid Bank (ABB)
Al Barid Bank operates two distinct procurement touchpoints:

### A. Supplier Portal (E-Procurement Platform)
- **URL**: `https://fournisseurs.albaridbank.ma`
- **Platform**: JAGGAER / BravoSolution ESOP (`/esop/tlh-host/...`)
- **Authentication**: **No login required for viewing current tenders!**
- **Public Opportunities Endpoint**:
  `https://fournisseurs.albaridbank.ma/esop/toolkit/opportunity/current/list.si?reset=true&resetstored=true&userAct=changeLangIndex&language=fr_FR`
- **DOM Structure**:
  - Table: `table.list-table`
  - Columns:
    1. Line Number (`Numéro de Ligne`)
    2. Procedure Type (`Type de procédure`, e.g. `UE - Procédure ouverte`, `Autre`)
    3. Buyer Organization (`Organisation Acheteur`, e.g. `Al Barid Bank`)
    4. Dossier Title (`Titre du dossier`, e.g. `BC_DP_2026_811_ ...`, `ACQUISITION DES ORDINATEURS...`)
    5. Category (`Catégorie de travaux`, e.g. `Services`, `Fournitures`, `Travaux`)
    6. Deadline (`Date limite d'affichage`, e.g. `23/11/2026 11:00`)
  - Row Links: Each row links to dossier view `/esop/toolkit/opportunity/current/{id}/detail.si`

### B. Institutional Site (Press Notices & PDF Avis)
- **URL**: `https://www.albaridbank.ma/fr`
- **Status**: Live Drupal CMS.
- **Section**: `/fr/espace-fournisseurs` and newsroom press releases.
- **Access**: Public. Notice PDFs follow naming pattern `Avis_*.pdf` or `AOO_*.pdf`.

---

## 3. OFPPT (Office de la Formation Professionnelle et de la Promotion du Travail)
- **Official Domain Probed**: `ofppt.ma` / `www.ofppt.ma`
- **DNS / Connectivity Status**:
  - Authority nameserver `ns1-03.azure-dns.com` currently reports no active A record for `www.ofppt.ma`.
  - Direct HTTP connection fails with DNS resolution error (`[Errno 11001] getaddrinfo failed`).
- **Procurement Regulatory Reality**:
  - In Morocco, OFPPT is legally bound by public procurement law to publish 100% of its calls for tender on the central PMMP (`marchespublics.gov.ma`) under buyer name *"Office de la Formation Professionnelle et de la Promotion du Travail"*.
- **Connector Strategy**:
  1. Primary ingestion: Query PMMP connector with buyer filter `OFPPT` or `Office de la Formation Professionnelle`.
  2. Backup direct connector: Monitored with automatic health check reporting DNS status in the Admin UI; when OFPPT's institutional portal restores DNS A records, direct scraping activates.

---

## 4. SOREC (Société Royale d'Encouragement du Cheval)
- **Official Domain Probed**: `https://www.sorec.ma`
- **Procurement Page**: `https://www.sorec.ma/appels-offres/` (HTTP 200, length ~132 KB)
- **DOM Structure**:
  - Content container: `main.site-main`
  - Tender Table / Card: `div.ao-card` or table with headers:
    `N° AO | Objet | Date limite | Statut`
  - Currently displays empty notice `"Aucun résultat trouvé"` because SOREC actively directs suppliers to PMMP.
- **Procurement Reality**:
  - SOREC tenders are centrally published on PMMP (`marchespublics.gov.ma`) under buyer name *"SOREC"* / *"Société Royale d'Encouragement du Cheval"*.
- **Connector Strategy**:
  - PMMP connector monitors SOREC tenders with priority badge.
  - Dedicated SOREC connector scrapes `https://www.sorec.ma/appels-offres/` detecting any direct RFP or PDF DCE links posted on their site.

---

## 5. Generic Configurable Buyer Connector
- For any additional public buyer (e.g. ANRT, DGSSI, Bank Al-Maghrib, ONEE, ONDA, CDG, Communes):
- **Configuration Fields**:
  - Name, Code, Base URL
  - Listing Type: HTML table / CSS selector card / RSS / JSON API / PDF list
  - Target Selectors: Container, Reference, Title, Deadline, Budget, Document Link
  - Pagination pattern
- Configurable from the Admin UI without modifying Python source code.
