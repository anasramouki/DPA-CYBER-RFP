#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
          CyberRFP Maroc - Connecteur & Analyseur Expert Google AI Studio
                    Modèle IA : Google Gemini 2.5 Flash
             Entreprise Utilisatrice : DPA (DataProtech Group)
              Portail Source : Portail Marocain des Marchés Publics
================================================================================
Ce script complet et autonome permet d'analyser n'importe quel Appel d'Offres (AO),
Cahier des Prescriptions Spéciales (CPS) ou Règlement de Consultation (RC) marocain
en utilisant le SDK officiel `google-genai` de Google DeepMind.

Il applique automatiquement :
- Le Décret n° 2-22-431 du 8 mars 2023 relatif aux marchés publics marocains.
- La Loi 05-20 relative à la cybersécurité et son décret d'application n° 2-21-406.
- La Directive Nationale de la Sécurité des Systèmes d'Information (DNSSI / DGSSI).
- Les normes ISO/IEC 27001, 27002 et les critères de sélection pour DPA.
================================================================================
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

# Reconfiguration de la sortie console en UTF-8 pour Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Importation du SDK officiel Google GenAI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[-] AVERTISSEMENT : Le module 'google-genai' n'est pas encore installé.")
    print("    Pour l'installer : pip install google-genai")


# ==============================================================================
# 1. SYSTEM PROMPT INSTITUTIONNEL SPÉCIALISÉ MARCHÉS PUBLICS MAROCAINS
# ==============================================================================
SYSTEM_INSTRUCTIONS = """Vous êtes l'Architecte Cybersécurité Principal et Expert en Marchés Publics Marocains de l'entreprise "DPA" (DataProtech Group - ICE : 003102490000030).
Votre rôle est d'analyser les consultations et appels d'offres du Portail Marocain des Marchés Publics (marchespublics.gov.ma).

CADRE JURIDIQUE ET RÉGLEMENTAIRE APPLICABLE AU ROYAUME DU MAROC :
1. Décret n° 2-22-431 du 8 mars 2023 (conditions de participation, cautionnement provisoire, offre technique/financière).
2. Loi n° 05-20 relative à la cybersécurité (Infrastructures d'Importance Vitale, prestataires agréés, obligations d'audit).
3. Directive Nationale de la Sécurité des Systèmes d'Information (DNSSI) édictée par la DGSSI / Administration de la Défense Nationale.
4. Référentiels techniques : ISO/IEC 27001, 27002, 27005, NIST, CIS Controls, OWASP.

CRITÈRES D'ANALYSE COMMERCIALE ET TECHNIQUE POUR DPA :
- Classifier le besoin : Cybersécurité (Audit, SOC/SIEM, Pare-feu, DLP, NDR, IAM, EDR, PKI, Homologation) ou IT / Infrastructure / Non pertinent.
- Évaluer l'opportunité pour DPA sur une échelle de 0 à 100%.
- Détecter les critères techniques éliminatoires (certifications d'experts exigées : CISSP, CISA, CEH, Lead Auditor ISO 27001, partenariats éditeurs).
- Élaborer une stratégie gagnante ("Win Strategy") pour remporter le marché face aux concurrents.
- Analyser les risques juridiques (pénalités de retard selon le CCAG-EMO / CCAG-T, cautionnement provisoire bancaire, délais d'approvisionnement).

FORMAT DE SORTIE :
Vous devez OBLIGATOIREMENT répondre en JSON strict conforme au schéma structuré fourni."""


