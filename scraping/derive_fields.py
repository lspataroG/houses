"""
Derive missing fields from listing descriptions and floor plans using Gemini.
"""

import json
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from google import genai

from .gemini import generate_gemini
from .llm_utils import get_part

logger = logging.getLogger(__name__)

# Gemini API Configuration
PROJECT_ID = "telefonica-425415"
LOCATION = "global"

# Schema for attributes extraction (from description only)
ATTRIBUTES_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A 2-3 sentence summary highlighting the best features of the property"
        },
        "bedrooms": {
            "type": "integer",
            "description": "Number of bedrooms"
        },
        "bathrooms": {
            "type": "integer",
            "description": "Number of bathrooms"
        },
        "kitchen_type": {
            "type": "string",
            "description": "Type of kitchen (e.g., 'abitabile', 'angolo cottura', 'a vista', 'separata')"
        },
        "balconies": {
            "type": "integer",
            "description": "Number of balconies (0 if none)"
        },
        "terraces": {
            "type": "integer",
            "description": "Number of terraces (0 if none)"
        },
        "has_cantina": {
            "type": "boolean",
            "description": "Whether the property has a cantina/cellar"
        },
        "has_garage": {
            "type": "boolean",
            "description": "Whether the property has a garage"
        },
        "parking_spots": {
            "type": "integer",
            "description": "Number of parking spots (0 if none)"
        },
        "has_elevator": {
            "type": "boolean",
            "description": "Whether the building has an elevator"
        },
        "floor_number": {
            "type": "integer",
            "description": "Floor number (0 for ground floor, -1 if unknown)"
        },
        "total_floors": {
            "type": "integer",
            "description": "Total floors in the building (-1 if unknown)"
        },
        "has_air_conditioning": {
            "type": "boolean",
            "description": "Whether the property has air conditioning"
        },
        "heating_type": {
            "type": "string",
            "description": "Type of heating (e.g., 'autonomo', 'centralizzato', 'a pavimento')"
        },
        "condition": {
            "type": "string",
            "description": "Condition of the property (e.g., 'nuovo', 'ristrutturato', 'da ristrutturare', 'buono')"
        },
        "exposure": {
            "type": "string",
            "description": "Exposure/orientation (e.g., 'doppia', 'tripla', 'sud', 'est-ovest')"
        },
        "has_garden": {
            "type": "boolean",
            "description": "Whether the property has a garden"
        },
        "energy_class": {
            "type": "string",
            "description": "Energy class (A, B, C, D, E, F, G)"
        }
    },
    "required": ["summary", "bedrooms", "bathrooms", "balconies", "terraces"]
}

# Schema for beauty score (from images)
BEAUTY_SCHEMA = {
    "type": "object",
    "properties": {
        "beauty_score": {
            "type": "integer",
            "description": "Beauty/attractiveness score from 1-5. 5=stunning/luxurious, 4=very nice, 3=average, 2=below average/dated, 1=poor/only exterior photos"
        },
        "beauty_notes": {
            "type": "string",
            "description": "Brief explanation of the beauty score (1 sentence)"
        }
    },
    "required": ["beauty_score"]
}

ATTRIBUTES_PROMPT = """Analyze this Italian real estate listing and extract key information.

LISTING TITLE: {title}

LOCATION: {location}

PRICE: {price}

DESCRIPTION:
{description}

EXISTING DATA (use this as reference, but verify/supplement from description):
- Surface: {surface} m²
- Rooms: {rooms}
- Bathrooms: {bathrooms}
- Floor: {floor}
- Elevator: {elevator}
- Heating: {heating}
- Energy class: {energy_class}

Based on the description, extract the following information in JSON format:

1. A compelling 2-3 sentence summary in Italian highlighting the best features

2. Number of bedrooms, bathrooms, balconies, terraces

3. Kitchen type, heating type, condition

4. Boolean features: cantina, garage, elevator, AC, garden

5. Floor information and building details

If information is not available, use reasonable defaults:
- For counts, use 0 if not mentioned
- For booleans, use false if not mentioned
- For strings, use empty string if not mentioned
- For floor_number and total_floors, use -1 if unknown

Return ONLY valid JSON matching the schema."""

