import json
import os
from pathlib import Path
from bs4 import BeautifulSoup

def parse_immobiliare_html(html_path):
    """Parse Immobiliare HTML and extract __NEXT_DATA__ JSON"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Find the script tag containing __NEXT_DATA__
    next_data_script = soup.find('script', id='__NEXT_DATA__')

    if not next_data_script:
        return None

    # Parse the JSON
    try:
        data = json.loads(next_data_script.string)
        return data
    except json.JSONDecodeError:
        return None

def extract_user_visible_fields(raw_data, listing_dir):
    """Extract only user-visible fields from the listing data"""

    page_props = raw_data.get('props', {}).get('pageProps', {})
    detail_data = page_props.get('detailData', {})
    real_estate = detail_data.get('realEstate', {})

    # Get the main property (first item in properties array)
    properties = real_estate.get('properties', [])
    if not properties:
        return None

    prop = properties[0]

    # Read URL from url.txt
    url_file = listing_dir / "url.txt"
    with open(url_file, 'r') as f:
        url = f.read().strip()

    # Extract ID
    listing_id = real_estate.get('id')

    # Extract main visible fields
    extracted = {
        # Core identifiers
        'id': f"immo_{listing_id}",
        'portal': 'immobiliare',
        'url': url,
        'reference': real_estate.get('reference', {}).get('code'),

        # Main info
        'title': real_estate.get('title', ''),
        'description': prop.get('description', ''),

        # Price
        'price': real_estate.get('price', {}).get('value'),
        'price_formatted': real_estate.get('price', {}).get('formattedValue'),
        'price_per_sqm': real_estate.get('price', {}).get('pricePerSquareMeter'),

        # Property details
        'typology': prop.get('typology', {}).get('name'),
        'typology_detail': prop.get('typologyValue'),
        'rooms': prop.get('rooms'),
        'bedrooms': prop.get('bedRoomsNumber'),
        'surface_sqm': prop.get('surface'),
        'bathrooms': prop.get('bathrooms'),
        'floor': prop.get('floor', {}).get('value'),
        'floors_building': prop.get('floors'),

        # Kitchen & furniture
        'kitchen': prop.get('kitchenStatus'),
        'furnished': prop.get('typologyValue'),  # Contains "Arredato" if furnished

        # Building features
        'elevator': prop.get('elevator'),
        'building_year': prop.get('buildingYear'),
        'condition': prop.get('condition'),
        'availability': prop.get('availability'),

        # Energy
        'energy_class': prop.get('energy', {}).get('energyStatus'),
        'heating': prop.get('energy', {}).get('heatingType'),
        'air_conditioning': prop.get('energy', {}).get('airConditioning'),

        # Location
        'address': prop.get('location', {}).get('address'),
        'city': prop.get('location', {}).get('city'),
        'zone': prop.get('location', {}).get('macrozone'),
        'microzone': prop.get('location', {}).get('microzone'),
        'latitude': prop.get('location', {}).get('latitude'),
        'longitude': prop.get('location', {}).get('longitude'),

        # Costs
        'condominium_fees': prop.get('costs', {}).get('condominiumExpenses'),

        # Features & amenities (extract visible ones)
        'features': [],
        'primary_features': [],

        # Metadata
        'luxury': real_estate.get('luxury'),
        'contract': real_estate.get('contract'),
        'created_at': real_estate.get('createdAt'),
        'updated_at': real_estate.get('updatedAt'),
        'last_update': prop.get('lastUpdate'),

        # Media count
        'photo_count': len(prop.get('multimedia', {}).get('photos', [])),
        'plan_count': len(prop.get('multimedia', {}).get('floorplans', [])),
        'floor_plan_indices': [],  # Will be calculated below
        'has_virtual_tour': len(prop.get('multimedia', {}).get('virtualTours', [])) > 0,
    }

    # Calculate floor plan indices (photos come first, then floor plans)
    photo_count = extracted['photo_count']
    plan_count = extracted['plan_count']
    if plan_count > 0:
        extracted['floor_plan_indices'] = list(range(photo_count, photo_count + plan_count))

    # Extract visible primary features
    primary_features = prop.get('primaryFeatures', [])
    for feature in primary_features:
        if feature.get('isVisible') and feature.get('name'):
            extracted['primary_features'].append(feature.get('name'))

    # Extract other features
    features = prop.get('features', [])
    if features:
        extracted['features'] = features

    # Extract main features for tags
    main_features = prop.get('mainFeatures', [])
    main_feature_labels = []
    for feat in main_features:
        if feat.get('label'):
            main_feature_labels.append(feat.get('label'))
    extracted['main_features'] = main_feature_labels

    return extracted

def process_listing(listing_dir):
    """Process a single listing directory"""
    html_path = listing_dir / "page.html"

    if not html_path.exists():
        return None

    raw_data = parse_immobiliare_html(html_path)
    if not raw_data:
        return None

    listing_data = extract_user_visible_fields(raw_data, listing_dir)
    return listing_data
