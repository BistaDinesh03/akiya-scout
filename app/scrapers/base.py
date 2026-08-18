"""
Base scraper interface for Akiya Scout
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models import Property

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class FetchError(ScraperError):
    """Exception raised when fetching fails."""
    pass


class ParseError(ScraperError):
    """Exception raised when parsing fails."""
    pass


class BaseScraper(ABC):
    """
    Abstract base class for all property scrapers.
    
    Each scraper must implement:
    - get_source_name()
    - fetch()
    - parse()
    - normalize()
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: str = "AkiyaScout/0.1.0 (compatible; +https://github.com/akiyascout)"
    ):
        """
        Initialize scraper with configurable timeout, retries, and user agent.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: User agent string for HTTP requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": self.user_agent})
        
        return session
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return the unique name of the source website.
        
        Returns:
            String identifier for the source
        """
        pass
    
    @abstractmethod
    def fetch(self, url: str) -> str:
        """
        Fetch HTML content from a URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            FetchError: If fetching fails
        """
        pass
    
    @abstractmethod
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content and extract property data.
        
        Args:
            html: HTML content as string
            
        Returns:
            List of dictionaries containing raw property data
            
        Raises:
            ParseError: If parsing fails
        """
        pass
    
    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> Property:
        """
        Normalize raw property data into a Property object.
        
        Args:
            raw_data: Dictionary containing raw property data
            
        Returns:
            Normalized Property object
            
        Raises:
            ParseError: If normalization fails
        """
        pass
    
    def scrape(self, url: str) -> List[Property]:
        """
        Complete scraping pipeline: fetch, parse, and normalize.
        
        Args:
            url: The URL to scrape
            
        Returns:
            List of normalized Property objects
            
        Raises:
            ScraperError: If any step fails
        """
        logger.info(f"[{self.get_source_name()}] Starting scrape for URL: {url}")
        
        try:
            # Fetch
            html = self.fetch(url)
            logger.debug(f"[{self.get_source_name()}] Fetched {len(html)} characters")
            
            # Parse
            raw_properties = self.parse(html)
            logger.info(f"[{self.get_source_name()}] Parsed {len(raw_properties)} raw properties")
            
            # Normalize
            properties = []
            for raw_data in raw_properties:
                try:
                    property_obj = self.normalize(raw_data)
                    properties.append(property_obj)
                except Exception as e:
                    logger.error(f"[{self.get_source_name()}] Failed to normalize property: {e}")
                    continue
            
            logger.info(f"[{self.get_source_name()}] Successfully normalized {len(properties)} properties")
            return properties
            
        except FetchError as e:
            logger.error(f"[{self.get_source_name()}] Fetch error: {e}")
            raise
        except ParseError as e:
            logger.error(f"[{self.get_source_name()}] Parse error: {e}")
            raise
        except Exception as e:
            logger.error(f"[{self.get_source_name()}] Unexpected error: {e}")
            raise ScraperError(f"Unexpected error during scraping: {e}")
    
    def close(self):
        """Close the requests session."""
        if self.session:
            self.session.close()
            logger.debug(f"[{self.get_source_name()}] Session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class HTMLScraper(BaseScraper):
    """
    Base class for HTML-based scrapers.
    Provides default implementation for fetching HTML content.
    """
    
    def fetch(self, url: str) -> str:
        """
        Fetch HTML content from a URL using requests.
        
        Args:
            url: The URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            FetchError: If fetching fails
        """
        try:
            logger.debug(f"[{self.get_source_name()}] Fetching URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
            
        except requests.exceptions.Timeout as e:
            raise FetchError(f"Timeout after {self.timeout} seconds: {e}")
        except requests.exceptions.RetryError as e:
            raise FetchError(f"Max retries ({self.max_retries}) exceeded: {e}")
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Request failed: {e}")
        except Exception as e:
            raise FetchError(f"Unexpected fetch error: {e}")