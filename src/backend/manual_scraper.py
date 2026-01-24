"""
Manual Assisted Scraper - Raw Archive Mode

Downloads and archives raw HTML + images for later parsing.

Uses YOUR real Chrome browser (with your cookies/profile) - NO bot detection!

How to use:
1. Close all Chrome windows
2. Run: `make scrape`
3. Your Chrome opens with remote debugging enabled
4. Browse normally to immobiliare.it or idealista.it
5. Click on any listing you want to save
6. Press ENTER in the terminal to download that listing
7. Continue browsing, press ENTER for each listing
8. Type 'quit' or 'q' when done

Supported sites:
- immobiliare.it (individual listing pages)
- idealista.it (individual listing pages)

Output: Raw HTML + all images saved to versioned folders
"""

import asyncio
import re
import requests
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright


STORAGE_DIR = Path(__file__).parent.parent.parent / 'data' / 'scraped'


def get_next_version_folder(listing_id):
    """
    Find the next version folder for a listing ID within today's date folder.

    Args:
        listing_id: e.g. 'immo_121549264' or 'ideal_12345'

    Returns:
        Path object like storage/2026_01_18/immo_121549264_v1 or storage/2026_01_18/immo_121549264_v3
    """
    # Create daily folder (YYYY_MM_DD format)
    today = datetime.now().strftime("%Y_%m_%d")
    daily_folder = STORAGE_DIR / today
    daily_folder.mkdir(parents=True, exist_ok=True)

    # Find existing versions within today's folder
    existing = list(daily_folder.glob(f"{listing_id}_v*"))

    if not existing:
        # First version
        version_folder = daily_folder / f"{listing_id}_v1"
    else:
        # Find highest version number
        versions = []
        for folder in existing:
            match = re.search(r'_v(\d+)$', folder.name)
            if match:
                versions.append(int(match.group(1)))

        next_version = max(versions) + 1 if versions else 1
        version_folder = daily_folder / f"{listing_id}_v{next_version}"

    version_folder.mkdir(parents=True, exist_ok=True)
    return version_folder


