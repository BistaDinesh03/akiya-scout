"""
Tests for image validation service
"""
import pytest
from unittest.mock import patch, Mock
from app.services.image_validation import (
    is_logo_or_branding,
    has_allowed_extension,
    validate_image_url,
    extract_best_image,
)


class TestLogoDetection:
    """Test logo/branding detection."""
    
    def test_detects_logo_url(self):
        """Test that logo URLs are detected."""
        assert is_logo_or_branding("https://example.com/images/logo.png")
        assert is_logo_or_branding("https://example.com/sitelogo.jpg")
        assert is_logo_or_branding("https://example.com/common/img/header.png")
    
    def test_detects_banner(self):
        """Test that banner URLs are detected."""
        assert is_logo_or_branding("https://example.com/banner.png")
        assert is_logo_or_branding("https://example.com/header-image.jpg")
    
    def test_detects_favicon(self):
        """Test that favicon URLs are detected."""
        assert is_logo_or_branding("https://example.com/favicon.ico")
    
    def test_allows_property_images(self):
        """Test that property images are not flagged as logos."""
        assert not is_logo_or_branding("https://example.com/wp-content/uploads/2026/08/property578.jpg")
        assert not is_logo_or_branding("https://example.com/uploads/house-photo.png")
    
    def test_allows_regular_images(self):
        """Test that regular image URLs pass."""
        assert not is_logo_or_branding("https://example.com/images/house.jpg")


class TestExtensionCheck:
    """Test extension validation."""
    
    def test_allows_jpg(self):
        assert has_allowed_extension("https://example.com/house.jpg")
    
    def test_allows_png(self):
        assert has_allowed_extension("https://example.com/house.png")
    
    def test_allows_webp(self):
        assert has_allowed_extension("https://example.com/house.webp")
    
    def test_rejects_non_image(self):
        assert not has_allowed_extension("https://example.com/house.pdf")
        assert not has_allowed_extension("https://example.com/house.html")
    
    def test_rejects_no_extension(self):
        assert not has_allowed_extension("https://example.com/house")


class TestImageValidation:
    """Test full image validation."""
    
    @patch('requests.head')
    def test_validates_real_image(self, mock_head):
        """Test that valid image passes."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_head.return_value = mock_response
        
        url = "https://example.com/wp-content/uploads/property.jpg"
        assert validate_image_url(url) is True
    
    @patch('requests.head')
    def test_rejects_non_image_content_type(self, mock_head):
        """Test that non-image content type is rejected."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_head.return_value = mock_response
        
        url = "https://example.com/not-an-image.jpg"
        assert validate_image_url(url) is False
    
    @patch('requests.head')
    def test_rejects_404(self, mock_head):
        """Test that 404 images are rejected."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_head.return_value = mock_response
        
        url = "https://example.com/missing.jpg"
        assert validate_image_url(url) is False
    
    def test_rejects_logo(self):
        """Test that logo URLs are rejected without HTTP request."""
        url = "https://example.com/sitelogo.png"
        assert validate_image_url(url) is False


class TestExtractBestImage:
    """Test extracting best image from list."""
    
    def test_extracts_property_image(self):
        """Test that property image is selected over logo."""
        images = [
            "https://example.com/logo.png",
            "https://example.com/wp-content/uploads/property.jpg",
        ]
        
        # Mock validate to skip HTTP
        with patch('app.services.image_validation.validate_image_url', side_effect=[False, True]):
            result = extract_best_image(images)
            assert result == images[1]
    
    def test_returns_none_when_all_rejected(self):
        """Test that None is returned when all images rejected."""
        images = [
            "https://example.com/logo.png",
            "https://example.com/banner.jpg",
        ]
        
        with patch('app.services.image_validation.validate_image_url', return_value=False):
            result = extract_best_image(images)
            assert result is None
    
    def test_returns_none_for_empty_list(self):
        """Test that None is returned for empty list."""
        result = extract_best_image([])
        assert result is None
    
    def test_skips_none_values(self):
        """Test that None values are skipped."""
        images = [None, "https://example.com/property.jpg"]
        
        with patch('app.services.image_validation.validate_image_url', return_value=True):
            result = extract_best_image(images)
            assert result == images[1]