# ==============================================================================
# 2. SCHÉMA DE SORTIE JSON STRICT (GOOGLE AI STUDIO COMPATIBLE)
# ==============================================================================
ANALYSIS_JSON_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_cybersecurity": {
            "type": "BOOLEAN",
            "description": "True si le marché comporte des prestations ou équipements de cybersécurité"
        },
        "relevance_score": {
            "type": "INTEGER",
            "description": "Score d'adéquation commerciale pour DPA de 0 à 100%"
        },
        "primary_category": {
            "type": "STRING",
            "enum": ["CYBERSECURITY", "DIGITALISATION_SYSTEMS", "IT_INFRASTRUCTURE", "NOT_RELEVANT"]
        },
        "sub_domain": {
            "type": "STRING",
            "description": "Sous-domaine précis (ex: DLP, SOC & SIEM, NDR, Audit & Pentest, Pare-feu/WAF, IAM/PAM)"
        },
        "executive_summary_fr": {
            "type": "STRING",
            "description": "Synthèse exécutive claire et concise du besoin en français (3-4 lignes max)"
        },
        "moroccan_regulatory_context": {
            "type": "STRING",
            "description": "Alignement avec la Loi 05-20, les exigences de la DGSSI et du Décret 2-22-431"
        },
        "dpa_commercial_strategy": {
            "type": "OBJECT",
            "properties": {
                "decision_recommendation": {
                    "type": "STRING",
                    "enum": ["GO", "NO_GO", "WATCHING"],
                    "description": "Recommandation de décision pour DPA"
                },
                "win_strategy": {
                    "type": "STRING",
                    "description": "Facteurs de différenciation pour obtenir la meilleure note technico-financière"
                },
                "required_expert_certifications": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Profils et certifications requises pour l'équipe de réponse (ex: CISSP, CISA, ISO 27001, etc.)"
                },
                "key_technologies": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Solutions, constructeurs et technologies ciblées"
                },
                "risk_factors": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Points de vigilance (délais de livraison, cautionnement, pénalités)"
                }
            },
            "required": [
                "decision_recommendation",
                "win_strategy",
                "required_expert_certifications",
                "key_technologies",
                "risk_factors"
            ]
        },
        "submission_checklist_decret_2_22_431": {
            "type": "OBJECT",
            "properties": {
                "caution_provisoire_dh": {
                    "type": "STRING",
                    "description": "Montant du cautionnement provisoire bancaire"
                },
                "declaration_sur_honneur_conforme": {
                    "type": "BOOLEAN",
                    "description": "Nécessité de la déclaration sur l'honneur selon l'art. 27 du décret 2-22-431"
                },
                "technical_threshold_points": {
                    "type": "STRING",
                    "description": "Seuil éliminatoire de la note technique (ex: 70/100 points)"
                },
                "closing_place": {
                    "type": "STRING",
                    "description": "Lieu de dépôt et d'ouverture des plis"
                }
            },
            "required": ["caution_provisoire_dh", "declaration_sur_honneur_conforme"]
        }
    },
    "required": [
        "is_cybersecurity",
        "relevance_score",
        "primary_category",
        "sub_domain",
        "executive_summary_fr",
        "moroccan_regulatory_context",
        "dpa_commercial_strategy",
        "submission_checklist_decret_2_22_431"
    ]
}


# ==============================================================================
# 3. CLASSE D'ANALYSE COMPLÈTE GOOGLE AI STUDIO
# ==============================================================================
class GoogleAIStudioAnalyzer:
    """Client haute performance pour Google AI Studio (Gemini 2.5 Flash)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY", "")
        ).strip()

        self.client = None
        if GENAI_AVAILABLE and self.api_key and self.api_key != "VOTRE_CLE_ICI":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[-] Erreur d'initialisation du client Google AI Studio: {e}")

    def analyze_rfp_dict(self, rfp: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse un appel d'offres structuré issu du Portail des Marchés Publics."""
        if not self.client:
            return {
                "error": "Clé API Google AI Studio manquante.",
                "message": "Veuillez définir votre clé via 'export GEMINI_API_KEY=AIzaSy...' ou passer l'argument --key."
            }

        prompt_content = f"""
VEUILLEZ ANALYSER CET APPEL D'OFFRES OFFICIEL ISSU DU PORTAIL MAROCAIN DES MARCHÉS PUBLICS :

- Référence de la consultation : {rfp.get('reference', 'Non spécifiée')}
- Acheteur Public : {rfp.get('buyer', rfp.get('buyer_name', 'Organisme Public'))}
- Objet de la consultation : {rfp.get('title', '')}
- Mode de passation : {rfp.get('procedure_type', "Appel d'offres ouvert")}
- Date de mise en ligne : {rfp.get('publication_date', 'Non spécifiée')}
- Date limite de remise des plis : {rfp.get('deadline', 'Non spécifiée')}
- Budget estimé TTC : {rfp.get('budget', rfp.get('estimated_budget', 'Non précisé'))} DH
- Cautionnement provisoire : {rfp.get('caution', rfp.get('provisional_guarantee', 'Non spécifiée'))}
- Lieu d'ouverture des plis : {rfp.get('bid_opening_place', 'Siège du Maître d\'Ouvrage')}
- Lien vers l'avis officiel : {rfp.get('portal_url', rfp.get('source_url', 'https://www.marchespublics.gov.ma'))}

EXTRAIT DU DOSSIER DE CONSULTATION / SPÉCIFICATIONS TECHNIQUES (CPS) :
{rfp.get('cps_excerpt', 'Fourniture, déploiement, paramétrage et maintenance selon les normes de l\'acheteur public.')}
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=ANALYSIS_JSON_SCHEMA
                )
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"Erreur lors de l'appel Google AI Studio: {str(e)}"}

    def analyze_raw_text(self, raw_text: str) -> Dict[str, Any]:
        """Analyse directement un texte brut copié depuis le portail ou un document PDF/CPS."""
        if not self.client:
            return {"error": "Clé API Google AI Studio manquante."}

        prompt_content = f"""
