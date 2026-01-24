"""
Shared utility functions for the backend.
"""

import requests
from pathlib import Path


def download_media(listing_id, media_list):
    """
    Download media files (photos, planimetry) for a listing.

    Args:
        listing_id: The listing ID (e.g., 'immo_12345')
        media_list: List of dicts with 'url', 'type', 'caption' keys

    Returns:
        List of media records with local_path filled in
    """
    storage_dir = Path(__file__).parent / 'storage' / listing_id
    storage_dir.mkdir(parents=True, exist_ok=True)

    media_records = []

    for idx, media in enumerate(media_list):
        try:
            url = media['url']
            media_type = media['type']
            caption = media.get('caption', '')

            # Determine filename
            ext = 'jpg'  # Default extension
            if '.' in url:
                ext = url.split('.')[-1].split('?')[0][:4]  # Get extension, remove query params

            # Create filename based on type and index
            if media_type == 'planimetry':
                filename = f'plan_{idx}.{ext}'
            elif media_type == 'photo':
                filename = f'photo_{idx}.{ext}'
            else:
                filename = f'media_{idx}.{ext}'

            local_path = storage_dir / filename

            # Download file
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                f.write(response.content)

            # Create media record
            media_records.append({
                'listing_id': listing_id,
                'media_type': media_type,
                'local_path': str(local_path.relative_to(Path(__file__).parent)),
                'remote_url': url,
                'caption': caption
            })

        except Exception as e:
            print(f"⚠️  Failed to download {media['url']}: {e}")
            continue

    return media_records
