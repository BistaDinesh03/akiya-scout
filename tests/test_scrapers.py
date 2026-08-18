"""
Tests for scraper architecture
"""
import pytest
from pathlib import Path
from app.scrapers.base import BaseScraper, HTMLScraper, ScraperError, FetchError, ParseError
from app.scrapers.registry import ScraperRegistry, registry
from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.scrapers.sources.another_source import AnotherSourceScraper
from app.models import Property

# Fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """Load test fixture HTML file."""
    fixture_path = FIXTURES_DIR / filename
    return fixture_path.read_text(encoding='utf-8')


class TestBaseScraper:
    """Test the base scraper interface."""
    
    def test_base_scraper_is_abstract(self):
        """Test that BaseScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseScraper()
    
    def test_html_scraper_is_abstract(self):
        """Test that HTMLScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            HTMLScraper()
    
    def test_scraper_error_exceptions(self):
        """Test that scraper exceptions are properly defined."""
        assert issubclass(ScraperError, Exception)
        assert issubclass(FetchError, ScraperError)
        assert issubclass(ParseError, ScraperError)


class TestAnotherSourceScraper:
    """Test the Another Source scraper."""
    
    def setup_method(self):
        self.scraper = AnotherSourceScraper()
        self.html = load_fixture("another_source_sample.html")
    
    def teardown_method(self):
        self.scraper.close()
    
    def test_get_source_name(self):
        """Test that source name is correct."""
        assert self.scraper.get_source_name() == "another_source"
    
    def test_parse_returns_list(self):
        """Test that parse returns a list."""
        result = self.scraper.parse(self.html)
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_parse_extracts_correct_data(self):
        """Test that parse extracts correct data."""
        result = self.scraper.parse(self.html)
        
        first_property = result[0]
        assert first_property['id'] == 'as-001'
        assert first_property['title'] == 'Countryside Farmhouse'
        assert first_property['prefecture'] == 'Fukuoka'
        assert first_property['municipality'] == 'Yame'
    
    def test_normalize_creates_property(self):
        """Test that normalize creates Property objects."""
        raw_data = {
            'id': 'as-001',
            'title': 'Test Property',
            'price': '¥2,800,000円',
            'prefecture': 'Fukuoka',
            'municipality': 'Yame',
            'area': 'Kuroki',
            'land_size_m2': '400m²',
            'building_size_m2': '150m²',
            'build_year': '1978',
            'rooms': '5DK',
            'structure': 'Wooden',
            'floors': '2',
            'parking': '2 cars',
            'description': 'Test description',
            'source_url': 'https://example.org/test',
            'image_url': 'https://example.org/image.jpg',
            'latitude': '33.2035',
            'longitude': '130.6543'
        }
        
        property_obj = self.scraper.normalize(raw_data)
        
        assert isinstance(property_obj, Property)
        assert property_obj.id == 'as-001'
        assert property_obj.price == 2800000
        assert property_obj.land_size_m2 == 400.0
        assert property_obj.building_size_m2 == 150.0
        assert property_obj.build_year == 1978
        assert property_obj.latitude == 33.2035
        assert property_obj.longitude == 130.6543
        assert property_obj.source_name == 'another_source'
    
    def test_normalize_handles_missing_data(self):
        """Test that normalize handles missing data gracefully."""
        raw_data = {
            'id': 'as-003',
            'title': 'Minimal Property',
            'source_url': 'https://example.org/minimal'
        }
        
        property_obj = self.scraper.normalize(raw_data)
        
        assert property_obj.price is None
        assert property_obj.land_size_m2 is None
        assert property_obj.building_size_m2 is None
        assert property_obj.latitude is None
        assert property_obj.longitude is None
    
    def test_scrape_with_fixture(self):
        """Test complete scraping pipeline with fixture HTML."""
        # Mock the fetch method to return fixture HTML
        self.scraper.fetch = lambda url: self.html
        
        properties = self.scraper.scrape("https://example.org/test")
        
        assert len(properties) == 2
        assert all(isinstance(p, Property) for p in properties)
        assert properties[0].source_name == 'another_source'


class TestScraperRegistry:
    """Test the scraper registry."""
    
    def setup_method(self):
        self.test_registry = ScraperRegistry()
    
    def test_register_scraper(self):
        """Test registering a scraper."""
        self.test_registry.register("saga_takeo", SagaTakeoScraper)
        assert "saga_takeo" in self.test_registry.list_scrapers()
    
    def test_register_duplicate(self):
        """Test that registering duplicate raises error."""
        self.test_registry.register("saga_takeo", SagaTakeoScraper)
        with pytest.raises(ValueError):
            self.test_registry.register("saga_takeo", SagaTakeoScraper)
    
    def test_get_scraper(self):
        """Test getting a scraper instance."""
        self.test_registry.register("saga_takeo", SagaTakeoScraper)
        scraper = self.test_registry.get_scraper("saga_takeo")
        assert isinstance(scraper, SagaTakeoScraper)
    
    def test_get_unregistered_scraper(self):
        """Test getting unregistered scraper raises error."""
        with pytest.raises(KeyError):
            self.test_registry.get_scraper("nonexistent")
    
    def test_list_scrapers(self):
        """Test listing scrapers."""
        self.test_registry.register("saga_takeo", SagaTakeoScraper)
        self.test_registry.register("another_source", AnotherSourceScraper)
        
        scrapers = self.test_registry.list_scrapers()
        assert "saga_takeo" in scrapers
        assert "another_source" in scrapers
        assert len(scrapers) == 2
    
    def test_global_registry(self):
        """Test that global registry exists."""
        assert isinstance(registry, ScraperRegistry)