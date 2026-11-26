"""
Generic Configurable Procurement Connector for CyberRFP Maroc
Allows scraping ANY Moroccan public buyer website using URL + CSS selectors / PDF link patterns
Configurable at runtime from the Admin UI with zero code modifications.
"""
import time
import hashlib
import re
import ipaddress
import socket
from urllib.parse import urlparse
from typing import List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

from src.connectors.base import BaseConnector
from src.models import Tender, ScraperHealth, DocumentItem
from src.utils.normalizers import parse_moroccan_amount, parse_moroccan_datetime
from src.utils.watchlist import match_buyer_watchlist


def validate_safe_url(url_str: str) -> None:
    """
    SSRF Protection: Validates that the provided URL uses http/https
    and does not resolve to private, loopback, multicast, or link-local IP addresses.
    """
    if not url_str:
        raise ValueError("URL ne peut pas être vide")
    parsed = urlparse(url_str)
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"Protocole non autorisé: '{scheme}'. Seuls HTTP et HTTPS sont acceptés.")
    
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Nom d'hôte invalide dans l'URL")

    # Reject localhost and broadcast names
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise ValueError("Accès interdit : les adresses localhost/boucle locale sont interdites (SSRF protection).")

    # Resolve IP and check if private / link-local / multicast
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
                raise ValueError(f"Accès interdit : l'hôte résout vers une adresse IP interne/privée ({ip_str}) - SSRF bloqué.")
    except socket.gaierror as e:
        raise ValueError(f"Impossible de résoudre le nom d'hôte '{hostname}': {e}")


class GenericConfigurableConnector(BaseConnector):
    """
    Generic Scraper driven by dynamic database configuration.
    """

    def __init__(self, config: Dict[str, Any], user_agent: Optional[str] = None):
        cid = config.get("id", f"gen_{hashlib.md5(config.get('listing_url', '').encode()).hexdigest()[:8]}")
        name = config.get("name", "Connecteur Personnalisé")
        base_url = config.get("base_url", "")
        super().__init__(connector_id=cid, name=name, base_url=base_url)

        self.listing_url = config.get("listing_url", base_url)
        self.item_selector = config.get("item_selector", "div.item")
        self.title_selector = config.get("title_selector", "a")
        self.ref_selector = config.get("ref_selector", "")
        self.deadline_selector = config.get("deadline_selector", "")
        self.budget_selector = config.get("budget_selector", "")
        self.doc_link_selector = config.get("doc_link_selector", "")
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberRFPMaroc/1.0"

    @staticmethod
    def _safe_get(client: httpx.Client, url: str, max_redirects: int = 5) -> httpx.Response:
        """Performs GET while re-validating every HTTP redirect hop against SSRF."""
        from urllib.parse import urljoin
        current_url = url
        for _ in range(max_redirects + 1):
            validate_safe_url(current_url)
            resp = client.get(current_url, follow_redirects=False)
            if resp.is_redirect:
                loc = resp.headers.get("location")
                if not loc:
                    return resp
                current_url = urljoin(current_url, loc)
                continue
            return resp
        raise ValueError("Trop de redirections HTTP (limite SSRF atteinte).")

    def fetch_tenders(
        self,
        max_pages: int = 1,
        keywords: Optional[List[str]] = None,
        buyer_filter: Optional[str] = None
    ) -> List[Tender]:
        tenders: List[Tender] = []
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            validate_safe_url(self.listing_url)
            with httpx.Client(verify=True, timeout=25.0, headers={"User-Agent": self.user_agent}) as client:
                r = self._safe_get(client, self.listing_url)
                if r.status_code != 200:
                    self.health.status = "WARNING"
                    self.health.error_message = f"HTTP {r.status_code} returned by {self.listing_url}"
                    return []

                soup = BeautifulSoup(r.text, "html.parser")
                items = soup.select(self.item_selector)

                for item in items:
                    # 1. Title
                    title_el = item.select_one(self.title_selector) if self.title_selector else item
                    if not title_el:
                        continue
                    title = title_el.get_text(separator=" ", strip=True)
                    if not title or len(title) < 5:
                        continue

                    # 2. Reference
                    if self.ref_selector:
                        ref_el = item.select_one(self.ref_selector)
                        ref = ref_el.get_text(strip=True) if ref_el else ""
                    else:
                        m_ref = re.search(r"\b([A-Z0-9_\-]+/\d{4}|\d+/[A-Z0-9_\-]+/\d{4})\b", title)
                        ref = m_ref.group(1).strip() if m_ref else f"{self.name[:4].upper()}-{hashlib.md5(title.encode()).hexdigest()[:6].upper()}"

                    # 3. Deadline
                    deadline_str = None
                    if self.deadline_selector:
                        dl_el = item.select_one(self.deadline_selector)
                        if dl_el:
                            deadline_str = parse_moroccan_datetime(dl_el.get_text(strip=True))

                    # 4. Budget
                    budget = 0.0
                    if self.budget_selector:
                        b_el = item.select_one(self.budget_selector)
                        if b_el:
                            budget = parse_moroccan_amount(b_el.get_text(strip=True))

                    # 5. Detail / Doc URL
                    link_el = item.find("a", href=True)
                    url = link_el.get("href") if link_el else self.listing_url
                    full_url = url if url.startswith("http") else f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"

                    # Priority check
                    is_prio, norm_b, badge = match_buyer_watchlist(self.name)

                    tender_id = f"gen:{hashlib.md5(f'{ref}:{title}'.encode()).hexdigest()[:12]}"

                    tenders.append(Tender(
                        id=tender_id,
                        reference=ref,
                        title=title,
                        buyer_name=self.name,
                        buyer_normalized=norm_b or self.name,
                        is_priority_buyer=is_prio,
                        priority_badge=badge,
                        estimated_budget=budget,
                        deadline=deadline_str,
                        source_name=self.name,
                        source_url=full_url,
                        document_links=[
                            DocumentItem(
                                title="Lien de consultation",
                                url=full_url,
                                doc_type="DCE"
                            )
                        ]
                    ))

                self.health.status = "HEALTHY"
                self.health.last_run_time = now_str
                self.health.last_success_time = now_str
                self.health.items_found_last_run = len(tenders)
                self.health.total_items_indexed += len(tenders)
                self.health.error_message = None

        except Exception as e:
            self.health.status = "ERROR"
            self.health.error_message = f"Scraping error: {str(e)}"

        return tenders

    def health_check(self) -> ScraperHealth:
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            validate_safe_url(self.listing_url)
            with httpx.Client(verify=True, timeout=10.0, headers={"User-Agent": self.user_agent}) as client:
                r = self._safe_get(client, self.listing_url)
                if r.status_code == 200:
                    self.health.status = "HEALTHY"
                    self.health.error_message = None
                else:
                    self.health.status = "WARNING"
                    self.health.error_message = f"HTTP {r.status_code}"
        except Exception as e:
            self.health.status = "ERROR"
            self.health.error_message = str(e)

        self.health.last_run_time = now_str
        self.health.last_success_time = now_str
        return self.health
