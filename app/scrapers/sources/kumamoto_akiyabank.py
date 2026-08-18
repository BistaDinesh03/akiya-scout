"""
Kumamoto Akiya Bank scraper (placeholder - access under review)
"""
import logging
from typing import List, Dict, Any, Optional
from app.scrapers.base import HTMLScraper, ParseError
from app.models import Property

logger = logging.getLogger(__name__)


class KumamotoAkiyaBankScraper(HTMLScraper):
    """
    Scraper for Kumamoto municipal Akiya bank.
    Status: Access under review - SSL/TLS verification needed.
    """
    
    BASE_URL = "https://www.pref.kumamoto.lg.jp"
    SOURCE_STATUS = "under_review"
    
    def get_source_name(self) -> str:
        """Return the source name."""
        return "kumamoto_akiyabank"
    
    def fetch(self, url: str) -> str:
        """
        Fetch content from URL.
        Currently disabled - source access under review.
        """
        logger.warning(f"[{self.get_source_name()}] Source access under review - fetch disabled")
        return ""
    
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content.
        Currently returns empty list - source access under review.
        """
        logger.warning(f"[{self.get_source_name()}] Source access under review - parse disabled")
        return []
    
    def normalize(self, raw_data: Dict[str, Any]) -> Property:
        """
        Normalize raw property data.
        Currently raises ParseError - source access under review.
        """
        raise ParseError(f"[{self.get_source_name()}] Source access under review")
    
    def scrape(self, url: str = None) -> List[Property]:
        """
        Scrape properties.
        Currently returns empty list - source access under review.
        """
        logger.warning(f"[{self.get_source_name()}] Source access under review - scrape disabled")
        return []