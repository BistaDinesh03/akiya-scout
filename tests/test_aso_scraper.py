"""
Tests for Aso City scraper
"""
import pytest
from pathlib import Path
from app.scrapers.sources.aso_kumamoto import AsoKumamotoScraper
from app.models import Property

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """Load test fixture HTML file."""
    return (FIXTURES_DIR / filename).read_text(encoding='utf-8')


class TestAsoScraper:
    """Test Aso City scraper."""
    
    def setup_method(self):
        self.scraper = AsoKumamotoScraper()
        self.html = load_fixture("aso_property_sample.html")
    
    def teardown_method(self):
        self.scraper.close()
    
    def test_source_name(self):
        """Test source name."""
        assert self.scraper.get_source_name() == "aso_kumamoto"
    
    def test_parse_extracts_title(self):
        """Test title extraction."""
        result = self.scraper.parse(self.html)
        assert len(result) == 1
        assert '578' in result[0]['title']
    
    def test_parse_extracts_price(self):
        """Test price extraction."""
        result = self.scraper.parse(self.html)
        # 42,000円/月 rental
        assert result[0]['price'] == 42000
    
    def test_parse_extracts_location(self):
        """Test location extraction."""
        result = self.scraper.parse(self.html)
        assert result[0]['prefecture'] == 'Kumamoto'
        assert result[0]['municipality'] == 'Aso'
        assert '黒川' in result[0]['area']
    
    def test_parse_extracts_size(self):
        """Test size extraction."""
        result = self.scraper.parse(self.html)
        assert result[0]['land_size_m2'] == 40.0
    
    def test_parse_extracts_structure_rooms(self):
        """Test structure/rooms extraction."""
        result = self.scraper.parse(self.html)
        assert result[0]['structure'] == '木造'
        assert result[0]['rooms'] == '2DK'
    
    def test_parse_extracts_year(self):
        """Test year extraction."""
        result = self.scraper.parse(self.html)
        # 築33年 = 2026 - 33 = 1993
        assert result[0]['build_year'] == 1993
    
    def test_normalize_creates_property(self):
        """Test normalization."""
        raw_data = {
            'title': '【物件番号578号】黒川の戸建貸家（2DK）',
            'price': 42000,
            'prefecture': 'Kumamoto',
            'municipality': 'Aso',
            'area': '阿蘇市黒川字子安川原1417-6',
            'land_size_m2': 40.0,
            'structure': '木造',
            'rooms': '2DK',
            'build_year': 1993,
            'source_url': 'https://www.city.aso.kumamoto.jp/akiya/578/',
        }
        
        prop = self.scraper.normalize(raw_data)
        
        assert isinstance(prop, Property)
        assert prop.id == 'aso-578'
        assert prop.source_name == 'aso_kumamoto'
        assert prop.price == 42000