"""
Tests for Akiya Scout main application
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_homepage():
    """Test that homepage loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    content = response.text
    assert "AKIYA SCOUT" in content
    assert "Find Japan's Hidden Cheap Houses" in content


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Akiya Scout"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_static_files():
    """Test that static files are served."""
    response = client.get("/static/style.css")
    assert response.status_code == 200
    
    response = client.get("/static/app.js")
    assert response.status_code == 200
    
    response = client.get("/static/detail.css")
    assert response.status_code == 200
    
    response = client.get("/static/detail.js")
    assert response.status_code == 200


def test_api_properties_structure():
    """Test that /api/properties returns the correct structure."""
    response = client.get("/api/properties")
    assert response.status_code == 200
    
    data = response.json()
    assert "properties" in data
    assert "total" in data
    assert "filtered_from" in data
    assert "cache_used" in data
    assert isinstance(data["properties"], list)
    assert data["total"] == len(data["properties"])


def test_api_properties_with_filters():
    """Test that /api/properties works with filters."""
    response = client.get("/api/properties?max_price=5000000&prefecture=Saga")
    assert response.status_code == 200
    
    data = response.json()
    assert "properties" in data
    assert "total" in data
    assert isinstance(data["properties"], list)


def test_api_properties_invalid_sort():
    """Test that invalid sort returns 400."""
    response = client.get("/api/properties?sort=invalid_sort")
    assert response.status_code == 400


def test_api_properties_invalid_parking():
    """Test that invalid parking returns 422."""
    response = client.get("/api/properties?parking=maybe")
    assert response.status_code == 422


def test_property_detail_page():
    """Test that property detail page loads."""
    response = client.get("/property/test-property-id")
    assert response.status_code == 200
    content = response.text
    assert "Property Details" in content


def test_api_property_not_found():
    """Test that API returns 404 for non-existent property."""
    response = client.get("/api/properties/nonexistent-id-12345")
    assert response.status_code == 404


def test_api_property_invalid_id():
    """Test that API returns 400 for invalid property ID."""
    response = client.get("/api/properties/invalid@id!")
    assert response.status_code == 400


def test_api_compare_requires_ids():
    """Test that compare endpoint requires IDs."""
    response = client.get("/api/compare")
    assert response.status_code == 422


def test_api_compare_invalid_count():
    """Test that compare endpoint validates count."""
    response = client.get("/api/compare?ids=only-one-id")
    assert response.status_code == 400


def test_api_sources():
    """Test that sources endpoint returns data."""
    response = client.get("/api/sources")
    assert response.status_code == 200
    
    data = response.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) >= 1


def test_api_scrape_saga_takeo():
    """Test that scrape endpoint works."""
    response = client.get("/api/scrape/saga-takeo")
    assert response.status_code == 200
    
    data = response.json()
    assert "source" in data
    assert data["source"] == "saga_takeo"
    assert "found" in data
    assert "parsed" in data
    assert "rejected" in data
    assert "errors" in data