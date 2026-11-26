"""
Official Press & Procurement Aggregator Connector for CyberRFP Maroc
Retrieves authentic, live procurement notices and press articles from verifiable
Moroccan public procurement directories and IT sector feeds:
  - AO Maroc (https://www.aomaroc.com) IT, Software, Telecom & Audit press feeds
  - MarocBiz (https://marocbiz.com) IT Hardware, Software & Security sector feed

Zero synthetic fabrication: every returned Tender links directly to its real,
verifiable tender announcement / press article URL.
"""
import re
import time
import hashlib
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

from src.connectors.base import BaseConnector
from src.models import Tender, DocumentItem, ScraperHealth
from src.classifier.rules import classify_text_rules
from src.utils.normalizers import parse_moroccan_amount, parse_moroccan_datetime
from src.utils.watchlist import match_buyer_watchlist

logger = logging.getLogger("cyberrfp.press_journal")


class PressJournalConnector(BaseConnector):
    """
    Live procurement press connector fetching authentic IT & Cybersecurity
    tenders published in Moroccan tender press aggregators and official directories.
    """

    AOMAROC_FEEDS: List[Tuple[str, str, str]] = [
        ("https://www.aomaroc.com/services/domaine/informatique-logiciels.html", "AO Maroc (Services IT & Logiciels)", "Services"),
        ("https://www.aomaroc.com/services/domaine/informatique-telecoms.html", "AO Maroc (Services IT & Télécoms)", "Services"),
        ("https://www.aomaroc.com/fournitures/domaine/informatique-logiciels.html", "AO Maroc (Fournitures IT & Sécurité)", "Fournitures"),
        ("https://www.aomaroc.com/fournitures/domaine/informatique-telecoms.html", "AO Maroc (Fournitures Réseaux & Télécoms)", "Fournitures"),
        ("https://www.aomaroc.com/services/domaine/conseil-audit-amo.html", "AO Maroc (Conseil & Audit)", "Services"),
    ]

    MAROCBIZ_FEEDS: List[Tuple[str, str, str]] = [
        (
            "https://marocbiz.com/appels-offres/secteur/materiel-informatique-logiciels-et-pieces-de-rechanges/",
            "MarocBiz (Presse IT & Systèmes)",
            "Fournitures",
        ),
    ]

    def __init__(self, rate_limit_delay: float = 0.25):
        super().__init__(
            connector_id="press_journal",
            name="Presse Marchés & Portails Maroc",
            base_url="https://www.aomaroc.com",
        )
        self.rate_limit_delay = rate_limit_delay
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }

    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            verify=True,
            timeout=15.0,
            headers=self.headers,
            follow_redirects=True,
        )

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"[\ue000-\uf8ff]", " ", text)
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def parse_aomaroc_html(
        cls,
        html_content: str,
        source_label: str = "Presse Marchés & AO Maroc",
        default_category: str = "Services",
        base_url: str = "https://www.aomaroc.com",
    ) -> List[Tender]:
        """Pure HTML parser for AO Maroc <article class='offre'> cards."""
        soup = BeautifulSoup(html_content, "html.parser")
        tenders: List[Tender] = []

        for article in soup.find_all("article", class_="offre"):
            try:
                title_el = article.select_one("h3 a[href]")
                if not title_el:
                    continue
                title = cls._clean_text(title_el.get_text(" ", strip=True))
                if not title:
                    continue

                raw_article_href = title_el.get("href", "").strip()
                article_url = urljoin(base_url, raw_article_href)

                # Reference & ISO deadline
                head_el = article.select_one("p.carte-tete")
                deadline_iso = None
                reference = ""
                if head_el:
                    dl_attr = head_el.get("data-dl", "").strip()
                    if dl_attr:
                        deadline_iso = dl_attr.replace("T", " ")[:19]
                    head_txt = cls._clean_text(head_el.get_text(" ", strip=True))
                    if "|" in head_txt:
                        reference = head_txt.split("|", 1)[-1].replace("📝", "").strip()
                    if not deadline_iso:
                        m_dt = re.search(r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})", head_txt)
                        if m_dt:
                            deadline_iso = parse_moroccan_datetime(m_dt.group(1))

                if not reference:
                    m_id = re.search(r"/offre/(\d+)\.html", article_url)
                    reference = f"AO-{m_id.group(1)}" if m_id else f"PRESS-{hashlib.md5(title.encode()).hexdigest()[:6].upper()}"

                # Buyer name
                buyer_el = article.select_one("p.ach a") or article.select_one("p.ach")
                buyer_name = cls._clean_text(buyer_el.get_text(" ", strip=True)) if buyer_el else "Organisme Public"
                buyer_name = re.sub(r"^[🏛️\s]+", "", buyer_name).strip() or "Organisme Public"
                is_prio, matched_buyer, badge = match_buyer_watchlist(buyer_name)

                # Budget & Caution
                mnt_el = article.select_one("span.mnt")
                budget = parse_moroccan_amount(mnt_el.get_text(" ", strip=True) if mnt_el else None)
                cau_el = article.select_one("span.cau")
                caution_text = cls._clean_text(cau_el.get_text(" ", strip=True).lstrip("🛡️ ")) if cau_el else None

                # Location
                loc_text = None
                for p in article.find_all("p"):
                    txt = p.get_text(" ", strip=True)
                    if "📍" in txt:
                        loc_text = cls._clean_text(txt.replace("📍", ""))
                        break

                # Document links: always include official portal + CPS if present alongside verified press article
                doc_links: List[DocumentItem] = [
                    DocumentItem(
                        title=f"Article & Fiche Officielle ({reference})",
                        url=article_url,
                        doc_type="Avis",
                    )
                ]
                for a in article.select("p.actions-carte a[href]"):
                    href = a.get("href", "").strip()
                    full_link = urljoin(base_url, href)
                    if "marchespublics.gov.ma" in full_link:
                        doc_links.append(DocumentItem(
                            title="Consultation Officielle PMMP",
                            url=full_link,
                            doc_type="Portal",
                        ))
                    elif "/cps?" in full_link:
                        doc_links.append(DocumentItem(
                            title="Cahier des Prescriptions (CPS)",
                            url=full_link,
                            doc_type="DCE",
                        ))

                m_cid = re.search(r"/offre/(\d+)\.html", article_url)
                uid = m_cid.group(1) if m_cid else hashlib.md5(f"{reference}:{buyer_name}".encode("utf-8")).hexdigest()[:10]
                tender_id = f"press:aomaroc-{uid}"

                t = Tender(
                    id=tender_id,
                    reference=reference,
                    title=title,
                    buyer_name=buyer_name,
                    buyer_normalized=matched_buyer or buyer_name,
                    is_priority_buyer=is_prio,
                    priority_badge=badge,
                    procedure_type="AOO" if "appel d'offres" in title.lower() or "ao" in reference.lower() else "Consultation",
                    category=default_category,
                    deadline=deadline_iso,
                    bid_opening_place=loc_text,
                    estimated_budget=budget,
                    provisional_guarantee=caution_text,
                    source_name=source_label,
                    source_url=article_url,
                    document_links=doc_links,
                    status="open",
                )
                tenders.append(t)
            except Exception as e:
                logger.debug(f"Skipping malformed aomaroc card: {e}")
                continue

        return tenders

    @classmethod
    def parse_marocbiz_html(
        cls,
        html_content: str,
        source_label: str = "MarocBiz (Presse IT & Systèmes)",
        base_url: str = "https://marocbiz.com",
    ) -> List[Tender]:
        """Pure HTML parser for MarocBiz <ul class='list'><li> tender cards."""
        soup = BeautifulSoup(html_content, "html.parser")
        tenders: List[Tender] = []

        for li in soup.select("ul.list li"):
            try:
                title_link = li.select_one("a.o[href]")
                if not title_link:
                    continue
                title = cls._clean_text(title_link.get_text(" ", strip=True))
                if not title:
                    continue

                article_url = urljoin(base_url, title_link["href"].strip())
                buyer_link = li.select_one("div.m a[href*='/acheteur/']")
                buyer_name = cls._clean_text(buyer_link.get_text(" ", strip=True)) if buyer_link else "Organisme Public"
                is_prio, matched_buyer, badge = match_buyer_watchlist(buyer_name)

                meta_text = cls._clean_text(li.select_one("div.m").get_text(" ", strip=True) if li.select_one("div.m") else "")
                deadline_iso = None
                m_dl = re.search(r"Limite\s*:\s*(\d{1,2}\s+\w+\.?\s+\d{4})", meta_text, re.I)
                if m_dl:
                    deadline_iso = parse_moroccan_datetime(m_dl.group(1))

                m_id = re.search(r"-(\d+)$", article_url)
                uid = m_id.group(1) if m_id else hashlib.md5(article_url.encode("utf-8")).hexdigest()[:10]
                reference = f"MBIZ-{uid}"

                tenders.append(Tender(
                    id=f"press:marocbiz-{uid}",
                    reference=reference,
                    title=title,
                    buyer_name=buyer_name,
                    buyer_normalized=matched_buyer or buyer_name,
                    is_priority_buyer=is_prio,
                    priority_badge=badge,
                    procedure_type="AOO",
                    category="Fournitures",
                    deadline=deadline_iso,
                    source_name=source_label,
                    source_url=article_url,
                    document_links=[
                        DocumentItem(
                            title="Article Presse MarocBiz",
                            url=article_url,
                            doc_type="Avis",
                        )
                    ],
                    status="open",
                ))
            except Exception as e:
                logger.debug(f"Skipping malformed marocbiz row: {e}")
                continue

        return tenders

    def fetch_tenders(
        self,
        max_pages: int = 1,
        keywords: Optional[List[str]] = None,
        buyer_filter: Optional[str] = None,
    ) -> List[Tender]:
        """Fetches real IT/Cyber tenders from live press aggregator feeds."""
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        collected: List[Tender] = []
        seen_keys = set()
        pages = max(1, min(max_pages, 3))
        errors: List[str] = []

        try:
            with self._get_client() as client:
                # 1. AO Maroc IT/Cyber/Audit feeds
                for feed_url, source_label, cat in self.AOMAROC_FEEDS:
                    for page_idx in range(1, pages + 1):
                        url = feed_url if page_idx == 1 else f"{feed_url}?page={page_idx}"
                        try:
                            resp = client.get(url)
                            if resp.status_code == 200:
                                items = self.parse_aomaroc_html(resp.text, source_label=source_label, default_category=cat)
                                for item in items:
                                    self._maybe_append(item, collected, seen_keys, keywords, buyer_filter)
                        except Exception as e:
                            errors.append(f"{feed_url}: {e}")
                        if self.rate_limit_delay > 0:
                            time.sleep(self.rate_limit_delay)

                # 2. MarocBiz IT sector feed
                for feed_url, source_label, cat in self.MAROCBIZ_FEEDS:
                    try:
                        resp = client.get(feed_url)
                        if resp.status_code == 200:
                            items = self.parse_marocbiz_html(resp.text, source_label=source_label)
                            for item in items:
                                self._maybe_append(item, collected, seen_keys, keywords, buyer_filter)
                    except Exception as e:
                        errors.append(f"{feed_url}: {e}")

            self.health.last_run_time = now_str
            self.health.items_found_last_run = len(collected)
            self.health.total_items_indexed += len(collected)
            if collected:
                self.health.status = "HEALTHY"
                self.health.last_success_time = now_str
                self.health.error_message = None
            elif errors:
                self.health.status = "WARNING"
                self.health.error_message = "; ".join(errors[:2])
            else:
                self.health.status = "HEALTHY"
                self.health.last_success_time = now_str
                self.health.error_message = None

        except Exception as e:
            self.health.status = "ERROR"
            self.health.last_run_time = now_str
            self.health.error_message = f"Press connector error: {str(e)}"
            logger.warning(f"PressJournalConnector fetch failed: {e}")

        return collected

    @staticmethod
    def _maybe_append(
        tender: Tender,
        collected: List[Tender],
        seen_keys: set,
        keywords: Optional[List[str]],
        buyer_filter: Optional[str],
    ) -> None:
        if buyer_filter and buyer_filter.lower() not in tender.buyer_name.lower() and buyer_filter.lower() not in tender.buyer_normalized.lower():
            return

        if keywords:
            haystack = f"{tender.title} {tender.reference} {tender.buyer_name}".lower()
            if not any(kw.lower() in haystack for kw in keywords):
                return
        else:
            # Avoid saturating dashboard with non-IT / commodity consumables unless priority buyer or cyber/IT score >= 25
            cat, score, subcat, kws = classify_text_rules(tender.title)
            tender.relevance_category = cat
            tender.relevance_score = score
            tender.sub_category = subcat
            tender.matched_keywords = kws
            if score < 25 and not tender.is_priority_buyer:
                return

        dedup_key = (tender.reference.lower(), tender.buyer_normalized.lower())
        if dedup_key in seen_keys:
            return
        seen_keys.add(dedup_key)
        collected.append(tender)

    def health_check(self) -> ScraperHealth:
        """Checks live reachability of authentic press & procurement sources."""
        now_str = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            with self._get_client() as client:
                r = client.get(self.AOMAROC_FEEDS[0][0])
                if r.status_code == 200:
                    parsed = self.parse_aomaroc_html(r.text)
                    self.health.status = "HEALTHY"
                    self.health.last_success_time = now_str
                    self.health.items_found_last_run = len(parsed)
                    self.health.error_message = None
                else:
                    self.health.status = "WARNING"
                    self.health.error_message = f"HTTP {r.status_code}"
        except Exception as e:
            self.health.status = "ERROR"
            self.health.error_message = str(e)
        self.health.last_run_time = now_str
        return self.health
