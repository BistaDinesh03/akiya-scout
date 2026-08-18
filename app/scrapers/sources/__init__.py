"""
Scraper sources package for Akiya Scout
"""
from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.scrapers.sources.another_source import AnotherSourceScraper
from app.scrapers.sources.fukuoka_akiyabank import FukuokaAkiyaBankScraper
from app.scrapers.sources.kumamoto_akiyabank import KumamotoAkiyaBankScraper
from app.scrapers.sources.oita_akiyabank import OitaAkiyaBankScraper
from app.scrapers.sources.imari_saga import ImariSagaScraper
from app.scrapers.sources.ureshino_saga import UreshinoSagaScraper
from app.scrapers.sources.aso_kumamoto import AsoKumamotoScraper

__all__ = [
    'SagaTakeoScraper',
    'AnotherSourceScraper',
    'FukuokaAkiyaBankScraper',
    'KumamotoAkiyaBankScraper',
    'OitaAkiyaBankScraper',
    'ImariSagaScraper',
    'UreshinoSagaScraper',
    'AsoKumamotoScraper',
]