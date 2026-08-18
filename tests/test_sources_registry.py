"""
Tests for source registry and additional sources
"""
import pytest
from app.scrapers.registry import ScraperRegistry
from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.scrapers.sources.another_source import AnotherSourceScraper
from app.scrapers.sources.fukuoka_akiyabank import FukuokaAkiyaBankScraper
from app.scrapers.sources.kumamoto_akiyabank import KumamotoAkiyaBankScraper
from app.scrapers.sources.oita_akiyabank import OitaAkiyaBankScraper


class TestSourceRegistry:
    """Test source registry with all sources."""
    
    def setup_method(self):
        self.registry = ScraperRegistry()
        self.registry.register("saga_takeo", SagaTakeoScraper)
        self.registry.register("another_source", AnotherSourceScraper)
        self.registry.register("fukuoka_akiyabank", FukuokaAkiyaBankScraper)
        self.registry.register("kumamoto_akiyabank", KumamotoAkiyaBankScraper)
        self.registry.register("oita_akiyabank", OitaAkiyaBankScraper)
    
    def test_all_sources_registered(self):
        """Test that all sources are registered."""
        scrapers = self.registry.list_scrapers()
        assert "saga_takeo" in scrapers
        assert "another_source" in scrapers
        assert "fukuoka_akiyabank" in scrapers
        assert "kumamoto_akiyabank" in scrapers
        assert "oita_akiyabank" in scrapers
        assert len(scrapers) == 5
    
    def test_source_status(self):
        """Test that source status returns correct info."""
        status_list = self.registry.get_source_status()
        
        assert len(status_list) == 5
        
        for status in status_list:
            assert "source" in status
            assert "municipality" in status
            assert "status" in status
            assert "last_scrape" in status
            assert "listing_count" in status
    
    def test_saga_takeo_active(self):
        """Test that saga_takeo is active."""
        status_list = self.registry.get_source_status()
        
        saga_status = [s for s in status_list if s["source"] == "saga_takeo"][0]
        assert saga_status["status"] == "active"
    
    def test_under_review_sources(self):
        """Test that unreviewed sources are marked correctly."""
        status_list = self.registry.get_source_status()
        
        for source_name in ["fukuoka_akiyabank", "kumamoto_akiyabank", "oita_akiyabank"]:
            source_status = [s for s in status_list if s["source"] == source_name][0]
            assert source_status["status"] == "under_review"


class TestUnderReviewScrapers:
    """Test that under-review scrapers behave correctly."""
    
    def test_fukuoka_scraper(self):
        """Test Fukuoka scraper returns empty list."""
        scraper = FukuokaAkiyaBankScraper()
        assert scraper.get_source_name() == "fukuoka_akiyabank"
        assert scraper.scrape() == []
        assert scraper.parse("<html></html>") == []
        scraper.close()
    
    def test_kumamoto_scraper(self):
        """Test Kumamoto scraper returns empty list."""
        scraper = KumamotoAkiyaBankScraper()
        assert scraper.get_source_name() == "kumamoto_akiyabank"
        assert scraper.scrape() == []
        assert scraper.parse("<html></html>") == []
        scraper.close()
    
    def test_oita_scraper(self):
        """Test Oita scraper returns empty list."""
        scraper = OitaAkiyaBankScraper()
        assert scraper.get_source_name() == "oita_akiyabank"
        assert scraper.scrape() == []
        assert scraper.parse("<html></html>") == []
        scraper.close()