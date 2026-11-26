"""
Al Barid Bank (ABB) Procurement Connector
Website 1: https://fournisseurs.albaridbank.ma (JAGGAER E-Procurement Portal)
Website 2: https://www.albaridbank.ma/fr (Institutional Portal - Avis de Presse PDFs)
"""
import re
import time
import hashlib
from typing import List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

from src.connectors.base import BaseConnector
from src.models import Tender, DocumentItem, ScraperHealth
from src.utils.normalizers import parse_moroccan_amount, parse_moroccan_datetime
from src.utils.watchlist import match_buyer_watchlist


class AlBaridBankConnector(BaseConnector):
    """
    Ingests public calls for tender from Al Barid Bank (and Barid Al-Maghrib group).
    Monitors both the e-procurement supplier portal and institutional press notices.
    """

    def __init__(
        self,
        portal_url: str = "https://fournisseurs.albaridbank.ma",
        institutional_url: str = "https://www.albaridbank.ma",
        user_agent: Optional[str] = None,
        rate_limit_delay: float = 1.0,
        fetch_details: bool = True
    ):
        super().__init__(
            connector_id="albaridbank",
            name="Al Barid Bank & Barid Al-Maghrib",
            base_url=portal_url
        )
        self.portal_url = portal_url.rstrip("/")
        self.institutional_url = institutional_url.rstrip("/")
        # Standard Desktop Chrome User-Agent required by JAGGAER/BravoSolution WAF
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        self.rate_limit_delay = rate_limit_delay
        self.fetch_details = fetch_details
        self.client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self.client is None or self.client.is_closed:
            self.client = httpx.Client(
                verify=False,
                timeout=35.0,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "fr,fr-FR;q=0.9,en;q=0.8",
                }
            )
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
        Fetches active tenders from Al Barid Bank.
        Combines e-procurement opportunities table and institutional press notices.
        """
        tenders: List[Tender] = []
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            # 1. Fetch from suppliers portal (ESOP / JAGGAER)
            portal_tenders = self._fetch_portal_tenders()
            tenders.extend(portal_tenders)

            # 2. Fetch from institutional portal (PDF avis de presse & espace fournisseurs)
            institutional_tenders = self._fetch_institutional_notices()
            tenders.extend(institutional_tenders)

            self.health.status = "HEALTHY"
            self.health.last_run_time = now_str
            self.health.last_success_time = now_str
            self.health.items_found_last_run = len(tenders)
            self.health.total_items_indexed += len(tenders)
            self.health.error_message = None

        except Exception as e:
            self.health.status = "WARNING"
            self.health.last_run_time = now_str
            self.health.error_message = f"ABB fetch warning: {str(e)}"

        return tenders

    def _fetch_portal_tenders(self) -> List[Tender]:
        """Scrapes the public list-table on fournisseurs.albaridbank.ma."""
        client = self._get_client()
        tenders: List[Tender] = []

        # Session initialization via public opportunity entry point
        entry_url = f"{self.portal_url}/esop/guest/go/public/opportunity/current?locale=fr_FR"
        r = client.get(entry_url, follow_redirects=True)
        if r.status_code != 200:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", class_=re.compile(r"list-table", re.I))
        if not table:
            return []

        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            proc_type = cols[0].get_text(strip=True)
            buyer_name = cols[1].get_text(strip=True) or "Al Barid Bank"
            title_cell = cols[2]
            raw_title = title_cell.get_text(strip=True)
            category = cols[3].get_text(strip=True)
            raw_deadline = cols[4].get_text(strip=True)

            # Extract opportunityId from onclick="javascript:goToDetail('9555', '02810')"
            opp_id = None
            link_el = title_cell.find("a")
            if link_el and link_el.get("onclick"):
                m_opp = re.search(r"goToDetail\('(\d+)'", link_el.get("onclick"))
                if m_opp:
                    opp_id = m_opp.group(1)

            detail_url = f"{self.portal_url}/esop/toolkit/opportunity/current/{opp_id}/detail.si" if opp_id else str(r.url)

            # Extract reference (e.g. BC_DP_2026_811 or AOO N° xx/ABB/2026)
            m_ref = re.search(r"\b([A-Z0-9_\-]+/\d{4}|[A-Z0-9_\-]+_\d{3,4}|\d+/[A-Z0-9_\-]+/\d{4})\b", raw_title)
            if m_ref:
                reference = m_ref.group(1).strip()
            elif opp_id:
                reference = f"ABB-OPP-{opp_id}"
            else:
                reference = f"ABB-{hashlib.md5(raw_title.encode('utf-8')).hexdigest()[:8].upper()}"

            deadline_str = parse_moroccan_datetime(raw_deadline)

            tender_id = f"abb:{hashlib.md5(f'{reference}:{raw_title}'.encode('utf-8')).hexdigest()[:12]}"

            tender = Tender(
                id=tender_id,
                reference=reference,
                title=raw_title,
                buyer_name="Al Barid Bank",
                buyer_normalized="Al Barid Bank",
                is_priority_buyer=True,
                priority_badge="Al Barid Bank (Prioritaire)",
                procedure_type="AOO" if "ouverte" in proc_type.lower() else proc_type,
                category=category or "Fournitures",
                deadline=deadline_str,
                source_name="Al Barid Bank",
                source_url=detail_url,
                status="open",
                document_links=[
                    DocumentItem(
                        title=f"Dossier d'opportunité Al Barid Bank ({reference})",
                        url=detail_url,
                        doc_type="DCE"
                    )
                ]
            )

            # Enrich from detail page if opp_id is available
            if self.fetch_details and opp_id:
                self._enrich_abb_detail(tender, detail_url, client)

            tenders.append(tender)

        return tenders

    def _enrich_abb_detail(self, tender: Tender, detail_url: str, client: httpx.Client):
        """Fetches opportunity detail page on ESOP and extracts documents and notice links."""
        try:
            self._sleep_polite()
            r = client.get(detail_url)
            if r.status_code != 200:
                return

            soup = BeautifulSoup(r.text, "html.parser")
            
            # Find downloadable documents (e.g. "Avis de presse FR VF.pdf")
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                txt = a.get_text(strip=True)
                if "DownloadProxy" in href or href.endswith(".pdf"):
                    full_link = f"{self.portal_url}{href}" if not href.startswith("http") else href
                    tender.document_links.append(DocumentItem(
                        title=txt or "Avis de presse officiel",
                        url=full_link,
                        doc_type="Avis"
                    ))

        except Exception:
            pass

    def _fetch_institutional_notices(self) -> List[Tender]:
        """Scrapes PDF notices ('Avis de presse', 'AOO N° xx/ABB/2025/2026') from www.albaridbank.ma."""
        client = self._get_client()
        tenders: List[Tender] = []

        target_urls = [
            f"{self.institutional_url}/fr/espace-fournisseurs",
            f"{self.institutional_url}/fr/newsroom/actualites"
        ]

        for page_url in target_urls:
            try:
                r = client.get(page_url, follow_redirects=True)
                if r.status_code != 200:
                    continue

                soup = BeautifulSoup(r.text, "html.parser")
                links = soup.find_all("a", href=True)

                for a in links:
                    href = a.get("href", "")
                    text = a.get_text(separator=" ", strip=True)
                    combined = f"{text} {href}".lower()

                    if any(k in combined for k in ["avis", "aoo", "appel d'offre", "fournisseur"]) and href.endswith(".pdf"):
                        full_pdf_url = href if href.startswith("http") else f"{self.institutional_url}/{href.lstrip('/')}"
                        
                        m_ref = re.search(r"(AOO\s*(?:N°)?\s*\d+/\w+/\d{4})", text, re.I)
                        ref = m_ref.group(1).strip() if m_ref else f"ABB-AVIS-{hashlib.md5(full_pdf_url.encode('utf-8')).hexdigest()[:6].upper()}"

                        tender_id = f"abb:{hashlib.md5(full_pdf_url.encode('utf-8')).hexdigest()[:12]}"
                        tender = Tender(
                            id=tender_id,
                            reference=ref,
                            title=f"Avis de presse d'appel d'offres : {text or ref}",
                            buyer_name="Al Barid Bank",
                            buyer_normalized="Al Barid Bank",
                            is_priority_buyer=True,
                            priority_badge="Al Barid Bank (Prioritaire)",
                            procedure_type="AOO",
                            category="Services",
                            source_name="Al Barid Bank",
                            source_url=full_pdf_url,
                            status="open",
                            document_links=[
                                DocumentItem(
                                    title=f"Avis de presse officiel ({ref})",
                                    url=full_pdf_url,
                                    doc_type="Avis"
                                )
                            ]
                        )
                        tenders.append(tender)

            except Exception:
                continue

        return tenders

    def health_check(self) -> ScraperHealth:
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            client = self._get_client()
            r = client.get(f"{self.portal_url}/esop/guest/go/public/opportunity/current?locale=fr_FR", follow_redirects=True)
            if r.status_code == 200:
                self.health.status = "HEALTHY"
                self.health.last_success_time = now_str
                self.health.error_message = None
            else:
                self.health.status = "WARNING"
                self.health.error_message = f"ABB portal returned HTTP {r.status_code}"
        except Exception as e:
            self.health.status = "ERROR"
            self.health.error_message = f"Health check error: {str(e)}"

        self.health.last_run_time = now_str
        return self.health
