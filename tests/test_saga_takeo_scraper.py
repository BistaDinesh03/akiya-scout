"""
Tests for Saga Takeo scraper with real data format
"""
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.models import Property

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """Load test fixture HTML file."""
    fixture_path = FIXTURES_DIR / filename
    return fixture_path.read_text(encoding='utf-8')


class TestSagaTakeoScraper:
    """Test Saga Takeo scraper with realistic data."""
    
    def setup_method(self):
        self.scraper = SagaTakeoScraper()
        self.html = load_fixture("takeo_property_sample.html")
    
    def teardown_method(self):
        self.scraper.close()
    
    def test_get_source_name(self):
        """Test source name."""
        assert self.scraper.get_source_name() == "saga_takeo"
    
    def test_parse_extracts_title(self):
        """Test that parse extracts title correctly."""
        result = self.scraper.parse(self.html)
        assert len(result) == 1
        assert result[0]['title'] == '№2602　買う／宅地／山内町大字犬走'
    
    def test_parse_extracts_price(self):
        """Test that parse extracts price in yen."""
        result = self.scraper.parse(self.html)
        # 230万円 = 2,300,000 yen
        assert result[0]['price'] == 2300000
    
    def test_parse_extracts_location(self):
        """Test that parse extracts location."""
        result = self.scraper.parse(self.html)
        assert result[0]['prefecture'] == 'Saga'
        assert result[0]['municipality'] == 'Takeo'
        assert result[0]['area'] == '大字犬走'
    
    def test_parse_extracts_land_size(self):
        """Test that parse extracts land size."""
        result = self.scraper.parse(self.html)
        assert result[0]['land_size_m2'] == 580.0
    
    def test_parse_handles_missing_fields(self):
        """Test that parse handles missing fields gracefully."""
        result = self.scraper.parse(self.html)
        raw_data = result[0]
        
        # These fields are '-' in the fixture
        assert raw_data['rooms'] is None
        assert raw_data['build_year'] is None
        assert raw_data['structure'] is None
        assert raw_data['parking'] is None
    
    def test_parse_extracts_image_url(self):
        """Test that parse extracts image URL."""
        result = self.scraper.parse(self.html)
        assert result[0]['image_url'] is not None
        assert 'takeo-ijyu.jp' in result[0]['image_url']
    
    def test_normalize_creates_property(self):
        """Test that normalize creates a Property object."""
        raw_data = {
            'title': '№2602　買う／宅地／山内町大字犬走',
            'price': 2300000,
            'prefecture': 'Saga',
            'municipality': 'Takeo',
            'area': '大字犬走',
            'land_size_m2': 580.0,
            'building_size_m2': None,
            'build_year': None,
            'rooms': None,
            'structure': None,
            'floors': None,
            'parking': None,
            'description': '南向きの土地で、日当たり良好',
            'source_url': 'https://takeo-ijyu.jp/bank/2781/',
            'image_url': 'https://takeo-ijyu.jp/wp-content/uploads/test.jpg',
            'latitude': None,
            'longitude': None,
        }
        
        property_obj = self.scraper.normalize(raw_data)
        
        assert isinstance(property_obj, Property)
        assert property_obj.id == 'takeo-2602'
        assert property_obj.price == 2300000
        assert property_obj.land_size_m2 == 580.0
        assert property_obj.source_name == 'saga_takeo'
        assert property_obj.source_url == 'https://takeo-ijyu.jp/bank/2781/'
    
    def test_normalize_extracts_id_from_title(self):
        """Test that normalize extracts ID from title."""
        raw_data = {
            'title': '№1234　買う／宅地／山内町大字犬走',
            'source_url': 'https://takeo-ijyu.jp/bank/1234/',
        }
        
        property_obj = self.scraper.normalize(raw_data)
        assert property_obj.id == 'takeo-1234'
    
    def test_normalize_handles_missing_title(self):
        """Test that normalize handles missing title."""
        raw_data = {
            'source_url': 'https://takeo-ijyu.jp/bank/9999/',
        }
        
        property_obj = self.scraper.normalize(raw_data)
        assert property_obj.id is not None
        assert property_obj.source_url == 'https://takeo-ijyu.jp/bank/9999/'
    
    def test_extract_price_handles_man_yen(self):
        """Test price extraction from 万円 format."""
        lines = ['希望価格', '230', '万円']
        price = self.scraper._extract_price(lines)
        assert price == 2300000
    
    def test_extract_price_handles_direct_yen(self):
        """Test price extraction from direct yen format."""
        lines = ['希望価格', '2,300,000', '円']
        price = self.scraper._extract_price(lines)
        assert price == 2300000
    
    def test_extract_price_returns_none_if_missing(self):
        """Test that price extraction returns None if missing."""
        lines = ['希望価格', '-']
        price = self.scraper._extract_price(lines)
        assert price is None
    
    def test_scrape_with_mock_api(self):
        """Test complete scrape with mocked API responses."""
        # Mock API response
        mock_listing = {
            'id': 2781,
            'title': {'rendered': '№2602　買う／宅地／山内町大字犬走'},
            'link': 'https://takeo-ijyu.jp/bank/2781/',
            'excerpt': {'rendered': 'Test excerpt'},
            '_embedded': {}
        }
        
        # Mock methods using unittest.mock
        with patch.object(self.scraper, 'fetch_listings', return_value=[mock_listing]):
            with patch.object(self.scraper, 'fetch', return_value=self.html):
                properties = self.scraper.scrape()
                
                assert len(properties) == 1
                assert isinstance(properties[0], Property)
                assert properties[0].source_name == 'saga_takeo'
                assert properties[0].price == 2300000