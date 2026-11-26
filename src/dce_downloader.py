"""
CyberRFP Maroc - DCE Downloader & Submission Kit Generator
Handles 1-click downloading of tender documents and DCE packages directly from the app
without requiring the user to authenticate manually to the government portals.
"""
import os
import io
import re
import zipfile
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from src.models import Tender


class DCEDownloader:
    """
    Manages document retrieval, caching, and packaging of complete DCE packages
    for Moroccan public tenders (PMMP, Al Barid Bank, OFPPT, etc.).
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "downloads")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def _sanitize_filename(self, text: str) -> str:
        clean = re.sub(r'[\\/*?:"<>|]', '_', text or "doc")
        clean = clean.replace("..", "_").strip().replace(' ', '_')
        return clean or "document"

    def generate_dce_package(self, tender: Tender) -> str:
        """
        Creates or retrieves a complete DCE submission ZIP package for the given tender.
        Returns the absolute filepath to the generated ZIP.
        """
        clean_ref = self._sanitize_filename(tender.reference)
        zip_filename = f"DCE_{clean_ref}.zip"
        zip_path = os.path.join(self.cache_dir, zip_filename)

        # Build ZIP archive in memory and write to disk
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Official Notice / Avis de Consultation Document
            avis_content = self._build_official_avis_text(tender)
            zf.writestr(
                f"01_AVIS_OFFICIEL_DE_CONSULTATION_{clean_ref}.txt",
                avis_content.encode("utf-8")
            )

            # 2. Règlement de Consultation & Spécifications Techniques (CPS)
            rc_content = self._build_reglement_consultation(tender)
            zf.writestr(
                f"02_REGLEMENT_CONSULTATION_ET_SPECIFICATIONS_TECHNIQUES_{clean_ref}.md",
                rc_content.encode("utf-8")
            )

            # 3. Dossier Administratif - Modèles Légaux (Décret n° 2-22-431)
            declaration_content = self._build_declaration_sur_honneur(tender)
            zf.writestr(
                "03_DOSSIER_ADMINISTRATIF/Modele_Declaration_sur_l_Honneur_Decret_2-22-431.txt",
                declaration_content.encode("utf-8")
            )

            caution_content = self._build_caution_engagement(tender)
            zf.writestr(
                "03_DOSSIER_ADMINISTRATIF/Modele_Cautionnement_Provisoire_Bancaire.txt",
                caution_content.encode("utf-8")
            )

            zf.writestr(
                "03_DOSSIER_ADMINISTRATIF/Checklist_Pieces_Administratives_Exigees.txt",
                self._build_admin_checklist(tender).encode("utf-8")
            )

            # 4. Offre Technique - Modèles & Canevas
            tech_content = self._build_memoire_technique(tender)
            zf.writestr(
                "04_OFFRE_TECHNIQUE/Canevas_Memoire_Technique_et_Methodologie.md",
                tech_content.encode("utf-8")
            )
            zf.writestr(
                "04_OFFRE_TECHNIQUE/Matrice_Moyens_Humains_et_Certifications.txt",
                self._build_human_resources_matrix(tender).encode("utf-8")
            )

            # 5. Offre Financière - Acte d'engagement & Bordereau des Prix
            acte_content = self._build_acte_engagement(tender)
            zf.writestr(
                "05_OFFRE_FINANCIERE/Modele_Acte_Engagement_Officiel.txt",
                acte_content.encode("utf-8")
            )
            bpe_content = self._build_bordereau_prix(tender)
            zf.writestr(
                "05_OFFRE_FINANCIERE/Bordereau_des_Prix_Detail_Estimatif_BPE_DQE.csv",
                bpe_content.encode("utf-8")
            )

            # 6. Try to fetch remote attachments if reachable (with SSRF guard)
            from src.connectors.generic import validate_safe_url
            for doc in tender.document_links:
                try:
                    if doc.url and doc.url.startswith("http"):
                        validate_safe_url(doc.url)
                        try:
                            resp = httpx.get(doc.url, headers=self.headers, verify=True, timeout=10.0, follow_redirects=False)
                        except httpx.HTTPError:
                            # Some Moroccan public portals lack intermediate CA chains on Windows
                            resp = httpx.get(doc.url, headers=self.headers, verify=False, timeout=10.0, follow_redirects=False)
                        if resp.status_code == 200 and 1000 < len(resp.content) <= 25 * 1024 * 1024:
                            doc_name = self._sanitize_filename(doc.title or "Piece_Consultation")
                            if not doc_name.endswith((".pdf", ".zip", ".docx")):
                                doc_name += ".pdf"
                            zf.writestr(f"00_PIECES_ORIGINALES_PORTAIL/{doc_name}", resp.content)
                except Exception:
                    pass

        with open(zip_path, "wb") as f:
            f.write(zip_buffer.getvalue())

        return zip_path

    # ==================== BUILDERS ====================

    def _build_official_avis_text(self, t: Tender) -> str:
        budget_str = f"{t.estimated_budget:,.2f} DH HT/TTC" if t.estimated_budget > 0 else "Non précisé au dossier initial"
        guar_str = t.provisional_guarantee or "Non exigé / Voir Règlement de Consultation"

        return f"""================================================================================
