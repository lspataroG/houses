"""
Manual Search Results Scraper

Downloads and archives search results pages to track listings over time.

Uses YOUR real Chrome browser (with your cookies/profile) - NO bot detection!

How to use:
1. Run: `make scrape_search_results`
2. Browse to Immobiliare or Idealista search results
3. Press ENTER to download the current search page
4. Navigate to next page (pag=2, pag=3, etc.)
5. Press ENTER to download each page
6. Type 'quit' or 'q' when done

Supported URLs:
- immobiliare.it search results (extracts page from ?pag=X parameter)
- idealista.it search results (extracts page from lista-X.htm pattern)

Output: Raw HTML saved to daily search_results folder
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs


STORAGE_DIR = Path(__file__).parent.parent.parent / 'data' / 'scraped'


def get_search_results_folder():
    """
    Get the search_results folder for today.

    Returns:
        Path object like storage/2026_01_18/search_results/
    """
    today = datetime.now().strftime("%Y_%m_%d")
    search_folder = STORAGE_DIR / today / 'search_results'
    search_folder.mkdir(parents=True, exist_ok=True)
    return search_folder


def extract_page_info(url):
    """
    Extract portal type and page number from URL.

    Args:
        url: The search results URL

    Returns:
        Tuple of (portal, page_num) or (None, None) if not a valid search URL
    """
    # Immobiliare.it: https://www.immobiliare.it/vendita-case/bologna/centro/?pag=2
    if 'immobiliare.it' in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Get page number from 'pag' parameter, default to 1
        page_num = params.get('pag', ['1'])[0]

        return ('immobiliare', page_num)

    # Idealista.it:
    # Page 1: https://www.idealista.it/vendita-case/bologna/centro/con-prezzo_700000.../
    # Page 2: https://www.idealista.it/vendita-case/bologna/centro/con-prezzo_700000.../lista-2.htm
    elif 'idealista.it' in url:
        # Check for lista-X.htm pattern
        match = re.search(r'/lista-(\d+)\.htm', url)

        if match:
            page_num = match.group(1)
        else:
            # No lista pattern means page 1
            page_num = '1'

        return ('idealista', page_num)

    return (None, None)


async def archive_search_page(page):
    """Archive a search results page."""
    print("🔍 Archiving search results page...")

    # Wait for page to be fully loaded
    print("   Waiting for page to load...")
    await page.wait_for_load_state('domcontentloaded')
    await page.wait_for_timeout(1000)

    html_content = await page.content()
    current_url = page.url

    # Extract portal and page number
    portal, page_num = extract_page_info(current_url)

    if not portal:
        print("❌ This doesn't appear to be an Immobiliare or Idealista search page")
        return None

    # Get search results folder
    search_folder = get_search_results_folder()

    # Create filename
    if portal == 'immobiliare':
        filename = f"immo_pag{page_num}.html"
    else:  # idealista
        filename = f"ideal_pag{page_num}.html"

    file_path = search_folder / filename

    # Check if file already exists
    if file_path.exists():
        print(f"⚠️  File {filename} already exists!")
        overwrite = await asyncio.get_event_loop().run_in_executor(
            None, input, "   Overwrite? (y/N): "
        )
        if overwrite.lower() != 'y':
            print("   Skipped.")
            return None

    # Save HTML
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Save URL reference
    url_file = search_folder / f"{filename}.url"
    with open(url_file, 'w', encoding='utf-8') as f:
        f.write(current_url)

    print(f"✅ Saved: {filename} ({len(html_content):,} bytes)")
    print(f"   Portal: {portal.title()}")
    print(f"   Page: {page_num}")

    return file_path


async def main():
    """Main search results scraper loop."""
    print("=" * 80)
    print("🎯 Manual Search Results Scraper")
    print("=" * 80)
    print("\nInstructions:")
    print("1. Navigate to a search results page (Immobiliare or Idealista)")
    print("2. Press ENTER here to download the search page")
    print("3. Click 'Next Page' in the browser")
    print("4. Press ENTER again to download that page")
    print("5. Repeat for all pages you want to archive")
    print("6. Type 'quit' or 'q' when done")
    print("\n" + "=" * 80 + "\n")

    async with async_playwright() as p:
        # Connect to Chrome with remote debugging
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
        print("   Navigate to search results pages manually in Chrome...")
        print("   (Your real Chrome - no bot detection!)\n")

        archived_count = 0

        while True:
            # Wait for user input
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "\n📍 Press ENTER to download current search page (or 'q' to quit): "
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

            # Archive the search page
            result = await archive_search_page(page)
            if result:
                archived_count += 1

        # Disconnect
        await browser.close()
        print("\n⚠️  Disconnected from Chrome (Chrome will stay open)")

    # Show summary
    today = datetime.now().strftime("%Y_%m_%d")
    search_folder = STORAGE_DIR / today / 'search_results'

    print("\n" + "=" * 80)
    print(f"✅ Search scraping complete! Archived {archived_count} pages")
    print("=" * 80)
    print(f"\nData saved to: {search_folder.absolute()}")
    print("You can close Chrome manually when done browsing.")


if __name__ == "__main__":
    asyncio.run(main())
