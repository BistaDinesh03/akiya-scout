"""
Ureshino City Akiya Bank scraper (Saga Prefecture)
Source: https://www.city.ureshino.lg.jp/kurashi/teiju/akiya/
Status: ACCESS_RESTRICTED - Data hosted on scinex.co.jp (returns 403 for direct requests)
"""
import logging
from typing import List, Dict, Any, Optional
from app.scrapers.base import HTMLScraper, ParseError
from app.models import Property

logger = logging.getLogger(__name__)


class UreshinoSagaScraper(HTMLScraper):
    """
    Scraper for Ureshino City Akiya Bank.
    Status: Data confirmed to exist but hosted on restricted platform.
    """
    
    BASE_URL = "https://www.city.ureshino.lg.jp"
    SOURCE_STATUS = "access_restricted"
    
    def get_source_name(self) -> str:
        """Return the source name."""
        return "ureshino_saga"
    
    def fetch(self, url: str) -> str:
        """
        Fetch content from URL.
        Data is on scinex.co.jp which returns 403 for direct access.
        """
        logger.warning(f"[{self.get_source_name()}] Access restricted - data on scinex.co.jp")
        return ""
    
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse HTML content - not available."""
        logger.warning(f"[{self.get_source_name()}] Access restricted - parse unavailable")
        return []
    
    def normalize(self, raw_data: Dict[str, Any]) -> Property:
        """Normalize raw property data - not available."""
        raise ParseError(f"[{self.get_source_name()}] Access restricted")
    
    def scrape(self, url: str = None) -> List[Property]:
        """Scrape properties - access restricted."""
        logger.warning(f"[{self.get_source_name()}] Access restricted - returning empty list")
        return []