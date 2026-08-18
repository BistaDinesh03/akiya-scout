\# Akiya Scout



\*\*Find Japan's Hidden Cheap Houses\*\*



Akiya Scout is a real-time search engine for Japanese akiya (abandoned/unoccupied houses) listings. It scrapes publicly accessible municipal Akiya bank websites, normalizes the data, and provides search, filtering, ranking, and comparison tools.



\## Features



\- \*\*Real-time scraping\*\* from municipal Akiya banks

\- \*\*Search \& filter\*\*: price, land size, building size, rooms, parking, prefecture

\- \*\*Ranking\*\*: cheapest, best value, largest land, lowest renovation

\- \*\*Property comparison\*\*: compare 2-3 properties side by side

\- \*\*Akiya Score (0-100)\*\*: transparent valuation breakdown

\- \*\*Estimated renovation \& total cost\*\*

\- \*\*Source transparency\*\*: original URL, collected time, refresh status

\- \*\*10-minute cache\*\*: avoids scraping on every request

\- \*\*No database\*\*: all data is transient, refreshed from sources



\## Supported Sources



| Source | Municipality | Status | Listings |

|--------|-------------|--------|----------|

| Takeo City Akiya Bank | Takeo, Saga | ✅ Active | 22+ |

| Aso City Akiya Bank | Aso, Kumamoto | ✅ Active | 3+ |

| Imari City | Imari, Saga | ⚠️ Access Restricted | - |

| Ureshino City | Ureshino, Saga | ⚠️ Access Restricted | - |

| Fukuoka Pref. | Fukuoka | ⚠️ Under Review | - |

| Kumamoto Pref. | Kumamoto | ⚠️ Under Review | - |

| Oita City | Oita | ⚠️ Under Review | - |



\## Architecture

akiya-scout/

├── app/

│ ├── main.py # FastAPI application

│ ├── models.py # Pydantic models

│ ├── config.py # Configuration

│ ├── services/

│ │ ├── search.py # Search, filter, rank, cache

│ │ ├── valuation.py # Akiya Score engine

│ │ └── image\_validation.py # Image URL validation

│ └── scrapers/

│ ├── base.py # Base scraper interface

│ ├── registry.py # Scraper registry

│ └── sources/ # Source adapters

│ ├── saga\_takeo.py

│ ├── aso\_kumamoto.py

│ └── ...

├── templates/ # HTML templates

├── static/ # CSS, JS

├── tests/ # Test suite

├── requirements.txt

├── render.yaml # Deployment config

├── .github/workflows/ # CI

└── README.md



text



\## Installation (Windows PowerShell)



\### Prerequisites



\- Python 3.12+



\### Setup



```powershell

\# Clone the repository

git clone <your-repo-url>

cd akiya-scout



\# Create virtual environment

python -m venv venv



\# Activate

.\\venv\\Scripts\\Activate.ps1



\# Install dependencies

pip install -r requirements.txt



\# Copy environment variables

copy .env.example .env



\# Run tests

python -m pytest

Running Locally

powershell

\# Activate virtual environment

.\\venv\\Scripts\\Activate.ps1



\# Start server

uvicorn app.main:app --reload



\# Or use PowerShell script

.\\run.ps1

Open: http://localhost:8000



API Endpoints

Endpoint	Description

GET /	Homepage

GET /health	Health check

GET /api/properties	Search properties

GET /api/properties/{id}	Property detail

GET /api/compare?ids=id1,id2	Compare properties

GET /api/sources	Source status

GET /api/scrape/saga-takeo	Manual scrape

GET /api/scrape/aso-kumamoto	Manual scrape

Deploying to Render

Push this repository to GitHub



Go to render.com



Click "New +" → "Web Service"



Connect your GitHub repository



Render will auto-detect render.yaml



Or manually configure:



Build Command: pip install -r requirements.txt



Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT



Environment Variables:



PYTHON\_VERSION=3.12



AKIYA\_ALLOW\_INSECURE\_SSL=false



CACHE\_TTL\_SECONDS=600



Data Source Rules

Only scrape publicly accessible data



Respect robots.txt and site terms



Do not bypass CAPTCHA, login, or anti-bot systems



Do not invent or fake listings



Preserve original source URLs



Rate limit all requests (1 second between requests)



Never use insecure SSL in production



Limitations

Property scores are for research purposes only; not professional real-estate estimates



Sources may change their HTML structure; scrapers need updates



Some sources are behind access restrictions



No database: all data is transient and refreshed on cache expiry



Disclaimer

Akiya Scout is a research tool. Listing data comes from public municipal sources. Scores and cost estimates are calculated using simple configurable rules and are not professional real-estate or renovation quotes.



License

MIT License - see LICENSE.txt



Contributing

See CONTRIBUTING.md



Topics

