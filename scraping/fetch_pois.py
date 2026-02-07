"""
Fetch Points of Interest (POIs) using H3 geoclustering and Google Places API.

Clusters listings into H3 hexagonal cells (resolution 10, ~130m across),
fetches POIs once per cell centroid, and assigns per-listing stats by pooling
results from each listing's cell + its 6 neighbors.
"""

import json
import os
import time
from pathlib import Path

import h3
import pandas as pd
import requests
import yaml

from scraping.utils import haversine_distance

H3_RESOLUTION = 10
SEARCH_RADIUS_M = 1000
POI_CACHE_PATH = Path("data/processed/poi_cache.json")

# Google Places API (New) — Nearby Search
PLACES_API_URL = "https://places.googleapis.com/v1/places:searchNearby"
FIELD_MASK = "places.id,places.displayName,places.types,places.location,places.formattedAddress"

# POI types to search, grouped into categories
POI_CATEGORIES = {
    "supermarket": ["supermarket", "grocery_store"],
    "restaurant": ["restaurant", "meal_takeaway", "meal_delivery", "cafe"],
    "pharmacy": ["pharmacy"],
    "school": ["school", "primary_school", "secondary_school"],
    "park": ["park"],
    "transit": ["transit_station", "subway_station", "bus_station", "train_station"],
    "gym": ["gym"],
    "bank": ["bank", "atm"],
    "shopping": ["shopping_mall", "clothing_store", "department_store"],
    "hospital": ["hospital", "doctor"],
    "bakery": ["bakery"],
    "bar": ["bar", "night_club"],
}

# Flat list of all types for the API call
ALL_POI_TYPES = []
for types in POI_CATEGORIES.values():
    ALL_POI_TYPES.extend(types)


def assign_h3_cells(df):
    """Add h3_cell column to DataFrame based on lat/lng coordinates."""
    def get_cell(row):
        lat = row.get("latitude")
        lng = row.get("longitude")
        if pd.notna(lat) and pd.notna(lng):
            return h3.latlng_to_cell(lat, lng, H3_RESOLUTION)
        return None

    df["h3_cell"] = df.apply(get_cell, axis=1)
    return df


def get_unique_cells(df):
    """Return all H3 cells needed: listing cells + their k=1 neighbors."""
    listing_cells = set(df["h3_cell"].dropna().unique())
    all_cells = set()
    for cell in listing_cells:
        all_cells.update(h3.grid_disk(cell, 1))
    return all_cells


def _load_cache():
    """Load POI cache from disk."""
    if POI_CACHE_PATH.exists():
        with open(POI_CACHE_PATH) as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    """Save POI cache to disk."""
    POI_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(POI_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def fetch_pois_for_cell(cell_id, api_key):
    """
    Fetch POIs for a single H3 cell centroid using Google Places Nearby Search (New).

    Returns list of POI dicts or None on error.
    """
    lat, lng = h3.cell_to_latlng(cell_id)

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    body = {
        "includedTypes": ALL_POI_TYPES,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": SEARCH_RADIUS_M,
            }
        },
        "maxResultCount": 20,
    }

    resp = requests.post(PLACES_API_URL, json=body, headers=headers, timeout=30)

    if resp.status_code != 200:
        print(f"  API error for {cell_id}: {resp.status_code} {resp.text[:200]}")
        return None

    data = resp.json()
    places = data.get("places", [])

    results = []
    for p in places:
        location = p.get("location", {})
        results.append({
            "id": p.get("id", ""),
            "name": p.get("displayName", {}).get("text", ""),
            "types": p.get("types", []),
            "lat": location.get("latitude"),
            "lng": location.get("longitude"),
            "address": p.get("formattedAddress", ""),
        })

    return results


def fetch_all_pois(df, api_key=None):
    """
    Incrementally fetch POIs for all H3 cells in the DataFrame.

    Loads cache, identifies missing cells, fetches them, and saves.
    Returns the updated cache dict.
    """
    if api_key is None:
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            api_key = config.get("google_maps_api_key")
    if api_key is None:
        api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError(
            "Google Maps API key not found. Set it in config.yaml or GOOGLE_MAPS_API_KEY env var."
        )

    cache = _load_cache()
    all_cells = get_unique_cells(df)
    missing = [c for c in all_cells if c not in cache]

    print(f"H3 cells: {len(all_cells)} total, {len(cache)} cached, {len(missing)} to fetch")

    if not missing:
        print("All cells already cached")
        return cache

    for i, cell_id in enumerate(sorted(missing)):
        pois = fetch_pois_for_cell(cell_id, api_key)
        if pois is not None:
            cache[cell_id] = pois
            print(f"  [{i+1}/{len(missing)}] {cell_id}: {len(pois)} POIs")
        else:
            # Store empty list so we don't retry on error
            cache[cell_id] = []
            print(f"  [{i+1}/{len(missing)}] {cell_id}: error (cached as empty)")

        # Rate limiting
        if i < len(missing) - 1:
            time.sleep(0.1)

    _save_cache(cache)
    print(f"Cache saved: {len(cache)} cells")

    return cache


def _categorize_poi(poi):
    """Return the category name for a POI based on its types."""
    poi_types = set(poi.get("types", []))
    for category, cat_types in POI_CATEGORIES.items():
        if poi_types & set(cat_types):
            return category
    return None


def compute_poi_stats_for_listing(listing, cache):
    """
    Compute POI statistics for a single listing.

    Pools POIs from the listing's H3 cell + its 6 neighbors,
    deduplicates by POI id, computes haversine distances, and
    returns per-category stats.
    """
    cell = listing.get("h3_cell")
    lat = listing.get("latitude")
    lng = listing.get("longitude")

    if not cell or pd.isna(lat) or pd.isna(lng):
        return {}

    # Gather POIs from cell + neighbors
    neighbor_cells = h3.grid_disk(cell, 1)
    all_pois = {}
    for c in neighbor_cells:
        for poi in cache.get(c, []):
            pid = poi.get("id")
            if pid and pid not in all_pois:
                all_pois[pid] = poi

    # Compute distances and categorize
    category_pois = {}  # category -> list of (distance_m, poi)
    for poi in all_pois.values():
        cat = _categorize_poi(poi)
        if not cat:
            continue
        poi_lat = poi.get("lat")
        poi_lng = poi.get("lng")
        if poi_lat is None or poi_lng is None:
            continue
        dist = haversine_distance(lat, lng, poi_lat, poi_lng)
        if dist <= SEARCH_RADIUS_M:
            category_pois.setdefault(cat, []).append((dist, poi))

    # Build stats
    stats = {}
    summary = {}

    for cat in POI_CATEGORIES:
        pois_with_dist = category_pois.get(cat, [])
        count = len(pois_with_dist)
        nearest = round(min(d for d, _ in pois_with_dist)) if pois_with_dist else None

        stats[f"poi_{cat}_count"] = count
        stats[f"poi_{cat}_nearest"] = nearest

        summary[cat] = {
            "count": count,
            "nearest_m": nearest,
        }

    stats["poi_summary"] = json.dumps(summary)

    return stats


def assign_poi_data_to_listings(df, cache):
    """
    Add flat POI columns to DataFrame by computing stats for each listing.
    """
    poi_rows = []
    for _, row in df.iterrows():
        stats = compute_poi_stats_for_listing(row, cache)
        poi_rows.append(stats)

    poi_df = pd.DataFrame(poi_rows, index=df.index)

    # Merge into main dataframe
    for col in poi_df.columns:
        df[col] = poi_df[col]

    return df
