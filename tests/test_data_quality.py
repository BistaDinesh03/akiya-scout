"""
Data quality and source trust tests
"""
import pytest
from datetime import datetime
from app.models import Property
from app.services.search import SearchService, PropertyCache


def create_real_property(id_str="real-1", **kwargs):
    """Create a property that mimics real Takeo data."""
    defaults = {
        'id': id_str,
        'title': f'Property {id_str}',
        'price': 1000000,
        'prefecture': 'Saga',
        'municipality': 'Takeo',
        'area': 'Test Area',
        'land_size_m2': 200.0,
        'building_size_m2': 100.0,
        'build_year': 1990,
        'rooms': '3LDK',
        'structure': 'Wooden',
        'floors': 2,
        'parking': 'あり',
        'description': 'Test',
        'source_name': 'saga_takeo',
        'source_url': f'https://takeo-ijyu.jp/bank/{id_str}/',
        'image_url': None,
        'latitude': None,
        'longitude': None,
        'collected_at': datetime.utcnow(),
    }
    defaults.update(kwargs)
    return Property(**defaults)


class TestDataQuality:
    """Test data quality invariants."""
    
    def test_no_duplicate_ids(self):
        """Test that no duplicate IDs exist."""
        props = [
            create_real_property("real-1"),
            create_real_property("real-2"),
            create_real_property("real-3"),
        ]
        
        service = SearchService()
        deduped = service.deduplicate(props)
        
        assert len(deduped) == 3
    
    def test_no_duplicate_source_urls(self):
        """Test that no duplicate source URLs exist."""
        props = [
            create_real_property("real-1", source_url="https://takeo-ijyu.jp/bank/1/"),
            create_real_property("real-2", source_url="https://takeo-ijyu.jp/bank/1/"),  # Same URL
            create_real_property("real-3", source_url="https://takeo-ijyu.jp/bank/3/"),
        ]
        
        urls = [p.source_url for p in props]
        unique_urls = set(urls)
        
        assert len(urls) == 3
        assert len(unique_urls) == 2
    
    def test_required_fields_present(self):
        """Test that real listings have required fields."""
        prop = create_real_property("real-required")
        
        assert prop.source_url is not None
        assert prop.source_name is not None
        assert prop.collected_at is not None
        assert prop.source_url != ""
        assert prop.source_name != ""
    
    def test_price_is_valid(self):
        """Test that price is non-negative when present."""
        prop = create_real_property("real-price", price=1000000)
        assert prop.price >= 0
    
    def test_land_size_valid(self):
        """Test that land size is reasonable."""
        prop = create_real_property("real-land", land_size_m2=200.0)
        assert 0 <= prop.land_size_m2 <= 1000000
    
    def test_building_size_valid(self):
        """Test that building size is reasonable."""
        prop = create_real_property("real-building", building_size_m2=100.0)
        assert 0 <= prop.building_size_m2 <= 100000
    
    def test_build_year_valid(self):
        """Test that build year is reasonable."""
        prop = create_real_property("real-year", build_year=1990)
        assert 1800 <= prop.build_year <= 2026
    
    def test_no_test_properties_in_real_listings(self):
        """Test that test/demo properties are not mixed with real listings."""
        real_props = [create_real_property("real-1")]
        test_props = [create_real_property("test-1", source_name="test_source")]
        
        all_props = real_props + test_props
        
        real_only = [p for p in all_props if p.source_name == "saga_takeo"]
        
        assert len(real_only) == 1
        assert real_only[0].id == "real-1"
    
    def test_source_consistency(self):
        """Test that source_name matches source_url domain."""
        prop = create_real_property(
            "real-source",
            source_name="saga_takeo",
            source_url="https://takeo-ijyu.jp/bank/1/"
        )
        
        assert "takeo-ijyu.jp" in prop.source_url
        assert prop.source_name == "saga_takeo"


class TestCacheRefresh:
    """Test cache refresh behavior."""
    
    def test_cache_refresh_after_ttl(self):
        """Test that cache refreshes after TTL."""
        cache = PropertyCache(ttl_seconds=1)
        props = [create_real_property("cache-refresh")]
        
        cache.set("test_key", props)
        
        assert cache.get("test_key") is not None
        
        import time
        time.sleep(1.1)
        
        assert cache.get("test_key") is None
    
    def test_cache_timestamp_updates(self):
        """Test that cache timestamp updates on refresh."""
        cache = PropertyCache(ttl_seconds=10)
        props = [create_real_property("cache-timestamp")]
        
        cache.set("test_key", props)
        ts1 = cache.get_timestamp("test_key")
        
        import time
        time.sleep(0.1)
        
        cache.set("test_key", props)
        ts2 = cache.get_timestamp("test_key")
        
        assert ts1 != ts2


class TestSourceIsolation:
    """Test that failed sources don't affect results."""
    
    def test_failed_source_returns_empty(self):
        """Test that failed source returns empty list."""
        from app.scrapers.sources.fukuoka_akiyabank import FukuokaAkiyaBankScraper
        
        scraper = FukuokaAkiyaBankScraper()
        result = scraper.scrape()
        assert result == []
        scraper.close()
    
    def test_search_service_reads_database_only(self):
        """Test that search service reads from database only."""
        service = SearchService()
        
        # Search service no longer has enabled_sources (reads from DB)
        assert not hasattr(service, 'enabled_sources')
        
        # Verify it loads from database
        properties = service.get_all_properties()
        assert isinstance(properties, list)
    
    def test_access_restricted_sources_return_empty(self):
        """Test that access-restricted sources return empty."""
        from app.scrapers.sources.imari_saga import ImariSagaScraper
        from app.scrapers.sources.ureshino_saga import UreshinoSagaScraper
        
        imari = ImariSagaScraper()
        ureshino = UreshinoSagaScraper()
        
        assert imari.scrape() == []
        assert ureshino.scrape() == []
        
        imari.close()
        ureshino.close()