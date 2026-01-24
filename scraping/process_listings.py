#!/usr/bin/env python3
"""
Process scraped listings into pandas dataframes.

Extracts data from listing HTML files (both Immobiliare and Idealista).
Returns dataframes - does NOT save to files.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
from bs4 import BeautifulSoup
from math import radians, sin, cos, sqrt, atan2

# Import existing extraction logic
from . import extract_immobiliare
from . import extract_idealista


def parse_listing_folder(folder_path):
    """
    Parse a single listing folder and return structured data.

    Args:
        folder_path: Path to the listing folder (e.g., data/scraped/2026_01_18/immo_123_v1)

    Returns:
        dict: Extracted listing data or None if parsing fails
    """
    folder_path = Path(folder_path)
    folder_name = folder_path.name

    # Extract portal and listing ID from folder name
    # Format: {portal}_{id}_v{version}
    match = re.match(r'(immo|ideal)_(\d+)_v(\d+)', folder_name)
    if not match:
        return None

    portal_prefix, listing_id, version = match.groups()
    portal = 'immobiliare' if portal_prefix == 'immo' else 'idealista'

    # Read URL
    url_path = folder_path / 'url.txt'
    url = None
    if url_path.exists():
        with open(url_path, 'r', encoding='utf-8') as f:
            url = f.read().strip()

    # Extract data using existing extraction scripts
    try:
        if portal == 'immobiliare':
            data = extract_immobiliare.process_listing(folder_path)
        else:
            data = extract_idealista.process_listing(folder_path)

        if data:
            # Add metadata
            data['listing_id'] = f"{portal_prefix}_{listing_id}"
            data['portal'] = portal
            data['version'] = int(version)
            data['url'] = url
            data['folder_path'] = str(folder_path)

            # Count media files
            image_count = len([f for f in folder_path.iterdir() if f.name.startswith('image_')])
            data['image_count'] = image_count

        return data
    except Exception:
        return None


def process_listings_directory(date_dir, date_str=None):
    """
    Process all listings from a date directory.

    Processes BOTH Immobiliare and Idealista listings.

    Args:
        date_dir: Path to date directory (e.g., data/scraped/2026_01_18)
        date_str: Date string (optional, extracted from directory name if not provided)

    Returns:
        pandas.DataFrame: Listings with columns including:
            - listing_id: unique ID (e.g., "immo_123456")
            - portal: "immobiliare" or "idealista"
            - url: full listing URL
            - title: listing title
            - price: price in euros
            - surface_sqm: size in square meters
            - rooms: number of rooms
            - bathrooms: number of bathrooms
            - floor: floor number
            - latitude, longitude: coordinates
            - energy_class: energy rating
            - has_elevator, has_balcony, etc.: boolean features
            - image_count: number of images downloaded
            - snapshot_date: date of the snapshot
    """
    date_dir = Path(date_dir)

    if not date_dir.exists():
        return pd.DataFrame()

    # Get date from directory name if not provided
    if not date_str:
        date_str = date_dir.name

    # Collect all listing folders (exclude search_results)
    listing_folders = [
        item for item in date_dir.iterdir()
        if item.is_dir() and item.name != 'search_results'
    ]

    if not listing_folders:
        return pd.DataFrame()

    # Parse all listings
    listings_data = []

    for folder in sorted(listing_folders):
        data = parse_listing_folder(folder)
        if data:
            listings_data.append(data)

    if not listings_data:
        return pd.DataFrame()

    # Create dataframe
    df = pd.DataFrame(listings_data)

    # Add snapshot date
    try:
        df['snapshot_date'] = pd.to_datetime(date_str, format='%Y_%m_%d')
    except:
        df['snapshot_date'] = pd.Timestamp.now()

    # Clean and normalize data
    df = clean_listings_dataframe(df)

    return df


def clean_listings_dataframe(df):
    """
    Clean and normalize the listings dataframe.
    """
    if df.empty:
        return df

    # Ensure numeric columns
    numeric_cols = ['price', 'bathrooms', 'latitude', 'longitude',
                    'price_per_sqm', 'image_count', 'version',
                    'photo_count', 'plan_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Normalize room counts (handle "5+", "4 locali", etc.)
    if 'rooms' in df.columns:
        df['rooms_count'] = df['rooms'].apply(_extract_room_count)

    # Extract numeric surface
    if 'surface_sqm' in df.columns:
        df['surface_numeric'] = df['surface_sqm'].apply(_extract_surface)

    # Clean boolean columns - handle mixed types
    boolean_cols = ['has_elevator', 'has_ac', 'has_garden', 'has_cellar',
                    'has_balcony', 'has_terrace', 'is_luxury', 'has_parking',
                    'has_virtual_tour', 'has_air_conditioning']
    for col in boolean_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: bool(x) if pd.notna(x) and x != '' and x != 'N/A' else False)

    # Ensure string columns are strings
    string_cols = ['title', 'description', 'address', 'floor', 'energy_class',
                   'heating', 'condition', 'listing_id', 'portal', 'url',
                   'folder_path', 'location']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str)

    # Handle mixed type columns (like elevator which might be dict/bool/str)
    problematic_cols = ['elevator', 'air_conditioning']
    for col in problematic_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else '')

    # Sort by listing_id and version (keep latest version per listing)
    if 'listing_id' in df.columns and 'version' in df.columns:
        df = df.sort_values(['listing_id', 'version'], ascending=[True, False])

    return df


def _extract_room_count(rooms_str):
    """Extract numeric room count from room string."""
    if pd.isna(rooms_str):
        return None
    match = re.search(r'(\d+)', str(rooms_str))
    if match:
        return int(match.group(1))
    return None


def _extract_surface(surface_str):
    """Extract numeric surface from surface string."""
    if pd.isna(surface_str):
        return None
    match = re.search(r'(\d+)', str(surface_str).replace('.', '').replace(',', ''))
    if match:
        return int(match.group(1))
    return None


def get_latest_version(df):
    """
    Keep only the latest version of each listing.

    Args:
        df: DataFrame with listing_id and version columns

    Returns:
        DataFrame with only the latest version of each listing
    """
    if 'listing_id' not in df.columns or 'version' not in df.columns:
        return df

    return df.loc[df.groupby('listing_id')['version'].idxmax()]


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in meters between two points on Earth.

    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point

    Returns:
        Distance in meters
    """
    R = 6371000  # Earth's radius in meters

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def find_duplicates(df, distance_threshold=100, surface_tolerance=5):
    """
    Find duplicate listings across different portals.

    A duplicate is identified when:
    - Distance between coordinates is within threshold (default 100m)
    - Price is exactly the same
    - Surface area is within tolerance (default 5 sqm)

    Each Idealista listing is matched to at most one Immobiliare listing
    (the closest one if multiple matches exist).

    Args:
        df: DataFrame with listings from multiple portals
        distance_threshold: Maximum distance in meters to consider a duplicate
        surface_tolerance: Maximum surface difference in sqm (default 5)

    Returns:
        List of tuples (immobiliare_idx, idealista_idx) of duplicate pairs
    """
    # Split by portal
    immo_df = df[df['portal'] == 'immobiliare'].copy()
    ideal_df = df[df['portal'] == 'idealista'].copy()

    # For each Idealista listing, find the best matching Immobiliare listing
    # Best = closest distance with exact same price and similar surface
    ideal_to_immo = {}  # ideal_idx -> (immo_idx, distance)

    for ideal_idx, ideal_row in ideal_df.iterrows():
        # Skip if no coordinates
        if pd.isna(ideal_row.get('latitude')) or pd.isna(ideal_row.get('longitude')):
            continue

        ideal_price = ideal_row.get('price')
        if pd.isna(ideal_price) or ideal_price == 0:
            continue

        ideal_surface = ideal_row.get('surface_numeric')

        best_match = None
        best_distance = float('inf')

        for immo_idx, immo_row in immo_df.iterrows():
            # Skip if no coordinates
            if pd.isna(immo_row.get('latitude')) or pd.isna(immo_row.get('longitude')):
                continue

            immo_price = immo_row.get('price')
            if pd.isna(immo_price) or immo_price == 0:
                continue

            # Check exact price match
            if immo_price != ideal_price:
                continue

            # Check surface similarity (if both have surface data)
            immo_surface = immo_row.get('surface_numeric')
            if pd.notna(ideal_surface) and pd.notna(immo_surface):
                if abs(immo_surface - ideal_surface) > surface_tolerance:
                    continue

            # Check distance
            distance = haversine_distance(
                immo_row['latitude'], immo_row['longitude'],
                ideal_row['latitude'], ideal_row['longitude']
            )

            if distance > distance_threshold:
                continue

            # Found a potential match - keep the closest one
            if distance < best_distance:
                best_distance = distance
                best_match = immo_idx

        if best_match is not None:
            ideal_to_immo[ideal_idx] = (best_match, best_distance)

    # Convert to list of tuples (immo_idx, ideal_idx)
    duplicates = [(immo_idx, ideal_idx) for ideal_idx, (immo_idx, _) in ideal_to_immo.items()]

    return duplicates


