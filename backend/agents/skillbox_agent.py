import logging
import time
import re
from datetime import date
from typing import List, Dict, Optional
from .base_agent import BaseAgent
from utils.city_config import get_city_aliases

logger = logging.getLogger(__name__)

class SkillboxAgent(BaseAgent):
    def __init__(self):
        super().__init__("Skillbox", "https://www.skillboxes.com/events")
        # Performance limits
        self.max_parallel_event_pages = 3
        self.page_wait_time = 3
        self.event_page_wait = 3 # Increased to allow Angular to load

    def _get_browser_config(self) -> dict:
        config = super()._get_browser_config()
        config["headless"] = False # Keep headful for manual selection
        return config

    def run_sync_extraction(self, location: str, target_count: int, max_price: Optional[int]) -> List[Dict]:
        """
        CUSTOM LOOP: Handles manual selection, location verification, and robust enrichment.
        """
        from playwright.sync_api import sync_playwright
        final_events = []
        seen_urls = set()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(**self._get_browser_config())
            context = browser.new_context(**self._get_context_config())
            
            # Resource Blocking for enrichment
            def intercept_resources(route):
                # We block images and videos but allow scripts and stylesheets for proper Angular rendering
                if route.request.resource_type in ["image", "video", "font", "media"]:
                    route.abort()
                else:
                    route.continue_()
            
            page = context.new_page()
            
            # Step 1: Open listing page
            logger.info(f"Skillbox: Opening {self.base_url}...")
            page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
            
            # Step 2: WAIT FOR USER to select city
            logger.info("\n" + "!"*60)
            logger.info(f"ACTION REQUIRED: Please select '{location}' in the Skillbox browser window.")
            logger.info("Once events are loaded, press Enter in THIS terminal.")
            logger.info("!"*60 + "\n")
            input(">>> Press Enter after city selection is complete...")

            # Step 3: Scrape listing (L1)
            # Dynamic Scrolling: If target_count is high, scroll more to get more candidates
            num_scrolls = max(3, min(10, target_count // 4)) 
            logger.info(f"Skillbox: Performing {num_scrolls} scrolls to meet target of {target_count} events...")
            
            # Wait for cards
            event_card_selector = 'a[href*="/events/"]'
            page.wait_for_selector(event_card_selector, timeout=10000)

            for _ in range(num_scrolls):
                page.evaluate("window.scrollBy(0, 1000)")
                page.wait_for_timeout(1000)

            # Extract card metadata
            candidates = self._perform_scraping_sync(page, location, target_count, max_price)
            
            # Step 4: Enrichment (L4) with Location Verification
            page.route("**/*", intercept_resources)
            
            logger.info(f"Skillbox: Verifying and Enriching {len(candidates)} candidates...")
            for raw in candidates:
                if len(final_events) >= target_count:
                    break
                
                url = raw.get("event_url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    try:
                        # Enrich and verify location
                        enriched = self._enrich_event_details(page, raw, location)
                        if enriched:
                            # Strict check: if the enrichment rejected the location, skip it
                            if enriched.get("_rejected"):
                                logger.info(f"[REJECTED] Skillbox: Rejected '{enriched['event_name']}' - Location mismatch.")
                                continue
                                
                            formatted = self._format_event(enriched)
                            if formatted:
                                final_events.append(formatted)
                                logger.info(f"[OK] Skillbox: Accepted '{formatted['event_name']}'")
                    except Exception as e:
                        logger.error(f"Skillbox Enrichment error: {e}")
            
            browser.close()
            
        return final_events

    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        """
        L1: Extract event URLs and basic names from the listing.
        """
        try:
            # Extract card metadata
            cards = page.evaluate("""() => {
                let results = [];
                let anchors = document.querySelectorAll('a[href*="/events/"]');
                let seen = new Set();
                anchors.forEach(a => {
                    let href = a.getAttribute('href');
                    if (!href || href === '/events' || href === '/events/' || seen.has(href)) return;
                    seen.add(href);
                    let container = a.closest('.col-12, .col-md-6, .col-lg-4, .card, [class*="event"]') || a.parentElement;
                    let img = a.querySelector('img');
                    let title = img ? img.getAttribute('alt') : '';
                    if (!title) title = container.innerText.split('\\n')[0];
                    results.push({ url: href, name: title });
                });
                return results;
            }""")

            return [{
                "platform": "Skillbox",
                "event_name": c["name"],
                "event_url": f"https://www.skillboxes.com{c['url']}" if c['url'].startswith('/') else c['url'],
                "city": location
            } for c in cards]

        except Exception as e:
            logger.error(f"Skillbox L1 Error: {e}")
            return []

    def _enrich_event_details(self, page, raw_event: dict, requested_city: str) -> dict:
        """
        L4: Detail page extraction WITH location verification.
        """
        try:
            # Use 'networkidle' to ensure Angular components and data are loaded
            page.goto(raw_event["event_url"], wait_until="networkidle", timeout=25000)
            page.wait_for_timeout(self.event_page_wait * 1000)

            # 1. Location Verification with Aliases
            city_aliases = [a.lower() for a in get_city_aliases(requested_city)]
            
            # Add specific requested aliases
            if "bangalore" in city_aliases or "bengaluru" in city_aliases:
                city_aliases.extend(["bangalore", "bengaluru"])
            if "mumbai" in city_aliases or "bombay" in city_aliases:
                city_aliases.extend(["mumbai", "bombay"])
            if "delhi" in city_aliases:
                city_aliases.extend(["delhincr", "new delhi", "ncr"])
            if "gurugram" in city_aliases or "gurgaon" in city_aliases:
                city_aliases.extend(["gurugram", "gurgaon", "gurugram(gurgaon)"])
            
            city_aliases = list(set(city_aliases))
            
            # Extract JSON-LD (Primary data source)
            ld_items = self._extract_json_ld(page)
            ld_event = next((it for it in ld_items if "event" in str(it.get("@type", "")).lower()), {})
            body_text = page.inner_text("body") or ""

            # Check JSON-LD location
            found_city = ""
            loc = ld_event.get("location")
            if isinstance(loc, dict):
                addr = loc.get("address")
                if isinstance(addr, dict):
                    found_city = (addr.get("addressLocality") or "").lower()
            
            # Verification: If JSON-LD has a city, it must match. If not, check body text.
            if found_city:
                if not any(alias in found_city for alias in city_aliases):
                    raw_event["_rejected"] = True
                    return raw_event
            else:
                # Body text verification fallback
                if not any(alias in body_text.lower() for alias in city_aliases):
                    raw_event["_rejected"] = True
                    return raw_event

            # 2. Detail Extraction
            # Name
            raw_event["event_name"] = ld_event.get("name") or raw_event.get("event_name")
            
            # Date with fallbacks
            raw_event["date"] = ld_event.get("startDate") or ""
            
            if not raw_event["date"]:
                # Fallback 1: Hero/Banner text (usually immediately after the title)
                date_el = page.query_selector('h1 + p, .event-detail-banner p')
                if date_el:
                    raw_event["date"] = date_el.inner_text().strip()
                
                # Fallback 2: Regex search for Skillbox date format (e.g., 09 May 2026 | 08:00 PM)
                if not raw_event["date"]:
                    date_m = re.search(r'(\d{2}\s+[A-Za-z]+\s+\d{4}\s*\|\s*\d{2}:\d{2}\s+[AP]M)', body_text, re.I)
                    if date_m:
                        raw_event["date"] = date_m.group(1).strip()
            
            # Description
            raw_event["description"] = ld_event.get("description") or ""
            if not raw_event["description"]:
                # Try to find description in DOM
                desc_el = page.query_selector('[class*="description"], [class*="about"]')
                if desc_el:
                    raw_event["description"] = desc_el.inner_text().strip()

            # Price
            price = "Not Mentioned"
            offers = ld_event.get("offers")
            if isinstance(offers, dict): price = offers.get("price")
            elif isinstance(offers, list) and offers: price = offers[0].get("price")
            
            if not price or price == "Not Mentioned":
                # Look for price patterns: INR 499, Rs.499, Rs 499
                price_m = re.search(r'(?:Rs.|INR|Rs\.?)\s*([\d,]+)', body_text, re.I)
                price = price_m.group(1).replace(",", "") if price_m else "Not Mentioned"
            raw_event["price"] = str(price)

            # Venue Extraction refinement
            venue = ""
            if isinstance(loc, dict): 
                venue = loc.get("name")
                # Sometimes venue name is in addressLocality
                if not venue and isinstance(loc.get("address"), dict):
                    venue = loc["address"].get("streetAddress")
            
            if not venue:
                # Try specific selectors for venue name
                v_el = page.query_selector('[class*="venue"], [class*="location-name"]')
                if v_el: venue = v_el.inner_text().strip()
                
            if not venue or len(venue) < 3:
                # Regex fallback for Venue: <Name>
                venue_m = re.search(r'(?:Venue|Location|At)\s*[:\-]?\s*([^\n]{3,100})', body_text, re.I)
                venue = venue_m.group(1).strip() if venue_m else requested_city
            
            raw_event["venue"] = venue

            # Organizer
            org_el = page.query_selector('a[href*="/organizer/"]')
            if org_el:
                raw_event["organizer"] = org_el.inner_text().strip()
            else:
                org_m = re.search(r'(?:Organized by|Organizer|Hosted by|By)\s*[:\-]?\s*([^\n]{3,80})', body_text, re.I)
                raw_event["organizer"] = org_m.group(1).strip() if org_m else "Skillbox"

            # Artist
            artist_m = re.search(r'(?:Artist|Performer|Featuring|ft\.?)\s*[:\-]?\s*([^\n]{3,100})', body_text, re.I)
            raw_event["artist"] = artist_m.group(1).strip() if artist_m else ""

            # Hashtags
            tag_els = page.query_selector_all('a[href*="/category/"], [class*="tag"], [class*="genre"]')
            hashtags = [el.inner_text().strip() for el in tag_els if el.inner_text().strip()]
            raw_event["hashtags"] = list(set(hashtags))[:5]

            # description polish
            if raw_event["description"]:
                raw_event["description"] = re.sub(r'<[^>]*>', '', raw_event["description"]).strip()

            return raw_event
        except Exception as e:
            logger.debug(f"Skillbox Enrichment error: {e}")
            return raw_event

    def _format_event(self, raw: dict) -> Optional[dict]:
        if not raw.get("event_name") or not raw.get("event_url"): return None
        return {
            "platform": "Skillbox",
            "event_name": raw.get("event_name", ""),
            "date": raw.get("date", ""),
            "organizer": raw.get("organizer", ""),
            "artist": raw.get("artist", ""),
            "venue": raw.get("venue", ""),
            "city": raw.get("city", ""),
            "price": raw.get("price", "Not Mentioned"),
            "hashtags": raw.get("hashtags", []),
            "description": raw.get("description", ""),
            "event_url": raw.get("event_url", "")
        }

    def _extract_json_ld(self, page) -> List[Dict]:
        try:
            return page.evaluate("""() => {
                return Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                    .map(s => { try { return JSON.parse(s.innerText); } catch(e) { return null; } })
                    .filter(x => x);
            }""")
        except: return []
