"""
Tests for Pydantic models
"""
import pytest
from datetime import datetime
from app.models import Property


def create_valid_property():
    """Helper function to create a valid property for testing."""
    return Property(
        id="test-123",
        title="Beautiful Akiya in Nagano",
        source_name="Test Source",
        source_url="https://example.com/property/123"
    )


def test_property_required_fields_only():
    """Test that a property can be created with only required fields."""
    property = create_valid_property()
    
    assert property.id == "test-123"
    assert property.title == "Beautiful Akiya in Nagano"
    assert property.source_name == "Test Source"
    assert property.source_url == "https://example.com/property/123"
    
    # All optional fields should be None
    assert property.price is None
    assert property.prefecture is None
    assert property.municipality is None
    assert property.area is None
    assert property.land_size_m2 is None
    assert property.building_size_m2 is None
    assert property.build_year is None
    assert property.rooms is None
    assert property.structure is None
    assert property.floors is None
    assert property.parking is None
    assert property.description is None
    assert property.image_url is None
    assert property.latitude is None
    assert property.longitude is None


def test_property_with_all_fields():
    """Test that a property can be created with all fields."""
    property = Property(
        id="test-456",
        title="Full Property",
        price=5000000,
        prefecture="Nagano",
        municipality="Matsumoto",
        area="Azumino",
        land_size_m2=300.5,
        building_size_m2=120.75,
        build_year=1985,
        rooms="4LDK",
        structure="Wooden",
        floors=2,
        parking="Available",
        description="A beautiful traditional Japanese house",
        source_name="Test Source",
        source_url="https://example.com/property/456",
        image_url="https://example.com/images/456.jpg",
        latitude=36.2381,
        longitude=137.9719,
        collected_at=datetime(2024, 1, 1, 12, 0, 0)
    )
    
    assert property.price == 5000000
    assert isinstance(property.price, int)
    assert property.land_size_m2 == 300.5
    assert isinstance(property.land_size_m2, float)
    assert property.building_size_m2 == 120.75
    assert isinstance(property.building_size_m2, float)
    assert property.build_year == 1985
    assert isinstance(property.build_year, int)
    assert property.latitude == 36.2381
    assert property.longitude == 137.9719


def test_property_price_must_be_integer():
    """Test that price must be integer when provided."""
    with pytest.raises(ValueError):
        Property(
            id="test-789",
            title="Invalid Price",
            price="5000000",  # String instead of integer
            source_name="Test Source",
            source_url="https://example.com/property/789"
        )


def test_property_price_must_be_positive():
    """Test that price cannot be negative."""
    with pytest.raises(ValueError):
        Property(
            id="test-101",
            title="Negative Price",
            price=-1000000,
            source_name="Test Source",
            source_url="https://example.com/property/101"
        )


def test_property_sizes_must_be_float():
    """Test that sizes must be float when provided."""
    with pytest.raises(ValueError):
        Property(
            id="test-102",
            title="Invalid Size",
            land_size_m2="300",  # String instead of float
            source_name="Test Source",
            source_url="https://example.com/property/102"
        )


def test_property_latitude_range():
    """Test latitude validation."""
    with pytest.raises(ValueError):
        Property(
            id="test-103",
            title="Invalid Latitude",
            latitude=91.0,  # Out of range
            source_name="Test Source",
            source_url="https://example.com/property/103"
        )


def test_property_longitude_range():
    """Test longitude validation."""
    with pytest.raises(ValueError):
        Property(
            id="test-104",
            title="Invalid Longitude",
            longitude=181.0,  # Out of range
            source_name="Test Source",
            source_url="https://example.com/property/104"
        )


def test_property_json_serialization():
    """Test JSON serialization of Property model."""
    property = create_valid_property()
    json_data = property.model_dump()
    
    # Check that datetime is properly serialized
    assert 'collected_at' in json_data
    assert json_data['id'] == 'test-123'
    assert json_data['price'] is None
    assert json_data['prefecture'] is None