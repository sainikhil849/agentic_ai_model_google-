from playwright.sync_api import sync_playwright

def test_district_extraction_live():
    """Test extraction logic on actual District.in event pages"""

    # Use real URLs found on the site
    test_urls = [
        "https://www.district.in/events/adult-jokes-only-jan9-2026-buy-tickets",
        "https://www.district.in/events/budx-nba-house-2026-buy-tickets",
        "https://www.district.in/events/ye-live-in-india-2026-buy-tickets",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for url in test_urls:
            print(f"\n{'='*80}")
            print(f"Testing: {url}")
            print('='*80)

            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=15000)
                if not response or response.status >= 400:
                    print(f"❌ Got status {response.status if response else 'None'}")
                    continue

                # Wait for JavaScript to render
                page.wait_for_timeout(2000)

                # Test 1: Extract event name from various selectors
                print("\n🎯 Testing Event Name Extraction:")
                selectors_to_test = [
                    ("h1", "h1"),
                    ("h1.event-title", "h1.event-title"),
                    ("h2[class*='title']", "h2[class*='title']"),
                    ("div[class*='title']", "div[class*='title']"),
                    ("div[class*='event-name']", "div[class*='event-name']"),   
                    ("[data-testid='event-title']", "[data-testid='event-title']"),
                    ("h1, h2, h3", "h1, h2, h3"),
                    ("span[class*='title']", "span[class*='title']"),
                    (".event-name", ".event-name"),
                    ("div[class*='heading']", "div[class*='heading']"),
                ]

                for selector, label in selectors_to_test:
                    try:
                        elements = page.query_selector_all(selector)
                        for i, el in enumerate(elements[:3]):  # First 3 matches
                            text = el.inner_text().strip()
                            if text and len(text) > 5:
                                print(f"  ✓ {label} [{i}]: {text[:70]}")      
                    except Exception as e:
                        pass

                # Test 2: Extract venue from various selectors
                print("\n📍 Testing Venue Extraction:")
                venue_selectors = [
                    ("p[class*='venue']", "p[class*='venue']"),
                    ("div[class*='venue']", "div[class*='venue']"),
                    ("span[class*='venue']", "span[class*='venue']"),
                    ("p[class*='location']", "p[class*='location']"),
                    ("div[class*='location']", "div[class*='location']"),       
                    ("p[class*='address']", "p[class*='address']"),
                    ("div[data-testid*='location']", "div[data-testid*='location']"),
                    (".venue", ".venue"),
                    (".location", ".location"),
                    ("span[class*='location']", "span[class*='location']"),
                ]

                for selector, label in venue_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        for i, el in enumerate(elements[:2]):
                            text = el.inner_text().strip()
                            if text and len(text) > 3:
                                print(f"  ✓ {label} [{i}]: {text[:70]}")      
                    except Exception as e:
                        pass

                # Test 3: Extract JSON-LD
                print("\n📋 Testing JSON-LD Extraction:")
                try:
                    ld_data = page.evaluate("""
                        () => {
                            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                            return Array.from(scripts).map(s => JSON.parse(s.textContent));
                        }
                    """)

                    for ld in ld_data:
                        if isinstance(ld, list):
                            ld = ld[0] if ld else {}

                        if "Event" in str(ld.get("@type", "")):
                            print(f"  ✓ Found Event JSON-LD:")
                            print(f"    - name: {ld.get('name', 'N/A')[:50]}")  
                            print(f"    - location: {ld.get('location', {}).get('name', 'N/A')[:50] if isinstance(ld.get('location'), dict) else 'N/A'}")       
                            print(f"    - startDate: {ld.get('startDate', 'N/A')}")
                except Exception as e:
                    print(f"  ❌ JSON-LD extraction failed: {e}")

                # Test 4: Get full page text and look for patterns
                print("\n🔍 Scanning Page Text for Venue Patterns:")
                body_text = page.inner_text("body")

                # Look for venue patterns
                import re
                venue_patterns = [
                    (r"(?:Venue|Location|Address|Where)\s*(?::|–|-|:)\s*([^\n]+?)(?:\n|$)", "Venue/Location line"),
                    (r"([A-Za-z\s0-9]+(?:Hyderabad|Bangalore|Delhi|Mumbai|Chennai|Pune|Bengaluru)[A-Za-z\s,]*?)(?:\n|$)", "City reference"),
                ]

                for pattern, ptype in venue_patterns:
                    matches = re.findall(pattern, body_text, re.I)
                    for match in matches[:2]:
                        cleaned = match.strip()[:60]
                        if cleaned and len(cleaned) > 5:
                            print(f"  ✓ {ptype}: {cleaned}")

                # Test 5: Common class/id patterns
                print("\n🎨 Testing Common Class/ID Patterns:")
                common_patterns = [
                    ("[class*='event']", "[class*='event']"),
                    ("[id*='event']", "[id*='event']"),
                    ("[class*='details']", "[class*='details']"),
                    ("[class*='info']", "[class*='info']"),
                ]
                
                for selector, label in common_patterns:
                    try:
                        elements = page.query_selector_all(selector)
                        if elements:
                            print(f"  ✓ {label}: Found {len(elements)} elements")
                    except Exception as e:
                        pass

            except Exception as e:
                print(f"❌ Error: {e}")

        browser.close()

if __name__ == "__main__":
    test_district_extraction_live()
