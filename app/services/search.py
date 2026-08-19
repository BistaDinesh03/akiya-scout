"""
Search service for Akiya Scout
Handles property search, filtering, sorting, ranking, and deduplication
"""
import logging
import time
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models import Property
from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.scrapers.sources.another_source import AnotherSourceScraper
from app.scrapers.sources.aso_kumamoto import AsoKumamotoScraper
from app.services.valuation import valuation_engine, ValuationResult
from app.db import load_properties, save_properties, get_property_count

logger = logging.getLogger(__name__)


class PropertyCache:
    """Simple in-memory cache for property listings."""
    
    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, List[Property]] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[List[Property]]:
        if key not in self._cache:
            return None
        
        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        return self._cache[key]
    
    def set(self, key: str, properties: List[Property]) -> None:
        self._cache[key] = properties
        self._timestamps[key] = time.time()
    
    def clear(self) -> None:
        self._cache.clear()
        self._timestamps.clear()
    
    def get_timestamp(self, key: str) -> Optional[str]:
        """Get cache timestamp as ISO string."""
        if key in self._timestamps:
            return datetime.fromtimestamp(self._timestamps[key]).isoformat()
        return None


class SearchService:
    """Search service with database-backed storage and caching."""
    
    CACHE_KEY = "all_properties"
    
    def __init__(self, cache_ttl: int = 600):
        self.cache = PropertyCache(ttl_seconds=cache_ttl)
        self.enabled_sources = [
            SagaTakeoScraper,
            AsoKumamotoScraper,
        ]
    
    def get_all_properties(self, force_refresh: bool = False) -> List[Property]:
        """
        Get all properties.
        First tries cache, then database, then live scraping.
        """
        # Check cache first
        if not force_refresh:
            cached = self.cache.get(self.CACHE_KEY)
            if cached is not None:
                logger.info(f"Returning {len(cached)} properties from cache")
                return cached
        
        # Try database
        db_properties = load_properties()
        if db_properties:
            logger.info(f"Loaded {len(db_properties)} properties from database")
            self.cache.set(self.CACHE_KEY, db_properties)
            return db_properties
        
        # Fallback: live scraping (for local dev)
        logger.info("Database empty, attempting live scraping")
        all_properties = self._scrape_all_sources()
        
        if all_properties:
            save_properties(all_properties)
            logger.info(f"Saved {len(all_properties)} properties to database")
        
        self.cache.set(self.CACHE_KEY, all_properties)
        return all_properties
    
    def _scrape_all_sources(self) -> List[Property]:
        """Scrape all enabled sources with graceful failure."""
        all_properties = []
        failed_sources = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            for scraper_class in self.enabled_sources:
                future = executor.submit(self._scrape_source, scraper_class)
                futures[future] = scraper_class.__name__
            
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    properties = future.result()
                    all_properties.extend(properties)
                    logger.info(f"Scraped {len(properties)} from {source_name}")
                except Exception as e:
                    logger.error(f"Source {source_name} failed: {e}")
                    failed_sources.append(source_name)
        
        unique = self.deduplicate(all_properties)
        return unique
    
    def _scrape_source(self, scraper_class) -> List[Property]:
        """Scrape a single source with error handling."""
        scraper = None
        source_name = scraper_class.__name__
        logger.info(f"[SOURCE: {source_name}] Request started")
        
        try:
            scraper = scraper_class()
            properties = scraper.scrape()
            logger.info(f"[SOURCE: {source_name}] Found {len(properties)} listings")
            return properties
        except Exception as e:
            logger.error(f"[SOURCE: {source_name}] FAILED: {type(e).__name__}: {e}")
            return []
        finally:
            if scraper:
                scraper.close()
    
    def deduplicate(self, properties: List[Property]) -> List[Property]:
        """Deduplicate properties by ID."""
        seen_ids = set()
        unique = []
        for prop in properties:
            if prop.id not in seen_ids:
                seen_ids.add(prop.id)
                unique.append(prop)
        return unique
    
    def filter_properties(
        self,
        properties: List[Property],
        max_price: Optional[int] = None,
        min_land: Optional[float] = None,
        min_building: Optional[float] = None,
        prefecture: Optional[str] = None,
        municipality: Optional[str] = None,
        min_rooms: Optional[int] = None,
        parking: Optional[str] = None,
        real_listings_only: bool = False,
        listing_type: Optional[str] = None,
    ) -> List[Property]:
        """Filter properties with graceful None handling."""
        filtered = []
        
        for prop in properties:
            if real_listings_only and not prop.source_url:
                continue
            
            if listing_type is not None:
                if prop.listing_type != listing_type:
                    continue
            
            if max_price is not None:
                if prop.price is None or prop.price > max_price:
                    continue
            
            if min_land is not None:
                if prop.land_size_m2 is None or prop.land_size_m2 < min_land:
                    continue
            
            if min_building is not None:
                if prop.building_size_m2 is None or prop.building_size_m2 < min_building:
                    continue
            
            if prefecture is not None:
                if prop.prefecture is None or prop.prefecture != prefecture:
                    continue
            
            if municipality is not None:
                if prop.municipality is None or prop.municipality != municipality:
                    continue
            
            if min_rooms is not None:
                if prop.rooms is None:
                    continue
                count = self._extract_room_count(prop.rooms)
                if count is None or count < min_rooms:
                    continue
            
            if parking is not None:
                if prop.parking is None:
                    continue
                if parking.lower() == 'yes' and 'なし' in prop.parking:
                    continue
                if parking.lower() == 'no' and 'あり' in prop.parking:
                    continue
            
            filtered.append(prop)
        
        return filtered
    
    def _extract_room_count(self, rooms: str) -> Optional[int]:
        match = re.match(r'(\d+)', rooms)
        return int(match.group(1)) if match else None
    
    def rank_properties(
        self,
        properties: List[Property],
        sort: Optional[str] = None,
    ) -> List[Property]:
        """Rank properties by various criteria."""
        if sort is None or sort == 'newest':
            return sorted(properties, key=lambda p: p.collected_at, reverse=True)
        
        elif sort == 'price_asc':
            sale_props = [p for p in properties if p.listing_type == 'SALE']
            rental_props = [p for p in properties if p.listing_type == 'RENTAL']
            sorted_sale = sorted(sale_props, key=lambda p: p.price if p.price is not None else float('inf'))
            sorted_rental = sorted(rental_props, key=lambda p: p.price if p.price is not None else float('inf'))
            return sorted_sale + sorted_rental
        
        elif sort == 'price_desc':
            sale_props = [p for p in properties if p.listing_type == 'SALE']
            rental_props = [p for p in properties if p.listing_type == 'RENTAL']
            sorted_sale = sorted(sale_props, key=lambda p: p.price if p.price is not None else float('-inf'), reverse=True)
            sorted_rental = sorted(rental_props, key=lambda p: p.price if p.price is not None else float('-inf'), reverse=True)
            return sorted_sale + sorted_rental
        
        elif sort == 'total_cost_asc':
            sale_props = [p for p in properties if p.listing_type == 'SALE']
            return sorted(sale_props, key=lambda p: self._get_total_cost(p))
        
        elif sort == 'value_score':
            sale_props = [p for p in properties if p.listing_type == 'SALE']
            return sorted(sale_props, key=lambda p: self._get_akiya_score(p), reverse=True)
        
        elif sort == 'land_asc':
            return sorted(properties, key=lambda p: p.land_size_m2 if p.land_size_m2 is not None else float('inf'))
        
        elif sort == 'land_desc':
            return sorted(properties, key=lambda p: p.land_size_m2 if p.land_size_m2 is not None else float('-inf'), reverse=True)
        
        elif sort == 'renovation_asc':
            sale_props = [p for p in properties if p.listing_type == 'SALE']
            return sorted(sale_props, key=lambda p: self._get_renovation_cost(p))
        
        return properties
    
    def _get_total_cost(self, prop: Property) -> float:
        if prop.listing_type == 'RENTAL':
            return float('inf')
        valuation = valuation_engine.valuate(prop)
        if valuation.estimated_total_cost > 0:
            return valuation.estimated_total_cost
        return float('inf')
    
    def _get_akiya_score(self, prop: Property) -> float:
        if prop.listing_type == 'RENTAL':
            return 0.0
        valuation = valuation_engine.valuate(prop)
        return valuation.akiya_score
    
    def _get_renovation_cost(self, prop: Property) -> float:
        if prop.listing_type == 'RENTAL':
            return float('inf')
        valuation = valuation_engine.valuate(prop)
        return valuation.estimated_renovation_cost
    
    def search(
        self,
        max_price: Optional[int] = None,
        min_land: Optional[float] = None,
        min_building: Optional[float] = None,
        prefecture: Optional[str] = None,
        municipality: Optional[str] = None,
        min_rooms: Optional[int] = None,
        parking: Optional[str] = None,
        sort: Optional[str] = None,
        force_refresh: bool = False,
        real_listings_only: bool = False,
        listing_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search properties with filters and ranking."""
        all_properties = self.get_all_properties(force_refresh=force_refresh)
        
        filtered = self.filter_properties(
            all_properties,
            max_price=max_price,
            min_land=min_land,
            min_building=min_building,
            prefecture=prefecture,
            municipality=municipality,
            min_rooms=min_rooms,
            parking=parking,
            real_listings_only=real_listings_only,
            listing_type=listing_type,
        )
        
        ranked = self.rank_properties(filtered, sort=sort)
        
        return {
            "properties": ranked,
            "total": len(ranked),
            "filtered_from": len(all_properties),
            "cache_used": not force_refresh and self.cache.get(self.CACHE_KEY) is not None,
            "last_refresh": self.cache.get_timestamp(self.CACHE_KEY),
        }


# Global search service instance
search_service = SearchService(cache_ttl=600)