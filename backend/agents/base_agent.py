import logging
import time
import json
import urllib.parse
import re
import datetime as dt
from datetime import date
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Response
import anyio
import pandas as pd
import os

from utils.validators import is_valid_event
from utils.price_extractor import extract_price
from utils.date_extractor import extract_date
from utils.venue_validator import (
    extract_venue_from_json_ld,
    format_venue_for_display,
    validate_venue_data,
    format_event_with_venue,
    enhance_venue_with_location,
    format_venue_for_bookmyshow,
)
from utils.city_config import parse_city, venue_city_matches_selection, get_city_aliases

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TODAY = date.today()


class BaseAgent:
    def __init__(self, platform_name: str, base_url: str):
        self.platform_name = platform_name
        self.base_url = base_url
        self.intercepted_api_data: List[Dict] = []

    # ─────────────────────────────────────────────
    # Browser configuration
    # ─────────────────────────────────────────────
    def _get_browser_config(self) -> dict:
        return {
            "headless": False,  # Use False to avoid anti-bot detection
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        }

    def _get_context_config(self) -> dict:
        return {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-IN",
            "timezone_id": "Asia/Kolkata",
        }

    # ─────────────────────────────────────────────
    # Main entry-point
    # ─────────────────────────────────────────────
    def run_sync_extraction(
        self, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        """
        4-Layer pipeline:
          L1  Direct JSON extraction  (_perform_scraping_sync)
          L2  Network API sniffing    (_handle_response via page.on)
          L3  Google stealth fallback (_google_search_fallback)
          L4  Detail-page enrichment  (_enrich_event_details)
        """
        final_events: List[Dict] = []
        self.intercepted_api_data = []   # reset per run

        with sync_playwright() as p:
            browser = p.chromium.launch(**self._get_browser_config())
            context = browser.new_context(**self._get_context_config())
            page = context.new_page()

            # Stealth: remove webdriver flag
            page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )

            try:
                # ── Point 1: Handle City Aliases/Normalisation ──
                from utils.location_validator import normalize_location
                search_location, is_valid = normalize_location(location)
                
                logger.info(f"CITY REQUESTED: {location} (Normalized: {search_location})")
                
                # Use normalized location for the rest of the extraction
                location = search_location

                # ── Layer 2 setup: intercept API responses ──
                page.on("response", self._handle_response)

                seen_urls: set = set()
                global_seen_events = set()
                loop_counter = 0

                # PRIMARY ARCHITECTURE CHANGE: Progressive discovery loop
                while len(final_events) < target_count and loop_counter < 5:
                    loop_counter += 1
                    start_count = len(final_events)
                    logger.info(f"{self.platform_name}: Starting loop {loop_counter} (Yield: {start_count}/{target_count})")
                    candidates: List[Dict] = []

                    # ── Layer 1: platform-specific direct scraping ──
                    try:
                        candidates = self._perform_scraping_sync(
                            page, location, target_count, max_price
                        )
                        logger.info(f"{self.platform_name}: L1 found {len(candidates)} candidates")
                    except Exception as exc:
                        logger.warning(f"{self.platform_name}: L1 failed – {exc}")

                    # ── Merge API-sniffed data (Layer 2 results) ──
                    if self.intercepted_api_data:
                        candidates.extend(self.intercepted_api_data)
                        self.intercepted_api_data = [] # consume

                    # ── Layer 3: Google stealth fallback (if still underfilled) ──
                    browser_healthy = (
                        page and not page.is_closed() and 
                        page.context and page.context.browser and 
                        page.context.browser.is_connected()
                    )
                    
                    # Trigger rule: if we don't have enough candidates to reach target, run fallback
                    if browser_healthy and len(final_events) < target_count:
                        try:
                            # ISSUE 3 FIX: Pass browser and context to fallback for safe page restoration
                            fallback_results = self._google_search_fallback(page, location, target_count, browser, context)
                            candidates.extend(fallback_results)
                        except Exception as l3_exc:
                            logger.debug(f"{self.platform_name}: L3 fallback error (skipping) – {l3_exc}")
                    elif not browser_healthy:
                        logger.info(f"{self.platform_name}: Browser became unstable during L1, skipping L3 fallback")

                    new_candidates_found = False

                    # ── Layer 4: enrich + validate each candidate ──
                    for raw in candidates:
                        if len(final_events) >= target_count:
                            break
                        
                        url = (raw.get("url") or "").strip()
                        if not url or url in seen_urls:
                            continue
                            
                        # Reject non-event URLs
                        if any(x in url for x in ["/topics/", "/find/", "/groups/"]):
                            continue
                        
                        seen_urls.add(url)
                        new_candidates_found = True
                        
                        # Check browser health
                        if not page.context or not page.context.browser or not page.context.browser.is_connected():
                            logger.warning(f"{self.platform_name}: Browser context closed, stopping enrichment loop")
                            break

                        # 1. Extract/Enrich event data
                        if not raw.get("is_enriched"):
                            try:
                                # HUMAN-LIKE DELAY: Prevent rapid-fire enrichment requests
                                import random as _random
                                time.sleep(_random.uniform(1.5, 3.5))
                                
                                raw = self._enrich_event_details(page, raw)
                            except Exception as e:
                                logger.debug(f"{self.platform_name}: Enrichment failed for {url}: {e}")
                                continue
                        
                        if raw is None:
                            continue
                        
                        # Convert to formatted dict
                        event = self._format_event(raw)
                        if not event:
                            continue

                        title = event.get("event_name", "Unknown Event")
                        
                        # 2. Clean venue
                        original_venue = event.get("venue") or "Not specified"
                        cv = self._global_clean_venue(original_venue)
                        
                        # Special case for TBA
                        if cv is None:
                            if "tba" in original_venue.lower() or "to be announced" in original_venue.lower() or original_venue == "__TBA__":
                                cv = location
                            else:
                                logger.info(f"REJECTED: venue near you")
                                continue
                        event["venue"] = cv

                        # ── Layer 4: Lenient Location Match for Meetup & Swiggy Scenes ──
                        if self.platform_name.lower() in ["meetup", "swiggy scenes"]:
                            # Trust Meetup's and Swiggy's search page results as per user request
                            pass
                        else:
                            # 4. Validate Location (STRICT CITY MATCH for others)
                            if not self._validate_event_location(cv, location):
                                logger.info(f"REJECTED: location mismatch ({cv})")
                                continue

                        # 5. Organizer Extraction (already in enrichment/formatting, but ensure it's not "Unknown")
                        if not event.get("organizer"):
                            event["organizer"] = self.platform_name

                        # 6. Remove Duplicates
                        dup_key = (title, event.get("event_date"))
                        if dup_key in global_seen_events:
                            continue
                        global_seen_events.add(dup_key)

                        # 7. Price Check & Accept
                        if max_price is None or event["price"] <= max_price:
                            final_events.append(event)
                            logger.info(
                                f"✓ Event accepted: {title}"
                            )

                    # If no new events found -> break
                    if not new_candidates_found or len(final_events) == start_count:
                        break

                # Export to Excel
                if final_events:
                    logger.info(f"Final events collected: {len(final_events)}")
                    self._export_to_excel(final_events, location)

            except Exception as exc:
                logger.error(f"{self.platform_name}: Pipeline error – {exc}")
            finally:
                try:
                    browser.close()
                except Exception as close_error:
                    logger.debug(f"{self.platform_name}: Browser close error (may be already closed): {close_error}")

        logger.info(
            f"{self.platform_name}: Final yield = {len(final_events)} / {target_count}"
        )
        return final_events if final_events is not None else []

    async def extract_events(
        self, location: str, target_count: int, max_price: Optional[int] = None
    ) -> List[Dict]:
        out = await anyio.to_thread.run_sync(
            self.run_sync_extraction, location, target_count, max_price
        )
        return out if out is not None else []

    # ─────────────────────────────────────────────
    # Layer 1 (override per platform)
    # ─────────────────────────────────────────────
    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        return []

    # ─────────────────────────────────────────────
    # Global Validations
    # ─────────────────────────────────────────────
    def _global_clean_venue(self, venue: str) -> Optional[str]:
        if not venue:
            return None
        v = venue.lower().strip()
        bad = [
            "near you",
            "venue near you",
            "nearby venue",
            "not specified"
        ]
        for b in bad:
            if b in v:
                return None
        return venue.strip()

    def _validate_event_location(self, venue: str, city: str) -> bool:
        # Check if it's an online event first
        is_online = self._is_online_event(venue)
        if is_online:
            return True

        if not venue:
            return False

        # Use centralized robust city matching (handles alias like Bengaluru/Bangalore)
        return venue_city_matches_selection(venue, city)

    def _is_online_event(self, location_text: str) -> bool:
        if not location_text:
            return False
        l = location_text.lower()
        if "online" in l or "virtual" in l:
            return True
        return False

    def _is_valid_meetup_title(self, title: str) -> bool:
        if not title:
            return False
        # Simplified rule as per latest instruction: Allow any title longer than 5 chars
        return len(title.strip()) > 5

    def _export_to_excel(self, events: List[Dict], city: str):
        """Export events to Excel file using events-{city}-{platform}.xlsx format."""
        try:
            # Filename format: events-{City}-{platform}.xlsx
            platform_slug = self.platform_name.lower().replace(" ", "-")
            city_clean = city.strip().capitalize()
            filename = f"events-{city_clean}-{platform_slug}.xlsx"
            
            # Use exports folder if available
            target_dir = os.path.join(os.getcwd(), "exports")
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            
            filepath = os.path.join(target_dir, filename)

            # Excel Permission Error Fix: remove locked file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    # If still locked, use a timestamped fallback name
                    ts = dt.datetime.now().strftime("%H%M%S")
                    filename = f"events-{city_clean}-{platform_slug}-{ts}.xlsx"
                    filepath = os.path.join(target_dir, filename)

            df_data = []
            for e in events:
                # Reuse logic for artist name/details
                artists_raw = e.get("artists", [])
                artist_names = "N/A"
                artist_details = "N/A"
                
                if isinstance(artists_raw, list) and artists_raw:
                    names = []
                    details = []
                    for a in artists_raw:
                        if isinstance(a, dict):
                            name = a.get("name") or a.get("title")
                            if name: names.append(str(name))
                            role = a.get("description") or a.get("role")
                            if role: details.append(f"{name}: {role}")
                        else:
                            names.append(str(a))
                    
                    if names: artist_names = ", ".join(names)
                    if details: artist_details = " | ".join(details)
                elif isinstance(artists_raw, str):
                    artist_names = artists_raw

                df_data.append({
                    "Event Name":        e.get("event_name", "N/A"),
                    "Date":              e.get("event_date", "N/A"),
                    "Time":              e.get("event_time", "-"),
                    "Price":             e.get("price", "Free"),
                    "Platform":          e.get("platform", self.platform_name),
                    "Organizer":         e.get("organizer", "Unknown"),
                    "Description":       e.get("about_event") or e.get("description") or "N/A",
                    "Duration":          e.get("duration", "N/A"),
                    "Hashtags":          e.get("hashtags", "N/A"),
                    "Artist Name":       artist_names,
                    "Artist Details":    artist_details,
                    "Interested People": e.get("people_interested") or e.get("attending") or "N/A",
                    "Venue Address":     e.get("venue_address", "N/A"),
                    "Language":          e.get("event_language", "-"),
                    "Type":              e.get("event_type", "-"),
                    "Format":            e.get("event_format", "-"),
                    "City":              e.get("city", city),
                    "Venue":             e.get("venue", "N/A"),
                    "Rating":            e.get("rating", "-"),
                    "Reviews":           e.get("review_count", "-"),
                    "View Link":         e.get("event_url", "N/A"),
                })

            df = pd.DataFrame(df_data)
            df.to_excel(filepath, index=False, sheet_name=self.platform_name)
            logger.info(f"✓ Excel exported: {filename} ({len(events)} events)")
        except Exception as e:
            logger.error(f"Failed to export Excel: {e}")

    # ─────────────────────────────────────────────
    # Layer 2: API sniffing
    # ─────────────────────────────────────────────
    def _handle_response(self, response: Response):
        try:
            ct = response.headers.get("content-type", "")
            if "application/json" not in ct:
                return
            url = response.url.lower()
            # Only intercept event-relevant endpoints
            if not any(x in url for x in ["/api/", "graphql", "events", "search", "activities"]):
                return
            try:
                data = response.json()
            except Exception:
                return
            extracted = self._parse_api_json(data)
            if extracted:
                self.intercepted_api_data.extend(extracted)
        except Exception:
            pass

    def _parse_api_json(self, json_data) -> List[Dict]:
        """Override in platform subclasses when API structure is known."""
        return []

    # ─────────────────────────────────────────────
    # Layer 3: Google stealth fallback
    # ─────────────────────────────────────────────
    def _google_search_fallback(
        self, page, location: str, count_needed: int, browser=None, context=None
    ) -> List[Dict]:
        """
        Extracts price, date, and event URLs directly from Google snippets.
        Does NOT default date to a past value — leaves it None so enrichment fires.
        ISSUE 3 FIX: Accepts browser/context to safely restore page if closed.
        """
        if count_needed <= 0:
            return []
        
        # ISSUE 3 FIX: Check if page was closed before starting fallback
        if page.is_closed():
            if context:
                page = context.new_page()
            elif browser:
                page = browser.new_page()
            else:
                logger.warning(f"{self.platform_name}: Page closed and no context/browser to restore")
                return []

        # Platform-domain mapping for precise site-specific Google queries
        domain_map = {
            "BookMyShow":   "in.bookmyshow.com",
            "District":     "district.in",
            "Swiggy Scenes": "swiggy.com",
            "Skillbox":     "skillboxes.com",
            "Sort My Scene": "sortmyscene.com",
            "Mera Events":  "meraevents.com",
            "Urbanaut":     "urbanaut.app",
            "Urbanot":      "urbanaut.app",
            "Meetup":       "meetup.com",
        }
        site = domain_map.get(self.platform_name, "")
        site_filter = f"site:{site}" if site else f'"{self.platform_name}"'

        # Search variations for higher yield across hard-to-scrape sites
        queries = [
            f"{site_filter} {location} {self.platform_name} events tickets",
            f"{site_filter} {location} {self.platform_name} upcoming events",
            f"{site_filter} {location} events",
            f"{site_filter} {location} things to do",
        ]
        
        # Add Dineout/Mepass queries for Swiggy Scenes
        if self.platform_name == "Swiggy Scenes":
            queries.extend([
                f"Swiggy Dineout {location} events",
                f"site:dineout.co.in {location} events",
                f"site:mepass.in {location} events",
            ])
            
        results: List[Dict] = []

        for query in queries:
            if len(results) >= count_needed * 4:
                break
            
            # Paginate through 2 pages of Google
            for page_num in range(2):
                start = page_num * 10
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={start}"
                try:
                    # ISSUE 3 FIX: Ensure page is still open before navigation
                    if page.is_closed():
                        logger.warning(f"{self.platform_name}: Page closed during Google fallback, attempting restore")
                        if context:
                            page = context.new_page()
                        elif browser:
                            page = browser.new_page()
                        else:
                            continue
                    
                    page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(4.0) # Increased delay for Google

                    domain_key = (site or self.platform_name).lower().replace(" ", "")
                    # Flexible domain matching (e.g. "swiggy" should match "swiggy.com")
                    if "." in domain_key:
                        domain_key_base = domain_key.split(".")[0]
                    else:
                        domain_key_base = domain_key

                    titles = page.query_selector_all("h3")
                    if not titles:
                        break # No more results

                    for h3 in titles:
                        if len(results) >= count_needed * 4: # increased limit for better selection
                            break
                        try:
                            anchor = h3.evaluate_handle("n=>n.closest('a')").as_element()
                            if not anchor:
                                continue
                            href = anchor.get_attribute("href") or ""
                            if not href or "google.com" in href:
                                continue

                            logger.debug(f"Google L3 found URL: {href}")

                            # Must be from target domain (using flexible base match)
                            # Allow dineout/mepass for Swiggy Scenes
                            allowed_domains = [domain_key_base]
                            if self.platform_name == "Swiggy Scenes":
                                allowed_domains.extend(["swiggy", "dineout", "mepass"])
                                
                            if not any(d in href.lower() for d in allowed_domains):
                                logger.debug(f"Skipped {href}: no allowed domains in href")
                                continue

                            # Reject non-event / listing URLs
                            from urllib.parse import urlparse as _urlparse
                            parsed_href = _urlparse(href)
                            path_segs = [s for s in parsed_href.path.split("/") if s]
                            
                            # Less strict path segment check for certain platforms
                            min_segs = 1 if self.platform_name in ["Swiggy Scenes", "Urbanaut"] else 2
                            if len(path_segs) < min_segs:
                                logger.debug(f"Skipped {href}: path_segs {path_segs} too short")
                                continue
                            if any(bad in href.lower() for bad in [
                                "/search?", "?q=", "/login", "/register",
                                "/explore\n", "/category",
                            ]):
                                continue

                            # Snippet text
                            block = h3.evaluate_handle(
                                "n=>n.closest('div.g,div.v7W49e,div.tF2Cxc,div.MjjYud')"
                            ).as_element()
                            snippet = block.inner_text().replace("\n", " ") if block else ""

                            # Price — leave None if not found (triggers enrichment)
                            price_m = re.search(
                                r"(?:₹|INR|Rs\.?)\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)",
                                snippet, re.I,
                            )
                            price = price_m.group(1).replace(",", "") if price_m else None
                            if "free" in snippet.lower():
                                price = "0"

                            # Date — leave None if not found (triggers enrichment)
                            date_m = re.search(
                                r"(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
                                r"(?:\s+\d{4})?|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
                                r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?)",
                                snippet, re.I,
                            )
                            raw_date = date_m.group(1) if date_m else None

                            # Extract optional fields from snippet
                            snippet_metadata = {}
                            
                            # Event time (HH:MM)
                            time_m = re.search(r"\b(\d{1,2}):(\d{2})\b", snippet)
                            if time_m:
                                snippet_metadata["event_time"] = time_m.group(1) + ":" + time_m.group(2)
                            
                            # Event language hints
                            if re.search(r"\b(English|Hindi|Telugu|Tamil)\b", snippet, re.I):
                                snippet_metadata["event_language"] = re.search(r"\b(English|Hindi|Telugu|Tamil)\b", snippet, re.I).group(1)
                            
                            # Event type hints
                            for ptype in ["Concert", "Workshop", "Conference", "Comedy Show"]:
                                if ptype.lower() in snippet.lower():
                                    snippet_metadata["event_type"] = ptype
                                    break
                            
                            # Online/offline format
                            if "online" in snippet.lower() or "virtual" in snippet.lower():
                                snippet_metadata["event_format"] = "Online"
                            elif "offline" in snippet.lower() or "in-person" in snippet.lower():
                                snippet_metadata["event_format"] = "Offline"

                            results.append({
                                "name":        h3.inner_text().replace(" ...", "").strip(),
                                "url":         href,
                                "price":       price,
                                "date":        raw_date,
                                "description": snippet[:400],
                                "organizer":   self.platform_name,
                                **snippet_metadata,
                            })
                        except Exception:
                            continue

                except Exception as exc:
                    logger.warning(f"{self.platform_name}: Google fallback pass error – {exc}")
                    break # Skip to next query if one page fails
                    
                time.sleep(1)

        return results

    # ─────────────────────────────────────────────
    # Layer 4: Detail-page enrichment
    # ─────────────────────────────────────────────
    def _extract_event_metadata_from_json_ld(self, item: dict, raw_event: dict) -> None:
        """
        Extract optional metadata fields from JSON-LD event schema.
        Populates: organizer, event_language, event_type, duration, event_time, event_format, attending, rating.
        """
        try:
            # Organizer
            if not raw_event.get("organizer") or raw_event.get("organizer") == self.platform_name:
                org = item.get("organizer")
                if isinstance(org, dict):
                    org_name = org.get("name")
                    if org_name:
                        raw_event["organizer"] = org_name
                elif isinstance(org, str) and org:
                    raw_event["organizer"] = org

            # Event language
            lang = item.get("inLanguage") or item.get("language")
            if lang:
                if isinstance(lang, dict):
                    lang = lang.get("name") or lang.get("alternateName")
                if isinstance(lang, str):
                    raw_event["event_language"] = lang[:20]

            # Event type / category
            event_type = item.get("eventType") or item.get("category")
            if event_type:
                if isinstance(event_type, list):
                    event_type = event_type[0] if event_type else None
                if isinstance(event_type, dict):
                    event_type = event_type.get("name")
                if isinstance(event_type, str):
                    raw_event["event_type"] = event_type[:50]

            # Duration
            duration = item.get("duration")
            if duration:
                if isinstance(duration, str):
                    raw_event["duration"] = duration[:30]

            # Event time (separate from date)
            start_dt = item.get("startDate") or item.get("startDateTime")
            if start_dt and isinstance(start_dt, str) and "T" in start_dt:
                try:
                    time_part = start_dt.split("T")[1].split("+")[0].split("Z")[0][:5]
                    if time_part:
                        raw_event["event_time"] = time_part
                except Exception:
                    pass

            # Event format (online/offline)
            attend_mode = item.get("eventAttendanceMode") or item.get("isOnline")
            if attend_mode:
                if isinstance(attend_mode, dict):
                    attend_mode = attend_mode.get("name")
                if isinstance(attend_mode, str):
                    if "OnlineAttendanceMode" in attend_mode:
                        attend_mode = "Online"
                    elif "OfflineAttendanceMode" in attend_mode:
                        attend_mode = "Offline"
                    raw_event["event_format"] = attend_mode[:20]
                elif isinstance(attend_mode, bool):
                    raw_event["event_format"] = "Online" if attend_mode else "Offline"

            # Attending / RSVP count
            attn = item.get("attendees") or item.get("attendeeCount") or item.get("yes_rsvp_count")
            if attn:
                try:
                    raw_event["attending"] = int(attn)
                except (ValueError, TypeError):
                    pass

            # Rating
            rating = item.get("aggregateRating") or item.get("rating") or item.get("reviewRating")
            if rating:
                if isinstance(rating, dict):
                    rating_val = rating.get("ratingValue")
                    if rating_val:
                        try:
                            raw_event["rating"] = float(rating_val)
                        except (ValueError, TypeError):
                            pass
                elif isinstance(rating, (int, float)):
                    try:
                        raw_event["rating"] = float(rating)
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass

    def _extract_event_metadata_from_text(self, page, raw_event: dict) -> None:
        """
        Extract optional metadata fields from visible page text when JSON-LD is missing or incomplete.
        Populates: organizer, event_language, event_type, event_time, event_format, rating.
        """
        try:
            body = page.inner_text("body")
            if not body:
                return

            # Event time (HH:MM pattern)
            if not raw_event.get("event_time"):
                time_m = re.search(r"\b(\d{1,2}):(\d{2})(?:\s*(am|pm|AM|PM|a\.m\.|p\.m\.))?\b", body)
                if time_m:
                    raw_event["event_time"] = time_m.group(1) + ":" + time_m.group(2)

            # Event language (common language keywords)
            if not raw_event.get("event_language"):
                lang_patterns = [(r"\b(English|Hindi|Telugu|Tamil|Kannada|Malayalam|Punjabi|Bengali|Marathi|Gujarati)\b", "language")]
                for pattern, _ in lang_patterns:
                    lang_m = re.search(pattern, body, re.I)
                    if lang_m:
                        raw_event["event_language"] = lang_m.group(1)[:20]
                        break

            # Event type / category (common keywords)
            if not raw_event.get("event_type"):
                type_patterns = ["Concert", "Workshop", "Conference", "Meetup", "Comedy Show", "Seminar", "Webinar", "Panel Discussion", "Networking Event"]
                for ptype in type_patterns:
                    if ptype.lower() in body.lower():
                        raw_event["event_type"] = ptype
                        break

            # Event format (online/offline hints)
            if not raw_event.get("event_format"):
                if re.search(r"\b(online|virtual|zoom|webinar)\b", body, re.I):
                    raw_event["event_format"] = "Online"
                elif re.search(r"\b(in-person|offline|on-site|venue)\b", body, re.I):
                    raw_event["event_format"] = "Offline"

            # Organizer fallback (patterns like \"Organized by ...\" or \"Organizer: ...\")
            if not raw_event.get("organizer") or raw_event.get("organizer") == self.platform_name:
                org_m = re.search(r"(?:Organized by|Organizer|Hosted by|By:)\s*([^\n.]{3,100})", body, re.I)
                if org_m:
                    org_text = org_m.group(1).strip()
                    if org_text and len(org_text) > 2:
                        raw_event["organizer"] = org_text[:80]

            # Rating (star ratings like 4.5/5)
            if not raw_event.get("rating"):
                rating_m = re.search(r"(\d\.\d|[0-5])\s*(?:/\s*5|stars?)\b", body, re.I)
                if rating_m:
                    try:
                        raw_event["rating"] = float(rating_m.group(1))
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass

    def _self_healing_extract(self, page, field_type: str) -> Optional[str]:
        """
        Production-grade extraction with fallback sequences for high resiliency.
        """
        targets = {
            "title": [
                "h1", "h2", "h3", ".card-title", ".event-title", ".title",
                "meta[property='og:title']", "a[class*='title'] div"
            ],
            "date": [
                "time", "[class*='date']", "[class*='Date']", "span:has-text('2025')", "span:has-text('2026')",
                "meta[property='event:start_time']"
            ],
            "location": [
                "[class*='location']", "[class*='venue']", "[class*='Venue']", ".address",
                "span:has-text('Hyderabad')", "meta[property='event:location']"
            ],
            "description": [
                "meta[name='description']", "meta[property='og:description']",
                "[class*='description']", "section[class*='about']", "[class*='snippet']"
            ],
            "price": [
                ".price", ".ticket-price", "[class*='Price']", "[class*='amount']",
                "span:has-text('₹')", "span:has-text('Rs')"
            ]
        }
        
        selectors = targets.get(field_type, [])
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    val = ""
                    if sel.startswith("meta"):
                        val = el.get_attribute("content") or ""
                    else:
                        val = el.inner_text().strip()
                    if val and len(val) > 1:
                        return val
            except Exception:
                continue
        return None

    def _enrich_event_details(self, page, raw_event: dict) -> dict:
        """
        Visits the event detail page to extract:
          1. JSON-LD schema (name, startDate, offers.price)
          2. Visible page text price regex fallback
          3. Visible page text date regex fallback
        """
        # Skip enrichment if page is already closed (browser resource exhaustion)
        if page.is_closed():
            logger.debug(f"{self.platform_name}: Page closed, skipping detail page enrichment")
            return raw_event
        
        url = (raw_event.get("url") or "").strip()
        if not url or "google.com" in url:
            return raw_event

        scrape_loc = str(raw_event.get("location") or "Hyderabad").split(",")[0].strip() or "Hyderabad"

        try:
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=18000)
            except Exception as goto_exc:
                # If page was closed during goto, it's a resource issue - just return raw event
                if "closed" in str(goto_exc).lower():
                    logger.debug(f"{self.platform_name}: Page closed during goto, skipping enrichment for {url[:50]}")
                    return raw_event
                # Other errors (timeout, network) - try to recover
                raise
            
            if not resp or resp.status >= 400:
                # Cloudflare / bot block — try a targeted Google search for price
                raw_event = self._google_price_lookup(page, raw_event)
                return raw_event

            # -- JSON-LD extraction (highest confidence) --
            ld_items = self._extract_json_ld(page)
            for item in ld_items:
                type_val = str(item.get("@type", "")).lower()
                if "event" in type_val:
                    # Price
                    offer = item.get("offers") or {}
                    if isinstance(offer, list):
                        offer = offer[0] if offer else {}
                    ld_price = str(offer.get("price", "") or "")
                    if ld_price and ld_price not in ("0", ""):
                        raw_event["price"] = ld_price

                    # Date
                    ld_date = item.get("startDate") or item.get("startDateTime") or ""
                    if ld_date:
                        raw_event["date"] = ld_date

                    # Venue
                    location = item.get("location") or {}
                    if isinstance(location, dict):
                        # Extract full venue object from JSON-LD Place schema
                        venue_obj = extract_venue_from_json_ld(
                            location, scraping_location=scrape_loc
                        )
                        if venue_obj:
                            raw_event["venue"] = venue_obj
                            logger.debug(f"{self.platform_name}: ✓ Extracted JSON-LD venue: {venue_obj.get('name')}")
                        else:
                            # Fallback to simple name extraction
                            ld_venue = location.get("name") or ""
                            if ld_venue:
                                raw_event["venue"] = ld_venue
                    else:
                        ld_venue = str(location) if location else ""
                        if ld_venue:
                            raw_event["venue"] = ld_venue

                    # Extract optional metadata from JSON-LD
                    self._extract_event_metadata_from_json_ld(item, raw_event)

                    # Only short-circuit when venue is present; otherwise run text fallbacks below
                    if (
                        raw_event.get("price")
                        and raw_event.get("date")
                        and raw_event.get("venue")
                    ):
                        return raw_event

            # -- Visible-text fallback for price --
            if not raw_event.get("price") or raw_event.get("price") in ("0", 0):
                # Search specific ticket sections first
                for p_sel in ["[class*='ticket']", "[class*='price']", "[class*='cost']"]:
                    try:
                        e = page.query_selector(p_sel)
                        if e:
                            pt = e.inner_text().strip()
                            pm = re.search(r"(?:₹|INR|Rs\.?)\s?([\d,]+)", pt, re.I)
                            if pm:
                                raw_event["price"] = pm.group(1).replace(",", "")
                                break
                    except Exception:
                        pass

                # Fallback to general body text
                if not raw_event.get("price") or raw_event.get("price") in ("0", 0):
                    try:
                        body = page.inner_text("body")
                        pm = re.search(
                            r"(?:₹|INR|Rs\.?)\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)",
                            body, re.I,
                        )
                        if pm:
                            raw_event["price"] = pm.group(1).replace(",", "")
                        elif re.search(r"\bfree\b", body, re.I):
                            raw_event["price"] = "0"
                    except Exception:
                        pass

            # -- Visible-text fallback for date --
            if not raw_event.get("date"):
                try:
                    body = page.inner_text("body")
                    dm = re.search(
                        r"(\d{1,2}(?:st|nd|rd|th)?\s+"
                        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
                        r"(?:\s+\d{4})?|\d{4}-\d{2}-\d{2})",
                        body, re.I,
                    )
                    if dm:
                        raw_event["date"] = dm.group(1)
                except Exception:
                    pass

            # -- Visible-text fallback for venue --
            if not raw_event.get("venue"):
                try:
                    # Search for venue/location specific elements
                    for v_sel in ["[class*='venue']", "[class*='location']", "[class*='address']"]:
                        try:
                            e = page.query_selector(v_sel)
                            if e:
                                vt = e.inner_text().strip()
                                if vt and len(vt) > 2:
                                    raw_event["venue"] = vt
                                    break
                        except Exception:
                            pass
                    
                    # Fallback to body text search for common venue indicators
                    if not raw_event.get("venue"):
                        body = page.inner_text("body")
                        # Look for patterns like "Venue: Something" or "Location: Something"
                        vm = re.search(r"(?:Venue|Location|Address)[\s:]*([^\n]{5,100})", body, re.I)
                        if vm:
                            venue_text = vm.group(1).strip()
                            # Clean up the text
                            venue_text = re.sub(r'[•\-*]', '', venue_text).strip()
                            if venue_text and len(venue_text) > 2:
                                raw_event["venue"] = venue_text
                except Exception:
                    pass

            # -- Extract description (for BookMyShow and similar platforms) --
            if not raw_event.get("description") or raw_event.get("description") in ("", "-", "Not available"):
                try:
                    body = page.inner_text("body")
                    
                    # Try to find description-specific sections
                    for desc_sel in ["[class*='description']", "[class*='about']", "[class*='details']"]:
                        try:
                            e = page.query_selector(desc_sel)
                            if e:
                                desc_text = e.inner_text().strip()
                                if desc_text and len(desc_text) > 20:
                                    raw_event["description"] = desc_text[:500]
                                    break
                        except Exception:
                            pass
                    
                    # Fallback: Look for common description patterns in body
                    if not raw_event.get("description") or raw_event.get("description") in ("", "-", "Not available"):
                        # Try patterns like "About:" or "Description:" sections
                        patterns = [
                            r"(?:About|Description|Details)[\s:]+([^\n]{50,300}?)(?:\n\n|$)",
                            r"(?:About|Description)[\s:]+([^\n]+?)(?:\n|$)",
                        ]
                        
                        for pattern in patterns:
                            dm = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
                            if dm:
                                desc_text = dm.group(1).strip()
                                if desc_text and len(desc_text) > 10:
                                    raw_event["description"] = desc_text[:500]
                                    break
                    
                    if raw_event.get("description") and len(str(raw_event.get("description", ""))) > 10:
                        logger.debug(f"{self.platform_name}: ✓ Extracted description ({len(str(raw_event.get('description', '')))} chars)")
                
                except Exception as e:
                    logger.debug(f"Description extraction error: {e}")

            # -- Extract optional metadata from visible text --
            self._extract_event_metadata_from_text(page, raw_event)

        except Exception as exc:
            # Check if this was a page closed error - if so, it's a resource exhaustion issue
            # and we should just return the raw event without logging it as an error
            if "closed" in str(exc).lower():
                logger.debug(f"Page closed during enrichment for {url[:50]}, returning raw event")
            else:
                logger.debug(f"Enrichment failed for {url}: {exc}")

        return raw_event

    # ─────────────────────────────────────────────
    # Utilities
    def _google_price_lookup(self, page, raw_event: dict) -> dict:
        """
        When direct URL is Cloudflare-blocked, search Google for
        '[event name] [city] price tickets' to extract price + date.
        """
        name = raw_event.get("name", "")
        if not name:
            return raw_event
        try:
            q = f'"{name}" price tickets 2025 2026'
            url = f"https://www.google.com/search?q={urllib.parse.quote(q)}"
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(1.5)
            body = page.inner_text("body")

            # Price
            if not raw_event.get("price") or raw_event.get("price") in (0, "0"):
                pm = re.search(
                    r"(?:₹|INR|Rs\.?)\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)",
                    body, re.I,
                )
                if pm:
                    raw_event["price"] = pm.group(1).replace(",", "")
                elif re.search(r"\bfree\b", body, re.I):
                    raw_event["price"] = "0"

            # Date (if also missing)
            if not raw_event.get("date"):
                dm = re.search(
                    r"(\d{1,2}(?:st|nd|rd|th)?\s+"
                    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
                    r"(?:\s+\d{4})?|\d{4}-\d{2}-\d{2})",
                    body, re.I,
                )
                if dm:
                    raw_event["date"] = dm.group(1)
        except Exception as exc:
            logger.debug(f"Google price lookup failed for '{name}': {exc}")
        return raw_event

    # ─────────────────────────────────────────────
    def _deep_scroll_page(self, page, scrolls: int = 8):
        """Scroll page N times with 2s waits to trigger lazy loading."""
        for i in range(scrolls):
            page.evaluate("window.scrollBy(0, 900)")
            time.sleep(2)

    def _extract_json_ld(self, page) -> List[Dict]:
        data: List[Dict] = []
        try:
            for s in page.query_selector_all("script[type='application/ld+json']"):
                try:
                    js = json.loads(s.inner_text().strip())
                    if isinstance(js, list):
                        data.extend(js)
                    else:
                        data.append(js)
                except Exception:
                    continue
        except Exception:
            pass
        return data

    def _extract_window_object(self, page, object_name: str) -> Optional[dict]:
        try:
            return page.evaluate(f"window.{object_name}")
        except Exception:
            return None

    # ─────────────────────────────────────────────
    # Strict validation & formatting
    # ─────────────────────────────────────────────
    def _format_event(self, raw_event: dict) -> Optional[dict]:
        event_url = str(raw_event.get("url", "")).strip()

        # URL sanity checks
        if not event_url or "http" not in event_url:
            return None
        if any(bad in event_url for bad in ["google.com", "/search?", "?q="]):
            return None

        # ── Point 3: Title Extraction & Rejection ──
        event_name = str(raw_event.get("name", "")).strip()
        # Reject events without title or generic names
        if not event_name or event_name.lower() in ["untitled", "event", "untitled event", "none", "null", "undefined"]:
            logger.info(f"{self.platform_name}: Rejecting untitled/generic event '{event_name}'")
            return None

        # ── Price Rule: if not found -> -1 (except Meetup: 'Not Specified' = 0) ──
        raw_price = str(raw_event.get("price", "")).strip()
        # For Meetup: "Not Specified" means likely free, "Free" = 0
        if raw_price.lower() in ("not specified", "not_specified", "not mentioned"):
            if self.platform_name.lower() == "meetup":
                price_val = -1  # User wants 'Not Mentioned' specifically
            else:
                price_val = -1
        elif raw_price.lower() == "free":
            price_val = 0
        else:
            price_val = extract_price(raw_price)
            if price_val is None:
                price_val = -1

        # ── Date Rule ──
        date_raw = str(raw_event.get("date", "") or "")
        date_val = extract_date(date_raw)
        
        if not date_val:
            if self.platform_name in ["Urbanaut", "Sort My Scene"]:
                date_val = "Unknown"
            else:
                logger.debug(f"{self.platform_name}: Discarding '{event_name}' — no parseable date")
                return None

        # Filter past dates (unless Unknown)
        if date_val != "Unknown":
            try:
                parsed_date = dt.datetime.strptime(date_val, "%Y-%m-%d").date()
                if parsed_date < TODAY:
                    logger.debug(f"{self.platform_name}: Discarding '{event_name}' — past date {date_val}")
                    return None
            except Exception:
                pass

        # ── Location Rule ──
        # Point 5: Scraper must use request location
        city = parse_city(str(raw_event.get("location") or "Hyderabad"))

        # ── Description Rule ──
        description = str(raw_event.get("description", "")).strip()
        if not description or len(description) < 5:
            description = "Not available"

        # ── Venue Rule (with validation and formatting) ──
        venue = raw_event.get("venue")
        
        # Handle list of venues (e.g., from JSON-LD arrays) - extract first one
        if isinstance(venue, list) and venue:
            venue = venue[0]
        
        # Filter out placeholder venues FIRST
        from utils.venue_validator import is_placeholder_venue, clean_venue_text
        if isinstance(venue, str):
            venue = clean_venue_text(venue)
        elif isinstance(venue, dict):
            venue_name = venue.get("name", "")
            if is_placeholder_venue(venue_name):
                # Try to use address as fallback
                address = venue.get("street_address") or venue.get("address", "")
                if address and not is_placeholder_venue(str(address)):
                    venue = clean_venue_text(str(address))
                else:
                    venue = "Not specified"
        
        # If venue is a dict (from JSON-LD Place schema), validate and format it
        if isinstance(venue, dict):
            is_valid_venue, venue_reason = validate_venue_data(venue)
            if is_valid_venue:
                venue_formatted = extract_venue_from_json_ld(venue, scraping_location=city)
                if venue_formatted:
                    venue_formatted = enhance_venue_with_location(venue_formatted, scraping_location=city)
                    if self.platform_name == "BookMyShow":
                        venue = format_venue_for_bookmyshow(venue_formatted)
                    else:
                        venue = venue_formatted
                else:
                    venue = "Not specified"
            else:
                venue = "Not specified"
        else:
            # Handle string or None venue
            venue_str = str(venue or "").strip()
            if not venue_str or venue_str.lower() in ["not specified", "none", "n/a"]:
                venue = "Not specified"
            else:
                venue = venue_str

        formatted = {
            "event_name":  event_name,
            "event_date":  date_val,
            "price":       price_val,
            "organizer":   str(raw_event.get("organizer") or ("Not Specified" if self.platform_name == "Sort My Scene" else self.platform_name)).strip(),
            "platform":    self.platform_name,
            "event_url":   event_url,
            "city":        city,
            "venue":       venue,
            "description": description[:500],
        }

        # Add optional metadata fields if present in raw_event
        for optional_field in [
            "event_language", "event_type", "duration", "event_time", 
            "event_format", "attending", "rating", "review_count",
            "about_event", "hashtags", "people_interested", "artists", 
            "venue_address", "organizer_url", "description", "attending"
        ]:
            if optional_field in raw_event and raw_event[optional_field]:
                formatted[optional_field] = raw_event[optional_field]

        # Format event with proper venue information for display
        formatted = format_event_with_venue(formatted)

        # ── ENSURE VENUE IS ALWAYS A STRING ──
        if not isinstance(formatted.get("venue"), str):
            venue_val = formatted.get("venue")
            if isinstance(venue_val, dict):
                formatted["venue"] = venue_val.get("name", "Not specified")
            elif isinstance(venue_val, list) and venue_val:
                formatted["venue"] = str(venue_val[0]).strip()
            else:
                formatted["venue"] = str(venue_val or "Not specified").strip()

        # ── STRICT VALIDATION RULES ──
        ev_name = str(formatted.get("event_name", ""))
        ev_venue = str(formatted.get("venue", ""))
        ev_date = str(formatted.get("event_date", ""))
        ev_price = formatted.get("price")
        
        # 1. Block Artist Pages (Skip for Swiggy Scenes as it hosts DJ/Party events)
        if self.platform_name.lower() != "swiggy scenes":
            invalid_keywords_artist = [
                "artist",
                "singer",
                "rapper",
                "dj",
                "band",
                "performer profile",
                "artist page"
            ]
            if any(k in ev_name.lower() for k in invalid_keywords_artist):
                logger.info(f"REJECTED: Artist page detected -> {ev_name}")
                return None

        # 2. Skip Generic Pages / Activities
        invalid_titles_generic = [
            "things to do",
            "activities in",
            "top events",
            "best events",
            "google play",
            "app store", 
            "download app"
        ]
        if any(x in ev_name.lower() for x in invalid_titles_generic):
            logger.info(f"REJECTED: Generic listing -> {ev_name}")
            return None

        # 4. VENUE EXTRACTION (Optional but logged)
        if not ev_venue:
            ev_venue = "Not specified"
            formatted["venue"] = ev_venue
            
        # 3. EVENT PAGE VALIDATION (Must have title, date, venue, price/free)
        # Skip generic rejection for Meetup (as per user request: "scrape whatever u found")
        if self.platform_name.lower() != "meetup":
            if not ev_name or ev_name.lower() in ["untitled", "event", "untitled event", "none", "null", "undefined"]:
                logger.info("REJECTED: missing or generic title")
                return None
            
        if not ev_date or ev_date.lower() in ["unknown", "none", "not available"]:
            # Certain platforms may not parse dates from snippets — don't reject
            if self.platform_name.lower() not in ["meetup", "urbanaut", "sort my scene", "swiggy scenes"]:
                logger.info(f"REJECTED: missing date ({ev_name})")
                return None
            
        if ev_price == -1 and "free" not in ev_name.lower() and "free" not in str(formatted.get("description", "")).lower():
            # Don't reject certain events for missing price (recovered during enrichment)
            if self.platform_name.lower() not in ["meetup", "urbanaut", "sort my scene", "swiggy scenes"]:
                logger.info(f"REJECTED: missing price ({ev_name})")
                return None
            else:
                formatted["price"] = -1  # Keep as Not Mentioned for recovery

        # 5. Automatic City Filtering (Skip Wrong Location)
        venue_text = ev_venue.lower()
        city_text = str(raw_event.get("location", city)).lower()
        search_city = city.lower()

        # Neutral city matching using centralized aliases
        search_terms = get_city_aliases(search_city)

        city_matched = False
        # Check venue text and event location field
        for term in search_terms:
            if term in venue_text or term in city_text:
                city_matched = True
                break

        # If not matched yet, check KNOWN_VENUES to see if a neighbourhood/area
        # maps to the requested city (e.g. "indiranagar" → Bangalore)
        if not city_matched:
            try:
                from utils.venue_validator import KNOWN_VENUES
                for area_key, area_info in KNOWN_VENUES.items():
                    if area_key in venue_text:
                        mapped_city = area_info.get("city", "").lower()
                        if mapped_city in search_terms or mapped_city == search_city:
                            city_matched = True
                            logger.info(
                                f"City matched via KNOWN_VENUES: '{area_key}' → {area_info.get('city')} "
                                f"for '{ev_name}'"
                            )
                            break
            except Exception:
                pass

        if not city_matched and self.platform_name.lower() not in ["meetup", "swiggy scenes"]:
            logger.info(f"REJECTED: Wrong city -> {ev_name} at {ev_venue}")
            return None

        is_valid, reason = is_valid_event(formatted)
        if not is_valid:
            logger.info(f"REJECTED: {reason} ({ev_name})")
            return None

        return formatted

    def _google_search_discovery(self, page, query: str, count: int = 50) -> List[str]:
        """
        Pure discovery: Returns a list of unique URLs matching the query and platform domain.
        Used to gather large candidate lists for hard-to-scrape platforms.
        """
        urls = []
        try:
            # ── Point 8: Prevent Google Fallback Timeout (20s) ──
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            time.sleep(3.5) # Wait for results
            
            domain_map = {
                "BookMyShow": "in.bookmyshow.com",
                "District": "district.in",
                "Swiggy Scenes": "swiggy.com",
                "Skillbox": "skillboxes.com",
                "Sort My Scene": "sortmyscene.com",
                "Mera Events": "meraevents.com",
                "Urbanaut": "urbanaut.app",
                "Meetup": "meetup.com",
            }
            domain_key = domain_map.get(self.platform_name, self.platform_name).lower().replace(" ", "")
            
            # Extract all links that belong to the platform
            anchors = page.query_selector_all("a[href]")
            for a in anchors:
                href = a.get_attribute("href") or ""
                # Clean URL and validate domain
                if domain_key in href.lower() and "google.com" not in href.lower():
                    clean_url = href.split("?")[0].split("#")[0]
                    if clean_url not in urls:
                        if "/events/" in clean_url or "/activities/" in clean_url:
                            urls.append(clean_url)
                        
            logger.info(f"{self.platform_name}: Google discovery found {len(urls)} URLs for '{query}'")
        except Exception as e:
            logger.debug(f"{self.platform_name}: Google discovery error for '{query}': {e}")
            
        return urls
