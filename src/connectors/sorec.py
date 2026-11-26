"""
SOREC Procurement Connector (Société Royale d'Encouragement du Cheval)
Website: https://www.sorec.ma/appels-offres/ + PMMP Dedicated Agency Channel
"""
import time
import re
import hashlib
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from src.connectors.base import BaseConnector
from src.connectors.pmmp import PMMPConnector
from src.models import Tender, ScraperHealth, DocumentItem
from src.utils.normalizers import parse_moroccan_datetime


class SORECConnector(BaseConnector):
    """
    Monitors SOREC tenders.
    Inspects https://www.sorec.ma/appels-offres/ and the central PMMP channel.
    """

    def __init__(
        self,
        base_url: str = "https://www.sorec.ma",
        user_agent: Optional[str] = None
    ):
        super().__init__(
            connector_id="sorec",
            name="SOREC (Encouragement du Cheval)",
            base_url=base_url
        )
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberRFPMaroc/1.0"
        self.pmmp_subconnector = PMMPConnector(fetch_details=True)

    def fetch_tenders(
        self,
        max_pages: int = 1,
        keywords: Optional[List[str]] = None,
        buyer_filter: Optional[str] = None
    ) -> List[Tender]:
        tenders: List[Tender] = []
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")

        # 1. Scrape direct site https://www.sorec.ma/appels-offres/
        try:
            with httpx.Client(verify=False, timeout=25.0, headers={"User-Agent": self.user_agent}) as client:
                r = client.get(f"{self.base_url}/appels-offres/", follow_redirects=True)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    main = soup.find("main") or soup
                    cards = main.find_all("div", class_=re.compile(r"ao-card|tender|offre", re.I))

                    for c in cards:
                        txt = c.get_text(separator=" ", strip=True)
                        if "aucun résultat" in txt.lower():
                            continue

                        # Extract N° AO, Objet, Date Limite
                        m_ao = re.search(r"N°\s*AO\s*:\s*([^\s|]+)", txt, re.I)
                        ref = m_ao.group(1).strip() if m_ao else f"SOREC-{hashlib.md5(txt.encode()).hexdigest()[:6].upper()}"

                        m_obj = re.search(r"Objet\s*:\s*([^|]+)", txt, re.I)
                        obj = m_obj.group(1).strip() if m_obj else txt[:120]

                        m_date = re.search(r"Date limite\s*:\s*([^|]+)", txt, re.I)
                        dl = parse_moroccan_datetime(m_date.group(1).strip()) if m_date else None

                        link_el = c.find("a", href=True)
                        url = link_el.get("href") if link_el else f"{self.base_url}/appels-offres/"

                        tender_id = f"sorec:{hashlib.md5(f'{ref}:{obj}'.encode()).hexdigest()[:12]}"
                        tenders.append(Tender(
                            id=tender_id,
                            reference=ref,
                            title=obj,
                            buyer_name="SOREC",
                            buyer_normalized="SOREC",
                            is_priority_buyer=True,
                            priority_badge="SOREC (Prioritaire)",
                            deadline=dl,
                            source_name="SOREC",
                            source_url=url if url.startswith("http") else f"{self.base_url}/{url.lstrip('/')}"
                        ))
        except Exception:
            pass

        # 2. Query PMMP channel for SOREC tenders
        try:
            pmmp_sorec = self.pmmp_subconnector.fetch_tenders(buyer_filter="SOREC")
            for t in pmmp_sorec:
                t.is_priority_buyer = True
                t.priority_badge = "SOREC (Prioritaire)"
                t.buyer_normalized = "SOREC"
                tenders.append(t)

            self.health.status = "HEALTHY"
            self.health.last_run_time = now_str
            self.health.last_success_time = now_str
            self.health.items_found_last_run = len(tenders)
            self.health.total_items_indexed += len(tenders)
            self.health.error_message = None
        except Exception as e:
            self.health.status = "WARNING"
            self.health.error_message = f"SOREC fetch warning: {str(e)}"

        return tenders

    def health_check(self) -> ScraperHealth:
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            with httpx.Client(verify=False, timeout=15.0, headers={"User-Agent": self.user_agent}) as client:
                r = client.get(f"{self.base_url}/appels-offres/")
                if r.status_code == 200:
                    self.health.status = "HEALTHY"
                    self.health.error_message = None
                else:
                    self.health.status = "WARNING"
                    self.health.error_message = f"SOREC returned HTTP {r.status_code}"
        except Exception as e:
            self.health.status = "ERROR"
            self.health.error_message = f"Health check failed: {str(e)}"

        self.health.last_run_time = now_str
        self.health.last_success_time = now_str
        return self.health
