"""Utility functions for processing listings."""

import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in meters between two points on Earth.
    """
    R = 6371000  # Earth's radius in meters

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c


def find_duplicates(df, distance_threshold=150):
    """
    Find duplicate listings across different portals.

    A duplicate is identified when:
    - Distance between coordinates is within threshold (default 100m)
    - Price is exactly the same
    - Surface area is exactly the same

    Each Idealista listing is matched to at most one Immobiliare listing
    (the closest one if multiple matches exist).

    Returns:
        List of tuples (immobiliare_idx, idealista_idx) of duplicate pairs
    """
    # Split by portal
    immo_df = df[df['portal'] == 'immobiliare'].copy()
    ideal_df = df[df['portal'] == 'idealista'].copy()

    ideal_to_immo = {}

    for ideal_idx, ideal_row in ideal_df.iterrows():
        if pd.isna(ideal_row.get('latitude')) or pd.isna(ideal_row.get('longitude')):
            continue

        ideal_price = ideal_row.get('price')
        if pd.isna(ideal_price) or ideal_price == 0:
            continue

        ideal_surface = ideal_row.get('surface_numeric')

        best_match = None
        best_distance = float('inf')

        for immo_idx, immo_row in immo_df.iterrows():
            if pd.isna(immo_row.get('latitude')) or pd.isna(immo_row.get('longitude')):
                continue

            immo_price = immo_row.get('price')
            if pd.isna(immo_price) or immo_price == 0:
                continue

            # Check exact price match
            if immo_price != ideal_price:
                continue

            # Check exact surface match
            immo_surface = immo_row.get('surface_numeric')
            if pd.notna(ideal_surface) and pd.notna(immo_surface):
                if immo_surface != ideal_surface:
                    continue

            # Check distance
            distance = haversine_distance(
                immo_row['latitude'], immo_row['longitude'],
                ideal_row['latitude'], ideal_row['longitude']
            )

            if distance > distance_threshold:
                continue

            if distance < best_distance:
                best_distance = distance
                best_match = immo_idx

        if best_match is not None:
            ideal_to_immo[ideal_idx] = (best_match, best_distance)

    return [(immo_idx, ideal_idx) for ideal_idx, (immo_idx, _) in ideal_to_immo.items()]


def merge_listing_data(primary_row, secondary_row):
    """
    Merge data from secondary listing into primary listing.
    Fills in empty/null fields in primary with values from secondary.
    """
    merged = primary_row.copy()

    # Store reference to the duplicate
    merged['duplicate_id'] = secondary_row.get('listing_id', secondary_row.name)
    merged['duplicate_url'] = secondary_row.get('url', '')

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

    def is_empty(val):
        if val is None:
            return True
        if isinstance(val, (list, np.ndarray)):
            return len(val) == 0
        try:
            if pd.isna(val):
                return True
        except (ValueError, TypeError):
            pass
        if val == '' or val == 'N/A':
            return True
        return False

    for field in merge_fields:
        if field not in merged.index:
            continue

        primary_val = merged.get(field)
        secondary_val = secondary_row.get(field)

        if is_empty(primary_val) and not is_empty(secondary_val):
            merged[field] = secondary_val

    return merged


def deduplicate_listings(df, distance_threshold=150, verbose=True):
    """
    Remove duplicate listings across portals, keeping Immobiliare and merging Idealista data.

    Args:
        df: DataFrame with listings from multiple portals
        distance_threshold: Maximum distance in meters to consider a duplicate
        verbose: Print progress messages

    Returns:
        DataFrame with duplicates removed and data merged
    """
    if df.empty:
        return df

    duplicates = find_duplicates(df, distance_threshold)

    if not duplicates:
        if verbose:
            print("No duplicates found")
        return df

    if verbose:
        print(f"Found {len(duplicates)} duplicate listings")

    idealista_duplicates = set(ideal_idx for _, ideal_idx in duplicates)

    for immo_idx, ideal_idx in duplicates:
        immo_row = df.loc[immo_idx]
        ideal_row = df.loc[ideal_idx]

        if verbose:
            print(f"  Merging: {ideal_row.get('listing_id', ideal_idx)} -> {immo_row.get('listing_id', immo_idx)}")

        merged_row = merge_listing_data(immo_row, ideal_row)
        df.loc[immo_idx] = merged_row

    df = df.drop(index=list(idealista_duplicates))

    if verbose:
        print(f"Removed {len(idealista_duplicates)} duplicate Idealista listings")

    return df


def fix_list_columns(df):
    """
    Fix columns that should be lists to ensure consistent types for parquet serialization.
    """
    list_columns = ['floor_plan_indices', 'features', 'primary_features',
                    'main_features', 'characteristics', 'prices']

    # First convert numpy arrays to lists
    for col in df.columns:
        if df[col].dtype == 'object':
            def fix_array(x):
                if x is None:
                    return None
                if isinstance(x, np.ndarray):
                    if x.ndim == 0:
                        return x.item()
                    return x.tolist()
                return x
            df[col] = [fix_array(x) for x in df[col]]

    # Ensure list columns are always lists
    for col in list_columns:
        if col not in df.columns:
            continue

        def ensure_list(x):
            if x is None:
                return []
            if isinstance(x, list):
                return x
            if isinstance(x, str):
                return [x] if x else []
            if isinstance(x, (int, np.integer, float)):
                if pd.isna(x):
                    return []
                return [x]
            return []

        df[col] = [ensure_list(x) for x in df[col]]

    return df
