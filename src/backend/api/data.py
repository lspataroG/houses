"""Parquet data loader with caching."""
import pandas as pd
import numpy as np
from pathlib import Path
from functools import lru_cache

DATA_PATH = Path("data/processed/listings.parquet")


@lru_cache(maxsize=1)
def load_listings_df() -> pd.DataFrame:
    """Load listings from parquet file with caching."""
    df = pd.read_parquet(DATA_PATH)
    # Sort by created_at descending (newest first)
    df = df.sort_values("created_at", ascending=False, na_position="last")
    return df


def _convert_value(value):
    """Convert a value to JSON-serializable format."""
    import math

    # Handle None first
    if value is None:
        return None

    # Handle numpy arrays - convert elements recursively
    if isinstance(value, np.ndarray):
        return [_convert_value(v) for v in value.tolist()]

    # Handle pandas Timestamp
    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    # Handle float NaN (including numpy floats)
    if isinstance(value, (float, np.floating)):
        if math.isnan(value) or math.isinf(value):
            return None
        if isinstance(value, np.floating):
            return float(value)
        return value

    # Handle numpy integers
    if isinstance(value, np.integer):
        return int(value)

    # Handle numpy bool
    if isinstance(value, np.bool_):
        return bool(value)

    # Handle pandas NA/NaT
    try:
        if pd.isna(value):
            return None
    except (ValueError, TypeError):
        pass

    return value


def get_all_listings(include_sold: bool = True, sold_only: bool = False) -> list[dict]:
    """Get all listings as list of dicts."""
    df = load_listings_df()
    if sold_only:
        df = df[df["is_sold"] == True]
        # Sort sold listings by date_sold descending (most recently sold first)
        if "date_sold" in df.columns:
            df = df.sort_values("date_sold", ascending=False, na_position="last")
    elif not include_sold:
        df = df[df["is_sold"] == False]

    # Convert to list of dicts, handling numpy types
    listings = []
    for _, row in df.iterrows():
        listing = {key: _convert_value(value) for key, value in row.to_dict().items()}
        listings.append(listing)

    return listings


def get_listing_by_id(listing_id: str) -> dict | None:
    """Get a single listing by ID."""
    df = load_listings_df()
    matches = df[df["id"] == listing_id]
    if matches.empty:
        return None

    row = matches.iloc[0]
    listing = {key: _convert_value(value) for key, value in row.to_dict().items()}
    return listing