VEUILLEZ ANALYSER CE TEXTE D'APPEL D'OFFRES MAROCAIN (COPIÉ DE MARCHESPUBLICS.GOV.MA OU D'UN CPS) :

--------------------------------------------------------------------------------
{raw_text}
--------------------------------------------------------------------------------
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=ANALYSIS_JSON_SCHEMA
                )
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"Erreur lors de l'appel Google AI Studio: {str(e)}"}

    def analyze_pdf_document(self, pdf_path: str) -> Dict[str, Any]:
        """Envoie directement un fichier PDF (CPS / Règlement de consultation) à Gemini 2.5 Flash."""
        if not self.client:
            return {"error": "Clé API Google AI Studio manquante."}

        if not os.path.exists(pdf_path):
            return {"error": f"Fichier introuvable : {pdf_path}"}

        try:
            print(f"[*] Téléversement du document PDF vers Google AI Studio : {os.path.basename(pdf_path)}...")
            uploaded_file = self.client.files.upload(file=pdf_path)

            prompt_content = [
                uploaded_file,
                "Analysez ce Cahier des Prescriptions Spéciales (CPS) marocain pour l'entreprise DPA. Identifiez les exigences de cybersécurité, les critères éliminatoires, le cautionnement provisoire et la stratégie pour remporter le marché."
            ]

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=ANALYSIS_JSON_SCHEMA
                )
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": f"Erreur d'analyse multimodale PDF: {str(e)}"}


# ==============================================================================
# 4. EXEMPLES DE CONSULTATIONS OFFICIELLES DU PORTAIL MAROCAIN
# ==============================================================================
SAMPLE_RFPS = {
    "CNSS_DLP": {
        "reference": "AOOI150/2026/CNSS",
        "buyer": "Caisse Nationale de Sécurité Sociale (CNSS)",
        "title": "L'Extension des licences de la solution de prévention des fuites de données (DLP) de la CNSS, en lot unique.",
        "procedure_type": "Appel d'offres ouvert",
        "publication_date": "12/11/2026 15:19",
        "deadline": "07/12/2026 15:00",
        "budget": "2 850 000,00",
        "caution": "30 000,00 DH",
        "bid_opening_place": "Siège de la CNSS, 649 Bd Mohammed V, Casablanca",
        "portal_url": "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1084220&orgAcronyme=o4d",
        "cps_excerpt": "Acquisition de 4500 souscriptions d'agents DLP endpoints, modules de détection de fuite sur passerelles de messagerie Office 365 / Exchange et serveurs de fichiers. Support éditeur 24/7/365 de niveau 3 exigé. L'intégrateur doit disposer du niveau de partenariat le plus élevé de l'éditeur au Maroc et justifier de 2 ingénieurs certifiés intervenant sur site."
    },
    "DGI_NPB": {
        "reference": "35/2026/DGI",
        "buyer": "Ministère de l'Économie et des Finances — Direction Générale des Impôts (DGI)",
        "title": "L’acquisition, l'installation et la mise en service d’une solution de courtier de paquets réseau (Network Packet Broker - NPB) au profit de la DGI",
        "procedure_type": "Appel d'offres ouvert",
        "publication_date": "16/11/2026 16:02",
        "deadline": "13/01/2027 10:00",
        "budget": "3 200 592,00",
        "caution": "30 000,00 DH",
        "bid_opening_place": "Direction des Impôts, Avenue Mohammed V, Rabat",
        "portal_url": "https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1035530&orgAcronyme=g8e&retraits",
        "cps_excerpt": "Fourniture de 2 châssis Network Packet Broker redondés pour les datacenters de Rabat et Casablanca. Capacité de commutation de 3.2 Tbps, ports 10G/25G/40G/100G, déduplication de paquets en temps réel, masquage de données sensibles (SSL/TLS decryption) et distribution des flux vers le SIEM et la sonde NDR."
    },
    "BAM_NDR": {
        "reference": "AO-BAM-08/2026/PMMP",
        "buyer": "Groupe Barid Al-Maghrib / Al Barid Bank",
        "title": "Acquisition d'une solution de détection et réponse réseau (NDR) et supervision sécurité Datacenter pour Al Barid Bank",
        "procedure_type": "Appel d'offres ouvert",
        "publication_date": "20/11/2026 10:30",
        "deadline": "24/12/2026 11:00",
        "budget": "4 500 000,00",
        "caution": "45 000,00 DH",
        "bid_opening_place": "Direction des Achats Al Barid Bank, Casablanca",
        "portal_url": "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1067820&orgAcronyme=b2m",
        "cps_excerpt": "Mise en place d'une solution de Network Detection and Response basée sur l'intelligence artificielle pour l'analyse comportementale du trafic inter-banque et inter-datacenter. Intégration native avec le SIEM existant et conformité à la Directive DNSSI."
    }
}