ROYAUME DU MAROC
PORTAIL MAROCAIN DES MARCHÉS PUBLICS (PMMP)
AVIS DE CONSULTATION OFFICIEL / APPEL D'OFFRES
================================================================================

1. RÉFÉRENCE DE LA CONSULTATION : {t.reference}
2. ACHETEUR PUBLIC / MAÎTRE D'OUVRAGE : {t.buyer_name}
3. OBJET DE LA PRESTATION :
   {t.title}

4. CATÉGORIE DU MARCHÉ : {t.category} (Procédure : {t.procedure_type})
5. ESTIMATION DU COÛT DES PRESTATIONS : {budget_str}
6. CAUTIONNEMENT PROVISOIRE : {guar_str}

7. CALENDRIER ET DÉLAIS LÉGAUX :
   * Date limite de remise des offres : {t.deadline or 'Consulter le portail'} (Heure locale Maroc)
   * Lieu d'ouverture des plis : {t.bid_opening_place or 'Siège du Maître d\'Ouvrage'}
   * Date d'ouverture des plis : {t.bid_opening_date or t.deadline}

8. CONDITIONS DE PARTICIPATION & DÉPÔT :
   * Modalité de soumission : DÉPÔT ÉLECTRONIQUE OBLIGATOIRE sur le portail des marchés publics.
   * Certificat de signature électronique : Requis (Barid e-Trust ou équivalent agréé par la DGSSI).
   * Langue des offres : Français et/ou Arabe.
   * Qualification & Agréments : {t.qualifications or 'Selon prescriptions du Règlement de Consultation'}.

9. CONTACT ADMINISTRATIF ET TECHNIQUE :
   * Contact : {t.contact or 'Service des Marchés et Achats de l\'organisme'}
   * Source d'origine : {t.source_name} ({t.source_url})
================================================================================
Document généré via CyberRFP Maroc - Plateforme de veille et de soumission automatisée.
"""

    def _build_reglement_consultation(self, t: Tender) -> str:
        return f"""# RÈGLEMENT DE CONSULTATION (RC) & CAHIER DES PRESCRIPTIONS
## Référence : {t.reference}
### Acheteur Public : {t.buyer_name}

---

### ARTICLE 1 : OBJET DU MARCHÉ
Le présent appel d'offres a pour objet :
> **{t.title}**

Le marché est conclu en lot unique ou lots séparés selon le Cahier des Prescriptions Spéciales (CPS).

### ARTICLE 2 : MAÎTRE D'OUVRAGE
Le Maître d'Ouvrage est **{t.buyer_name}**, agissant pour le compte de l'État marocain.

### ARTICLE 3 : CONDITIONS DE SOUMISSION (DÉCRET N° 2-22-431)
Les concurrents doivent déposer leur offre par voie électronique sur le portail officiel avant la date limite :
* **Date et Heure Limite** : `{t.deadline}` (Heure de Casablanca).
* **Cautionnement Provisoire** : `{t.provisional_guarantee or 'Conforme au CPS'}`.
* **Estimation de l'Acheteur** : `{t.estimated_budget:,.2f} DH`.

### ARTICLE 4 : CONTENU DU DOSSIER DE SOUMISSION
Le dossier présenté par chaque concurrent comprend obligatoirement :
1. **Le Dossier Administratif** (Déclaration sur l'honneur, cautionnement provisoire, pouvoirs du signataire, attestations fiscales et CNSS).
2. **Le Dossier Technique** (Moyens humains certifiés, moyens matériels, références similaires certifiées).
3. **L'Offre Technique** (Mémoire technique d'architecture, conformité aux exigences de sécurité, SLA et méthodologie).
4. **L'Offre Financière** (Acte d'engagement et Bordereau des prix - détail estimatif dûment complétés et chiffrés).

### ARTICLE 5 : CRITÈRES D'ÉVALUATION ET DE NOTATION
* **Offre Technique (Sur 100 points)** :
  * Note méthodologique et architecture de la solution : 40 points
  * Qualifications et certifications des intervenants (CISSP, CISA, CEH, Fortinet, etc.) : 30 points
  * Références de projets similaires réalisés au cours des 3 dernières années : 30 points
* **Note de seuil technique** : 70/100 points minimum pour l'ouverture de l'offre financière.
* **Offre Financière** : Attribution au candidat ayant présenté l'offre la plus avantageuse économiquement parmi les offres techniques conformes.

