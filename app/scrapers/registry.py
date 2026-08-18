"""
Scraper registry for Akiya Scout
"""
import logging
from typing import Dict, Type, Optional, List, Any
from app.scrapers.base import BaseScraper
from app.scrapers.sources.fukuoka_akiyabank import FukuokaAkiyaBankScraper
from app.scrapers.sources.kumamoto_akiyabank import KumamotoAkiyaBankScraper
from app.scrapers.sources.oita_akiyabank import OitaAkiyaBankScraper
from app.scrapers.sources.imari_saga import ImariSagaScraper
from app.scrapers.sources.ureshino_saga import UreshinoSagaScraper
from app.scrapers.sources.aso_kumamoto import AsoKumamotoScraper

logger = logging.getLogger(__name__)


class ScraperRegistry:
    """
    Registry for managing scraper instances.
    Allows registering and retrieving scrapers by name.
    """
    
    def __init__(self):
        self._scrapers: Dict[str, Type[BaseScraper]] = {}
        self._instances: Dict[str, BaseScraper] = {}
        self._last_scrape: Dict[str, str] = {}
        self._listing_counts: Dict[str, int] = {}
    
    def register(self, name: str, scraper_class: Type[BaseScraper]) -> None:
        """
        Register a scraper class.
        
        Args:
            name: Unique identifier for the scraper
            scraper_class: Scraper class to register
            
        Raises:
            ValueError: If name already exists
        """
        if name in self._scrapers:
            raise ValueError(f"Scraper '{name}' is already registered")
        
        self._scrapers[name] = scraper_class
        logger.info(f"Registered scraper: {name}")
    
    def get_scraper(self, name: str) -> Optional[BaseScraper]:
        """
        Get a scraper instance by name.
        Creates a new instance if not already created.
        
        Args:
            name: The name of the scraper
            
        Returns:
            Scraper instance or None if not found
            
        Raises:
            KeyError: If scraper is not registered
        """
        if name not in self._scrapers:
            raise KeyError(f"Scraper '{name}' is not registered")
        
        if name not in self._instances:
            self._instances[name] = self._scrapers[name]()
            logger.debug(f"Created new instance of scraper: {name}")
        
        return self._instances[name]
    
    def get_all_scrapers(self) -> Dict[str, BaseScraper]:
        """Get all registered scraper instances."""
        for name in self._scrapers:
            if name not in self._instances:
                self._instances[name] = self._scrapers[name]()
        
        return self._instances
    
    def list_scrapers(self) -> List[str]:
        """List all registered scraper names."""
        return list(self._scrapers.keys())
    
    def get_source_status(self) -> List[Dict[str, Any]]:
        """Get status of all registered scrapers."""
        status_list = []
        
        for name in self._scrapers:
            status = {
                "source": name,
                "municipality": self._get_municipality(name),
                "status": self._get_status(name),
                "last_scrape": self._last_scrape.get(name),
                "listing_count": self._listing_counts.get(name, 0),
            }
            status_list.append(status)
        
        return status_list
    
    def _get_municipality(self, source_name: str) -> str:
        """Get municipality name from source name."""
        mapping = {
            "saga_takeo": "Takeo City, Saga",
            "another_source": "Test Source",
            "fukuoka_akiyabank": "Fukuoka Prefecture",
            "kumamoto_akiyabank": "Kumamoto Prefecture",
            "oita_akiyabank": "Oita City, Oita",
            "imari_saga": "Imari City, Saga",
            "ureshino_saga": "Ureshino City, Saga",
            "aso_kumamoto": "Aso City, Kumamoto",
        }
        return mapping.get(source_name, "Unknown")
    
    def _get_status(self, source_name: str) -> str:
        """Get status of source."""
        if source_name == "saga_takeo":
            return "active"
        elif source_name == "aso_kumamoto":
            return "active"
        elif source_name == "another_source":
            return "test"
        elif source_name in ["imari_saga", "ureshino_saga"]:
            return "access_restricted"
        else:
            return "under_review"
    
    def update_scrape_stats(self, name: str, listing_count: int) -> None:
        """Update scrape statistics for a source."""
        from datetime import datetime, timezone
        self._last_scrape[name] = datetime.now(timezone.utc).isoformat()
        self._listing_counts[name] = listing_count
        logger.debug(f"Updated scrape stats for {name}: {listing_count} listings")
    
    def unregister(self, name: str) -> None:
        """Unregister a scraper."""
        if name not in self._scrapers:
            raise KeyError(f"Scraper '{name}' is not registered")
        
        del self._scrapers[name]
        if name in self._instances:
            self._instances[name].close()
            del self._instances[name]
        
        if name in self._last_scrape:
            del self._last_scrape[name]
        
        if name in self._listing_counts:
            del self._listing_counts[name]
        
        logger.info(f"Unregistered scraper: {name}")
    
    def clear(self) -> None:
        """Clear all registered scrapers."""
        for instance in self._instances.values():
            instance.close()
        self._scrapers.clear()
        self._instances.clear()
        self._last_scrape.clear()
        self._listing_counts.clear()
        logger.info("Cleared all scrapers")


# Global registry instance
registry = ScraperRegistry()