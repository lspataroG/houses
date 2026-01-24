# Quick Start Guide - Parquet-Based Workflow

## ✅ What's Been Done

The project has been successfully refactored to use **parquet files** instead of a database. Here's what was completed:

### Removed
- ❌ `houses.db` (SQLite database)
- ❌ `src/backend/database.py` (schema)
- ❌ `src/backend/main.py` (FastAPI server)
- ❌ Frontend dependencies (FastAPI, uvicorn, etc.)

### Added
- ✅ `process_listings_to_parquet.py` - Convert scraped listings to parquet
- ✅ `process_search_results_to_parquet.py` - Convert search results to parquet
- ✅ `compare_search_results.py` - Compare snapshots to find new listings
- ✅ `analysis_example.ipynb` - Jupyter notebook for data analysis
- ✅ New dependencies: pandas, pyarrow, jupyter, openpyxl
- ✅ Updated Makefile with new commands
- ✅ Completely rewritten README

### Tested & Working
- ✅ Search results processing: **157 listings** extracted from 2026_01_18
- ✅ Listings processing: **152 listings** (87 Immobiliare + 65 Idealista) from 2026_01_18
- ✅ Parquet files created successfully in `data/` directory

---

## 🚀 Your New Workflow

### Today: Scrape This Week's Data

```bash
# 1. Scrape search results for this week
make scrape_search_results
# Navigate through all pages in Chrome, press ENTER for each page

# 2. Process the search results
make process_search DATE=2026_01_24

# 3. Compare with last week to find new listings
make compare PREV=2026_01_18 CURR=2026_01_24

# This creates: data/comparisons/compare_2026_01_18_to_2026_01_24_new_urls.txt
# Open that file to see which listings to scrape
```

### Then: Scrape the New Listings

```bash
# 4. Scrape the new listings
make scrape
# Use the URLs from the comparison file to navigate and scrape each new listing

# 5. Process the new listings
make process_listings DATE=2026_01_24

# 6. Analyze with pandas
uv run python
>>> import pandas as pd
>>> df = pd.read_parquet('data/listings/2026_01_24.parquet')
>>> df.head()
```

---

## 📊 What You Can Do Now

### Compare Snapshots
```python
import pandas as pd

# Load both dates
df_old = pd.read_parquet('data/listings/2026_01_18.parquet')
df_new = pd.read_parquet('data/listings/2026_01_24.parquet')

# Find new listings
new_ids = set(df_new['listing_id']) - set(df_old['listing_id'])
print(f"New listings: {len(new_ids)}")
```

### Track Price Changes
```python
# Merge on listing_id
merged = df_old.merge(
    df_new, 
    on='listing_id', 
    suffixes=('_old', '_new')
)

# Find price drops
price_drops = merged[merged['price_new'] < merged['price_old']]
print(price_drops[['title_new', 'price_old', 'price_new']])
```

### Export to Excel
```python
# Export for sharing
df_new.to_excel('listings_2026_01_24.xlsx', index=False)
```

### Find Best Deals
```python
# Sort by price per sqm
deals = df_new.sort_values('price_per_sqm').head(10)
print(deals[['title', 'price', 'surface_sqm', 'price_per_sqm']])
```

---

## 🎯 Your Next Steps

1. **Today**: Scrape this week's search results
   ```bash
   make scrape_search_results
   make process_search DATE=2026_01_24
   ```

2. **Compare with last week**:
   ```bash
   make compare PREV=2026_01_18 CURR=2026_01_24
   ```
   This will output: `data/comparisons/compare_2026_01_18_to_2026_01_24_new_urls.txt`

3. **Scrape new listings**: Use the URLs from the comparison

4. **Analyze**: Use Jupyter or pandas scripts

---

## 📁 What's in Your Data

### Current Files

```
data/
├── search_results/
│   └── 2026_01_18.parquet       # 157 search results
└── listings/
    └── 2026_01_18.parquet       # 152 full listings
```

### Schemas

**Search Results:**
- `listing_id`, `portal`, `url`, `page_number`, `position`, `search_url`, `snapshot_date`

**Listings:**
- `id`, `portal`, `url`, `title`, `description`, `price`, `surface_sqm`, `rooms`, `bathrooms`
- `floor`, `latitude`, `longitude`, `location`, `energy_class`, `elevator`, `parking`
- `has_balcony`, `has_terrace`, `has_garden`, `price_per_sqm`, `photo_count`
- `snapshot_date`, `listing_id`, `version`, `folder_path`, `image_count`

---

## 💡 Tips

- Use `make jupyter` to start Jupyter notebook for interactive analysis
- All parquet files are gitignored - they won't be committed
- Each day is a separate file, making it easy to track changes over time
- Parquet is much smaller than JSON (~70% compression)
- You can query parquet with DuckDB for SQL-like analysis

---

## 🆘 Troubleshooting

**Can't find parquet file?**
```bash
# Make sure you ran the processing step
make process_search DATE=2026_01_18
make process_listings DATE=2026_01_18
```

**Getting import errors?**
```bash
# Reinstall dependencies
make install
```

**Need to reprocess old data?**
```bash
# Process any date you've scraped
make process_all DATE=2026_01_18
```

---

For full documentation, see [README.md](README.md)