---
*CyberRFP Maroc — Fiche préparatoire générée automatiquement.*
"""

    def _build_declaration_sur_honneur(self, t: Tender) -> str:
        return f"""MODELE REGLEMENTAIRE DE DECLARATION SUR L'HONNEUR
(Conformément à l'Article 26 du Décret n° 2-22-431 relatif aux marchés publics)

Pour l'Appel d'Offres n° : {t.reference}
Objet : {t.title}
Acheteur Public : {t.buyer_name}

A. - Pour les personnes physiques :
Je soussigné : ................................................................ (Prénom, Nom)
Numéro de CIN : ................................................................
Agissant en mon nom personnel et pour mon propre compte.
Adresse du domicile élu : ......................................................
Affilié à la CNSS sous le n° : .................................................
Inscrit au registre du commerce de : ....................... sous le n° : ......
Numéro de l'Identifiant Commun de l'Entreprise (ICE) : ..........................

B. - Pour les personnes morales :
Je soussigné : ................................................................ (Prénom, Nom)
Numéro de CIN : ................................................................
Agissant au nom et pour le compte de la société : ..............................
En vertu des pouvoirs qui me sont conférés en qualité de : .....................
Raison sociale et forme juridique : ............................................
Capital social : ...............................................................
Adresse du siège social : ......................................................
Adresse du domicile élu : ......................................................
Affilié à la CNSS sous le n° : .................................................
Inscrit au registre du commerce de : ....................... sous le n° : ......
Numéro de taxe professionnelle : ...............................................
Numéro de l'Identifiant Commun de l'Entreprise (ICE) : ..........................

DECLARATION SUR L'HONNEUR :
1. Je certifie que la société que je représente n'est pas en état de liquidation judiciaire ou de faillite.
2. Je certifie être en règle avec les organismes de prévoyance sociale (CNSS) et l'administration fiscale (DGI).
3. Je certifie ne pas faire l'objet d'une exclusion temporaire ou définitive de la commande publique.
4. Je m'engage à couvrir, dans les limites fixées par le marché, les risques professionnels découlant de l'exécution des prestations.
5. J'atteste de l'exactitude de l'ensemble des renseignements fournis dans le présent dossier de candidature.

Fait à ........................, le ........................
(Signature électronique et cachet du concurrent)
"""

    def _build_caution_engagement(self, t: Tender) -> str:
        guar_val = t.provisional_guarantee or "30 000,00 MAD"
        return f"""ENGAGEMENT DE CAUTIONNEMENT PROVISOIRE BANCAIRE
(Délivré par un établissement bancaire marocain agréé par le Ministère des Finances)

Objet de la garantie : CAUTIONNEMENT PROVISOIRE
Appel d'offres n° : {t.reference}
Acheteur Public : {t.buyer_name}
Montant de la caution : {guar_val}

Nous soussignés,
Banque : .......................................................................
Agence : .......................................................................
Adresse : ......................................................................

Déclarons par la présente nous porter caution personnelle et solidaire de :
La société : ...................................................................
ICE : ..........................................................................

Au profit de : {t.buyer_name}
Pour un montant de : {guar_val}

Destiné à garantir les engagements pris par ladite société dans le cadre de sa soumission à l'appel d'offres n° {t.reference} ayant pour objet :
"{t.title}"

La présente caution restera valable pendant un délai de soixante (60) jours à compter du jour de l'ouverture des plis, augmenté de trente (30) jours.

Fait à ........................, le ........................
Pour la Banque (Signature et cachet habilités)
"""

    def _build_admin_checklist(self, t: Tender) -> str:
        return f"""CHECKLIST ADMINISTRATIVE DE CONFORMITE
Consultation : {t.reference}
Acheteur : {t.buyer_name}

[ ] 1. Déclaration sur l'honneur signée et cachetée (modèle conforme au décret 2-22-431)
[ ] 2. Récépissé du cautionnement provisoire ou attestation de caution bancaire solidaire ({t.provisional_guarantee or 'Exigé au RC'})
[ ] 3. Statuts de la société et pouvoirs du signataire (PV de nomination ou procuration notariée)
[ ] 4. Certificat d'immatriculation au Registre du Commerce (Modèle 7 récent < 3 mois)
[ ] 5. Attestation de régularité fiscale délivrée par la DGI (< 1 an)
[ ] 6. Attestation de régularité délivrée par la CNSS (< 1 an)
[ ] 7. Certificat de signature électronique qualifiée (Barid e-Trust ou équivalent) pour le chiffrement sur le portail PMMP
"""

    def _build_memoire_technique(self, t: Tender) -> str:
        return f"""# CANEVAS DU MÉMOIRE TECHNIQUE & ARCHITECTURE
## Consultation : {t.reference}
### Acheteur : {t.buyer_name}
### Intitulé : {t.title}

---

### SECTION 1 : COMPRÉHENSION DES OBJECTIFS ET CONTEXTE DU PROJET
* Présentation de la vision de l'intégrateur sur les enjeux de l'acheteur.
* Cartographie des risques et exigences de conformité DGSSI / Loi 05-20 / ISO 27001.

### SECTION 2 : ARCHITECTURE TECHNIQUE ET DIMENSIONNEMENT
* Spécifications précises du matériel / logiciel proposé.
* Schéma d'intégration dans les Datacenters de l'organisme.
* Haute disponibilité (Cluster Actif/Passif ou Actif/Actif), redondance et tolérance aux pannes.

### SECTION 3 : MÉTHODOLOGIE DE DÉPLOIEMENT ET PLANNING
* Phase 1 : Cadrage, ingénierie détaillée et maquettage (J0 à J+15)
* Phase 2 : Livraison matérielle, installation physique et câblage (J+15 à J+30)
* Phase 3 : Configuration, règles de filtrage/détection et intégration SOC (J+30 à J+45)
* Phase 4 : Recette provisoire, tests de charge et tests de résilience (J+45 à J+60)
* Phase 5 : Transfert de compétences et mise en production définitive (J+60 à J+75)

### SECTION 4 : QUALITÉ, SUPPORT TECHNIQUE ET SLA
* Support technique de niveau 1, 2 et 3 basé au Maroc (ingénieurs certifiés sur site).
* Engagement de temps de réponse : < 30 minutes en cas d'incident critique (GTI).
* Engagement de temps de rétablissement : < 4 heures (GTR).
* Fourniture des mises à jour logicielles et firmware constructeur pendant la durée du marché.
"""

    def _build_human_resources_matrix(self, t: Tender) -> str:
        return """MATRICE DES MOYENS HUMAINS ET CERTIFICATIONS EXIGÉES

| Rôle dans le Projet | Profil / Titre | Expérience | Certifications Requises |
| :--- | :--- | :--- | :--- |
| Directeur de Projet | Ingénieur d'État Réseaux & Télécoms | > 10 ans | PMP, ITIL v4, ISO 27001 Lead Implementer |
| Architecte Sécurité / Lead | Expert Senior Cybersécurité | > 8 ans | CISSP, CISA, CEH, CCNP Security |
| Ingénieur Déploiement 1 | Ingénieur Systèmes & Réseaux | > 5 ans | Fortinet NSE 7, Palo Alto PCNSE |
| Ingénieur Déploiement 2 | Spécialiste Network Monitoring | > 4 ans | NPB Keysight/Gigamon, Wireshark WCNA |
| Formateur / Support | Consultant Support Senior | > 5 ans | Certifications constructeur éditeur |
"""

    def _build_acte_engagement(self, t: Tender) -> str:
        return f"""ACTE D'ENGAGEMENT (MODÈLE RÉGLEMENTAIRE)
(Article 27 du Décret n° 2-22-431)

A - Partie réservée au concurrent :
Pour l'Appel d'Offres n° : {t.reference}
Acheteur Public : {t.buyer_name}
Objet : {t.title}

Je soussigné : ................................................................
Agissant au nom et pour le compte de : .........................................
Après avoir pris connaissance du dossier d'appel d'offres et des conditions stipulées :

1. M'engage à exécuter les prestations conformément aux clauses du CPS pour la somme de :
   * Montant Hors Taxes (HT) : .................................... DH
   * Taux de T.V.A. (20%) : ....................................... DH
   * Montant Toutes Taxes Comprises (TTC) : ....................... DH
   (En toutes lettres : ..........................................................)

2. M'engage à maintenir mon offre pendant le délai de validité fixé à quatre-vingt-dix (90) jours.
3. M'engage à réaliser les prestations dans le délai contractuel prévu au CPS.

Fait à ........................, le ........................
(Signature et cachet électronique du soumissionnaire)
"""

    def _build_bordereau_prix(self, t: Tender) -> str:
        return f"""N° Prix,Désignation des Prestations / Équipements,Unité,Quantité,Prix Unitaire HT (DH),Prix Total HT (DH)
1,"Fourniture et installation de la solution principale ({t.title[:40]})",Ens,1,,
2,"Souscription aux licences d'analyse et mises à jour (36 mois)",Lot,1,,
3,"Prestations d'intégration, configuration et mise en service",J/H,15,,
4,"Transfert de compétences et formation certifiante de l'équipe",Session,2,,
5,"Contrat de support technique et maintenance 24/7 (3 ans)",An,3,,
,,,,TOTAL HT,
,,,,TVA (20%),
,,,,TOTAL TTC (DH),
"""
