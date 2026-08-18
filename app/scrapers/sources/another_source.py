"""
Another source scraper (placeholder - not connecting to real website yet)
"""
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from app.scrapers.base import HTMLScraper, ParseError
from app.models import Property

logger = logging.getLogger(__name__)


class AnotherSourceScraper(HTMLScraper):
    """
    Scraper for another akiya source.
    This is a placeholder implementation for testing.
    """
    
    def get_source_name(self) -> str:
        """Return the source name."""
        return "another_source"
    
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
        try:
            soup = BeautifulSoup(html, 'html.parser')
            properties = []
            
            # Find property listings (placeholder selector)
            listings = soup.find_all('article', class_='akiya-card')
            
            for listing in listings:
                raw_data = {
                    'id': listing.get('data-property-id'),
                    'title': listing.find('h3', class_='card-title').text.strip() if listing.find('h3', class_='card-title') else None,
                    'price': listing.find('div', class_='card-price').text.strip() if listing.find('div', class_='card-price') else None,
                    'prefecture': listing.find('span', class_='pref').text.strip() if listing.find('span', class_='pref') else None,
                    'municipality': listing.find('span', class_='city').text.strip() if listing.find('span', class_='city') else None,
                    'area': listing.find('span', class_='district').text.strip() if listing.find('span', class_='district') else None,
                    'land_size_m2': listing.find('span', class_='land').text.strip() if listing.find('span', class_='land') else None,
                    'building_size_m2': listing.find('span', class_='building').text.strip() if listing.find('span', class_='building') else None,
                    'build_year': listing.find('span', class_='year').text.strip() if listing.find('span', class_='year') else None,
                    'rooms': listing.find('span', class_='layout').text.strip() if listing.find('span', class_='layout') else None,
                    'structure': listing.find('span', class_='structure').text.strip() if listing.find('span', class_='structure') else None,
                    'floors': listing.find('span', class_='floors').text.strip() if listing.find('span', class_='floors') else None,
                    'parking': listing.find('span', class_='parking').text.strip() if listing.find('span', class_='parking') else None,
                    'description': listing.find('div', class_='description').text.strip() if listing.find('div', class_='description') else None,
                    'source_url': listing.find('a', class_='detail-link').get('href') if listing.find('a', class_='detail-link') else None,
                    'image_url': listing.find('img', class_='main-image').get('src') if listing.find('img', class_='main-image') else None,
                    'latitude': listing.find('span', class_='lat').text.strip() if listing.find('span', class_='lat') else None,
                    'longitude': listing.find('span', class_='lng').text.strip() if listing.find('span', class_='lng') else None,
                }
                properties.append(raw_data)
            
            return properties
            
        except Exception as e:
            raise ParseError(f"Failed to parse HTML: {e}")
    
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
        try:
            # Convert string values to appropriate types
            price = None
            if raw_data.get('price'):
                try:
                    # Remove currency symbols and commas
                    price_str = raw_data['price'].replace('¥', '').replace(',', '').replace('円', '').strip()
                    price = int(price_str)
                except ValueError:
                    price = None
            
            land_size = None
            if raw_data.get('land_size_m2'):
                try:
                    land_size = float(raw_data['land_size_m2'].replace('m²', '').strip())
                except ValueError:
                    land_size = None
            
            building_size = None
            if raw_data.get('building_size_m2'):
                try:
                    building_size = float(raw_data['building_size_m2'].replace('m²', '').strip())
                except ValueError:
                    building_size = None
            
            build_year = None
            if raw_data.get('build_year'):
                try:
                    build_year = int(raw_data['build_year'])
                except ValueError:
                    build_year = None
            
            floors = None
            if raw_data.get('floors'):
                try:
                    floors = int(raw_data['floors'])
                except ValueError:
                    floors = None
            
            latitude = None
            if raw_data.get('latitude'):
                try:
                    latitude = float(raw_data['latitude'])
                except ValueError:
                    latitude = None
            
            longitude = None
            if raw_data.get('longitude'):
                try:
                    longitude = float(raw_data['longitude'])
                except ValueError:
                    longitude = None
            
            return Property(
                id=raw_data.get('id', ''),
                title=raw_data.get('title', ''),
                price=price,
                prefecture=raw_data.get('prefecture'),
                municipality=raw_data.get('municipality'),
                area=raw_data.get('area'),
                land_size_m2=land_size,
                building_size_m2=building_size,
                build_year=build_year,
                rooms=raw_data.get('rooms'),
                structure=raw_data.get('structure'),
                floors=floors,
                parking=raw_data.get('parking'),
                description=raw_data.get('description'),
                source_name=self.get_source_name(),
                source_url=raw_data.get('source_url', ''),
                image_url=raw_data.get('image_url'),
                latitude=latitude,
                longitude=longitude,
            )
            
        except Exception as e:
            raise ParseError(f"Failed to normalize property data: {e}")