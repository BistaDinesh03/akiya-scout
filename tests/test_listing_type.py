"""
Tests for SALE/RENTAL listing type distinction
"""
import pytest
from datetime import datetime
from app.models import Property
from app.services.search import SearchService


def create_test_property(id_str="test-1", listing_type="SALE", **kwargs):
    """Helper to create test Property objects."""
    defaults = {
        'id': id_str,
        'title': f'Property {id_str}',
        'listing_type': listing_type,
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


class TestListingType:
    """Test listing type validation."""
    
    def test_sale_listing(self):
        """Test SALE listing type."""
        prop = create_test_property("sale-1", listing_type="SALE")
        assert prop.listing_type == "SALE"
    
    def test_rental_listing(self):
        """Test RENTAL listing type."""
        prop = create_test_property("rental-1", listing_type="RENTAL")
        assert prop.listing_type == "RENTAL"
    
    def test_invalid_listing_type(self):
        """Test invalid listing type raises error."""
        with pytest.raises(ValueError):
            create_test_property("invalid-1", listing_type="INVALID")
    
    def test_lowercase_converts_to_uppercase(self):
        """Test that lowercase listing_type is converted."""
        prop = create_test_property("lower-1", listing_type="sale")
        assert prop.listing_type == "SALE"


class TestListingTypeFiltering:
    """Test filtering by listing type."""
    
    def setup_method(self):
        self.service = SearchService()
        self.properties = [
            create_test_property("sale-1", listing_type="SALE", price=5000000),
            create_test_property("sale-2", listing_type="SALE", price=3000000),
            create_test_property("rental-1", listing_type="RENTAL", price=48000),
            create_test_property("rental-2", listing_type="RENTAL", price=42000),
        ]
    
    def test_filter_sale_only(self):
        """Test filtering SALE only."""
        result = self.service.filter_properties(self.properties, listing_type="SALE")
        assert len(result) == 2
        assert all(p.listing_type == "SALE" for p in result)
    
    def test_filter_rental_only(self):
        """Test filtering RENTAL only."""
        result = self.service.filter_properties(self.properties, listing_type="RENTAL")
        assert len(result) == 2
        assert all(p.listing_type == "RENTAL" for p in result)
    
    def test_no_filter_returns_all(self):
        """Test that no filter returns all."""
        result = self.service.filter_properties(self.properties)
        assert len(result) == 4


class TestListingTypeRanking:
    """Test ranking with SALE/RENTAL separation."""
    
    def setup_method(self):
        self.service = SearchService()
        self.properties = [
            create_test_property("sale-1", listing_type="SALE", price=5000000),
            create_test_property("sale-2", listing_type="SALE", price=3000000),
            create_test_property("rental-1", listing_type="RENTAL", price=48000),
            create_test_property("rental-2", listing_type="RENTAL", price=42000),
        ]
    
    def test_price_asc_sale_first(self):
        """Test that SALE listings come before RENTAL in price_asc."""
        result = self.service.rank_properties(self.properties, sort="price_asc")
        # First two should be SALE (sorted by price)
        assert result[0].listing_type == "SALE"
        assert result[1].listing_type == "SALE"
        # Last two should be RENTAL
        assert result[2].listing_type == "RENTAL"
        assert result[3].listing_type == "RENTAL"
        # SALE sorted by price ascending
        assert result[0].price < result[1].price
    
    def test_price_asc_never_mixes_sale_rental(self):
        """Test that monthly rent is never compared with purchase price."""
        result = self.service.rank_properties(self.properties, sort="price_asc")
        
        sale_prices = [p.price for p in result if p.listing_type == "SALE"]
        rental_prices = [p.price for p in result if p.listing_type == "RENTAL"]
        
        # Sale prices are in millions, rental in thousands
        # They should be in separate groups
        assert len(sale_prices) == 2
        assert len(rental_prices) == 2
        # No rental price should be between sale prices
        assert all(r < min(sale_prices) for r in rental_prices)
    
    def test_value_score_only_sale(self):
        """Test that value_score only includes SALE listings."""
        result = self.service.rank_properties(self.properties, sort="value_score")
        assert all(p.listing_type == "SALE" for p in result)
    
    def test_total_cost_only_sale(self):
        """Test that total_cost_asc only includes SALE listings."""
        result = self.service.rank_properties(self.properties, sort="total_cost_asc")
        assert all(p.listing_type == "SALE" for p in result)
    
    def test_renovation_only_sale(self):
        """Test that renovation_asc only includes SALE listings."""
        result = self.service.rank_properties(self.properties, sort="renovation_asc")
        assert all(p.listing_type == "SALE" for p in result)