"""
Google AI Studio (Gemini) Deep Analysis Engine for CyberRFP Maroc
Provides expert procurement analysis, DNSSI/Loi 05-20 compliance scoring,
expert certifications matrix, risk detection, and win strategy.
"""
import os
import json
import re
from typing import Dict, Any, Optional


class GoogleStudioClassifier:
    """
    Client for Google AI Studio Gemini API (Gemini 2.5 Flash / Pro).
    Acts as a Senior Moroccan Cybersecurity Bid & Public Procurement Consultant.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model_name = model_name
        self.client = None
        self._init_client()

    def set_api_key(self, api_key: str):
        """Updates API key dynamically at runtime."""
        self.api_key = api_key.strip()
        os.environ["GEMINI_API_KEY"] = self.api_key
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            self.client = None
            return
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception:
            self.client = None

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.client is not None)

    def get_status(self) -> Dict[str, Any]:
        return {
            "configured": bool(self.api_key),
            "client_initialized": self.client is not None,
            "model": self.model_name,
            "masked_key": f"{self.api_key[:6]}...{self.api_key[-4:]}" if self.api_key and len(self.api_key) > 10 else None
        }

    def analyze_tender(
        self,
        title: str,
        buyer_name: str,
        procedure_type: str = "AOO",
        budget: float = 0.0,
        caution: str = "",
        deadline: str = "",
        text_excerpt: str = ""
    ) -> Dict[str, Any]:
        """
        Submits tender details to Gemini for comprehensive bid analysis.
        If no API key is configured, generates an intelligent rule-based template.
        """
        if not self.is_available:
            return self._fallback_rule_analysis(title, buyer_name, budget, caution)

        prompt = f"""Tu es un Directeur Technique & Consultant Senior en marchés publics de cybersécurité au Maroc.
Tu maîtrises parfaitement le cadre réglementaire marocain :
- Décret n° 2-22-431 relatif aux marchés publics
- Loi n° 05-20 relative à la cybersécurité
- Directive Nationale de la Sécurité des Systèmes d'Information (DNSSI) émise par la DGSSI
- Norme ISO/IEC 27001 et référentiels d'homologation de l'État marocain

Analyse en détail l'appel d'offres marocain suivant :
ACHETEUR PUBLIC : {buyer_name}
RÉFÉRENCE & PROCÉDURE : {procedure_type}
OBJET (TITRE DU MARCHÉ) : {title}
ESTIMATION DU MAÎTRE D'OUVRAGE : {budget:,.2f} DH
CAUTION PROVISOIRE : {caution}
DATE LIMITE : {deadline}
EXTRAIT DU DOSSIER / CPS :
{text_excerpt[:3500]}