BEAUTY_PROMPT = """Rate the beauty and attractiveness of this property based on the photos.

PROPERTY: {title}
PRICE: {price}

Look at the attached property photos and rate the overall beauty/attractiveness on a scale of 1-5:

- 5 = Stunning, luxurious, beautifully renovated, high-end finishes, designer interiors
- 4 = Very nice, modern, well-maintained, attractive finishes
- 3 = Average, decent condition, nothing special but acceptable
- 2 = Below average, dated decor, needs updating, worn finishes
- 1 = Poor condition, OR only shows exterior/panorama/neighborhood photos (no interior = likely hiding bad condition)

IMPORTANT: If you see mostly exterior shots, neighborhood views, or building facades with few/no interior photos, this is a RED FLAG - score it 1 or 2 as they are likely hiding a poor interior.

Return ONLY valid JSON with beauty_score (1-5) and brief beauty_notes."""


def get_gemini_client():
    """Initialize and return Gemini client."""
    return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


def load_listing_images(listing: pd.Series, data_dir: Path, max_images: int = 8) -> list:
    """Load images for a listing (excluding floor plans for beauty assessment)."""
    images = []

    folder_path = listing.get('folder_path')
    if not folder_path or pd.isna(folder_path):
        return images

    full_path = data_dir / folder_path
    if not full_path.exists():
        return images

    # Get floor plan indices to exclude them
    floor_plan_indices = listing.get('floor_plan_indices', [])
    if floor_plan_indices is None or (isinstance(floor_plan_indices, float) and pd.isna(floor_plan_indices)):
        floor_plan_indices = []
    if not isinstance(floor_plan_indices, list):
        floor_plan_indices = []
    floor_plan_set = set(floor_plan_indices)

    # Get image count
    image_count = listing.get('image_count', 0)
    if pd.isna(image_count):
        image_count = 0

    # Load regular images (not floor plans)
    loaded = 0
    for i in range(int(image_count)):
        if loaded >= max_images:
            break
        if i in floor_plan_set:
            continue

        image_path = full_path / f"image_{i:03d}.jpg"
        if image_path.exists():
            try:
                with open(image_path, 'rb') as f:
                    images.append(f.read())
                    loaded += 1
            except Exception as e:
                logger.warning(f"Failed to load image {image_path}: {e}")

    return images


def derive_fields_for_listing(
    listing: pd.Series,
    client,
    data_dir: Path,
    model: str = "gemini-3-flash-preview"
) -> Optional[dict]:
    """
    Derive fields for a single listing using Gemini.
    Makes two separate calls:
    1. Attributes extraction from description (no images)
    2. Beauty score from images

    Args:
        listing: Pandas Series with listing data
        client: Gemini client
        data_dir: Path to data directory
        model: Model to use

    Returns:
        Dictionary with derived fields or None on error
    """
    result = {}

    # === CALL 1: Extract attributes from description ===
    description = listing.get('description', '')
    if pd.isna(description) or not description:
        description = "No description available"

    attributes_prompt = ATTRIBUTES_PROMPT.format(
        title=listing.get('title', 'N/A'),
        location=listing.get('location', 'N/A'),
        price=listing.get('price_formatted', listing.get('price', 'N/A')),
        description=description,
        surface=listing.get('surface_numeric', 'N/A'),
        rooms=listing.get('rooms_count', listing.get('rooms', 'N/A')),
        bathrooms=listing.get('bathrooms', 'N/A'),
        floor=listing.get('floor', 'N/A'),
        elevator=listing.get('elevator', 'N/A'),
        heating=listing.get('heating', 'N/A'),
        energy_class=listing.get('energy_class', 'N/A'),
    )

    try:
        attributes_response = generate_gemini(
            text_images_pieces=[attributes_prompt],
            client=client,
            schema=ATTRIBUTES_SCHEMA,
            model=model
        )

        if attributes_response:
            result.update(json.loads(attributes_response))
    except Exception as e:
        logger.error(f"Failed to extract attributes for {listing.get('id')}: {e}")

    # === CALL 2: Beauty score from images ===
    images = load_listing_images(listing, data_dir, max_images=8)

    if images:
        beauty_prompt = BEAUTY_PROMPT.format(
            title=listing.get('title', 'N/A'),
            price=listing.get('price_formatted', listing.get('price', 'N/A')),
        )

        try:
            beauty_response = generate_gemini(
                text_images_pieces=[beauty_prompt] + images,
                client=client,
                schema=BEAUTY_SCHEMA,
                model=model
            )

            if beauty_response:
                beauty_data = json.loads(beauty_response)
                result.update(beauty_data)
        except Exception as e:
            logger.error(f"Failed to get beauty score for {listing.get('id')}: {e}")
            result['beauty_score'] = 0  # Default if image analysis fails
    else:
        result['beauty_score'] = 0  # Default if no images

    # Return result only if we got at least the summary
    if 'summary' in result:
        return result
    return None


