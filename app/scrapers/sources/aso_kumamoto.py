"""
Aso City Akiya Bank scraper (Kumamoto Prefecture)
Source: https://www.city.aso.kumamoto.jp/akiya/
Uses WordPress REST API and HTML parsing
"""
import logging
import re
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, FetchError, ParseError
from app.models import Property
from app.config import settings

logger = logging.getLogger(__name__)


class AsoKumamotoScraper(BaseScraper):
    """
    Scraper for Aso City Akiya Bank.
    Uses WordPress API at https://www.city.aso.kumamoto.jp/wp-json/wp/v2/posts
    """
    
    BASE_URL = "https://www.city.aso.kumamoto.jp"
    AKIYA_URL = "https://www.city.aso.kumamoto.jp/akiya/"
    API_URL = "https://www.city.aso.kumamoto.jp/wp-json/wp/v2/posts"
    RATE_LIMIT_DELAY = 1.0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_request_time = 0
    
    def get_source_name(self) -> str:
        """Return the source name."""
        return "aso_kumamoto"
    
    def _rate_limit(self):
        """Ensure rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self._last_request_time = time.time()
    
    def _get_verify(self) -> bool:
        """Get SSL verification setting."""
        return not settings.allow_insecure_ssl
    
    def fetch(self, url: str) -> str:
        """Fetch content with rate limiting."""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=self.timeout, verify=self._get_verify())
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout as e:
            raise FetchError(f"Timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Request failed: {e}")
    
    def fetch_json(self, url: str) -> Any:
        """Fetch JSON with rate limiting."""
        self._rate_limit()
        try:
            response = self.session.get(url, timeout=self.timeout, verify=self._get_verify())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            raise FetchError(f"Timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Request failed: {e}")
        except ValueError as e:
            raise FetchError(f"Invalid JSON: {e}")
    
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """Parse Aso City Akiya property detail page."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Get title
            title_elem = soup.find('h1') or soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract from tables
            raw_data = {
                'title': title,
                'price': None,
                'prefecture': 'Kumamoto',
                'municipality': 'Aso',
                'area': None,
                'land_size_m2': None,
                'building_size_m2': None,
                'build_year': None,
                'rooms': None,
                'structure': None,
                'floors': None,
                'parking': None,
                'description': None,
                'source_url': None,
                'image_url': None,
                'latitude': None,
                'longitude': None,
            }
            
            # Parse tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if '登録番号' in label:
                            raw_data['id_hint'] = value
                        elif '物件住所' in label or '所在地' in label:
                            raw_data['area'] = value
                            if '阿蘇市' in value:
                                raw_data['municipality'] = 'Aso'
                        elif '価格' in label:
                            raw_data['price'] = self._parse_price(value)
                        elif '面積' in label:
                            raw_data['land_size_m2'] = self._parse_size(value)
                        elif '構造' in label and '間取り' in label:
                            parts = value.split('／')
                            if len(parts) >= 2:
                                raw_data['structure'] = parts[0].strip()
                                raw_data['rooms'] = parts[1].strip()
                        elif '築年数' in label:
                            raw_data['build_year'] = self._parse_year(value)
            
            # Get image URL - look for property images specifically
            img = soup.find('img', src=re.compile(r'upload|akiya|property', re.I))
            if img and img.get('src'):
                raw_data['image_url'] = img['src']
            
            return [raw_data]
            
        except Exception as e:
            raise ParseError(f"Failed to parse HTML: {e}")
    
    def _parse_price(self, price_text: str) -> Optional[int]:
        """Parse Japanese price format."""
        # Check for rental price (賃貸)
        if '賃貸' in price_text:
            match = re.search(r'(\d+(?:,\d+)?)円/月', price_text)
            if match:
                return int(match.group(1).replace(',', ''))
        
        # Check for sale price
        match = re.search(r'(\d+(?:,\d+)?)\s*万円', price_text)
        if match:
            man_value = float(match.group(1).replace(',', ''))
            return int(man_value * 10000)
        
        # Direct yen
        match = re.search(r'(\d+(?:,\d+)?)\s*円', price_text)
        if match:
            return int(match.group(1).replace(',', ''))
        
        return None
    
    def _parse_size(self, size_text: str) -> Optional[float]:
        """Parse size in m²."""
        match = re.search(r'(\d+(?:\.\d+)?)\s*㎡', size_text)
        if match:
            return float(match.group(1))
        return None
    
    def _parse_year(self, year_text: str) -> Optional[int]:
        """Parse building age (築X年) to build year."""
        match = re.search(r'築(\d+)年', year_text)
        if match:
            years_old = int(match.group(1))
            return 2026 - years_old
        return None
    
    def normalize(self, raw_data: Dict[str, Any]) -> Property:
        """Normalize raw data into Property model."""
        try:
            # Extract property number from title
            title = raw_data.get('title', '')
            match = re.search(r'物件番号(\d+)号', title)
            property_id = f"aso-{match.group(1)}" if match else raw_data.get('id_hint', str(hash(title)))
            
            return Property(
                id=property_id,
                title=title,
                listing_type="RENTAL",
                price=raw_data.get('price'),
                prefecture=raw_data.get('prefecture', 'Kumamoto'),
                municipality=raw_data.get('municipality', 'Aso'),
                area=raw_data.get('area'),
                land_size_m2=raw_data.get('land_size_m2'),
                building_size_m2=raw_data.get('building_size_m2'),
                build_year=raw_data.get('build_year'),
                rooms=raw_data.get('rooms'),
                structure=raw_data.get('structure'),
                floors=raw_data.get('floors'),
                parking=raw_data.get('parking'),
                description=raw_data.get('description'),
                source_name=self.get_source_name(),
                source_url=raw_data.get('source_url', ''),
                image_url=raw_data.get('image_url'),
                latitude=raw_data.get('latitude'),
                longitude=raw_data.get('longitude'),
            )
        except Exception as e:
            raise ParseError(f"Failed to normalize: {e}")
    
    def scrape(self, url: str = None) -> List[Property]:
        """Scrape all Aso City Akiya listings."""
        logger.info(f"[{self.get_source_name()}] Starting scrape")
        
        all_properties = []
        rejected = 0
        errors = 0
        
        try:
            # Fetch Akiya page to find listing links
            page_html = self.fetch(self.AKIYA_URL)
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Find all property links
            listing_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                if '物件番号' in text and '/akiya/' in href:
                    if href not in listing_links:
                        listing_links.append(href)
            
            logger.info(f"[{self.get_source_name()}] Found {len(listing_links)} listing links")
            
            # Process each listing
            for link in listing_links:
                try:
                    if not link.startswith('http'):
                        link = self.BASE_URL + link if link.startswith('/') else self.AKIYA_URL + link
                    
                    page_html = self.fetch(link)
                    raw_properties = self.parse(page_html)
                    
                    for raw_data in raw_properties:
                        raw_data['source_url'] = link
                        try:
                            prop = self.normalize(raw_data)
                            all_properties.append(prop)
                        except Exception as e:
                            rejected += 1
                            logger.warning(f"Rejected: {e}")
                
                except FetchError as e:
                    errors += 1
                    logger.error(f"Failed to fetch {link}: {e}")
                except Exception as e:
                    errors += 1
                    logger.error(f"Error processing {link}: {e}")
            
            logger.info(f"[{self.get_source_name()}] Scrape complete: {len(all_properties)} accepted, {rejected} rejected, {errors} errors")
            
        except Exception as e:
            logger.error(f"[{self.get_source_name()}] Scrape failed: {e}")
            raise
        
        return all_properties