def extract_all_image_urls(html_content, portal):
    """
    Extract all image URLs from HTML content.

    Args:
        html_content: The raw HTML string
        portal: 'immobiliare' or 'idealista'

    Returns:
        List of image URLs
    """
    image_urls = []

    if portal == 'immobiliare':
        # Extract from __NEXT_DATA__ JSON
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content, re.DOTALL)
        if match:
            import json
            try:
                data = json.loads(match.group(1))
                page_props = data.get('props', {}).get('pageProps', {})

                # Navigate to multimedia
                re_data = None
                if 'realEstate' in page_props:
                    re_data = page_props['realEstate']
                elif 'detailData' in page_props and 'realEstate' in page_props['detailData']:
                    re_data = page_props['detailData']['realEstate']

                if re_data:
                    props = re_data.get('properties', [{}])[0] if re_data.get('properties') else {}
                    multimedia = props.get('multimedia', {})

                    # Photos
                    for photo in multimedia.get('photos', []):
                        url = photo.get('urls', {}).get('large') or photo.get('urls', {}).get('medium')
                        if url:
                            image_urls.append(url)

                    # Floor plans
                    for floorplan in multimedia.get('floorplans', []):
                        url = floorplan.get('urls', {}).get('large') or floorplan.get('urls', {}).get('medium')
                        if url:
                            image_urls.append(url)
            except:
                pass

        # Also get from og:image meta tags as backup
        og_images = re.findall(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html_content)
        image_urls.extend(og_images)

    elif portal == 'idealista':
        # Extract from og:image
        og_images = re.findall(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html_content)
        image_urls.extend(og_images)

        # Extract from gallery (idealista uses img.idealista.it domain)
        gallery_imgs = re.findall(r'https://img\d+\.idealista\.it/[^"\'\s]+\.jpg', html_content)
        image_urls.extend(gallery_imgs)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in image_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def download_image(url, output_path):
    """
    Download an image from URL to local path.

    Args:
        url: Image URL
        output_path: Path object where to save the image

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"   ⚠️  Failed to download {url}: {e}")
        return False


async def archive_immobiliare_listing(page):
    """Archive an Immobiliare.it listing page."""
    print("🏠 Archiving Immobiliare.it listing...")

    # Wait for page to be fully loaded
    print("   Waiting for page to load...")
    await page.wait_for_load_state('domcontentloaded')
    await page.wait_for_timeout(1000)

    html_content = await page.content()
    current_url = page.url

    # Extract listing ID from HTML JSON
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content, re.DOTALL)
    if not match:
        print("❌ Could not find __NEXT_DATA__ on this page")
        return None

    try:
        import json
        data = json.loads(match.group(1))
        page_props = data.get('props', {}).get('pageProps', {})

        re_data = None
        if 'realEstate' in page_props:
            re_data = page_props['realEstate']
        elif 'detailData' in page_props and 'realEstate' in page_props['detailData']:
            re_data = page_props['detailData']['realEstate']

        if not re_data or 'id' not in re_data:
            print("❌ No real estate ID found in JSON")
            return None

        listing_id = f"immo_{re_data['id']}"
        title = re_data.get('title', 'Unknown')

    except Exception as e:
        print(f"❌ Error extracting listing ID: {e}")
        return None

    # Get versioned folder
    version_folder = get_next_version_folder(listing_id)
    print(f"📁 Saving to: {version_folder.name}")

    # Save HTML
    html_path = version_folder / 'page.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   ✅ Saved HTML ({len(html_content):,} bytes)")

    # Save URL
    url_path = version_folder / 'url.txt'
    with open(url_path, 'w', encoding='utf-8') as f:
        f.write(current_url)

    # Extract and download all images
    image_urls = extract_all_image_urls(html_content, 'immobiliare')
    print(f"   🖼️  Found {len(image_urls)} images")

    downloaded = 0
    for idx, img_url in enumerate(image_urls):
        ext = 'jpg'
        if '.' in img_url:
            ext = img_url.split('.')[-1].split('?')[0][:4]

        img_path = version_folder / f"image_{idx:03d}.{ext}"
        if download_image(img_url, img_path):
            downloaded += 1

    print(f"   ✅ Downloaded {downloaded}/{len(image_urls)} images")
    print(f"✅ Archived: {title[:60]}")

    return version_folder


async def archive_idealista_listing(page):
    """Archive an Idealista.it listing page."""
    print("🏠 Archiving Idealista.it listing...")

    # Wait for page to be fully loaded
    print("   Waiting for page to load...")
    await page.wait_for_load_state('domcontentloaded')
    await page.wait_for_timeout(1000)

    html_content = await page.content()
    current_url = page.url

    # Extract listing ID from URL
    url_match = re.search(r'/immobile/(\d+)/', current_url)
    if not url_match:
        print("❌ Could not extract property ID from URL")
        return None

    property_code = url_match.group(1)
    listing_id = f"ideal_{property_code}"

    # Extract title for display
    title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html_content)
    title = title_match.group(1) if title_match else 'Unknown'

    # Get versioned folder
    version_folder = get_next_version_folder(listing_id)
    print(f"📁 Saving to: {version_folder.name}")

    # Save HTML
    html_path = version_folder / 'page.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   ✅ Saved HTML ({len(html_content):,} bytes)")

    # Save URL
    url_path = version_folder / 'url.txt'
    with open(url_path, 'w', encoding='utf-8') as f:
        f.write(current_url)

    # Extract and download all images
    image_urls = extract_all_image_urls(html_content, 'idealista')
    print(f"   🖼️  Found {len(image_urls)} images")

    downloaded = 0
    for idx, img_url in enumerate(image_urls):
        ext = 'jpg'
        if '.' in img_url:
            ext = img_url.split('.')[-1].split('?')[0][:4]

        img_path = version_folder / f"image_{idx:03d}.{ext}"
        if download_image(img_url, img_path):
            downloaded += 1

    print(f"   ✅ Downloaded {downloaded}/{len(image_urls)} images")
    print(f"✅ Archived: {title[:60]}")

    return version_folder


async def main():
    """Main manual scraper loop."""
    print("=" * 80)
    print("🎯 Manual Assisted Scraper - Raw Archive Mode")
    print("=" * 80)
    print("\nInstructions:")
    print("1. Browser will open - navigate manually to any listing")
    print("2. When on a listing page, press ENTER here to download it")
    print("3. Continue browsing and pressing ENTER for each listing")
    print("4. Type 'quit' or 'q' when done")
    print("\n" + "=" * 80 + "\n")

    async with async_playwright() as p:
        # Use your actual Chrome with your real profile (no automation fingerprints)
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print("❌ Could not connect to Chrome!")
            print(f"\nError: {e}")
            print("\n📋 Chrome should have been launched automatically.")
            print("   If you see this error, try manually running:")
            print('   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 &')
            print("")
            return

        # Get default context
        contexts = browser.contexts
        if not contexts:
            print("❌ No browser context found.")
            return

        context = contexts[0]

        print("✅ Connected to your Chrome browser!")
        print("   Navigate to listings manually in the Chrome window...")
        print("   (Your real Chrome - no bot detection!)\n")

        archived_count = 0

        while True:
            # Wait for user input in terminal
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "\n📍 Press ENTER to download current page (or 'q' to quit): "
            )

            if user_input.lower() in ['q', 'quit', 'exit']:
                break

            # Get currently open pages - use CDP to get fresh target list
            try:
                cdp = await browser.new_browser_cdp_session()
                targets = await cdp.send("Target.getTargets")
                await cdp.detach()

                # Find real page targets (not iframes, workers, etc)
                # Must be type "page", no parentId (not iframe), and not chrome:// URLs
                page_targets = [
                    t for t in targets.get("targetInfos", [])
                    if t.get("type") == "page"
                    and "parentId" not in t  # Not an iframe
                    and not t.get("url", "").startswith(('chrome://', 'about:', 'chrome-extension://'))
                ]

                if not page_targets:
                    print("❌ No valid web pages open")
                    continue

                # Match targets to Playwright page objects
                all_pages = context.pages
                pages = []
                for target in page_targets:
                    target_url = target.get("url", "")
                    for p in all_pages:
                        if p.url == target_url and p not in pages:
                            pages.append(p)
                            break

                # Fallback if matching failed
                if not pages:
                    pages = [p for p in all_pages if not p.url.startswith(('chrome://', 'about:', 'chrome-extension://'))]

            except Exception:
                # Fallback to original method
                all_pages = context.pages
                pages = [p for p in all_pages if not p.url.startswith(('chrome://', 'about:', 'chrome-extension://'))]

            if not pages:
                print("❌ No valid web pages open (only internal Chrome pages)")
                continue

            # Show all tabs and let user choose
            if len(pages) == 1:
                page = pages[0]
            else:
                print(f"\n📑 Found {len(pages)} open web page(s):")
                for idx, p in enumerate(pages):
                    url = p.url
                    print(f"   [{idx + 1}] {url[:80]}...")

                # Ask which tab to use
                while True:
                    tab_choice = await asyncio.get_event_loop().run_in_executor(
                        None, input, f"\nWhich tab to scrape? [1-{len(pages)}] (or press ENTER for tab 1): "
                    )

                    if tab_choice.strip() == "":
                        page = pages[0]
                        break

                    try:
                        tab_num = int(tab_choice)
                        if 1 <= tab_num <= len(pages):
                            page = pages[tab_num - 1]
                            break
                        else:
                            print(f"   ⚠️  Please enter a number between 1 and {len(pages)}")
                    except ValueError:
                        print("   ⚠️  Please enter a valid number")

            current_url = page.url
            print(f"\n🔍 Reading from: {current_url}")

            # Detect which portal
            if 'immobiliare.it' in current_url:
                result = await archive_immobiliare_listing(page)
                if result:
                    archived_count += 1
            elif 'idealista.it' in current_url:
                result = await archive_idealista_listing(page)
                if result:
                    archived_count += 1
            else:
                print("❌ This doesn't appear to be an Immobiliare or Idealista listing page")
                print("   Supported URLs:")
                print("   - https://www.immobiliare.it/annunci/...")
                print("   - https://www.idealista.it/immobile/...")

        # Disconnect (but don't close Chrome - let user keep browsing)
        await browser.close()
        print("\n⚠️  Disconnected from Chrome (Chrome will stay open)")

    # Show where data was saved
    today = datetime.now().strftime("%Y_%m_%d")
    daily_folder = STORAGE_DIR / today

    print("\n" + "=" * 80)
    print(f"✅ Manual scraping complete! Archived {archived_count} listings")
    print("=" * 80)
    print(f"\nData saved to: {daily_folder.absolute()}")
    print("You can close Chrome manually when done browsing.")


if __name__ == "__main__":
    asyncio.run(main())
