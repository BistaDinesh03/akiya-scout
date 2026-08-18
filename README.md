\# Akiya Scout



An open-source tool for discovering and analyzing publicly listed vacant and affordable houses in rural Japan.



Akiya Scout fetches property listings from public municipal Akiya bank websites, normalizes the data, and provides search, filtering, ranking, and comparison tools. The application runs without a permanent database; all property data is fetched from sources and cached temporarily in memory.



\## Features



\- Real public-source property collection

\- Search and filtering by price, land size, building size, rooms, and parking

\- Sale and rental listing separation

\- Property scoring (Akiya Score, 0-100)

\- Renovation cost estimates

\- Total-cost estimates

\- Property comparison (2-3 properties)

\- Original source links and collection timestamps

\- Map support when coordinates exist

\- In-memory caching (default: 10 minutes)



\## How It Works

User

|

v

FastAPI

|

v

Public property sources (municipal Akiya banks)

|

v

Normalize

|

v

Deduplicate

|

v

Analyze (score, renovation estimate, total cost)

|

v

Search results



text



The current version does not use a permanent database. All data is transient and refreshed from sources when the cache expires.



\## Current Sources



| Source | Area | Type | Status |

| --- | --- | --- | --- |

| Takeo City | Saga | Sale | Active |

| Aso City | Kumamoto | Rental | Active |



Additional sources may be unavailable because of access restrictions (403 responses, SSL issues, or anti-bot systems). Sources that cannot be accessed are not enabled.



\## Quick Start



Requirements: Python 3.12 or later, Windows PowerShell.



```powershell

git clone https://github.com/BistaDinesh03/akiya-scout.git

cd akiya-scout

python -m venv venv

.\\venv\\Scripts\\Activate.ps1

pip install -r requirements.txt

uvicorn app.main:app --reload

Open: http://127.0.0.1:8000



API

Endpoint	Description

/api/properties	Search and filter properties

/api/sources	List all sources and their status

/api/compare	Compare 2-3 properties

/health	Health check

/api/docs	Interactive API documentation

Configuration

Variable	Default	Description

PYTHON\_VERSION	3.12	Python runtime version

CACHE\_TTL\_SECONDS	600	Cache time-to-live in seconds

AKIYA\_ALLOW\_INSECURE\_SSL	false	Allow SSL verification bypass

Insecure SSL should remain disabled in production. Setting AKIYA\_ALLOW\_INSECURE\_SSL=true is for development only when a source has a self-signed certificate.



Testing

Run the test suite:



powershell

python -m pytest

At the time of this README update, the test suite contains 163+ passing tests. The exact count may change as tests are added or updated.



Adding a Source

Source adapters live in app/scrapers/sources/. Each adapter extends BaseScraper or HTMLScraper and implements:



get\_source\_name()



fetch()



parse()



normalize()



After creating an adapter, register it in app/scrapers/registry.py and add fixture tests in tests/fixtures/.



Data and Source Policy

Only use publicly accessible sources.



Respect robots.txt and site terms.



Do not bypass CAPTCHA, login, anti-bot systems, or access restrictions.



Preserve original source links.



Akiya Scout does not verify property ownership, condition, legality, or availability.



Property and renovation values are estimates for research purposes.



Limitations

Limited number of active sources (currently 2).



Some sources may block automated access from certain IP ranges.



Some properties lack coordinates.



Renovation estimates are approximate.



Data can change at the source without notice.



No permanent database in the current version.



Rental and sale properties are handled separately and are not compared directly.



Project Structure

text

akiya-scout/

|-- app/

|   |-- main.py

|   |-- models.py

|   |-- config.py

|   |-- scrapers/

|   |   |-- base.py

|   |   |-- registry.py

|   |   `-- sources/

|   `-- services/

|       |-- search.py

|       |-- valuation.py

|       `-- image\_validation.py

|-- templates/

|-- static/

|-- tests/

|-- requirements.txt

|-- render.yaml

`-- README.md

Contributing

See CONTRIBUTING.md.



License

MIT License. See LICENSE.txt.



Disclaimer

Akiya Scout is a research tool. It is not professional real-estate, legal, financial, construction, or valuation advice. Listing data comes from public municipal sources. Scores and cost estimates are calculated using simple configurable rules and are not professional quotes.



text



Save and close Notepad.



\## Step 2: Commit and push



```powershell

git add README.md

git commit -m "Rewrite README with professional style"

git push origin main

Let me know the output!





