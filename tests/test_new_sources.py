"""
Tests for Imari and Ureshino source adapters
"""
import pytest
from app.scrapers.sources.imari_saga import ImariSagaScraper
from app.scrapers.sources.ureshino_saga import UreshinoSagaScraper
from app.scrapers.registry import ScraperRegistry


class TestImariScraper:
    """Test Imari City scraper."""
    
    def test_source_name(self):
        scraper = ImariSagaScraper()
        assert scraper.get_source_name() == "imari_saga"
        scraper.close()
    
    def test_access_restricted(self):
        """Test that scraper returns empty list (no fake data)."""
        scraper = ImariSagaScraper()
        assert scraper.scrape() == []
        assert scraper.parse("<html></html>") == []
        scraper.close()
    
    def test_no_fake_data(self):
        """Test that scraper doesn't produce fake properties."""
        scraper = ImariSagaScraper()
        properties = scraper.scrape()
        assert len(properties) == 0
        scraper.close()


class TestUreshinoScraper:
    """Test Ureshino City scraper."""
    
    def test_source_name(self):
        scraper = UreshinoSagaScraper()
        assert scraper.get_source_name() == "ureshino_saga"
        scraper.close()
    
    def test_access_restricted(self):
        """Test that scraper returns empty list (no fake data)."""
        scraper = UreshinoSagaScraper()
        assert scraper.scrape() == []
        assert scraper.parse("<html></html>") == []
        scraper.close()
    
    def test_no_fake_data(self):
        """Test that scraper doesn't produce fake properties."""
        scraper = UreshinoSagaScraper()
        properties = scraper.scrape()
        assert len(properties) == 0
        scraper.close()


class TestRegistryWithNewSources:
    """Test registry includes new sources."""
    
    def test_registry_includes_imari(self):
        registry = ScraperRegistry()
        registry.register("imari_saga", ImariSagaScraper)
        assert "imari_saga" in registry.list_scrapers()
    
    def test_registry_includes_ureshino(self):
        registry = ScraperRegistry()
        registry.register("ureshino_saga", UreshinoSagaScraper)
        assert "ureshino_saga" in registry.list_scrapers()
    
    def test_access_restricted_status(self):
        registry = ScraperRegistry()
        registry.register("imari_saga", ImariSagaScraper)
        registry.register("ureshino_saga", UreshinoSagaScraper)
        
        status_list = registry.get_source_status()
        imari_status = [s for s in status_list if s["source"] == "imari_saga"][0]
        ureshino_status = [s for s in status_list if s["source"] == "ureshino_saga"][0]
        
        assert imari_status["status"] == "access_restricted"
        assert ureshino_status["status"] == "access_restricted"