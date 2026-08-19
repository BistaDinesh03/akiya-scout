"""
SQLite database module for Akiya Scout.
Stores scraped property listings for production use.
"""
import sqlite3
import logging
from typing import List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Default database path - relative to project root
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "properties.db"


def get_db_path() -> Path:
    """
    Get database path from environment or default.
    Uses AKIYA_DB_PATH if set, otherwise uses default project path.
    """
    import os
    db_path = os.getenv("AKIYA_DB_PATH", str(DEFAULT_DB_PATH))
    return Path(db_path)


def database_exists(db_path: Optional[Path] = None) -> bool:
    """Check if database file exists and has data."""
    path = db_path or get_db_path()
    return path.exists() and path.stat().st_size > 0


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Create database tables if they don't exist.
    Does NOT overwrite existing data.
    """
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            listing_type TEXT DEFAULT 'SALE',
            price INTEGER,
            prefecture TEXT,
            municipality TEXT,
            area TEXT,
            land_size_m2 REAL,
            building_size_m2 REAL,
            build_year INTEGER,
            rooms TEXT,
            structure TEXT,
            floors INTEGER,
            parking TEXT,
            description TEXT,
            source_name TEXT NOT NULL,
            source_url TEXT,
            image_url TEXT,
            latitude REAL,
            longitude REAL,
            collected_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_properties(properties: list, db_path: Optional[Path] = None) -> int:
    """
    Save properties to database using INSERT OR REPLACE.
    Does NOT delete existing data.
    Returns number of properties saved.
    """
    path = db_path or get_db_path()
    init_db(path)
    
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    saved = 0
    for prop in properties:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO properties (
                    id, title, listing_type, price, prefecture, municipality,
                    area, land_size_m2, building_size_m2, build_year, rooms,
                    structure, floors, parking, description, source_name,
                    source_url, image_url, latitude, longitude, collected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prop.id,
                prop.title,
                prop.listing_type,
                prop.price,
                prop.prefecture,
                prop.municipality,
                prop.area,
                prop.land_size_m2,
                prop.building_size_m2,
                prop.build_year,
                prop.rooms,
                prop.structure,
                prop.floors,
                prop.parking,
                prop.description,
                prop.source_name,
                prop.source_url,
                prop.image_url,
                prop.latitude,
                prop.longitude,
                prop.collected_at.isoformat() if prop.collected_at else datetime.utcnow().isoformat(),
            ))
            saved += 1
        except Exception as e:
            logger.error(f"Failed to save property {prop.id}: {e}")
    
    conn.commit()
    conn.close()
    logger.info(f"Saved {saved} properties to database at {path}")
    return saved


def load_properties(db_path: Optional[Path] = None) -> List:
    """
    Load all properties from database.
    Returns empty list if database doesn't exist (does NOT create empty DB).
    """
    from app.models import Property
    
    path = db_path or get_db_path()
    
    # Check if database exists - do NOT create empty database silently
    if not database_exists(path):
        logger.warning(f"Database not found at {path}. Returning empty list.")
        return []
    
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM properties ORDER BY collected_at DESC")
    rows = cursor.fetchall()
    
    properties = []
    for row in rows:
        try:
            prop = Property(
                id=row['id'],
                title=row['title'],
                listing_type=row['listing_type'],
                price=row['price'],
                prefecture=row['prefecture'],
                municipality=row['municipality'],
                area=row['area'],
                land_size_m2=row['land_size_m2'],
                building_size_m2=row['building_size_m2'],
                build_year=row['build_year'],
                rooms=row['rooms'],
                structure=row['structure'],
                floors=row['floors'],
                parking=row['parking'],
                description=row['description'],
                source_name=row['source_name'],
                source_url=row['source_url'] or '',
                image_url=row['image_url'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                collected_at=datetime.fromisoformat(row['collected_at']),
            )
            properties.append(prop)
        except Exception as e:
            logger.error(f"Failed to load property {row['id']}: {e}")
    
    conn.close()
    logger.info(f"Loaded {len(properties)} properties from database")
    return properties


def get_property_count(db_path: Optional[Path] = None) -> int:
    """Get count of properties in database. Returns 0 if DB missing."""
    path = db_path or get_db_path()
    
    if not database_exists(path):
        return 0
    
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM properties")
    count = cursor.fetchone()[0]
    conn.close()
    return count