DIRECTIVES D'ANALYSE :
1. Évalue la pertinence cybersécurité (0 à 100) : élimine les faux positifs (sécurité incendie, gardiennage physique, surveillance humaine sauf SI).
2. Détermine le sous-domaine précis (ex: Network Packet Broker & Monitoring, SOC/SIEM, Audit & Pentest, Firewall/WAF, IAM/PAM, Sauvegarde & PRA, etc.).
3. Identifie les exigences de conformité réglementaire marocaine (DNSSI, Loi 05-20, hébergement souverain, homologation).
4. Établis la liste des profils et certifications obligatoires ou recommandées pour gagner (ex: CISSP, CISA, CEH, ISO 27001 Lead Auditor, Fortinet NSE 7, Palo Alto PCNSE).
5. Évalue les risques et pièges du marché (délais d'exécution, pénalités de retard, contraintes de support sur site).
6. Fournis une stratégie de réponse gagnante (Win Strategy) et une recommandation GO / NO-GO argumentée.

RÉPONDS STRICTEMENT sous forme d'un objet JSON valide avec cette structure exacte :
{{
  "relevance_score": <nombre entre 0 et 100>,
  "relevance_category": <"CYBERSECURITY" | "MAYBE" | "NOT_RELEVANT">,
  "sub_category": <nom court du sous-domaine technique en français>,
  "summary_fr": <résumé exécutif en 2 à 3 phrases claires en français>,
  "dnssi_compliance_points": [
    <point clé 1 de conformité DGSSI / Loi 05-20>,
    <point clé 2 de conformité>
  ],
  "required_certifications": [
    <certification 1, ex: CISSP>,
    <certification 2, ex: ISO 27001 Lead Auditor>,
    <certification 3, ex: Partenariat constructeur Tier-1>
  ],
  "risk_analysis": [
    <risque identifié 1, ex: Délais serrés de mise en service>,
    <risque identifié 2, ex: Pénalités de retard selon CCAG-EMO>
  ],
  "win_strategy": <stratégie commerciale et technique pour maximiser la note technique>,
  "recommended_bid_action": <"GO" | "GO AVEC PARTENAIRE ÉDITEUR" | "NO-GO">
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            raw_text = response.text.strip()
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return {
                    "relevance_score": int(data.get("relevance_score", 0)),
                    "relevance_category": str(data.get("relevance_category", "NOT_RELEVANT")),
                    "sub_category": str(data.get("sub_category", "Sécurité des SI")),
                    "summary_fr": str(data.get("summary_fr", "")).strip(),
                    "dnssi_compliance_points": data.get("dnssi_compliance_points", []),
                    "required_certifications": data.get("required_certifications", []),
                    "risk_analysis": data.get("risk_analysis", []),
                    "win_strategy": str(data.get("win_strategy", "")).strip(),
                    "recommended_bid_action": str(data.get("recommended_bid_action", "GO")),
                    "powered_by": "Google AI Studio (Gemini 2.5)"
                }
        except Exception as e:
            return self._fallback_rule_analysis(title, buyer_name, budget, caution, error_msg=str(e))

        return self._fallback_rule_analysis(title, buyer_name, budget, caution)

    def _fallback_rule_analysis(
        self,
        title: str,
        buyer_name: str,
        budget: float,
        caution: str,
        error_msg: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provides heuristic fallback analysis when Gemini API is unavailable or unconfigured."""
        t_lower = title.lower()
        is_cyber = any(k in t_lower for k in [
            "sécurité", "cyber", "pare-feu", "firewall", "waf", "soc", "siem",
            "audit", "pentest", "ndr", "paquet", "réseau", "iam", "pam", "chiffrement", "dnssi"
        ])

        subcat = "Sécurité Réseau & SI"
        if "ndr" in t_lower or "paquet" in t_lower or "broker" in t_lower:
            subcat = "Network Packet Broker & Traffic Monitoring"
        elif "soc" in t_lower or "siem" in t_lower:
            subcat = "SOC & Supervision SIEM"
        elif "audit" in t_lower or "pentest" in t_lower:
            subcat = "Audit de Sécurité & Tests d'intrusion"
        elif "firewall" in t_lower or "pare-feu" in t_lower:
            subcat = "Pare-feu & Filtrage Réseau"

        score = 90 if is_cyber else 15
        cat = "CYBERSECURITY" if is_cyber else "NOT_RELEVANT"

        return {
            "relevance_score": score,
            "relevance_category": cat,
            "sub_category": subcat,
            "summary_fr": f"Consultation publique de {buyer_name} pour des prestations/fournitures informatiques ({title[:90]}...).",
            "dnssi_compliance_points": [
                "Exigence de souveraineté des données et de traçabilité conforme à la Directive Nationale DGSSI",
                "Conformité à la Loi 05-20 sur la protection des infrastructures d'importance vitale (IIV)"
            ] if is_cyber else [],
            "required_certifications": [
                "CISSP / CISA pour le chef de projet",
                "Certifications constructeur officielles (Tier-1 Partner)",
                "ISO 27001 Lead Auditor"
            ] if is_cyber else ["Certifications techniques standard"],
            "risk_analysis": [
                "Vérifier le délai de validité de la caution provisoire (60 jours minimum)",
                "Respecter le seuil technique éliminatoire de 70/100"
            ],
            "win_strategy": "Mettre en avant des références similaires récentes avec attestations de bonne exécution auprès d'organismes publics marocains et une équipe d'ingénieurs certifiés basés localement au Maroc.",
            "recommended_bid_action": "GO" if is_cyber else "À QUALIFIER",
            "powered_by": "Moteur Heuristique Intégré (Renseignez votre clé Google AI Studio pour l'analyse Gemini en direct)"
        }
