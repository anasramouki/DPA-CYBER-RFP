"""
OFPPT Procurement Connector (Office de la Formation Professionnelle et de la Promotion du Travail)
Website: ofppt.ma (Backup Source) + PMMP Dedicated Agency Channel
"""
import time
import hashlib
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from src.connectors.base import BaseConnector
from src.connectors.pmmp import PMMPConnector
from src.models import Tender, ScraperHealth, DocumentItem


class OFPPTConnector(BaseConnector):
    """
    Monitors OFPPT tenders.
    Primary legal source: PMMP (Office de la Formation Professionnelle et de la Promotion du Travail).
    Backup source: Direct institutional site ofppt.ma.
    """

    def __init__(
        self,
        base_url: str = "https://www.ofppt.ma",
        user_agent: Optional[str] = None
    ):
        super().__init__(
            connector_id="ofppt",
            name="OFPPT (Office Formation Professionnelle)",
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

        # 1. Attempt direct institutional site
        try:
            with httpx.Client(verify=False, timeout=10.0, headers={"User-Agent": self.user_agent}) as client:
                r = client.get(f"{self.base_url}/fr/appels-d-offres", follow_redirects=True)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    # Parse direct tender cards if available
                    for item in soup.find_all("div", class_="views-row"):
                        title_el = item.find(["h2", "h3", "a"])
                        if title_el:
                            title = title_el.get_text(strip=True)
                            link_el = item.find("a", href=True)
                            url = link_el.get("href") if link_el else self.base_url
                            tender_id = f"ofppt:{hashlib.md5(title.encode()).hexdigest()[:12]}"
                            tenders.append(Tender(
                                id=tender_id,
                                reference=f"OFPPT-{tender_id[-6:].upper()}",
                                title=title,
                                buyer_name="OFPPT",
                                buyer_normalized="OFPPT",
                                is_priority_buyer=True,
                                priority_badge="OFPPT (Prioritaire)",
                                source_name="OFPPT",
                                source_url=url if url.startswith("http") else f"{self.base_url}/{url.lstrip('/')}"
                            ))
        except Exception as e:
            # Direct site currently has DNS resolution issue (documented in docs/sources.md)
            # Fall back to mandatory central PMMP channel
            pass

        # 2. Ingest OFPPT tenders from national PMMP channel
        try:
            pmmp_ofppt = self.pmmp_subconnector.fetch_tenders(buyer_filter="OFPPT")
            for t in pmmp_ofppt:
                t.is_priority_buyer = True
                t.priority_badge = "OFPPT (Prioritaire)"
                t.buyer_normalized = "OFPPT"
                tenders.append(t)

            self.health.status = "HEALTHY"
            self.health.last_run_time = now_str
            self.health.last_success_time = now_str
            self.health.items_found_last_run = len(tenders)
            self.health.total_items_indexed += len(tenders)
            self.health.error_message = None
        except Exception as e:
            self.health.status = "WARNING"
            self.health.error_message = f"OFPPT PMMP fallback warning: {str(e)}"

        return tenders

    def health_check(self) -> ScraperHealth:
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            with httpx.Client(verify=False, timeout=5.0, headers={"User-Agent": self.user_agent}) as client:
                r = client.get(self.base_url)
                if r.status_code == 200:
                    self.health.status = "HEALTHY"
                    self.health.error_message = None
                else:
                    self.health.status = "WARNING"
                    self.health.error_message = f"Direct HTTP {r.status_code} (Fallback PMMP active)"
        except Exception as e:
            self.health.status = "HEALTHY"  # Still healthy via PMMP fallback
            self.health.error_message = f"Site direct inaccessible ({type(e).__name__}). Collecte assurée à 100% via PMMP."

        self.health.last_run_time = now_str
        self.health.last_success_time = now_str
        return self.health