# ==============================================================================
# 5. CLI INTERACTIVE & POINT D'ENTRÉE DU SCRIPT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="CyberRFP Maroc - Analyseur IA pour Google AI Studio (DPA)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :
  python google_ai_studio_analyzer.py --demo cnss
  python google_ai_studio_analyzer.py --demo dgi
  python google_ai_studio_analyzer.py --key AIzaSy... --demo cnss
  python google_ai_studio_analyzer.py --text "Fourniture de licences antivirus et pare-feu..."
  python google_ai_studio_analyzer.py --pdf /chemin/vers/CPS_AO_35_2026.pdf
"""
    )
    parser.add_argument("--key", help="Clé API Google AI Studio (Gemini)", default="")
    parser.add_argument("--demo", choices=["cnss", "dgi", "bam"], help="Exécute une démo sur un AO réel du portail marocain")
    parser.add_argument("--text", help="Texte brut d'appel d'offres ou d'avis PMMP à analyser")
    parser.add_argument("--pdf", help="Chemin d'un document CPS au format PDF à analyser")

    args = parser.parse_args()

    # Bannière d'accueil
    print("=" * 80)
    print("      CYBERRFP MAROC — MODULE EXPERT GOOGLE AI STUDIO (GEMINI 2.5)")
    print("                ENTREPRISE : DPA (DataProtech Group)")
    print("=" * 80)

    analyzer = GoogleAIStudioAnalyzer(api_key=args.key)

    if not analyzer.client:
        print("\n[-] Clé API Google AI Studio manquante ou non valide.")
        print("[!] Veuillez obtenir votre clé gratuite sur : https://aistudio.google.com/")
        print("[!] Puis exécutez le script avec l'option --key VOTRE_CLE_ICI")
        print("    ou définissez la variable d'environnement : set GEMINI_API_KEY=AIzaSy...\n")
        
        # En mode démonstration sans clé, affiche le schéma et un aperçu
        print("[*] Affichage du format JSON contractuel généré par l'IA :")
        print(json.dumps(ANALYSIS_JSON_SCHEMA, indent=2))
        return

    # 1. Analyse par PDF
    if args.pdf:
        print(f"[*] Analyse du fichier PDF : {args.pdf}")
        result = analyzer.analyze_pdf_document(args.pdf)
        print("\n[+] RÉSULTAT DE L'ANALYSE GOOGLE AI STUDIO :")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # 2. Analyse par texte brut
    if args.text:
        print("[*] Analyse du texte personnalisé en cours...")
        result = analyzer.analyze_raw_text(args.text)
        print("\n[+] RÉSULTAT DE L'ANALYSE GOOGLE AI STUDIO :")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # 3. Analyse Démo (CNSS par défaut)
    demo_key = "CNSS_DLP"
    if args.demo == "dgi":
        demo_key = "DGI_NPB"
    elif args.demo == "bam":
        demo_key = "BAM_NDR"

    sample = SAMPLE_RFPS[demo_key]
    print(f"[*] Lancement de l'analyse IA sur l'appel d'offres officiel : {sample['reference']}")
    print(f"    Acheteur : {sample['buyer']}")
    print(f"    Objet    : {sample['title']}\n")

    result = analyzer.analyze_rfp_dict(sample)

    print("[+] RÉSULTAT OBTENU DE GOOGLE AI STUDIO (GEMINI 2.5 FLASH) :")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Affichage de synthèse pour DPA
    if "dpa_commercial_strategy" in result:
        strat = result["dpa_commercial_strategy"]
        print("\n" + "=" * 80)
        print(f"🎯 RECOMMANDATION DPA : {strat.get('decision_recommendation')} (Score Pertinence : {result.get('relevance_score')}%)")
        print(f"💡 STRATÉGIE GAGNANTE : {strat.get('win_strategy')}")
        print(f"📋 CERTIFICATIONS REQUISES : {', '.join(strat.get('required_expert_certifications', []))}")
        print("=" * 80)


if __name__ == "__main__":
    main()