def merge_listing_data(primary_row, secondary_row):
    """
    Merge data from secondary listing into primary listing.

    Fills in empty/null fields in primary with values from secondary.
    Also stores reference to the duplicate listing.

    Args:
        primary_row: Series - the primary listing (Immobiliare)
        secondary_row: Series - the secondary listing (Idealista)

    Returns:
        Series with merged data
    """
    merged = primary_row.copy()

    # Store reference to the duplicate
    merged['duplicate_id'] = secondary_row.get('listing_id', secondary_row.name)
    merged['duplicate_portal'] = secondary_row.get('portal', 'idealista')
    merged['duplicate_url'] = secondary_row.get('url', '')
    merged['duplicate_folder_path'] = secondary_row.get('folder_path', '')

    # Fields to potentially merge from secondary
    merge_fields = [
        'description', 'surface_sqm', 'surface_commercial', 'surface_usable',
        'rooms', 'bathrooms', 'floor', 'elevator', 'building_year', 'condition',
        'heating', 'energy_class', 'has_balcony', 'has_terrace', 'has_garden',
        'has_cellar', 'has_air_conditioning', 'parking', 'condominium_fees',
        'characteristics', 'bedrooms', 'floors_building', 'kitchen', 'furnished',
        'availability', 'features', 'primary_features', 'main_features',
        'floor_plan_indices'
    ]

    for field in merge_fields:
        if field not in merged.index:
            continue

        primary_val = merged.get(field)
        secondary_val = secondary_row.get(field)

        # Check if primary is empty/null
        is_primary_empty = (
            pd.isna(primary_val) or
            primary_val == '' or
            primary_val == 'N/A' or
            (isinstance(primary_val, (list, np.ndarray)) and len(primary_val) == 0)
        )

        # Check if secondary has value
        has_secondary_value = (
            pd.notna(secondary_val) and
            secondary_val != '' and
            secondary_val != 'N/A' and
            not (isinstance(secondary_val, (list, np.ndarray)) and len(secondary_val) == 0)
        )

        if is_primary_empty and has_secondary_value:
            merged[field] = secondary_val

    # Merge image info - keep higher image count
    if secondary_row.get('image_count', 0) > merged.get('image_count', 0):
        # Store alternate folder path for images
        merged['alt_folder_path'] = secondary_row.get('folder_path', '')
        merged['alt_image_count'] = secondary_row.get('image_count', 0)

    # Merge floor plans if secondary has them and primary doesn't
    primary_plans = merged.get('floor_plan_indices', [])
    secondary_plans = secondary_row.get('floor_plan_indices', [])
    if (not primary_plans or len(primary_plans) == 0) and secondary_plans and len(secondary_plans) > 0:
        merged['floor_plan_indices'] = secondary_plans
        # Note: floor plans from secondary need the secondary folder path
        merged['floor_plan_folder'] = secondary_row.get('folder_path', '')

    return merged


