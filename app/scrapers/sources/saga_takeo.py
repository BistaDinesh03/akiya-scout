"""
Saga Takeo scraper - Takeo City vacant-house bank
https://takeo-ijyu.jp/bank/
Uses WordPress REST API for listing data
"""
import logging
import re
import time
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, FetchError, ParseError
from app.models import Property

logger = logging.getLogger(__name__)


class SagaTakeoScraper(BaseScraper):
    """
    Scraper for Takeo City vacant-house bank.
    Uses WordPress REST API at https://takeo-ijyu.jp/wp-json/wp/v2/bank
    """
    
    BASE_URL = "https://takeo-ijyu.jp"
    API_URL = "https://takeo-ijyu.jp/wp-json/wp/v2/bank"
    RATE_LIMIT_DELAY = 1.0  # seconds between requests
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_request_time = 0
    
    def get_source_name(self) -> str:
        """Return the source name."""
        return "saga_takeo"
    
    def _rate_limit(self):
        """Ensure we respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self._last_request_time = time.time()
    
    def fetch(self, url: str) -> str:
        """
        Fetch content from URL with rate limiting.
        
        Args:
            url: The URL to fetch
            
        Returns:
            Content as string
            
        Raises:
            FetchError: If fetching fails
        """
        self._rate_limit()
        try:
            logger.debug(f"[{self.get_source_name()}] Fetching URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.Timeout as e:
            raise FetchError(f"Timeout after {self.timeout} seconds: {e}")
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Request failed: {e}")
        except Exception as e:
            raise FetchError(f"Unexpected fetch error: {e}")
    
    def fetch_json(self, url: str) -> Any:
        """
        Fetch JSON data from URL with rate limiting.
        
        Args:
            url: The URL to fetch
            
        Returns:
            JSON data
            
        Raises:
            FetchError: If fetching fails
        """
        self._rate_limit()
        try:
            logger.debug(f"[{self.get_source_name()}] Fetching JSON: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout as e:
            raise FetchError(f"Timeout after {self.timeout} seconds: {e}")
        except requests.exceptions.RequestException as e:
            raise FetchError(f"Request failed: {e}")
        except ValueError as e:
            raise FetchError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise FetchError(f"Unexpected fetch error: {e}")
    
    def fetch_listings(self, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch property listings from WordPress API.
        
        Args:
            page: Page number
            per_page: Number of items per page
            
        Returns:
            List of raw property data from API
        """
        url = f"{self.API_URL}?page={page}&per_page={per_page}&_embed"
        logger.info(f"[{self.get_source_name()}] Fetching listings page {page}")
        
        data = self.fetch_json(url)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'code' in data:
            # WordPress error response
            raise FetchError(f"API error: {data.get('message', 'Unknown error')}")
        return []
    
    def parse(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content from a single property page.
        
        Args:
            html: HTML content of a property page
            
        Returns:
            List with single raw property data dict
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1') or soup.find('h2')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Get all text lines
            text = soup.get_text('\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            # Extract property details from text
            raw_data = {
                'title': title,
                'price': self._extract_price(lines),
                'prefecture': 'Saga',
                'municipality': 'Takeo',
                'area': self._extract_area(lines),
                'land_size_m2': self._extract_land_size(soup),
                'building_size_m2': None,
                'build_year': self._extract_build_year(lines),
                'rooms': self._extract_rooms(lines),
                'structure': self._extract_structure(lines),
                'parking': self._extract_parking(lines),
                'description': self._extract_description(lines),
                'source_url': None,
                'image_url': self._extract_image_url(soup),
                'latitude': None,
                'longitude': None,
            }
            
            return [raw_data]
            
        except Exception as e:
            raise ParseError(f"Failed to parse HTML: {e}")
    
    def _extract_price(self, lines: List[str]) -> Optional[int]:
        """Extract price in yen from text lines."""
        for i, line in enumerate(lines):
            if '希望価格' in line or '価格' in line:
                # Check next few lines for price
                for j in range(i + 1, min(i + 4, len(lines))):
                    price_text = lines[j]
                    
                    # Skip if it's just a label
                    if price_text in ['万円', '円']:
                        continue
                    
                    # Get unit from current line or next line
                    unit_text = ''
                    if '万円' in price_text:
                        unit_text = '万円'
                    elif price_text.endswith('円') and '万円' not in price_text:
                        unit_text = '円'
                    elif j + 1 < len(lines) and lines[j + 1] in ['万円', '円']:
                        unit_text = lines[j + 1]
                    
                    # Extract number from price text (supports multiple commas)
                    match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)', price_text)
                    if not match:
                        continue
                    
                    number = match.group(1).replace(',', '')
                    
                    # Convert based on unit
                    if unit_text == '万円':
                        man_value = float(number)
                        return int(man_value * 10000)
                    elif unit_text == '円':
                        return int(float(number))
                    elif re.match(r'^\d+(?:,\d+)*$', price_text):
                        # Standalone number - check next line for unit
                        if j + 1 < len(lines):
                            if lines[j + 1] == '万円':
                                man_value = float(number)
                                return int(man_value * 10000)
                            elif lines[j + 1] == '円':
                                return int(float(number))
        return None
    
    def _extract_area(self, lines: List[str]) -> Optional[str]:
        """Extract area/neighborhood from text lines."""
        for i, line in enumerate(lines):
            if '所在地' in line and i + 1 < len(lines):
                return lines[i + 1]
        return None
    
    def _extract_land_size(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract land size from table."""
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2 and '土地面積' in cells[0].get_text():
                    size_text = cells[1].get_text(strip=True)
                    match = re.search(r'(\d+(?:\.\d+)?)', size_text)
                    if match:
                        return float(match.group(1))
        return None
    
    def _extract_build_year(self, lines: List[str]) -> Optional[int]:
        """Extract build year from text lines."""
        for i, line in enumerate(lines):
            if '建築時期' in line and i + 1 < len(lines):
                year_text = lines[i + 1]
                match = re.search(r'(\d{4})', year_text)
                if match:
                    return int(match.group(1))
        return None
    
    def _extract_rooms(self, lines: List[str]) -> Optional[str]:
        """Extract room layout from text lines."""
        for i, line in enumerate(lines):
            if '間取り' in line and i + 1 < len(lines):
                rooms = lines[i + 1]
                return rooms if rooms != '-' else None
        return None
    
    def _extract_structure(self, lines: List[str]) -> Optional[str]:
        """Extract building structure from text lines."""
        for i, line in enumerate(lines):
            if '構造' in line and i + 1 < len(lines):
                structure = lines[i + 1]
                return structure if structure != '-' else None
        return None
    
    def _extract_parking(self, lines: List[str]) -> Optional[str]:
        """Extract parking info from text lines."""
        for i, line in enumerate(lines):
            if '駐車' in line and i + 1 < len(lines):
                parking = lines[i + 1]
                return parking if parking != '-' else None
        return None
    
    def _extract_description(self, lines: List[str]) -> Optional[str]:
        """Extract description from text lines."""
        descriptions = []
        # Look for description after 掲載日 and before エリア
        in_description = False
        for line in lines:
            if '掲載日' in line:
                in_description = True
                continue
            if in_description:
                if line in ['エリア', '所在地']:
                    break
                if len(line) > 10 and not line.startswith('№'):
                    descriptions.append(line)
        
        return ' '.join(descriptions) if descriptions else None
    
    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main image URL."""
        img = soup.find('img')
        if img and img.get('src'):
            # Prefer larger images
            src = img['src']
            # Remove WordPress thumbnail size suffix
            src = re.sub(r'-\d+x\d+(?=\.(jpg|jpeg|png|gif))', '', src)
            return src
        return None
    
    def normalize(self, raw_data: Dict[str, Any]) -> Property:
        """
        Normalize raw property data into a Property object.
        
        Args:
            raw_data: Dictionary containing raw property data
            
        Returns:
            Normalized Property object
        """
        try:
            # Generate ID from title or URL
            title = raw_data.get('title', '')
            id_match = re.search(r'№?(\d+)', title)
            property_id = f"takeo-{id_match.group(1)}" if id_match else raw_data.get('id', str(hash(title)))
            
            # Generate source URL if not provided
            source_url = raw_data.get('source_url')
            if not source_url and raw_data.get('id'):
                source_url = f"{self.BASE_URL}/bank/{raw_data['id']}/"
            
            # Extract area from title (山内町大字犬走 etc.)
            area = raw_data.get('area')
            if not area:
                # Try to extract from title
                area_match = re.search(r'(.+町.+)$', title)
                if area_match:
                    area = area_match.group(1)
            
            return Property(
                id=property_id,
                title=title,
                listing_type="SALE",
                price=raw_data.get('price'),
                prefecture=raw_data.get('prefecture', 'Saga'),
                municipality=raw_data.get('municipality', 'Takeo'),
                area=area,
                land_size_m2=raw_data.get('land_size_m2'),
                building_size_m2=raw_data.get('building_size_m2'),
                build_year=raw_data.get('build_year'),
                rooms=raw_data.get('rooms'),
                structure=raw_data.get('structure'),
                floors=raw_data.get('floors'),
                parking=raw_data.get('parking'),
                description=raw_data.get('description'),
                source_name=self.get_source_name(),
                source_url=source_url or '',
                image_url=raw_data.get('image_url'),
                latitude=raw_data.get('latitude'),
                longitude=raw_data.get('longitude'),
            )
            
        except Exception as e:
            raise ParseError(f"Failed to normalize property data: {e}")
    
    def scrape(self, url: str = None) -> List[Property]:
        """
        Scrape all listings from Takeo City vacant-house bank.
        
        Args:
            url: Optional URL (ignored for API-based scraping)
            
        Returns:
            List of normalized Property objects
        """
        logger.info(f"[{self.get_source_name()}] Starting scrape")
        
        all_properties = []
        rejected = 0
        errors = 0
        
        try:
            # Fetch first page
            first_page = self.fetch_listings(page=1, per_page=100)
            
            # Fetch remaining pages if needed
            all_raw_listings = first_page
            page = 2
            while len(first_page) == 100 and page <= 10:  # Limit to first 1000 listings
                try:
                    page_data = self.fetch_listings(page=page, per_page=100)
                    if not page_data:
                        break
                    all_raw_listings.extend(page_data)
                    page += 1
                except FetchError:
                    break
            
            logger.info(f"[{self.get_source_name()}] Found {len(all_raw_listings)} raw listings")
            
            # Process each listing
            for raw_listing in all_raw_listings:
                try:
                    # Extract data from WordPress API response
                    title = raw_listing.get('title', {}).get('rendered', '')
                    listing_id = raw_listing.get('id')
                    link = raw_listing.get('link', '')
                    
                    # Get featured image
                    image_url = None
                    if '_embedded' in raw_listing and 'wp:featuredmedia' in raw_listing['_embedded']:
                        media = raw_listing['_embedded']['wp:featuredmedia']
                        if media and media[0].get('source_url'):
                            image_url = media[0]['source_url']
                    
                    # Create raw data dict
                    raw_data = {
                        'id': str(listing_id),
                        'title': title,
                        'price': None,
                        'prefecture': 'Saga',
                        'municipality': 'Takeo',
                        'area': None,
                        'land_size_m2': None,
                        'building_size_m2': None,
                        'build_year': None,
                        'rooms': None,
                        'structure': None,
                        'floors': None,
                        'parking': None,
                        'description': None,
                        'source_url': link,
                        'image_url': image_url,
                        'latitude': None,
                        'longitude': None,
                    }
                    
                    # Fetch individual page for detailed info (rate limited)
                    if link:
                        try:
                            page_html = self.fetch(link)
                            page_soup = BeautifulSoup(page_html, 'html.parser')
                            
                            # Extract details from page
                            page_text = page_soup.get_text('\n', strip=True)
                            page_lines = [l.strip() for l in page_text.split('\n') if l.strip()]
                            
                            raw_data['price'] = self._extract_price(page_lines)
                            raw_data['area'] = self._extract_area(page_lines)
                            raw_data['land_size_m2'] = self._extract_land_size(page_soup)
                            raw_data['build_year'] = self._extract_build_year(page_lines)
                            raw_data['rooms'] = self._extract_rooms(page_lines)
                            raw_data['structure'] = self._extract_structure(page_lines)
                            raw_data['parking'] = self._extract_parking(page_lines)
                            raw_data['description'] = self._extract_description(page_lines)
                            raw_data['image_url'] = self._extract_image_url(page_soup) or image_url
                            
                        except FetchError as e:
                            logger.warning(f"[{self.get_source_name()}] Failed to fetch detail page {link}: {e}")
                    
                    # Normalize and add
                    try:
                        property_obj = self.normalize(raw_data)
                        all_properties.append(property_obj)
                    except Exception as e:
                        logger.error(f"[{self.get_source_name()}] Failed to normalize listing {listing_id}: {e}")
                        rejected += 1
                        
                except Exception as e:
                    logger.error(f"[{self.get_source_name()}] Error processing listing: {e}")
                    errors += 1
            
            logger.info(f"[{self.get_source_name()}] Scrape complete: {len(all_properties)} parsed, {rejected} rejected, {errors} errors")
            
        except FetchError as e:
            logger.error(f"[{self.get_source_name()}] Fetch error: {e}")
            raise
        except Exception as e:
            logger.error(f"[{self.get_source_name()}] Unexpected error: {e}")
            raise ScraperError(f"Unexpected error during scraping: {e}")
        
        return all_properties