def derive_fields_for_dataset(
    df: pd.DataFrame,
    data_dir: Path,
    force_reprocess: bool = False,
    model: str = "gemini-3-flash-preview",
    verbose: bool = True,
    max_workers: int = 10
) -> pd.DataFrame:
    """
    Derive fields for all listings in the dataset that don't have them yet.
    Uses parallel processing for faster execution.

    Args:
        df: DataFrame with listings
        data_dir: Path to data directory (parent of 'scraped' folder)
        force_reprocess: If True, reprocess all listings
        model: Model to use
        verbose: Print progress
        max_workers: Maximum number of parallel workers

    Returns:
        DataFrame with derived_fields column added/updated
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if df.empty:
        return df

    # Initialize derived_fields column if it doesn't exist
    if 'derived_fields' not in df.columns:
        df['derived_fields'] = None

    # Find listings that need processing
    if force_reprocess:
        to_process = df.index.tolist()
    else:
        to_process = df[df['derived_fields'].isna()].index.tolist()

    if not to_process:
        if verbose:
            print("All listings already have derived fields")
        return df

    if verbose:
        print(f"Deriving fields for {len(to_process)} listings using {max_workers} workers...")

    # Initialize client (thread-safe for Gemini)
    client = get_gemini_client()

    # Process function for each listing
    def process_listing(idx):
        listing = df.loc[idx]
        listing_id = listing.get('id', idx)
        derived = derive_fields_for_listing(listing, client, data_dir, model)
        return idx, listing_id, derived

    processed = 0
    errors = 0
    results = {}

    # Run in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_listing, idx): idx for idx in to_process}

        for future in as_completed(futures):
            try:
                idx, listing_id, derived = future.result()
                if derived:
                    results[idx] = derived
                    processed += 1
                    if verbose:
                        print(f"  {listing_id}: OK ({processed}/{len(to_process)})")
                else:
                    errors += 1
                    if verbose:
                        print(f"  {listing_id}: FAILED")
            except Exception as e:
                errors += 1
                if verbose:
                    print(f"  Error: {e}")

    # Apply results to dataframe
    for idx, derived in results.items():
        df.at[idx, 'derived_fields'] = derived

    if verbose:
        print(f"Completed: {processed} processed, {errors} errors")

    return df


def serialize_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Serialize derived_fields dict to JSON string for parquet storage.
    """
    if 'derived_fields' not in df.columns:
        return df

    def to_json_str(val):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        if isinstance(val, dict):
            return json.dumps(val)
        if isinstance(val, str):
            return val
        return None

    df['derived_fields'] = df['derived_fields'].apply(to_json_str)
    return df


def deserialize_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deserialize derived_fields JSON string back to dict after loading from parquet.
    """
    if 'derived_fields' not in df.columns:
        return df

    def from_json_str(val):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return None
        return None

    df['derived_fields'] = df['derived_fields'].apply(from_json_str)
    return df