def deduplicate_listings(df, distance_threshold=100):
    """
    Remove duplicate listings across portals, keeping Immobiliare and merging Idealista data.

    Args:
        df: DataFrame with listings from multiple portals
        distance_threshold: Maximum distance in meters to consider a duplicate

    Returns:
        DataFrame with duplicates removed and data merged
    """
    if df.empty:
        return df

    # Find duplicates (requires exact price match)
    duplicates = find_duplicates(df, distance_threshold)

    if not duplicates:
        return df

    print(f"Found {len(duplicates)} duplicate listings")

    # Get indices of idealista listings that are duplicates
    idealista_duplicates = set(ideal_idx for _, ideal_idx in duplicates)

    # Merge data into immobiliare listings
    for immo_idx, ideal_idx in duplicates:
        immo_row = df.loc[immo_idx]
        ideal_row = df.loc[ideal_idx]

        print(f"  Merging: {ideal_row.get('listing_id', ideal_idx)} -> {immo_row.get('listing_id', immo_idx)}")

        merged_row = merge_listing_data(immo_row, ideal_row)
        df.loc[immo_idx] = merged_row

    # Remove the duplicate idealista listings
    df = df.drop(index=list(idealista_duplicates))

    print(f"Removed {len(idealista_duplicates)} duplicate Idealista listings")

    return df
