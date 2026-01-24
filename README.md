# 🏠 HouseHunter Pro: Local Real Estate Archive

**Project Type:** Python Data Pipeline (Pandas + Parquet + Jupyter)
**Objective:** Scrape and analyze real estate listings from Idealista/Immobiliare using parquet files, pandas dataframes, and Jupyter notebooks.

---

## 🏗 Architecture

### Jupyter-First Workflow
This project uses **Jupyter notebooks** for all data processing and analysis. Raw scraping is done via command-line tools, but everything else happens in notebooks.

### The Data Flow

```
1. SCRAPE → Raw HTML + Images (command line)
2. PROCESS → Jupyter notebook imports functions and creates dataframes
3. ANALYZE → All analysis in Jupyter with pandas
4. EXPORT → Save to parquet, Excel, or CSV
```

---

## 📁 Project Structure

```
/houses
├── househunter_workflow.ipynb     # Main Jupyter notebook (your workflow)
├── scraping/                      # Python modules (imported by notebook)
│   ├── __init__.py
│   ├── process_listings_to_parquet.py
│   ├── process_search_results_to_parquet.py
│   ├── compare_search_results.py
│   ├── extract_immobiliare.py
│   └── extract_idealista.py
├── src/backend/                   # Scraping scripts
│   ├── manual_scraper.py          # Listing scraper
│   └── manual_scraper_search.py   # Search results scraper
├── data/
│   ├── scraped/                   # Raw HTML + images
│   │   └── YYYY_MM_DD/            # Daily snapshots
│   ├── listings/                  # Processed parquet files
│   ├── search_results/            # Processed search results
│   └── comparisons/               # Comparison outputs
├── Makefile                       # Helper commands
└── README.md                      # This file
```

---

## 🚀 Quick Start

### 1. Installation

```bash
make install
```

This installs all dependencies and Playwright browsers.

### 2. Scraping (Week 1)

```bash
# Scrape search results
make scrape_search_results
# Navigate through all pages in Chrome, press ENTER for each page

# Scrape individual listings (optional for week 1)
make scrape
# Navigate to listings, press ENTER for each
```

