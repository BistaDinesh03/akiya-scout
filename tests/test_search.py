"""
Tests for search service
"""
import pytest
import time
from datetime import datetime, timedelta
from app.services.search import SearchService, PropertyCache
from app.models import Property


def create_test_property(id_str="test-1", **kwargs):
    """Helper to create test Property objects."""
    defaults = {
        'id': id_str,
        'title': f'Property {id_str}',
        'price': 5000000,
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
        'description': 'Test property',
        'source_name': 'test_source',
        'source_url': f'https://example.com/{id_str}',
        'image_url': None,
        'latitude': None,
        'longitude': None,
        'collected_at': datetime.utcnow(),
    }
    defaults.update(kwargs)
    return Property(**defaults)


class TestPropertyCache:
    """Test the property cache."""
    
    def test_cache_set_and_get(self):
        """Test that cache stores and retrieves data."""
        cache = PropertyCache(ttl_seconds=10)
        properties = [create_test_property("cache-1")]
        
        cache.set("test_key", properties)
        result = cache.get("test_key")
        
        assert result is not None
        assert len(result) == 1
        assert result[0].id == "cache-1"
    
    def test_cache_expires(self):
        """Test that cache expires after TTL."""
        cache = PropertyCache(ttl_seconds=1)
        properties = [create_test_property("cache-expire")]
        
        cache.set("test_key", properties)
        
        time.sleep(1.1)
        
        result = cache.get("test_key")
        assert result is None
    
    def test_cache_clear(self):
        """Test that cache can be cleared."""
        cache = PropertyCache(ttl_seconds=10)
        properties = [create_test_property("cache-clear")]
        
        cache.set("test_key", properties)
        cache.clear()
        
        result = cache.get("test_key")
        assert result is None
    
    def test_cache_get_timestamp(self):
        """Test that cache returns timestamp."""
        cache = PropertyCache(ttl_seconds=10)
        properties = [create_test_property("cache-timestamp")]
        
        cache.set("test_key", properties)
        timestamp = cache.get_timestamp("test_key")
        
        assert timestamp is not None


class TestDeduplication:
    """Test deduplication functionality."""
    
    def test_deduplicate_removes_duplicates(self):
        """Test that duplicates are removed."""
        service = SearchService()
        prop1 = create_test_property("dup-1")
        prop2 = create_test_property("dup-1")
        prop3 = create_test_property("dup-2")
        
        properties = [prop1, prop2, prop3]
        deduped = service.deduplicate(properties)
        
        assert len(deduped) == 2
        assert deduped[0].id == "dup-1"
        assert deduped[1].id == "dup-2"
    
    def test_deduplicate_empty_list(self):
        """Test that empty list works."""
        service = SearchService()
        assert service.deduplicate([]) == []


class TestFiltering:
    """Test property filtering."""
    
    def setup_method(self):
        self.service = SearchService()
        self.properties = [
            create_test_property("filter-1", price=3000000, land_size_m2=150.0, building_size_m2=80.0, rooms="3LDK", parking="あり"),
            create_test_property("filter-2", price=5000000, land_size_m2=250.0, building_size_m2=120.0, rooms="4LDK", parking="あり"),
            create_test_property("filter-3", price=8000000, land_size_m2=400.0, building_size_m2=180.0, rooms="5DK", parking="なし"),
            create_test_property("filter-4", price=None, land_size_m2=None, building_size_m2=None, rooms=None, parking=None),
        ]
    
    def test_filter_by_max_price(self):
        """Test filtering by maximum price."""
        result = self.service.filter_properties(self.properties, max_price=6000000)
        assert len(result) == 2
        assert all(p.price <= 6000000 for p in result if p.price is not None)
    
    def test_filter_by_min_land(self):
        """Test filtering by minimum land size."""
        result = self.service.filter_properties(self.properties, min_land=200.0)
        assert len(result) == 2
        assert all(p.land_size_m2 >= 200.0 for p in result if p.land_size_m2 is not None)
    
    def test_filter_by_min_building(self):
        """Test filtering by minimum building size."""
        result = self.service.filter_properties(self.properties, min_building=100.0)
        assert len(result) == 2
        assert all(p.building_size_m2 >= 100.0 for p in result if p.building_size_m2 is not None)
    
    def test_filter_by_prefecture(self):
        """Test filtering by prefecture."""
        result = self.service.filter_properties(self.properties, prefecture="Saga")
        assert len(result) == 4
    
    def test_filter_by_municipality(self):
        """Test filtering by municipality."""
        result = self.service.filter_properties(self.properties, municipality="Takeo")
        assert len(result) == 4
    
    def test_filter_by_min_rooms(self):
        """Test filtering by minimum rooms."""
        result = self.service.filter_properties(self.properties, min_rooms=4)
        assert len(result) == 2
    
    def test_filter_by_parking(self):
        """Test filtering by parking."""
        result = self.service.filter_properties(self.properties, parking="yes")
        assert len(result) == 2
        assert all('あり' in p.parking for p in result if p.parking is not None)
    
    def test_filter_combined(self):
        """Test combined filters."""
        result = self.service.filter_properties(
            self.properties,
            max_price=6000000,
            min_land=200.0,
            min_rooms=4,
        )
        assert len(result) == 1
        assert result[0].id == "filter-2"
    
    def test_filter_real_listings_only(self):
        """Test filtering for real listings only."""
        # Property with empty source_url (not a real listing)
        self.properties.append(
            create_test_property("filter-5", source_url="")
        )
        result = self.service.filter_properties(self.properties, real_listings_only=True)
        assert len(result) == 4
        assert all(p.source_url for p in result)


class TestRanking:
    """Test property ranking."""
    
    def setup_method(self):
        self.service = SearchService()
        self.properties = [
            create_test_property("rank-1", price=5000000, land_size_m2=250.0),
            create_test_property("rank-2", price=3000000, land_size_m2=150.0),
            create_test_property("rank-3", price=8000000, land_size_m2=400.0),
        ]
    
    def test_rank_by_price_asc(self):
        """Test ranking by price ascending."""
        result = self.service.rank_properties(self.properties, sort="price_asc")
        assert result[0].price == 3000000
        assert result[1].price == 5000000
        assert result[2].price == 8000000
    
    def test_rank_by_price_desc(self):
        """Test ranking by price descending."""
        result = self.service.rank_properties(self.properties, sort="price_desc")
        assert result[0].price == 8000000
        assert result[1].price == 5000000
        assert result[2].price == 3000000
    
    def test_rank_by_land_asc(self):
        """Test ranking by land size ascending."""
        result = self.service.rank_properties(self.properties, sort="land_asc")
        assert result[0].land_size_m2 == 150.0
        assert result[1].land_size_m2 == 250.0
        assert result[2].land_size_m2 == 400.0
    
    def test_rank_by_land_desc(self):
        """Test ranking by land size descending."""
        result = self.service.rank_properties(self.properties, sort="land_desc")
        assert result[0].land_size_m2 == 400.0
        assert result[1].land_size_m2 == 250.0
        assert result[2].land_size_m2 == 150.0
    
    def test_rank_by_value_score(self):
        """Test ranking by value score."""
        result = self.service.rank_properties(self.properties, sort="value_score")
        assert len(result) == 3
    
    def test_rank_by_renovation_asc(self):
        """Test ranking by renovation cost."""
        result = self.service.rank_properties(self.properties, sort="renovation_asc")
        assert len(result) == 3
    
    def test_rank_by_total_cost_asc(self):
        """Test ranking by total cost."""
        result = self.service.rank_properties(self.properties, sort="total_cost_asc")
        assert len(result) == 3