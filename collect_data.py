"""
Collect property data locally and save to SQLite database.
Run this script locally where all sources are accessible.
"""
import logging
from app.db import save_properties, get_property_count, init_db
from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.scrapers.sources.aso_kumamoto import AsoKumamotoScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_all():
    """Collect from all sources and save to database."""
    all_properties = []
    
    # Collect Takeo
    logger.info("Collecting from Takeo...")
    scraper = SagaTakeoScraper()
    try:
        properties = scraper.scrape()
        logger.info(f"Takeo: {len(properties)} properties")
        all_properties.extend(properties)
    except Exception as e:
        logger.error(f"Takeo failed: {e}")
    finally:
        scraper.close()
    
    # Collect Aso
    logger.info("Collecting from Aso...")
    scraper = AsoKumamotoScraper()
    try:
        properties = scraper.scrape()
        logger.info(f"Aso: {len(properties)} properties")
        all_properties.extend(properties)
    except Exception as e:
        logger.error(f"Aso failed: {e}")
    finally:
        scraper.close()
    
    # Save to database
    if all_properties:
        saved = save_properties(all_properties)
        logger.info(f"Saved {saved} properties to database")
    else:
        logger.warning("No properties collected")
    
    count = get_property_count()
    logger.info(f"Database now has {count} properties")


if __name__ == "__main__":
    collect_all()