**Output:** `data/scraped/2026_01_18/` (or whatever today's date is)

### 3. Processing & Analysis

```bash
# Open Jupyter
make jupyter

# Then open: househunter_workflow.ipynb
# Follow the notebook cells to process and analyze data
```

The notebook will:
- Process search results → dataframe → parquet
- Process listings → dataframe → parquet
- Compare snapshots to find new listings
- Analyze and visualize the data
- Export to Excel

### 4. Next Week (Week 2)

```bash
# Scrape this week's search results
make scrape_search_results

# Open Jupyter
make jupyter

# In the notebook:
# - Update CURRENT_DATE to this week
# - Run cells to process new search results
# - Compare with last week to find NEW listings
# - The comparison outputs URLs to scrape

# Scrape only the NEW listings
make scrape
# Use the URLs from comparison output

# Process new listings in notebook
```

---

## 📊 The Jupyter Notebook Workflow

Open `househunter_workflow.ipynb` and follow these sections:

### Section 1: Process Search Results
```python
# Imports functions from scraping/ module
from scraping import process_search_results_directory

# Processes HTML → pandas dataframe → parquet
df_search = process_search_results_directory(...)
```

### Section 2: Process Listings
```python
from scraping import process_date_directory

# Processes listing HTML → pandas dataframe → parquet
df_listings = process_date_directory(...)
```

### Section 3: Compare Snapshots
```python
from scraping import compare_snapshots

# Compares two weeks, finds new listings
comparison = compare_snapshots(current, previous)
new_listings = comparison['new']  # URLs to scrape
```

### Section 4: Analyze Data
```python
# All standard pandas operations
df = pd.read_parquet('data/listings/2026_01_24.parquet')

# Filter
best_deals = df.nsmallest(10, 'price_per_sqm')

# Visualize
df['price'].hist()

# Export
df.to_excel('listings.xlsx')
```

---

## 🎯 Portal Targets

### Immobiliare.it
```
https://www.immobiliare.it/vendita-case/bologna/centro/
  ?prezzoMinimo=450000&prezzoMassimo=700000
  &superficieMinima=120&localiMinimo=4
```

### Idealista.it
```
https://www.idealista.it/vendita-case/bologna/centro/
  con-prezzo_700000,prezzo-min_450000,
  dimensione_120,quadrilocali-4
```

---

## 🛠 Available Commands

```bash
make install               # Install all dependencies
make scrape                # Scrape individual listings
make scrape_search_results # Scrape search result pages
make jupyter               # Open Jupyter notebook
```

**All processing happens in the Jupyter notebook!**

---

## 📦 Dependencies

**Core:**
- `pandas` - Data manipulation
- `pyarrow` - Parquet file support
- `jupyter` - Notebook interface
- `playwright` - Browser automation
- `beautifulsoup4` - HTML parsing

**Optional:**
- `openpyxl` - Excel export
- `matplotlib` - Visualizations

---

## 💡 Key Benefits

### Why Jupyter?
- **Interactive**: See results immediately, iterate quickly
- **Reproducible**: Re-run cells as needed
- **Visual**: Built-in plotting and dataframe display
- **Flexible**: Import functions from `scraping/` module
- **Shareable**: Export notebooks or Excel files

### Why Parquet?
- **Fast**: Columnar format, optimized for analytics
- **Small**: ~70% compression vs JSON
- **Typed**: Preserves data types (dates, numbers, booleans)
- **Portable**: Works with pandas, DuckDB, Spark, etc.

### Why Daily Snapshots?
- **Track changes**: Compare this week vs last week
- **Price history**: See price drops over time
- **Market trends**: Analyze listing velocity
- **Incremental**: Only scrape new listings

---

## 📁 Data Schema

### Search Results Parquet
```python
{
    'listing_id': 'immo_123456',
    'portal': 'immobiliare',
    'url': 'https://...',
    'page_number': 1,
    'position': 5,
    'search_url': 'https://...',
    'snapshot_date': '2026-01-24'
}
```

### Listings Parquet
```python
{
    'listing_id': 'immo_123456',
    'portal': 'immobiliare',
    'url': 'https://...',
    'title': 'Apartment in Centro',
    'price': 550000,
    'surface_sqm': '120 m2',
    'rooms': '4 locali',
    'bathrooms': 2,
    'floor': '2',
    'latitude': 44.4949,
    'longitude': 11.3426,
    'price_per_sqm': 4583,
    'energy_class': 'E',
    'has_elevator': True,
    'photo_count': 15,
    'snapshot_date': '2026-01-24'
}
```

---

## 🔍 Example Analyses

### Find Best Deals
```python
df = pd.read_parquet('data/listings/2026_01_24.parquet')
df.nsmallest(10, 'price_per_sqm')
```

### Compare Prices
```python
df_old = pd.read_parquet('data/listings/2026_01_18.parquet')
df_new = pd.read_parquet('data/listings/2026_01_24.parquet')

merged = df_old.merge(df_new, on='listing_id', suffixes=('_old', '_new'))
price_drops = merged[merged['price_new'] < merged['price_old']]
```

### Custom Filters
```python
filtered = df[
    (df['price'] >= 450000) &
    (df['price'] <= 650000) &
    (df['surface_numeric'] >= 120)
]
```

### Export to Excel
```python
df.to_excel('listings_2026_01_24.xlsx', index=False)
```

---

## 📝 Notes

- Scrapers save to `data/scraped/` instead of `src/backend/storage/`
- All processing happens in Jupyter notebook
- Import functions from `scraping/` module
- Parquet files are gitignored
- Each week is a separate snapshot

---

## 🎓 Tips

1. **Weekly workflow**: Scrape search results → compare → scrape new listings
2. **Version dates**: Use `YYYY_MM_DD` format consistently
3. **Notebook workflow**: Process → analyze → export, all in one place
4. **Reusable functions**: Import from `scraping/` module
5. **Interactive analysis**: Iterate quickly in Jupyter

---

## 🆘 Troubleshooting

**Can't import scraping module?**
```python
import sys
sys.path.insert(0, '/Users/lspataro/projects/houses')
from scraping import process_date_directory
```

**Chrome not starting?**
```bash
# Close all Chrome windows first
pkill -9 Chrome
make scrape
```

**Module not found?**
```bash
make install  # Reinstall dependencies
```

---

For quick reference, see [QUICK_START.md](QUICK_START.md)
