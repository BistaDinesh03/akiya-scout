"""
Akiya Scout - Main Application
Japan Cheap House Finder
"""
import logging
from pathlib import Path
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from typing import Optional, List
import re

from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.scrapers.sources.another_source import AnotherSourceScraper
from app.scrapers.sources.fukuoka_akiyabank import FukuokaAkiyaBankScraper
from app.scrapers.sources.kumamoto_akiyabank import KumamotoAkiyaBankScraper
from app.scrapers.sources.oita_akiyabank import OitaAkiyaBankScraper
from app.scrapers.sources.imari_saga import ImariSagaScraper
from app.scrapers.sources.ureshino_saga import UreshinoSagaScraper
from app.scrapers.sources.aso_kumamoto import AsoKumamotoScraper
from app.scrapers.registry import registry
from app.services.search import search_service
from app.services.valuation import valuation_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Akiya Scout",
    description="Japan Cheap House Finder",
    version="0.1.0"
)

# CORS configuration (safe defaults - no wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Setup static files and templates
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Valid sort options
VALID_SORT_OPTIONS = [
    'price_asc', 'price_desc', 'total_cost_asc', 'value_score',
    'land_asc', 'land_desc', 'renovation_asc', 'newest'
]


def validate_property_id(property_id: str) -> bool:
    """Validate property ID format to prevent injection."""
    return bool(re.match(r'^[a-zA-Z0-9\-_]+$', property_id))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main homepage."""
    logger.info("Serving homepage")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Akiya Scout",
            "subtitle": "Japan Cheap House Finder",
            "status_message": "System ready for real-time property search."
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Akiya Scout",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/properties")
async def get_properties(
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price in yen"),
    min_land: Optional[float] = Query(None, ge=0, description="Minimum land size in m²"),
    min_building: Optional[float] = Query(None, ge=0, description="Minimum building size in m²"),
    prefecture: Optional[str] = Query(None, max_length=50, description="Prefecture name"),
    municipality: Optional[str] = Query(None, max_length=100, description="Municipality name"),
    min_rooms: Optional[int] = Query(None, ge=0, le=20, description="Minimum number of rooms"),
    parking: Optional[str] = Query(None, pattern="^(yes|no)$", description="Parking filter"),
    sort: Optional[str] = Query(None, description="Sort criteria"),
    force_refresh: Optional[bool] = Query(False, description="Force refresh cache"),
    real_listings_only: Optional[bool] = Query(False, description="Show only real listings"),
    listing_type: Optional[str] = Query(None, pattern="^(SALE|RENTAL)$", description="Listing type filter"),
):
    """Get property listings with filters and ranking."""
    if sort is not None and sort not in VALID_SORT_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid sort option. Valid: {', '.join(VALID_SORT_OPTIONS)}")
    
    logger.info(f"Property search: max_price={max_price}, sort={sort}, listing_type={listing_type}")
    
    results = search_service.search(
        max_price=max_price,
        min_land=min_land,
        min_building=min_building,
        prefecture=prefecture,
        municipality=municipality,
        min_rooms=min_rooms,
        parking=parking,
        sort=sort,
        force_refresh=force_refresh,
        real_listings_only=real_listings_only,
        listing_type=listing_type,
    )
    
    properties_with_valuation = []
    for prop in results["properties"]:
        valuation = valuation_engine.valuate(prop)
        prop_dict = prop.model_dump()
        prop_dict["akiya_score"] = round(valuation.akiya_score, 2) if prop.listing_type == "SALE" else None
        prop_dict["estimated_renovation_cost"] = valuation.estimated_renovation_cost if prop.listing_type == "SALE" else None
        prop_dict["estimated_total_cost"] = valuation.estimated_total_cost if prop.listing_type == "SALE" else None
        properties_with_valuation.append(prop_dict)
    
    return {
        "properties": properties_with_valuation,
        "total": results["total"],
        "filtered_from": results["filtered_from"],
        "cache_used": results["cache_used"],
        "last_refresh": results["last_refresh"],
    }


@app.get("/api/properties/{property_id}")
async def get_property_detail(property_id: str):
    """Get detailed information for a specific property."""
    if not validate_property_id(property_id):
        raise HTTPException(status_code=400, detail="Invalid property ID format")
    
    logger.info(f"Property detail requested: {property_id}")
    
    results = search_service.search(force_refresh=False)
    properties = results["properties"]
    
    property_obj = None
    for p in properties:
        if p.id == property_id:
            property_obj = p
            break
    
    if property_obj is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    valuation = valuation_engine.valuate(property_obj)
    
    return {
        "property": property_obj.model_dump(),
        "valuation": valuation.to_dict() if property_obj.listing_type == "SALE" else None
    }


@app.get("/api/compare")
async def compare_properties(
    ids: str = Query(..., description="Comma-separated property IDs to compare (max 3)"),
):
    """Compare 2-3 properties."""
    id_list = [id.strip() for id in ids.split(',') if id.strip()]
    
    if len(id_list) < 2 or len(id_list) > 3:
        raise HTTPException(status_code=400, detail="Compare requires 2-3 property IDs")
    
    for pid in id_list:
        if not validate_property_id(pid):
            raise HTTPException(status_code=400, detail=f"Invalid property ID: {pid}")
    
    results = search_service.search(force_refresh=False)
    properties = results["properties"]
    
    comparisons = []
    for pid in id_list:
        prop = next((p for p in properties if p.id == pid), None)
        if prop is None:
            raise HTTPException(status_code=404, detail=f"Property not found: {pid}")
        
        valuation = valuation_engine.valuate(prop) if prop.listing_type == "SALE" else None
        comparisons.append({
            "property": prop.model_dump(),
            "valuation": valuation.to_dict() if valuation else None
        })
    
    return {"comparisons": comparisons}


@app.get("/property/{property_id}", response_class=HTMLResponse)
async def property_detail_page(request: Request, property_id: str):
    """Serve the property detail page."""
    if not validate_property_id(property_id):
        raise HTTPException(status_code=400, detail="Invalid property ID")
    
    return templates.TemplateResponse(
        request=request,
        name="property_detail.html",
        context={
            "title": "Akiya Scout - Property Details",
            "property_id": property_id
        }
    )


@app.get("/api/sources")
async def get_sources():
    """Get status of all registered scrapers."""
    registry.clear()
    registry.register("saga_takeo", SagaTakeoScraper)
    registry.register("another_source", AnotherSourceScraper)
    registry.register("fukuoka_akiyabank", FukuokaAkiyaBankScraper)
    registry.register("kumamoto_akiyabank", KumamotoAkiyaBankScraper)
    registry.register("oita_akiyabank", OitaAkiyaBankScraper)
    registry.register("imari_saga", ImariSagaScraper)
    registry.register("ureshino_saga", UreshinoSagaScraper)
    registry.register("aso_kumamoto", AsoKumamotoScraper)
    
    return {"sources": registry.get_source_status()}


@app.get("/api/scrape/saga-takeo")
async def scrape_saga_takeo():
    """Scrape Takeo City vacant-house bank listings."""
    scraper = SagaTakeoScraper()
    try:
        properties = scraper.scrape()
        registry.update_scrape_stats("saga_takeo", len(properties))
        
        return {
            "source": "saga_takeo",
            "found": len(properties),
            "parsed": len(properties),
            "rejected": 0,
            "errors": 0,
        }
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        return {
            "source": "saga_takeo",
            "found": 0,
            "parsed": 0,
            "rejected": 0,
            "errors": 1,
            "error_message": str(e)
        }
    finally:
        scraper.close()


@app.get("/api/scrape/aso-kumamoto")
async def scrape_aso_kumamoto():
    """Scrape Aso City Akiya Bank listings."""
    scraper = AsoKumamotoScraper()
    try:
        properties = scraper.scrape()
        registry.update_scrape_stats("aso_kumamoto", len(properties))
        
        return {
            "source": "aso_kumamoto",
            "found": len(properties),
            "parsed": len(properties),
            "rejected": 0,
            "errors": 0,
        }
    except Exception as e:
        logger.error(f"Scrape failed: {e}")
        return {
            "source": "aso_kumamoto",
            "found": 0,
            "parsed": 0,
            "rejected": 0,
            "errors": 1,
            "error_message": str(e)
        }
    finally:
        scraper.close()