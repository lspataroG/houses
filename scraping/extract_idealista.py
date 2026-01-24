import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

def extract_number(text):
    """Extract numeric value from text"""
    if not text:
        return None
    match = re.search(r'([\d.]+)', text.replace('.', '').replace(',', '.'))
    if match:
        try:
            return int(match.group(1))
        except:
            return match.group(1)
    return None

def parse_idealista_html(html_path):
    """Parse Idealista HTML and extract user-visible fields"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract all user-visible fields
    data = {}

    # Title
    title_main = soup.find('span', class_='main-info__title-main')
    title_minor = soup.find('span', class_='main-info__title-minor')

    if title_main:
        data['title'] = title_main.get_text(strip=True)
    if title_minor:
        data['location'] = title_minor.get_text(strip=True)

    # Price
    price_elem = soup.find('span', class_='info-data-price')
    if price_elem:
        price_text = price_elem.get_text(strip=True)
        data['price'] = extract_number(price_text)
        data['price_formatted'] = price_text

    # Main features (size, rooms, floor)
    info_features = soup.find('div', class_='info-features')
    if info_features:
        features = info_features.find_all('span')
        for i, feat in enumerate(features):
            feat_text = feat.get_text(strip=True)
            if 'm2' in feat_text or 'm²' in feat_text:
                data['surface_sqm'] = feat_text
            elif 'locali' in feat_text:
                data['rooms'] = feat_text
            elif 'piano' in feat_text:
                data['floor'] = feat_text

    # Description
    comment = soup.find('div', class_='comment')
    if comment:
        data['description'] = comment.get_text(strip=True)

    # Detailed characteristics
    characteristics = []
    details_sections = soup.find_all('div', class_='details-property_features')

    for section in details_sections:
        items = section.find_all('li')
        for item in items:
            char_text = item.get_text(strip=True)
            characteristics.append(char_text)

            # Extract specific fields
            if 'm² commerciali' in char_text:
                data['surface_commercial'] = char_text
            elif 'm² calpestabili' in char_text:
                data['surface_usable'] = char_text
            elif 'bagn' in char_text.lower():
                data['bathrooms'] = char_text
            elif 'Cantina' in char_text:
                data['has_cellar'] = True
            elif 'Riscaldamento' in char_text:
                data['heating'] = char_text
            elif 'Classe energetica' in char_text:
                data['energy_class'] = char_text
            elif 'Costruito nel' in char_text:
                data['building_year'] = extract_number(char_text)
            elif 'Balcone' in char_text:
                data['has_balcony'] = True
            elif 'Giardino' in char_text:
                data['has_garden'] = True
            elif 'Terrazzo' in char_text:
                data['has_terrace'] = True
            elif 'ascensore' in char_text.lower():
                data['elevator'] = char_text
            elif 'Posto auto' in char_text or 'Garage' in char_text:
                data['parking'] = char_text
            elif 'stato' in char_text.lower() or 'ristruttur' in char_text.lower():
                data['condition'] = char_text
            elif 'Aria condizionata' in char_text:
                data['has_air_conditioning'] = True

    data['characteristics'] = characteristics

    # Price per m²
    price_per_sqm_elem = soup.find('span', class_='flex-feature-details', string=re.compile(r'€/m²'))
    if price_per_sqm_elem:
        data['price_per_sqm'] = price_per_sqm_elem.get_text(strip=True)

    # Condominium fees
    expenses_elem = soup.find('p', string=re.compile(r'spese condominiali', re.I))
    if expenses_elem:
        data['condominium_fees'] = expenses_elem.get_text(strip=True)

    # Update date (relative text)
    date_update = soup.find('p', class_='date-update-text')
    if date_update:
        data['last_update'] = date_update.get_text(strip=True)

    # Listing date from stats-text: "Annuncio aggiornato il 11 novembre"
    stats_texts = soup.find_all('p', class_='stats-text')
    for stats in stats_texts:
        text = stats.get_text(strip=True)
        # Match "Annuncio aggiornato il DD mese"
        match = re.search(r'aggiornato il (\d{1,2}) (\w+)', text, re.I)
        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()

            # Italian month names to numbers
            months = {
                'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
                'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
                'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
            }

            if month_name in months:
                month = months[month_name]
                # Assume current year, but if date would be in future, use previous year
                from datetime import datetime
                today = datetime.now()
                year = today.year
                try:
                    listing_date = datetime(year, month, day)
                    if listing_date > today:
                        listing_date = datetime(year - 1, month, day)
                    data['created_at'] = listing_date.timestamp()
                except ValueError:
                    pass
            break

    # Count multimedia and extract coordinates
    photo_count = 0
    plan_count = 0
    floor_plan_indices = []

    # Extract floor plan info from the full HTML content
    # Get pairs of (url, isPlan) from multimedia data
    pattern = r'imageDataService:"([^"]+)"[^}]*"isPlan":(true|false)'
    matches = re.findall(pattern, html_content)

    if matches:
        # Get unique floor plan image IDs
        floor_plan_image_ids = set()
        for url, is_plan in matches:
            if is_plan == 'true':
                # Extract image ID from URL
                id_match = re.search(r'/(\d+)\.(?:jpg|webp)', url)
                if id_match:
                    floor_plan_image_ids.add(id_match.group(1))

        # Get downloaded image URLs in order (same pattern as scraper uses)
        downloaded_urls = re.findall(r'(https://img\d+\.idealista\.it/[^"\'\s]+\.jpg)', html_content)
        # Keep unique URLs in order
        seen = set()
        unique_downloaded = []
        for url in downloaded_urls:
            if url not in seen:
                seen.add(url)
                unique_downloaded.append(url)

        # Map floor plan image IDs to downloaded indices
        for i, url in enumerate(unique_downloaded):
            id_match = re.search(r'/(\d+)\.jpg', url)
            if id_match and id_match.group(1) in floor_plan_image_ids:
                if i not in floor_plan_indices:
                    floor_plan_indices.append(i)

        # Count photos and plans
        plan_count = len(floor_plan_indices)
        photo_count = len(unique_downloaded) - plan_count

    # Check for 3D tour and coordinates in scripts
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            script_text = script.string

            # Check for 3D tour
            if 'tour3d' in script_text.lower() or 'virtual' in script_text.lower():
                data['has_virtual_tour'] = True

            # Extract coordinates from Google Maps URL
            if 'maps.googleapis.com' in script_text:
                coord_match = re.search(r'center=([\d.]+)%2C([\d.]+)', script_text)
                if coord_match:
                    data['latitude'] = float(coord_match.group(1))
                    data['longitude'] = float(coord_match.group(2))

    data['photo_count'] = photo_count
    data['plan_count'] = plan_count
    data['floor_plan_indices'] = floor_plan_indices

    return data

def extract_user_visible_fields(raw_data, listing_dir):
    """Process extracted data and add metadata"""

    # Read URL from url.txt
    url_file = listing_dir / "url.txt"
    with open(url_file, 'r') as f:
        url = f.read().strip()

    # Extract ID from directory name
    listing_id = listing_dir.name.replace('_v1', '')

    # Build final structured data
    extracted = {
        # Core identifiers
        'id': listing_id,
        'portal': 'idealista',
        'url': url,

        # Main info
        'title': raw_data.get('title', ''),
        'location': raw_data.get('location', ''),
        'description': raw_data.get('description', ''),

        # Price
        'price': raw_data.get('price'),
        'price_formatted': raw_data.get('price_formatted'),
        'price_per_sqm': raw_data.get('price_per_sqm'),

        # Property details
        'surface_sqm': raw_data.get('surface_sqm'),
        'surface_commercial': raw_data.get('surface_commercial'),
        'surface_usable': raw_data.get('surface_usable'),
        'rooms': raw_data.get('rooms'),
        'bathrooms': raw_data.get('bathrooms'),
        'floor': raw_data.get('floor'),

        # Building features
        'elevator': raw_data.get('elevator'),
        'building_year': raw_data.get('building_year'),
        'condition': raw_data.get('condition'),
        'heating': raw_data.get('heating'),
        'energy_class': raw_data.get('energy_class'),

        # Amenities
        'has_balcony': raw_data.get('has_balcony', False),
        'has_terrace': raw_data.get('has_terrace', False),
        'has_garden': raw_data.get('has_garden', False),
        'has_cellar': raw_data.get('has_cellar', False),
        'has_air_conditioning': raw_data.get('has_air_conditioning', False),
        'parking': raw_data.get('parking'),

        # Costs
        'condominium_fees': raw_data.get('condominium_fees'),

        # Location coordinates
        'latitude': raw_data.get('latitude'),
        'longitude': raw_data.get('longitude'),

        # All characteristics as tags
        'characteristics': raw_data.get('characteristics', []),

        # Metadata
        'last_update': raw_data.get('last_update'),
        'created_at': raw_data.get('created_at'),

        # Media
        'photo_count': raw_data.get('photo_count', 0),
        'plan_count': raw_data.get('plan_count', 0),
        'floor_plan_indices': raw_data.get('floor_plan_indices', []),
        'has_virtual_tour': raw_data.get('has_virtual_tour', False),
    }

    return extracted

def process_listing(listing_dir):
    """Process a single listing directory"""
    html_path = listing_dir / "page.html"

    if not html_path.exists():
        return None

    raw_data = parse_idealista_html(html_path)
    if not raw_data:
        return None

    listing_data = extract_user_visible_fields(raw_data, listing_dir)
    return listing_data
