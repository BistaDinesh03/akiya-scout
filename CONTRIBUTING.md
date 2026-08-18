\# Contributing to Akiya Scout



\## Development Setup



1\. Fork and clone the repository

2\. Create a virtual environment:

&#x20;  ```powershell

&#x20;  python -m venv venv

&#x20;  .\\venv\\Scripts\\Activate.ps1

Install dependencies:



powershell

pip install -r requirements.txt

Run tests:



powershell

python -m pytest

Adding a New Scraper

Create a new file in app/scrapers/sources/



Extend BaseScraper or HTMLScraper



Implement: get\_source\_name(), fetch(), parse(), normalize()



Add fixture tests in tests/fixtures/



Register the scraper in app/scrapers/registry.py



Run tests



Data Source Rules

Only scrape publicly accessible data



Respect robots.txt



Do not bypass CAPTCHA, login, or anti-bot systems



Do not invent or fake listings



Preserve original source URLs



Rate limit all requests

