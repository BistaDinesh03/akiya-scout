"""
Test Takeo scraper image extraction
"""
from app.scrapers.sources.saga_takeo import SagaTakeoScraper
from app.services.image_validation import clear_image_cache

print("=" * 60)
print("TESTING TAKEO IMAGE EXTRACTION")
print("=" * 60)

# Clear any cached validation
clear_image_cache()

scraper = SagaTakeoScraper()
try:
    # Get listings from API
    listings = scraper.fetch_listings(page=1, per_page=3)
    
    for listing in listings[:3]:
        title = listing.get('title', {}).get('rendered', '')
        link = listing.get('link', '')
        listing_id = listing.get('id')
        
        print(f"\nProperty: {listing_id}")
        print(f"Title: {title[:60]}")
        
        # Fetch detail page
        html = scraper.fetch(link)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        image_url = scraper._extract_image_url(soup)
        
        print(f"Image URL: {image_url}")
        
        if image_url and 'logo' in image_url.lower():
            print("  FAIL: Logo detected!")
        elif image_url:
            print("  OK: Property image found")
        else:
            print("  OK: No image (null)")
    
finally:
    scraper.close()

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)