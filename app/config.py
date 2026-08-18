"""
Configuration for Akiya Scout
"""
import os
from typing import Optional


def get_bool_env(name: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(name, '').lower()
    if value in ['true', '1', 'yes', 'on']:
        return True
    elif value in ['false', '0', 'no', 'off']:
        return False
    return default


class Settings:
    """Application settings."""
    
    def __init__(self):
        # SSL settings
        self.allow_insecure_ssl = get_bool_env('AKIYA_ALLOW_INSECURE_SSL', default=False)
        
        # Cache settings
        self.cache_ttl_seconds = int(os.getenv('CACHE_TTL_SECONDS', '600'))
        
        # Rate limiting
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', '1.0'))
        
        # Timeouts
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.image_timeout = int(os.getenv('IMAGE_TIMEOUT', '5'))


# Global settings
settings = Settings()