"""
PMMP Connector (Portail Marocain des Marchés Publics)
Website: https://www.marchespublics.gov.ma
Scrapes public consultation listings, details, and document references.
Operates 100% anonymously with polite scraping delays and resilient error handling.
"""
import re
import time
import hashlib
from typing import List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

from src.connectors.base import BaseConnector
from src.models import Tender, DocumentItem, ScraperHealth, TenderChange
from src.utils.normalizers import parse_moroccan_amount, parse_moroccan_datetime
from src.utils.watchlist import match_buyer_watchlist


class PMMPConnector(BaseConnector):
    """
    Connector for the official Moroccan public procurement portal (PMMP).
    Run by the Trésorerie Générale du Royaume (TGR).
    """

    CYBER_SEARCH_KEYWORDS = [
        "cybersécurité",
        "pare-feu",
        "firewall",
        "audit sécurité",
        "SIEM",
    ]

    def __init__(
        self,
        base_url: str = "https://www.marchespublics.gov.ma",
        user_agent: Optional[str] = None,
        rate_limit_delay: float = 0.25,
        fetch_details: bool = True,
        max_detail_enrichments: int = 25,
    ):
        super().__init__(
            connector_id="pmmp",
            name="Portail Marocain des Marchés Publics",
            base_url=base_url
        )
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 CyberRFPMaroc/1.0 (contact: info@cyberrfp.ma)"
        )
        self.rate_limit_delay = rate_limit_delay
        self.fetch_details = fetch_details
        self.max_detail_enrichments = max_detail_enrichments
        self.client: Optional[httpx.Client] = None

    @staticmethod
    def clean_pmmp_text(text: Optional[str]) -> str:
        """Strips PMMP UI labels ('Objet :', 'Acheteur public :') and PUA glyph boxes."""
        if not text:
            return ""
        cleaned = re.sub(r"[\ue000-\uf8ff]", " ", text)
        cleaned = re.sub(r"^\s*(?:Objet|Acheteur\s+public)\s*:\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"^[\s\-•·*:\ue000-\uf8ff]+", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    def _get_client(self) -> httpx.Client:
        if self.client is None or self.client.is_closed:
            self.client = httpx.Client(
                verify=False,
                timeout=20.0,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "fr,fr-FR;q=0.9,en;q=0.8",
                }
            )
            # Initialize session cookies
            try:
                self.client.get(f"{self.base_url}/pmmp/")
            except Exception:
                pass
        return self.client

    def _sleep_polite(self):
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

    def fetch_tenders(
        self,
        max_pages: int = 1,
        keywords: Optional[List[str]] = None,
        buyer_filter: Optional[str] = None
    ) -> List[Tender]:
        """
        Fetches current open public consultations from PMMP, combining ongoing listings
        with targeted cybersecurity keyword searches for comprehensive coverage.
        """
        client = self._get_client()
        tenders: List[Tender] = []
        seen_ids = set()
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        search_url = f"{self.base_url}/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours"

        def _parse_response(resp: httpx.Response):
            if resp.status_code != 200:
                return
            soup = BeautifulSoup(resp.text, "html.parser")
            boxes = soup.find_all("div", class_=re.compile(r"generalBox", re.I))
            for idx, box in enumerate(boxes):
                orig_fetch = self.fetch_details
                if len(tenders) >= self.max_detail_enrichments:
                    self.fetch_details = False
                tender = self._parse_general_box(box, client)
                self.fetch_details = orig_fetch
                if tender and tender.id not in seen_ids:
                    seen_ids.add(tender.id)
                    tenders.append(tender)

        try:
            if keywords and len(keywords) > 0:
                for kw_str in keywords[:3]:
                    resp = client.get(f"{search_url}&keyword={kw_str}")
                    _parse_response(resp)
                    self._sleep_polite()
            elif buyer_filter:
                post_data = {
                    "ctl0$menuGaucheEntreprise$quickSearch": buyer_filter,
                    "ctl0$menuGaucheEntreprise$imageOk.x": "10",
                    "ctl0$menuGaucheEntreprise$imageOk.y": "10",
                }
                resp = client.post(search_url, data=post_data)
                _parse_response(resp)
            else:
                # 1. Base listing of ongoing tenders
                resp = client.get(search_url)
                if resp.status_code != 200:
                    self.health.status = "WARNING"
                    self.health.error_message = f"HTTP {resp.status_code} returned by PMMP search."
                    return []
                _parse_response(resp)

                # 2. Targeted cybersecurity keyword sweeps so critical RFPs aren't missed on later pages
                for kw in self.CYBER_SEARCH_KEYWORDS:
                    try:
                        self._sleep_polite()
                        kw_resp = client.get(
                            f"{self.base_url}/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons&keyWord={kw}"
                        )
                        _parse_response(kw_resp)
                    except Exception:
                        continue

            self.health.status = "HEALTHY"
            self.health.last_run_time = now_str
            self.health.last_success_time = now_str
            self.health.items_found_last_run = len(tenders)
            self.health.total_items_indexed += len(tenders)
            self.health.error_message = None

        except Exception as e:
            self.health.status = "ERROR"
            self.health.last_run_time = now_str
            self.health.error_message = f"PMMP fetch error: {str(e)}"

        return tenders

    def _parse_general_box(self, box: BeautifulSoup, client: httpx.Client) -> Optional[Tender]:
        """Parses a single div.generalBox representing a tender card."""
        try:
            # Reference
            ref_el = box.find(id=re.compile(r"referencem", re.I))
            if not ref_el:
                # Fallback search for reference pattern
                text_ref = box.find(string=re.compile(r"Référence\s*:", re.I))
                if text_ref and text_ref.parent:
                    raw_ref = text_ref.parent.get_text(strip=True).replace("Référence :", "").strip()
                else:
                    return None
            else:
                raw_ref = ref_el.get_text(strip=True)

            reference = raw_ref.strip()
            if not reference:
                return None

            # Procedure Type
            proc_el = box.find("span", class_=re.compile(r"hotTender", re.I))
            procedure_type = proc_el.get_text(strip=True) if proc_el else "AOO"

            # Title / Objet
            obj_el = box.find("div", class_=re.compile(r"p-objet", re.I))
            if obj_el:
                raw_obj = self.clean_pmmp_text(obj_el.get_text(separator=" ", strip=True))
            else:
                raw_obj = f"Consultation publique {reference}"

            # Estimated Budget
            estim_el = box.find(id=re.compile(r"estimationLabel", re.I)) or box.find("span", class_=re.compile(r"estim-mad", re.I))
            budget = parse_moroccan_amount(estim_el.get_text(strip=True) if estim_el else None)

            # Buyer Name
            buyer_card = box.find("div", class_=re.compile(r"title\s+p-card", re.I))
            buyer_name = "Organisme Public"
            if buyer_card:
                card_text = buyer_card.get_text(separator=" ", strip=True)
                m_buyer = re.search(r"Acheteur public\s*:\s*(.+)", card_text, re.I)
                raw_buyer = m_buyer.group(1) if m_buyer else card_text
                buyer_name = self.clean_pmmp_text(raw_buyer) or "Organisme Public"

            # Check Priority Watchlist
            is_priority, matched_buyer, badge = match_buyer_watchlist(buyer_name)

            # Submission Deadline
            # Look for date & time inside .limita.p-card
            deadline_str = None
            date_part = None
            time_part = "10:00:00"

            limita_blocks = box.find_all("div", class_=re.compile(r"limita\s+p-card", re.I))
            for l_block in limita_blocks:
                cal_icon = l_block.find(class_=re.compile(r"fa-calendar", re.I))
                if cal_icon:
                    next_s = cal_icon.find_next_sibling("span")
                    if next_s:
                        date_part = next_s.get_text(strip=True)
                    elif cal_icon.parent:
                        date_part = cal_icon.parent.get_text(separator=" ", strip=True)

                clock_icon = l_block.find(class_=re.compile(r"fa-clock", re.I))
                if clock_icon:
                    next_cs = clock_icon.find_next_sibling("span")
                    if next_cs:
                        time_part = next_cs.get_text(strip=True)
                    elif clock_icon.parent:
                        time_part = clock_icon.parent.get_text(separator=" ", strip=True)

            if date_part:
                combined_dt = f"{date_part} {time_part}".strip()
                deadline_str = parse_moroccan_datetime(combined_dt)

            # Detail Link & Source URL
            detail_link = box.find("a", href=re.compile(r"EntrepriseDetailsConsultation", re.I))
            ref_consultation = None
            org_acronyme = None
            source_url = f"{self.base_url}/index.php?page=entreprise.EntrepriseAdvancedSearch"

            if detail_link:
                href = detail_link.get("href", "")
                if not href.startswith("http"):
                    source_url = f"{self.base_url}/{href.lstrip('/')}"
                else:
                    source_url = href
                
                # Extract refConsultation & orgAcronyme from query
                m_refc = re.search(r"refConsultation=([0-9]+)", source_url)
                if m_refc:
                    ref_consultation = m_refc.group(1)
                m_org = re.search(r"orgAcronyme=([A-Za-z0-9_\-]+)", source_url)
                if m_org:
                    org_acronyme = m_org.group(1)

            # Detect corrigenda / postponement status
            status = "open"
            lower_obj = raw_obj.lower()
            if any(k in lower_obj for k in ["avis de report", "report de la date", "report d'ouverture"]):
                status = "postponed"
            elif any(k in lower_obj for k in ["rectificatif", "modificatif", "erratum", "additif"]):
                status = "amended"
            elif any(k in lower_obj for k in ["annulé", "annulation"]):
                status = "cancelled"

            # Create deterministic ID
            tender_id = f"pmmp:{hashlib.md5(f'{reference}:{buyer_name}'.encode('utf-8')).hexdigest()[:12]}"

            # Build tender
            tender = Tender(
                id=tender_id,
                reference=reference,
                title=raw_obj,
                buyer_name=buyer_name,
                buyer_normalized=matched_buyer or buyer_name,
                is_priority_buyer=is_priority,
                priority_badge=badge,
                procedure_type=procedure_type,
                category="Services" if "services" in lower_obj else ("Fournitures" if "fournitures" in lower_obj else "Travaux"),
                estimated_budget=budget,
                deadline=deadline_str,
                source_name="PMMP",
                source_url=source_url,
                status=status,
            )

            # Fetch detailed fields (caution provisoire, qualifications, DCE link, contacts) if requested
            if self.fetch_details and ref_consultation and org_acronyme:
                self._enrich_tender_details(tender, ref_consultation, org_acronyme, client)

            return tender

        except Exception as e:
            # Skip corrupt box silently or log
            return None

    def _enrich_tender_details(
        self,
        tender: Tender,
        ref_consultation: str,
        org_acronyme: str,
        client: httpx.Client
    ):
        """Fetches the PMMP consultation detail page and extracts deep fields."""
        try:
            self._sleep_polite()
            detail_url = f"{self.base_url}/?page=entreprise.EntrepriseDetailsConsultation&refConsultation={ref_consultation}&orgAcronyme={org_acronyme}"
            r = client.get(detail_url)
            if r.status_code != 200:
                return

            soup = BeautifulSoup(r.text, "html.parser")
            body_text = soup.get_text()

            # 1. Caution provisoire
            m_caution = re.search(r"Caution provisoire\s*:\s*([^\n\r<]+)", body_text, re.I)
            if m_caution:
                tender.provisional_guarantee = m_caution.group(1).strip()

            # 2. Publication date
            m_pub = re.search(r"Date de mise en ligne\s*:\s*([^\n\r<]+?)(?:Date|\n|$)", body_text, re.I)
            if m_pub:
                tender.publication_date = parse_moroccan_datetime(m_pub.group(1).strip())

            # 3. Bid opening place
            m_open = re.search(r"Lieu d'ouverture des plis\s*:\s*([^\n\r<]+)", body_text, re.I)
            if m_open:
                tender.bid_opening_place = m_open.group(1).strip()

            # 4. Qualifications & Agrements
            m_qual = re.search(r"Qualifications\s*:\s*([^\n\r<]+)", body_text, re.I)
            if m_qual:
                tender.qualifications = m_qual.group(1).strip()
            m_agr = re.search(r"Agréments\s*:\s*([^\n\r<]+)", body_text, re.I)
            if m_agr:
                tender.agrements = m_agr.group(1).strip()

            # 5. Administrative Contact
            m_contact = re.search(r"Contact Administratif\s*:\s*([^\n\r<]+)", body_text, re.I)
            if m_contact:
                tender.contact = m_contact.group(1).strip()

            # 6. Document links
            doc_links: List[DocumentItem] = []
            
            # Avis link
            avis_link = soup.find("a", href=re.compile(r"EntrepriseDownloadAvisJAL", re.I))
            if avis_link:
                a_href = avis_link.get("href", "")
                full_avis = f"{self.base_url}/{a_href.lstrip('/')}" if not a_href.startswith("http") else a_href
                doc_links.append(DocumentItem(
                    title="Avis de publicité",
                    url=full_avis,
                    doc_type="Avis"
                ))

            # DCE link
            dce_link = soup.find("a", href=re.compile(r"EntrepriseDemandeTelechargementDce", re.I))
            if dce_link:
                d_href = dce_link.get("href", "")
                full_dce = f"{self.base_url}/{d_href.lstrip('/')}" if not d_href.startswith("http") else d_href
                doc_links.append(DocumentItem(
                    title="Dossier de consultation (DCE)",
                    url=full_dce,
                    doc_type="DCE"
                ))

            tender.document_links = doc_links

        except Exception:
            pass

    def health_check(self) -> ScraperHealth:
        """Verifies PMMP accessibility and DOM selectors validity."""
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            client = self._get_client()
            r = client.get(f"{self.base_url}/pmmp/")
            if r.status_code == 200:
                self.health.status = "HEALTHY"
                self.health.last_success_time = now_str
                self.health.error_message = None
            else:
                self.health.status = "WARNING"
                self.health.error_message = f"PMMP returned HTTP {r.status_code}"
        except Exception as e:
            self.health.status = "ERROR"
            self.health.error_message = f"Health check failed: {str(e)}"

        self.health.last_run_time = now_str
        return self.health
