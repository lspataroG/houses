#!/usr/bin/env python3
"""
Process scraped search results into pandas dataframes.

Extracts listing URLs from search result HTML pages (both Immobiliare and Idealista).
Returns dataframes - does NOT save to files.
"""

import os
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import re
from datetime import datetime


def extract_urls_from_immobiliare_search(html_content):
    """
    Extract listing URLs and prices from Immobiliare search results page.

    Returns:
        list: List of dicts with {url, listing_id, position, portal, price}
    """
    import json
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    seen_ids = set()

    # Build price lookup from JSON if available
    price_lookup = {}
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        try:
            data = json.loads(next_data.string)
            page_props = data.get('props', {}).get('pageProps', {})
            dehydrated = page_props.get('dehydratedState', {})
            queries = dehydrated.get('queries', [])

            for q in queries:
                state = q.get('state', {})
                data_content = state.get('data', {})
                if isinstance(data_content, dict) and 'results' in data_content:
                    for r in data_content['results']:
                        real_estate = r.get('realEstate', {})
                        listing_id = real_estate.get('id')
                        price = real_estate.get('price', {}).get('value')
                        if listing_id and price:
                            price_lookup[str(listing_id)] = price
        except (json.JSONDecodeError, KeyError):
            pass

    # Extract from HTML links (more complete than JSON)
    links = soup.find_all('a', href=re.compile(r'/annunci/\d+'))
    for idx, link in enumerate(links):
        href = link.get('href')
        match = re.search(r'/annunci/(\d+)', href)
        if match:
            listing_id = match.group(1)

            # Skip duplicates
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)

            if href.startswith('/'):
                url = f"https://www.immobiliare.it{href}"
            else:
                url = href

            # Get price from JSON lookup if available
            price = price_lookup.get(listing_id)

            # If not in JSON, try to extract from HTML
            if price is None:
                # Find the listing card by ID
                listing_card = soup.find('li', id=listing_id)
                if listing_card:
                    # Look for price div
                    price_div = listing_card.find('div', class_=re.compile(r'Price', re.I))
                    if price_div:
                        price_text = price_div.get_text(strip=True)
                        # Parse price: "€ 700.000" -> 700000
                        price_match = re.search(r'€\s*([\d.]+)', price_text)
                        if price_match:
                            try:
                                # Remove dots (thousands separator) and convert to int
                                price = int(price_match.group(1).replace('.', ''))
                            except ValueError:
                                pass

            results.append({
                'url': url,
                'listing_id': f"immo_{listing_id}",
                'position': len(results) + 1,
                'portal': 'immobiliare',
                'price': price
            })

    return results


def extract_urls_from_idealista_search(html_content):
    """
    Extract listing URLs and prices from Idealista search results page.

    Returns:
        list: List of dicts with {url, listing_id, position, portal, price}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Find all listing articles
    articles = soup.find_all('article', class_='item')

    for idx, article in enumerate(articles):
        # Find the listing link
        link = article.find('a', href=re.compile(r'/immobile/\d+'))
        if not link:
            continue

        href = link.get('href')

        # Extract listing ID
        match = re.search(r'/immobile/(\d+)', href)
        if not match:
            continue

        listing_id = match.group(1)

        # Build full URL if relative
        if href.startswith('/'):
            url = f"https://www.idealista.it{href}"
        else:
            url = href

        # Extract price
        price = None
        price_elem = article.find('span', class_='item-price')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Parse price: "528.000€" -> 528000
            price_match = re.search(r'([\d.]+)', price_text.replace('.', ''))
            if price_match:
                try:
                    price = int(price_match.group(1))
                except ValueError:
                    pass

        results.append({
            'url': url,
            'listing_id': f"ideal_{listing_id}",
            'position': idx + 1,
            'portal': 'idealista',
            'price': price
        })

    return results


def process_search_results_directory(search_dir, date_str=None):
    """
    Process all search result HTML files from a directory.

    Processes BOTH Immobiliare and Idealista search results.

    Args:
        search_dir: Path to search_results directory (string or Path)
        date_str: Date string (e.g., "2026_01_18"), optional

    Returns:
        pandas.DataFrame: Search results with columns:
            - listing_id: unique ID (e.g., "immo_123456")
            - portal: "immobiliare" or "idealista"
            - url: full listing URL
            - page_number: page number in search results
            - position: position on the page
            - html_file: source HTML file
            - snapshot_date: date of the snapshot
    """
    search_path = Path(search_dir)

    if not search_path.exists():
        return pd.DataFrame()

    # Find all HTML files
    html_files = list(search_path.glob('*.html'))

    if not html_files:
        return pd.DataFrame()

    # Process each file
    all_results = []

    for html_file in sorted(html_files):
        # Determine portal and page number from filename
        # Format: {portal}_pag{N}.html
        match = re.match(r'(immo|ideal)_pag(\d+)\.html', html_file.name)
        if not match:
            continue

        portal_prefix, page_num = match.groups()
        portal = 'immobiliare' if portal_prefix == 'immo' else 'idealista'

        # Read HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Read URL if available
        url_file = Path(str(html_file) + '.url')
        search_url = None
        if url_file.exists():
            with open(url_file, 'r', encoding='utf-8') as f:
                search_url = f.read().strip()

        # Extract listing URLs
        try:
            if portal == 'immobiliare':
                listings = extract_urls_from_immobiliare_search(html_content)
            else:
                listings = extract_urls_from_idealista_search(html_content)

            # Add page metadata
            for listing in listings:
                listing['page_number'] = int(page_num)
                listing['search_url'] = search_url
                listing['html_file'] = str(html_file)

            all_results.extend(listings)

        except Exception:
            pass

    if not all_results:
        return pd.DataFrame()

    # Create dataframe
    df = pd.DataFrame(all_results)

    # Add snapshot date
    if date_str:
        df['snapshot_date'] = pd.to_datetime(date_str, format='%Y_%m_%d')
    else:
        # Try to extract from directory name
        parent_name = Path(search_dir).parent.name
        if re.match(r'\d{4}_\d{2}_\d{2}', parent_name):
            df['snapshot_date'] = pd.to_datetime(parent_name, format='%Y_%m_%d')
        else:
            df['snapshot_date'] = pd.Timestamp.now()

    # Sort by portal, page, and position
    df = df.sort_values(['portal', 'page_number', 'position'])

    return df


def compare_search_snapshots(df_current, df_previous):
    """
    Compare two search result dataframes to find changes.

    Args:
        df_current: Current week's search results
        df_previous: Previous week's search results

    Returns:
        dict with keys:
            - new: DataFrame of new listings
            - removed: DataFrame of removed listings
            - common: DataFrame of common listings
    """
    current_ids = set(df_current['listing_id'].unique())
    previous_ids = set(df_previous['listing_id'].unique())

    new_ids = current_ids - previous_ids
    removed_ids = previous_ids - current_ids
    common_ids = current_ids & previous_ids

    return {
        'new': df_current[df_current['listing_id'].isin(new_ids)].copy(),
        'removed': df_previous[df_previous['listing_id'].isin(removed_ids)].copy(),
        'common': df_current[df_current['listing_id'].isin(common_ids)].copy(),
        'summary': {
            'new_count': len(new_ids),
            'removed_count': len(removed_ids),
            'common_count': len(common_ids)
        }
    }
