"""
Base Connector Interface for CyberRFP Maroc
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.models import Tender, ScraperHealth


class BaseConnector(ABC):
    def __init__(self, connector_id: str, name: str, base_url: str):
        self.connector_id = connector_id
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.health = ScraperHealth(
            connector_id=connector_id,
            name=name,
            url=base_url,
            status="HEALTHY"
        )

    @abstractmethod
    def fetch_tenders(
        self,
        max_pages: int = 1,
        keywords: Optional[List[str]] = None,
        buyer_filter: Optional[str] = None
    ) -> List[Tender]:
        """Fetch and parse tenders from this source."""
        pass

    @abstractmethod
    def health_check(self) -> ScraperHealth:
        """Run connectivity and selector health check."""
        pass
