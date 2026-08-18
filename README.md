# Akiya Scout

A transparent, open-source research tool for discovering and analyzing publicly listed vacant properties in rural Japan.

## Overview

Akiya Scout provides structured access to rural property data from municipal Akiya bank websites across Japan. The application aggregates public listings, normalizes diverse data formats, and enables intelligent search and analysis without requiring a permanent database.

All data is sourced from publicly accessible municipal websites. Property information is cached temporarily in memory and automatically refreshed, ensuring current data availability.

## Key Features

- **Public Data Source**: Aggregates listings from official municipal Akiya banks
- **Advanced Search & Filtering**: Filter by price, land size, building dimensions, room count, and parking availability
- **Property Scoring**: Akiya Score system (0-100 scale) for comparative analysis
- **Cost Estimation**: Renovation and total ownership cost calculations
- **Property Comparison**: Side-by-side analysis of 2-3 properties
- **Source Transparency**: Direct links to original listings with collection timestamps
- **Mapping Support**: Geographic visualization where coordinates are available
- **Efficient Caching**: In-memory data management with configurable cache duration (default: 10 minutes)
- **Separate Listing Types**: Sale and rental properties handled independently for clarity

## How It Works

```
User Query
    ↓
FastAPI Server
    ↓
Public Municipal Sources (Akiya Banks)
    ↓
Data Normalization Layer
    ↓
Deduplication & Analysis
    ↓
Property Scoring & Cost Estimation
    ↓
Search Results
```

The system operates as a stateless aggregator. All property data is sourced from public municipal websites and cached temporarily—no permanent database is maintained.

## Current Data Sources

| Source | Prefecture | Region | Property Type | Status |
|--------|-----------|--------|---------------|--------|
| Takeo City | Saga | Rural | For Sale | Active |
| Aso City | Kumamoto | Mountain | For Rent | Active |

**Note**: Some municipal Akiya banks cannot be accessed due to technical barriers (403 responses, SSL certificate issues, or active bot detection). Unavailable sources are not activated in this version.

## Getting Started

### Requirements

- Python 3.12 or later
- Windows PowerShell (or equivalent shell environment)
- Git

### Installation

```powershell
git clone https://github.com/BistaDinesh03/akiya-scout.git
cd akiya-scout
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open your browser and navigate to: **http://127.0.0.1:8000**

### Verify Installation

- **API Docs**: http://127.0.0.1:8000/api/docs
- **Health Check**: http://127.0.0.1:8000/health

## API Reference

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/properties` | GET | Search and filter property listings |
| `/api/sources` | GET | List all sources and operational status |
| `/api/compare` | POST | Compare 2-3 properties in detail |
| `/health` | GET | System health verification |
| `/api/docs` | GET | Interactive Swagger documentation |

### Example Query

```
GET /api/properties?price_max=5000000&land_size_min=200&rooms_min=3
```

## Configuration

| Environment Variable | Default Value | Description |
|----------------------|---------------|-------------|
| `PYTHON_VERSION` | 3.12 | Required Python runtime version |
| `CACHE_TTL_SECONDS` | 600 | Cache duration in seconds (10 minutes) |
| `AKIYA_ALLOW_INSECURE_SSL` | false | Allow connections with self-signed certificates |

**Security Note**: `AKIYA_ALLOW_INSECURE_SSL` should remain `false` in production environments. Enable this only during development when accessing sources with self-signed SSL certificates.

## Testing

The project includes a comprehensive test suite to ensure data quality and system reliability:

```powershell
python -m pytest
```

**Current Status**: 163+ passing tests. Test coverage continues to expand as new features are added.

## Project Architecture

```
akiya-scout/
├── app/
│   ├── main.py                    # Application entry point
│   ├── models.py                  # Data models and schemas
│   ├── config.py                  # Configuration management
│   ├── scrapers/
│   │   ├── base.py               # Base scraper classes
│   │   ├── registry.py           # Source registration
│   │   └── sources/              # Individual source adapters
│   └── services/
│       ├── search.py             # Search and filtering logic
│       ├── valuation.py          # Cost estimation algorithms
│       └── image_validation.py   # Image analysis utilities
├── templates/                     # HTML templates
├── static/                        # Static assets (CSS, JavaScript)
├── tests/                         # Test suite and fixtures
├── requirements.txt               # Python dependencies
├── render.yaml                    # Deployment configuration
└── README.md                      # This file
```

## Adding a New Data Source

### Creating a Source Adapter

Source adapters are located in `app/scrapers/sources/`. Each adapter must inherit from either `BaseScraper` or `HTMLScraper` and implement these required methods:

```python
def get_source_name() -> str
    """Return the unique identifier for this source"""

def fetch() -> bytes or str
    """Retrieve raw data from the public source"""

def parse() -> list[dict]
    """Parse raw data into structured format"""

def normalize() -> list[Property]
    """Convert to standard Property model"""
```

### Registration

1. Create your adapter file in `app/scrapers/sources/`
2. Register the adapter in `app/scrapers/registry.py`
3. Add test fixtures in `tests/fixtures/`
4. Run the test suite: `python -m pytest`

## Data & Source Policy

Akiya Scout operates under strict ethical guidelines for public data access:

- **Public Access Only**: Source exclusively from publicly accessible data sources
- **Respect Robots.txt**: Honor website crawling policies and terms of service
- **No Access Bypassing**: Do not attempt to bypass CAPTCHA, login systems, rate limiting, or other access restrictions
- **Preserve Attribution**: Maintain direct links to original property listings
- **Compliance First**: Follow all applicable laws and regulations regarding web access

## Limitations & Important Disclaimers

### Technical Limitations

- Limited number of active sources (currently 2 municipalities)
- Some sources may implement IP-based rate limiting or geographic restrictions
- Approximately 30-40% of properties lack geographic coordinates
- Renovation cost estimates are approximate calculations, not professional quotes
- Source data can change or become unavailable without notice
- No permanent database—data is cached temporarily only

### Data Limitations

- Properties are not verified for actual availability, condition, or legal status
- Sale and rental properties are maintained separately and not cross-compared
- Akiya Score is a research tool, not a professional property appraisal
- Cost estimates are calculated using simplified configurable algorithms

### Legal & Professional Disclaimer

**Akiya Scout is provided for research and informational purposes only.**

This tool is not a substitute for:
- Professional real estate consultation
- Legal advice from qualified attorneys
- Financial advisory services
- Structural engineering assessments
- Licensed property appraisals

All property data originates from public municipal sources. Akiya Scout makes no guarantee regarding property ownership, condition, legality, or actual availability. Users are solely responsible for conducting independent verification and due diligence before any property transaction.

## Contributing

Contributions are welcome. Please review **CONTRIBUTING.md** for guidelines on code standards, testing requirements, and submission procedures.

## License

Akiya Scout is distributed under the **MIT License**. See **LICENSE.txt** for full terms.

## Support & Questions

For issues, questions, or suggestions:

1. Check existing GitHub issues
2. Review the API documentation at `/api/docs` (when running locally)
3. Submit a new issue with detailed information about your question or problem

---

**Last Updated**: 2026  
**Status**: Active Development  
**Python Support**: 3.12+
