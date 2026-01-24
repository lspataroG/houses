# HouseHunter

Real estate listing tracker for Bologna with web frontend and AI-powered analysis.

## Features

- **Multi-portal scraping**: Immobiliare.it and Idealista.it
- **Duplicate detection**: Matches listings across portals by price, surface, and location
- **Sold tracking**: Detects when listings disappear from search results
- **AI analysis**: Gemini extracts missing fields and generates summaries from descriptions/floor plans
- **Web frontend**: React app with map view, filters, favorites, and image galleries

## Quick Start

```bash
# Install dependencies
make install

# Run the web app
make backend   # API on port 8000
make frontend  # React app on port 5173
```

Open http://localhost:5173

## Project Structure

```
/houses
├── househunter_workflow.ipynb  # Data processing notebook
├── scraping/                   # Python modules
│   ├── extract_immobiliare.py
│   ├── extract_idealista.py
│   ├── utils.py               # Deduplication
│   └── derive_fields.py       # AI field extraction
├── src/
│   ├── backend/api/           # FastAPI server
│   └── frontend/              # React + Vite + Tailwind
├── data/
│   ├── scraped/               # Raw HTML + images by date
│   └── processed/             # Final parquet + user state
└── Makefile
```

## Workflow

1. **Scrape** search results and listings (manual browser)
2. **Process** in Jupyter notebook:
   - Parse HTML into dataframe
   - Deduplicate across portals
   - Derive missing fields with AI
   - Save to parquet
3. **Browse** via web frontend with map and filters

## Data Pipeline

The notebook (`househunter_workflow.ipynb`) runs these steps:

1. Load search results from all scrape dates
2. Detect new/sold listings by comparing dates
3. Parse listing HTML files
4. Deduplicate (exact price + surface + 100m distance)
5. Derive fields with Gemini (summary, bedrooms, etc.)
6. Save to `data/processed/listings.parquet`

## Web Frontend

- Split view: listing cards + interactive map
- Filters: Active, Sold, Favorites, Removed
- Image gallery with lightbox and floor plans
- AI-generated summary on each card
- Click active listings to open on portal
- Click sold listings to view saved details

## AI Field Extraction

Uses Gemini with two separate API calls:

1. **Attributes** (from description text):
   - Summary: 2-3 sentences highlighting best features
   - Extracted: bedrooms, bathrooms, balconies, terraces, cantina, garage, elevator, heating, AC, condition

2. **Beauty score** (from property images):
   - Score 1-5 rating based on interior quality and finishes
   - Notes explaining the rating

Results are cached in `data/processed/derived_fields.json` and flattened into the parquet file. Only processes listings not already in cache (incremental).

## Commands

```bash
make install        # Install dependencies
make backend        # Start API server (port 8000)
make frontend       # Start React dev server (port 5173)
make jupyter        # Open Jupyter notebook
make scrape         # Scrape individual listings
make scrape_search  # Scrape search result pages
```

## Requirements

- Python 3.11+ with uv
- Node.js 18+ for frontend
- Google Cloud auth for Vertex AI (Gemini)
