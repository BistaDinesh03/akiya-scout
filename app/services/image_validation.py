"""
Image validation service for Akiya Scout
Rejects logos, banners, and non-property images
"""
import logging
import re
import requests
from typing import Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Known logo/branding patterns to reject
LOGO_PATTERNS = [
    r'logo',
    r'logo\.jpg',
    r'logo\.png',
    r'logo-footer',
    r'logo-header',
    r'sitelogo',
    r'header',
    r'banner',
    r'favicon',
    r'icon',
    r'gnavi',
    r'footer',
    r'common/img',
    r'theme',
    r'plugin',
    r'wp-content/themes',
    r'social',
    r'twitter',
    r'facebook',
    r'instagram',
    r'youtube',
    r'placeholder',
    r'default',
    r'no-image',
    r'noimage',
    r'blank',
    r'spacer',
    r'pixel',
    r'transparent',
]

# Allowed image extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

# Cache for validated URLs
_validated_url_cache: Set[str] = set()
_rejected_url_cache: Set[str] = set()

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
IMAGE_TIMEOUT = 5  # seconds


def is_logo_or_branding(image_url: str) -> bool:
    """Check if URL appears to be a logo or branding image."""
    url_lower = image_url.lower()
    
    for pattern in LOGO_PATTERNS:
        if re.search(pattern, url_lower):
            return True
    
    return False


def has_allowed_extension(image_url: str) -> bool:
    """Check if URL has an allowed image extension."""
    path = urlparse(image_url).path.lower()
    return any(path.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def validate_image_url(image_url: str) -> bool:
    """
    Validate that an image URL is a real property image.
    """
    if not image_url:
        return False
    
    if image_url in _validated_url_cache:
        return True
    if image_url in _rejected_url_cache:
        return False
    
    if is_logo_or_branding(image_url):
        _rejected_url_cache.add(image_url)
        return False
    
    if not has_allowed_extension(image_url):
        if 'wp-content/uploads' not in image_url:
            _rejected_url_cache.add(image_url)
            return False
    
    try:
        response = requests.head(image_url, timeout=IMAGE_TIMEOUT, allow_redirects=True)
        
        if response.status_code == 405:
            response = requests.get(image_url, timeout=IMAGE_TIMEOUT, stream=True)
        
        if response.status_code != 200:
            _rejected_url_cache.add(image_url)
            return False
        
        content_type = response.headers.get('content-type', '').lower()
        if 'image' not in content_type:
            _rejected_url_cache.add(image_url)
            return False
        
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > MAX_IMAGE_SIZE:
            _rejected_url_cache.add(image_url)
            return False
        
        _validated_url_cache.add(image_url)
        return True
        
    except Exception as e:
        logger.debug(f"Image validation failed for {image_url}: {e}")
        _rejected_url_cache.add(image_url)
        return False


def extract_best_image(images: list) -> Optional[str]:
    """
    Extract the best property image from a list of image URLs.
    Rejects logos and branding.
    Returns None if no trustworthy image found.
    """
    for image_url in images:
        if image_url and validate_image_url(image_url):
            return image_url
    
    return None


def clear_image_cache():
    """Clear all cached image validation results."""
    _validated_url_cache.clear()
    _rejected_url_cache.clear()
    logger.info("Image validation cache cleared")