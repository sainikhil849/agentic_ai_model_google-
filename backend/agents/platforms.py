import time
import json
import re
import logging
import os
import pandas as pd
from typing import List, Dict, Optional
from .base_agent import BaseAgent
from .skillbox_agent import SkillboxAgent
from datetime import datetime
from utils.city_config import bookmyshow_explore_slug, parse_city, urbanaut_city_query, district_city_slug, get_city_aliases

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# BOOKMYSHOW — L1: __INITIAL_STATE__ + detail-page price/desc
# ══════════════════════════════════════════════════════════════
class BookMyShowAgent(BaseAgent):
    def __init__(self):
        super().__init__("BookMyShow", "https://in.bookmyshow.com/explore/events-hyderabad")

    def _is_valid_bms_venue(self, raw: str) -> bool:
        """
        New minimal validation: reject ONLY empty or obviously generic UI fragments.
        Venue is now optional metadata, we never reject the event here.
        """
        lower = raw.lower().strip()
        if not lower or lower in ["", "-", "view", "others"]:
            return False
        return True

    def _clean_bms_venue(self, raw: str) -> str:
        """
        Clean UI garbage but DO NOT reject events.
        Keep only the first line and strip.
        """
        if not raw: return ""
        
        # Keep only first line
        text = str(raw).split("\n")[0].strip()
        
        bad_phrases = [
            "venue near you",
            "near you",
            "book now",
            "book tickets",
            "select seats",
            "view",
            "others",
            "share",
        ]
        
        lower = text.lower()
        for phrase in bad_phrases:
            if phrase in lower:
                return ""
                
        return text.strip()

    def _extract_bookmyshow_organizer(self, page) -> str:
        """
        Extract organizer/presenter details.
        1. JSON-LD: organizer.name
        2. DOM: Search text near 'Organizer', 'Presented by', 'Hosted by'
        """
        try:
            # 1. JSON-LD
            import json as _json
            for s in page.query_selector_all("script[type='application/ld+json']"):
                try:
                    obj = _json.loads(s.inner_text().strip())
                    items = obj if isinstance(obj, list) else [obj]
                    for item in items:
                        org = item.get("organizer") or {}
                        name = org.get("name")
                        if name:
                            logger.info(f"BookMyShow: ✓ Organizer extracted (JSON-LD) → {name}")
                            return name.strip()
                except Exception: continue
        except Exception: pass

        try:
            # 2. Text Search Fallback
            for kw in ["Organizer", "Presented by", "Hosted by"]:
                target = page.locator(f"text=/{kw}/i").locator("xpath=..").first
                if target.count() > 0:
                    text = target.inner_text().strip()
                    # Remove the keyword label
                    clean = re.sub(fr"(?i){kw}\s*:?", "", text).strip()
                    if clean and len(clean) > 2:
                        logger.info(f"BookMyShow: ✓ Organizer extracted (DOM) → {clean}")
                        return clean
        except Exception: pass

        return "BookMyShow"

    def _extract_bookmyshow_venue_name(self, page, city: str = "Hyderabad") -> str:
        """
        Venue extraction priority:
        1. JSON-LD
        2. Venue link
        3. Venue label
        4. Meta tags
        5. Title fallback
        """
        # 1. JSON-LD
        try:
            import json as _json
            for s in page.query_selector_all("script[type='application/ld+json']"):
                try:
                    obj = _json.loads(s.inner_text().strip())
                    items = obj if isinstance(obj, list) else [obj]
                    for item in items:
                        if not isinstance(item, dict): continue
                        if "event" in str(item.get("@type", "")).lower():
                            loc = item.get("location")
                            if isinstance(loc, list) and loc:
                                loc = loc[0]
                            
                            name = ""
                            if isinstance(loc, dict):
                                name = loc.get("name") or ""
                            
                            candidate = self._clean_bms_venue(name)
                            if candidate:
                                # Lenient match for Bangalore/Bengaluru
                                if city and city.lower() in ["bangalore", "bengaluru"]:
                                    if any(x in candidate.lower() for x in ["bangalore", "bengaluru"]):
                                        logger.info(f"BookMyShow: \u2713 Venue extracted (LD/Alias) \u2192 {candidate}")
                                        return candidate

                                logger.info(f"BookMyShow: \u2713 Venue extracted (JSON-LD) \u2192 {candidate}")
                                return candidate
                except Exception: continue
        except Exception: pass

        # 2. Venue Link
        try:
            venue_link = page.query_selector('a[href*="/venue/"]')
            if venue_link:
                raw = (venue_link.inner_text() or "").strip()
                candidate = self._clean_bms_venue(raw)
                if candidate:
                    logger.info(f"BookMyShow: \u2713 Venue extracted (Link) \u2192 {candidate}")
                    return candidate
        except Exception: pass

        # 3. Venue Label
        try:
            for label in ["Venue", "Location"]:
                el = page.locator(f"text=/^{label}:/i").first
                if el.count() > 0:
                    raw = el.inner_text().strip()
                    clean = re.sub(fr"(?i)^{label}:?\s*", "", raw).strip()
                    candidate = self._clean_bms_venue(clean)
                    if candidate:
                        logger.info(f"BookMyShow: \u2713 Venue extracted (Label) \u2192 {candidate}")
                        return candidate
        except Exception: pass

        # 4. Meta Tags
        try:
            meta = page.query_selector('meta[property="og:description"]')
            if meta:
                content = meta.get_attribute("content") or ""
                match = re.search(r"(?i)\bat\b\s+([^,]+?)(?=\s+on|\s+at|\s+in|\||\.|$)", content)
                if match:
                    candidate = self._clean_bms_venue(match.group(1))
                    if candidate:
                        logger.info(f"BookMyShow: \u2713 Venue extracted (Meta) \u2192 {candidate}")
                        return candidate
        except Exception: pass

        # 5. Title Fallback
        try:
            title_el = page.locator("h1").first
            if title_el.count() > 0:
                title = title_el.inner_text()
                match = re.search(r" at ([A-Za-z0-9 ,&\-]+)", title, re.I)
                if match:
                    candidate = self._clean_bms_venue(match.group(1))
                    if candidate:
                        logger.info(f"BookMyShow: \u2713 Venue extracted (Title) \u2192 {candidate}")
                        return candidate
        except Exception: pass

        return None

    def _enrich_event_details(self, page, raw_event: dict) -> dict:
        # Step 1: Base Delay
        page.wait_for_timeout(800)

        # Step 2: Normalize City
        requested_city = getattr(self, "_current_scrape_city", "Delhi")
        display_city = parse_city(raw_event.get("location") or requested_city)
        raw_event["location"] = display_city

        # Step 3: Event Name Fallback
        try:
            event_name = page.locator("h1").first.inner_text().strip()
            if event_name and event_name.lower() not in ["untitled", "event"]:
                raw_event["name"] = event_name
        except Exception: pass

        # Step 4: Global City Validation (Neutral Alias-based)
        from utils.city_config import get_city_aliases
        page_text = (page.inner_text("body") or "").lower()
        allowed_variants = get_city_aliases(display_city)
        found_requested = any(v.lower() in page_text for v in allowed_variants)

        if not found_requested:
            # Strictly exclude major cities if they appear and are NOT in allowed variants
            major_cities = ["delhi","mumbai","bombay","bangalore","bengaluru","hyderabad","chennai","pune","kolkata","ahmedabad","gurgaon","gurugram","noida"]
            for city in major_cities:
                if city not in [v.lower() for v in allowed_variants] and re.search(fr"\b{city}\b", page_text):
                    logger.info(f"REJECTED: City mismatch \u2192 requested '{display_city}' but found '{city}'")
                    return None

        # Step 5: Base Enrichment
        enriched = super()._enrich_event_details(page, raw_event)
        if not enriched: return None

        # Step 6: Advanced Extraction
        try:
            # 6.1: Evaluate browser-side for rich metadata
            extra_data = page.evaluate("""
                () => {
                    const data = { 
                        ld: [], 
                        interests: "", 
                        about: "", 
                        duration: "", 
                        artists: [], 
                        hashtags: "", 
                        organizer: "" 
                    };
                    
                    // 1. JSON-LD
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    scripts.forEach(s => { try { data.ld.push(JSON.parse(s.innerText)); } catch(e) {} });

                    // 2. Deep State Extraction
                    const state = window.__INITIAL_STATE__;
                    if (state && state.eventsSynopsisApi && state.eventsSynopsisApi.queries) {
                        const queries = state.eventsSynopsisApi.queries;
                        
                        // Recursive finder
                        const findData = (name) => {
                            for (let k in queries) {
                                if (k.includes(name) && queries[k].data) return queries[k].data;
                            }
                            return null;
                        };

                        const primary = findData('getPrimaryData');
                        const sessions = findData('getPrimarySessionData');

                        if (sessions && sessions.widgets) {
                            const iw = sessions.widgets.EVENT_TAGS_AND_INTERESTED;
                            if (iw && iw.cards && iw.cards[0] && iw.cards[0].leftRightText) {
                                const lr = iw.cards[0].leftRightText[0];
                                
                                // Tags (Hashtags)
                                try {
                                    const tags = lr.leftText.text[0].components.map(c => c.text).filter(t => t);
                                    if (tags.length > 0) data.hashtags = tags.join(", ");
                                } catch(e) {}

                                // Interests
                                try {
                                    const intComp = lr.rightText.text[0].components.find(c => c.text && c.text.toLowerCase().includes('interested'));
                                    if (intComp) data.interests = intComp.text;
                                } catch(e) {}
                            }
                            
                            // Artists fallback
                            const aw = sessions.widgets.DESKTOP_ARTIST;
                            if (aw && aw.cards) {
                                aw.cards.forEach(c => {
                                    if (c.text && c.text[0] && c.text[0].components) {
                                        const name = c.text[0].components[0].text;
                                        if (name) data.artists.push({ name: name, description: "" });
                                    }
                                });
                            }
                        }

                        if (primary && primary.widgets) {
                            // About fallback
                            const abw = primary.widgets.ABOUT_THE_EVENT;
                            if (abw && abw.cards) {
                                const card = abw.cards.find(c => c.text && c.text[0] && c.text[0].text);
                                if (card) data.about = card.text[0].text.replace(/<[^>]*>/g, '').trim();
                            }
                            if (!data.about) data.about = primary.synopsis || primary.description || "";
                        }
                    }

                    // 3. DOM Fallbacks (if state failed)
                    if (!data.interests) {
                        const el = Array.from(document.querySelectorAll('span, div, p')).find(e => 
                            e.innerText && /interested/i.test(e.innerText) && /\\d+/.test(e.innerText) && e.innerText.length < 60
                        );
                        if (el) data.interests = el.innerText.trim();
                    }

                    if (!data.hashtags) {
                        const tagEls = Array.from(document.querySelectorAll('[class*="event-tags"], .event-attributes span'));
                        data.hashtags = tagEls.map(el => el.innerText.trim()).filter(v => v && v.length < 30).join(", ");
                    }

                    if (data.artists.length === 0) {
                        const artContainers = document.querySelectorAll('[class*="CastCard"], [class*="ArtistCard"]');
                        artContainers.forEach(c => {
                            const lines = c.innerText.split('\\n').map(l => l.trim()).filter(l => l);
                            if (lines[0]) data.artists.push({ name: lines[0], description: lines[1] || "" });
                        });
                    }

                    if (!data.organizer) {
                        const orgPatterns = [/Presented by/i, /Organized by/i, /Hosted by/i];
                        for (const p of orgPatterns) {
                            const el = Array.from(document.querySelectorAll('span, div, a, p')).find(e => 
                                e.innerText && p.test(e.innerText) && e.innerText.length < 120
                            );
                            if (el) {
                                data.organizer = el.innerText.replace(p, "").replace(/^[:\\s-]+/, "").trim();
                                break;
                            }
                        }
                    }

                    return data;
                }
            """)

            # 6.2: Process JSON-LD
            ld_event = {}
            for item in extra_data.get('ld', []):
                items = item if isinstance(item, list) else [item]
                for it in items:
                    if isinstance(it, dict) and "event" in str(it.get("@type", "")).lower():
                        ld_event = it
                        break
                if ld_event: break

            if ld_event:
                # 1. Price
                offers = ld_event.get("offers", [])
                if isinstance(offers, dict): offers = [offers]
                if isinstance(offers, list):
                    prices = []
                    for o in offers:
                        if isinstance(o, dict) and o.get("price"):
                            try: prices.append(float(o["price"]))
                            except: pass
                    if prices:
                        min_p, max_p = int(min(prices)), int(max(prices))
                        enriched["price"] = f"\u20b9{min_p}" if min_p == max_p else f"\u20b9{min_p} - \u20b9{max_p}"
                
                # 2. About
                if not extra_data.get("about") and ld_event.get("description"):
                    extra_data["about"] = ld_event["description"]

                # 3. Artists
                if not extra_data.get("artists") and ld_event.get("performers"):
                    perf = ld_event["performers"]
                    if isinstance(perf, list):
                        extra_data["artists"] = [{"name": p.get("name"), "description": ""} for p in perf if p.get("name")]

            # 6.3: INITIAL_STATE Fallback (Pure HTML Parsing for Stability)
            try:
                html = page.content()
                state_match = re.search(r"window\.__INITIAL_STATE__\s*=\s*({.*?});", html)
                if state_match:
                    state = json.loads(state_match.group(1))
                    
                    # Target the known RTK Query path
                    queries = state.get("eventsSynopsisApi", {}).get("queries", {})
                    
                    def get_data(name):
                        for k, v in queries.items():
                            if name in k and isinstance(v, dict) and v.get("data"):
                                return v["data"]
                        return None

                    primary = get_data("getPrimaryData")
                    session = get_data("getPrimarySessionData")

                    if session:
                        widgets = session.get("widgets", {})
                        # 1. Interests and Tags (Visible Labels)
                        iw = widgets.get("EVENT_TAGS_AND_INTERESTED")
                        if iw and iw.get("cards"):
                            card = iw["cards"][0]
                            lr_list = card.get("leftRightText") or []
                            if lr_list:
                                lr = lr_list[0]
                                try:
                                    # Categories / Hashtags (e.g. Comedy Shows)
                                    tags = [c.get("text") for c in lr.get("leftText", {}).get("text", [{}])[0].get("components", []) if c.get("text")]
                                    if tags: enriched["hashtags"] = ", ".join(tags)
                                    # Interests (e.g. 1.4k interested)
                                    comps = lr.get("rightText", {}).get("text", [{}])[0].get("components", [])
                                    txt = next((c.get("text") for c in comps if c.get("text") and "interested" in c.get("text").lower()), None)
                                    if txt: enriched["people_interested"] = txt
                                except: pass
                        
                        # 2. Artist Details
                        if not enriched.get("artists"):
                            aw = widgets.get("DESKTOP_ARTIST")
                            if aw and aw.get("cards"):
                                art_objs = []
                                for ac in aw["cards"]:
                                    comps = ac.get("text", [{}])[0].get("components", [])
                                    name = next((c.get("text") for c in comps if c.get("text")), None)
                                    if name: art_objs.append({"name": name, "description": ""})
                                if art_objs: enriched["artists"] = art_objs

                    if primary:
                        # 3. About Event (Synopsis)
                        if not enriched.get("about_event"):
                            abw = primary.get("widgets", {}).get("ABOUT_THE_EVENT")
                            if abw and abw.get("cards"):
                                for c in abw["cards"]:
                                    if c.get("text") and c["text"][0].get("text"):
                                        txt = c["text"][0]["text"]
                                        enriched["about_event"] = re.sub(r"<[^>]*>", "", txt).strip()
                                        break
                            if not enriched.get("about_event"):
                                enriched["about_event"] = primary.get("synopsis") or primary.get("description")
                            
                            # 4. Duration
                            if not enriched.get("duration"):
                                enriched["duration"] = primary.get("duration") or primary.get("sessionDuration")

                            # 5. Rich Venue (Building from state)
                            if not enriched.get("venue") or enriched.get("venue") == display_city:
                                vn = primary.get("venueName")
                                if vn:
                                    # Try to find area in session data
                                    area = ""
                                    if session:
                                        # Look for area in the session summary or locality
                                        area = session.get("locality") or session.get("venueAddress") or ""
                                        if "," in area: area = area.split(",")[0].strip()
                                    
                                    enriched["venue"] = f"{vn}, {area}" if area and area.lower() not in vn.lower() else vn
                
            except Exception: pass

            # 6.4: Map Extra Eval Data
            if extra_data.get("about"): enriched["about_event"] = extra_data["about"]
            if extra_data.get("interests"): enriched["people_interested"] = extra_data["interests"]
            if extra_data.get("duration"): enriched["duration"] = extra_data["duration"]
            if extra_data.get("organizer"): enriched["organizer"] = extra_data["organizer"]
            if extra_data.get("artists"): enriched["artists"] = extra_data["artists"]
            if extra_data.get("hashtags"): enriched["hashtags"] = extra_data["hashtags"]
            
            # Map hashtags to event_type if event_type is missing
            if enriched.get("hashtags") and not enriched.get("event_type"):
                enriched["event_type"] = enriched["hashtags"].split(",")[0].strip()

        except Exception as e:
            logger.debug(f"BookMyShow rich enrichment error: {e}")

        # Step 7: Final Polish
        if not enriched.get("organizer"): enriched["organizer"] = "BookMyShow"
        if enriched.get("about_event"):
            enriched["about_event"] = enriched["about_event"].split("Read More")[0].strip()
        
        extracted_venue = self._extract_bookmyshow_venue_name(page, city=display_city)
        enriched["venue"] = extracted_venue or enriched.get("venue_name") or display_city

        return enriched

    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        try:
            slug = bookmyshow_explore_slug(location)
            display_city = parse_city(location)
            self._current_scrape_city = display_city
            url = f"https://in.bookmyshow.com/explore/events-{slug}"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                page.wait_for_selector("a[href*='/events/'], body", timeout=20000)
            except Exception:
                pass
            # Increase scroll depth for high target counts
            scroll_passes = 25 if target_count < 50 else 50
            self._deep_scroll_page(page, scrolls=scroll_passes)

            raw_candidates = []

            # L1a — Window state (fast path)
            state = self._extract_window_object(page, "__INITIAL_STATE__") or {}
            explore = state.get("explore", {})
            for group in explore.get("groups", []):
                for item in group.get("events", []):
                    event_path = item.get("eventUrl")
                    if event_path:
                        raw_candidates.append({
                            "name":  item.get("eventName"),
                            "url":   f"https://in.bookmyshow.com{event_path}",
                            "date":  item.get("displayDate"),
                            "price": item.get("price"),
                            "location": display_city,
                        })

            # L1b — DOM fallback when state is empty (Cloudflare block)
            if not raw_candidates:
                for a in page.query_selector_all("a[href*='/events/']"):
                    href = a.get_attribute("href") or ""
                    if href.count("/") >= 2:
                        full_url = (
                            f"https://in.bookmyshow.com{href}"
                            if href.startswith("/") else href
                        )
                        name_el = a.query_selector("h3, h4, [class*='title'], [class*='name']")
                        raw_candidates.append({
                            "name": name_el.inner_text().strip() if name_el else None,
                            "url":  full_url,
                            "location": display_city,
                        })

            # Return candidates for Layer 4 processing
            # Layer 4 will handle all enrichment including optional metadata extraction
            return raw_candidates[:target_count * 5]
        except Exception as exc:
            logger.debug(f"BookMyShow L1 error: {exc}")
            return []

    def _parse_api_json(self, data) -> List[Dict]:
        """Parse BMS event API shards intercepted during page load (Case-Insensitive)."""
        results = []
        try:
            def _recurse(obj):
                if isinstance(obj, dict):
                    # Robust case-insensitive check for common BMS event keys
                    name = obj.get("eventName") or obj.get("EventName") or obj.get("eventname")
                    url_path = obj.get("eventUrl") or obj.get("EventURL") or obj.get("eventurl")
                    
                    if name and url_path:
                        results.append({
                            "name":  name,
                            "url":   f"https://in.bookmyshow.com{url_path}" if url_path.startswith("/") else url_path,
                            "date":  obj.get("displayDate") or obj.get("DisplayDate") or obj.get("eventDate"),
                            "price": obj.get("price") or obj.get("Price") or obj.get("minPrice"),
                            "location": getattr(self, "_current_scrape_city", "Hyderabad"),
                        })
                    for v in obj.values():
                        _recurse(v)
                elif isinstance(obj, list):
                    for item in obj:
                        _recurse(item)
            _recurse(data)
        except Exception:
            pass
        return results


# ══════════════════════════════════════════════════════════════
# DISTRICT — Multi-level scraping: Main page + Google + Enrichment
# ══════════════════════════════════════════════════════════════
class DistrictAgent(BaseAgent):
    def __init__(self):
        super().__init__("District", "https://www.district.in/events/")
        self.excel_filepath = None
        self.events_count_saved = 0

    # ── City alias map for filtering ──
    CITY_ALIASES = {
        'hyderabad': ['hyderabad', 'secunderabad', 'telangana', 'gachibowli', 'boulder hills', 'hitech city', 'madhapur'],
        'bangalore': ['bengaluru', 'bangalore', 'whitefield', 'koramangala'],
        'bengaluru': ['bengaluru', 'bangalore', 'whitefield', 'koramangala'],
        'delhi': ['delhi', 'delhi/ncr', 'new delhi', 'ncr', 'dwarka'],
        'mumbai': ['mumbai', 'bombay', 'navi mumbai', 'bandra', 'andheri', 'thane'],
        'bombay': ['mumbai', 'bombay', 'navi mumbai', 'bandra', 'andheri', 'thane'],
        'pune': ['pune'],
        'chennai': ['chennai', 'madras'],
        'kolkata': ['kolkata', 'calcutta'],
        'gurgaon': ['gurgaon', 'gurugram'],
        'gurugram': ['gurgaon', 'gurugram'],
        'noida': ['noida', 'greater noida'],
        'ahmedabad': ['ahmedabad', 'gandhinagar'],
        'goa': ['goa', 'panjim', 'panaji', 'margao'],
        'jaipur': ['jaipur'],
        'kochi': ['kochi', 'cochin', 'ernakulam'],
        'lucknow': ['lucknow'],
        'chandigarh': ['chandigarh'],
        'indore': ['indore'],
    }

    def _get_city_terms(self, city: str) -> list:
        """Get all alias terms for a city."""
        return self.CITY_ALIASES.get(city.lower(), [city.lower()])

    def _city_matches(self, text: str, city_terms: list) -> bool:
        """Check if any city term appears in text."""
        text_lower = text.lower()
        return any(term in text_lower for term in city_terms)

    # ─────────────────────────────────────────────────────────
    # Card text parser — extracts date, name, venue, city, price
    # from District's concatenated card text WITHOUT visiting pages
    # ─────────────────────────────────────────────────────────
    def _parse_district_card(self, card_text: str) -> Optional[Dict]:
        """
        Parse concatenated card text from District event card.
        Format: {date ending AM/PM}{event name}{venue, city}{₹price onwards}{Book tickets}
        """
        if not card_text or len(card_text) < 15:
            return None

        text = card_text.strip()

        # Step 1: Remove "Book tickets" from end
        text = re.sub(r'\s*Book\s+tickets\s*$', '', text, flags=re.I).strip()

        # Step 2: Extract price from end
        price = 'N/A'
        price_match = re.search(r'(₹[\d,]+(?:\s*onwards)?|Coming\s+soon)\s*$', text, re.I)
        if price_match:
            raw_price = price_match.group(1)
            if 'coming soon' in raw_price.lower():
                price = 'Coming soon'
            else:
                digits = re.search(r'[\d,]+', raw_price)
                if digits:
                    price = digits.group().replace(',', '')
            text = text[:price_match.start()].strip()

        # Step 3: Extract date from beginning
        # Patterns: "Mon, DD Mon, HH:MM AM/PM" or date ranges or recurring
        date_str = ''
        date_patterns = [
            # "Mon, DD Mon – Mon, DD Mon, HH:MM AM/PM" (date range)
            r'^((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,\s+\d{1,2}\s+\w+\s*–\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,\s+\d{1,2}\s+\w+,\s+(?:\d{1,2}:\d{2}\s*(?:AM|PM)|Multiple\s+slots))',
            # "Mon, DD Mon, HH:MM AM/PM" (single date)
            r'^((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,\s+\d{1,2}\s+\w+,\s+\d{1,2}:\d{2}\s*(?:AM|PM))',
            # "Every Mon, HH:MM AM/PM to HH:MM AM/PM"
            r'^(Every\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,\s+\d{1,2}:\d{2}\s*(?:AM|PM)\s+to\s+\d{1,2}:\d{2}\s*(?:AM|PM))',
            # "Mon, DD Mon onwards, Multiple Dates"
            r'^((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,\s+\d{1,2}\s+\w+\s+onwards,\s*Multiple\s+Dates)',
            # "Daily, Multiple slots"
            r'^(Daily,\s*Multiple\s+slots)',
        ]

        for pattern in date_patterns:
            m = re.match(pattern, text, re.I)
            if m:
                date_str = m.group(1).strip()
                text = text[m.end():].strip()
                break

        if not date_str:
            # Fallback: find AM/PM boundary
            am_pm_match = re.search(r'(AM|PM)', text)
            if am_pm_match:
                date_str = text[:am_pm_match.end()].strip()
                text = text[am_pm_match.end():].strip()

        if not date_str:
            return None

        # Step 4: Separate event name from venue
        # Known city names that appear at end of venue text
        known_cities = [
            'Delhi/NCR', 'New Delhi', 'Delhi', 'Mumbai', 'Bengaluru', 'Bangalore',
            'Hyderabad', 'Secunderabad', 'Chennai', 'Pune', 'Kolkata',
            'Gurgaon', 'Gurugram', 'Noida', 'Greater Noida', 'Ahmedabad',
            'Goa', 'Jaipur', 'Kochi', 'Lucknow', 'Chandigarh', 'Indore',
        ]

        event_city = ''
        venue = ''
        event_name = text

        # Try to find city at end of text (sorted longest first to match "Delhi/NCR" before "Delhi")
        for c in sorted(known_cities, key=len, reverse=True):
            pattern = re.compile(r',\s*' + re.escape(c) + r'\s*$', re.I)
            m = pattern.search(text)
            if m:
                event_city = c
                before_city = text[:m.start()].strip()

                # Now before_city = event_name + venue_name
                # Find where venue starts using known venue keywords
                venue_keywords = [
                    'Stadium', 'Ground', 'Arena', 'Park', 'Garden', 'Gardens',
                    'Hall', 'Theatre', 'Theater', 'Club', 'Cafe', 'Café',
                    'Center', 'Centre', 'Hotel', 'Resort', 'Studio',
                    'Auditorium', 'Convention', 'Maidan', 'Bhavan', 'Mandapam',
                    'Sector', 'Gate No', 'JLN', 'HICC', 'HITEX', 'JNTU',
                    'The ', 'Shri ', 'St.', 'Jawaharlal', 'Bharat',
                    'Yashobhoomi', 'Nesco', 'NSCI', 'Dome', 'Palace',
                ]

                # Find where venue name likely starts by searching right-to-left for keywords
                venue_start = len(before_city)
                for kw in venue_keywords:
                    # Search for keyword in the text, taking the earliest possible venue start
                    idx = before_city.find(kw)
                    if idx > 0 and idx < venue_start:
                        # Walk backward to find the actual start of the venue name
                        # (usually starts with an uppercase letter)
                        candidate_start = idx
                        for j in range(idx - 1, -1, -1):
                            if before_city[j].isupper() and (j == 0 or not before_city[j-1].isalpha()):
                                candidate_start = j
                                break
                        if candidate_start < venue_start:
                            venue_start = candidate_start

                if venue_start < len(before_city) and venue_start > 2:
                    event_name = before_city[:venue_start].strip()
                    venue = before_city[venue_start:].strip() + ", " + event_city
                else:
                    # Can't separate — use full text as name, city as venue
                    event_name = before_city
                    venue = event_city
                break

        if not event_city:
            # No city detected — might be online or unknown city
            event_name = text
            venue = ''

        # Clean up event name
        event_name = event_name.strip().rstrip(',').rstrip('|').strip()
        
        # Remove common generic prefixes if they leaked into name
        event_name = re.sub(r'(?i)^(onwards|buy tickets|book now|tickets|at)\s+', '', event_name).strip()

        if not event_name or len(event_name) < 3 or event_name.lower() in ('onwards', 'tickets', 'district'):
            return None

        return {
            'name': event_name,
            'date': date_str,
            'venue': venue or event_city or 'N/A',
            'city': event_city,
            'price': price,
        }

    # ─────────────────────────────────────────────────────────
    # __NEXT_DATA__ parser for structured event JSON
    # ─────────────────────────────────────────────────────────
    def _parse_next_data_events(self, next_data: dict, city_terms: list, city: str) -> List[Dict]:
        """Extract structured events from __NEXT_DATA__ and filter by city."""
        events = []

        def _recurse(obj, depth=0):
            if depth > 10 or len(events) > 300:
                return
            if isinstance(obj, dict):
                has_name = obj.get('eventName') or obj.get('name') or obj.get('title')
                has_url = obj.get('eventUrl') or obj.get('url') or obj.get('slug') or obj.get('link')

                if has_name and has_url:
                    name = str(has_name).strip()
                    url_part = str(has_url).strip()

                    if url_part.startswith('http'):
                        full_url = url_part
                    elif url_part.startswith('/'):
                        full_url = f"https://www.district.in{url_part}"
                    else:
                        full_url = f"https://www.district.in/events/{url_part}"

                    # Skip artist pages
                    if '/artist' in full_url.lower():
                        return

                    # Venue/city info
                    venue_name = ''
                    event_city = ''
                    venue_obj = obj.get('venue') or obj.get('location') or obj.get('venueName') or {}
                    if isinstance(venue_obj, dict):
                        venue_name = venue_obj.get('name', '')
                        event_city = venue_obj.get('city', '') or venue_obj.get('cityName', '')
                    elif isinstance(venue_obj, str):
                        venue_name = venue_obj
                    if not event_city:
                        event_city = str(obj.get('city') or obj.get('cityName') or '').strip()

                    # City filter
                    all_text = f"{name} {venue_name} {event_city}".lower()
                    if not any(t in all_text for t in city_terms):
                        return

                    price = obj.get('price') or obj.get('startingPrice') or obj.get('minPrice') or 'N/A'
                    date_val = obj.get('date') or obj.get('startDate') or obj.get('eventDate') or ''
                    organizer = obj.get('organizer') or obj.get('organiserName') or ''
                    if isinstance(organizer, dict):
                        organizer = organizer.get('name', '')

                    events.append({
                        'name': name,
                        'url': full_url,
                        'event_link': full_url,
                        'location': city,
                        'platform': 'District',
                        'price': str(price) if price else 'N/A',
                        'date': str(date_val) if date_val else 'TBD',
                        'venue': venue_name or event_city or city,
                        'organizer': str(organizer).strip() if organizer else 'District',
                        'source': 'district',
                        'is_enriched': True,
                    })

                for v in obj.values():
                    _recurse(v, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    _recurse(item, depth + 1)

        try:
            _recurse(next_data)
        except Exception:
            pass
        return events

    # ─────────────────────────────────────────────────────────
    # PIPELINE ENTRY POINT
    # ─────────────────────────────────────────────────────────
    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        """
        Multi-level District scraping pipeline:
        L1: Main /events/, /activities/, /play/ pages → card-level extraction with city filter
        L2: Multiple Google searches for additional events/activities
        L3: Organizer enrichment from detail pages
        """
        try:
            city = parse_city(location)
            city_terms = self._get_city_terms(city)
            logger.info(f"District PIPELINE: Starting for '{city}', target: {target_count}")
            print(f"[*] District PIPELINE: {city} ({target_count} events)")

            all_events = []
            seen_urls = set()
            seen_names = set()

            def _add_event(ev):
                url = ev.get('url', '')
                name = ev.get('name', '')
                if url not in seen_urls and name.lower() not in seen_names:
                    seen_urls.add(url)
                    seen_names.add(name.lower())
                    all_events.append(ev)

            # ─── LEVEL 1: Scrape Event Categories ───
            categories = [
                "https://www.district.in/events/",
                "https://www.district.in/activities/",
                "https://www.district.in/play/"
            ]
            
            for cat_url in categories:
                if len(all_events) >= target_count:
                    break
                logger.info(f"District L1: Scraping {cat_url}")
                l1_events = self._l1_main_page_scrape(page, cat_url, city, city_terms, target_count)
                for ev in l1_events:
                    _add_event(ev)
                logger.info(f"District L1: ✓ {len(all_events)} items after {cat_url}")

            if len(all_events) >= target_count:
                all_events = self._l3_enrich_organizers(page, all_events[:target_count], city, city_terms)
                return all_events

            # ─── LEVEL 2: Multi-query Google search ───
            needed = target_count - len(all_events)
            logger.info(f"District L2: Google multi-search for {needed} more events")
            l2_events = self._l2_google_multi_search(page, city, city_terms, needed)
            for ev in l2_events:
                _add_event(ev)
            logger.info(f"District L2: ✓ {len(all_events)} items after L2")

            # ─── LEVEL 3: Organizer enrichment & Validation ───
            all_events = self._l3_enrich_organizers(page, all_events[:target_count], city, city_terms)

            logger.info(f"District PIPELINE: ✓ Total {len(all_events)} valid items for '{city}'")
            return all_events[:target_count]

        except Exception as pipeline_err:
            logger.error(f"District PIPELINE error: {pipeline_err}")
            return []

    # ─────────────────────────────────────────────────────────
    # L1: Main page card-level extraction
    # ─────────────────────────────────────────────────────────
    def _l1_main_page_scrape(self, page, url: str, city: str, city_terms: list, target_count: int) -> List[Dict]:
        """
        Level 1: Navigate to main category page, scroll aggressively, extract, filter.
        """
        events = []
        try:
            # Use domcontentloaded for speed rather than waiting for entire network idle
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(800)

            # Faster, jumpier scrolling to trigger lazy loads without waiting as long
            for i in range(10):
                page.evaluate("window.scrollBy(0, 2500)")
                page.wait_for_timeout(300)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(150)

            # ── Method 1: Try __NEXT_DATA__ for structured JSON ──
            next_data = self._extract_window_object(page, "__NEXT_DATA__")
            if next_data:
                nd_events = self._parse_next_data_events(next_data, city_terms, city)
                if nd_events:
                    logger.info(f"District L1: Found {len(nd_events)} events from __NEXT_DATA__ in {url}")
                    events.extend(nd_events)

            # ── Method 2: DOM card extraction ──
            link_elements = page.query_selector_all('a[href*="buy-tickets"], a[href*="/events/"], a[href*="/activities/"]')
            
            for link_el in link_elements:
                if len(events) >= target_count * 3:
                    break
                try:
                    href = link_el.get_attribute('href') or ""
                    if not href or '/artist' in href.lower() or '/search' in href or '/policies' in href:
                        continue
                    if href.rstrip('/') in ['/events', '/activities', '/play', '/movies']:
                        continue

                    full_url = href if href.startswith('http') else f"https://www.district.in{href}"
                    full_url = full_url.split("?")[0].split("#")[0]

                    if full_url in {e.get('url') for e in events}:
                        continue

                    card_text = link_el.inner_text().strip()
                    if not card_text or len(card_text) < 10:
                        continue

                    # City filter
                    if not self._city_matches(card_text, city_terms):
                        continue

                    parsed = self._parse_district_card(card_text)
                    if parsed:
                        events.append({
                            'name': parsed['name'],
                            'url': full_url,
                            'event_link': full_url,
                            'location': city,
                            'platform': 'District',
                            'price': parsed.get('price', 'N/A'),
                            'date': parsed.get('date', 'TBD'),
                            'venue': parsed.get('venue', city),
                            'source': 'district',
                            'is_enriched': True,
                        })
                except Exception:
                    continue

            return events

        except Exception as l1_err:
            logger.error(f"District L1 error: {l1_err}")
            return events

    # ─────────────────────────────────────────────────────────
    # L2: Multi-query Google search for higher yield
    # ─────────────────────────────────────────────────────────
    def _l2_google_multi_search(self, page, city: str, city_terms: list, needed_count: int) -> List[Dict]:
        """
        Level 2: Multiple Google searches with varied keywords.
        Does NOT assume location; forces validation in L3.
        """
        events = []
        if needed_count <= 0:
            return events

        search_queries = [
            f"site:district.in {city} activities",
            f"site:district.in {city} comedy show OR live event",
            f"site:district.in {city} sports OR play OR workshop",
            f"site:district.in {city} events tickets",
        ]

        seen_urls = set()

        for query in search_queries:
            if len(events) >= needed_count * 3: # Gather extra since L3 will filter
                break

            try:
                google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=20"
                page.goto(google_url, wait_until="domcontentloaded", timeout=10000)
                page.wait_for_timeout(200)

                for _ in range(2):
                    page.evaluate("window.scrollBy(0, 800)")
                    page.wait_for_timeout(100)

                result_links = page.query_selector_all('a[href*="district.in"]')

                for link in result_links:
                    try:
                        href = link.get_attribute('href') or ""

                        if 'district.in' not in href or 'google' in href.lower() or '/artist' in href.lower():
                            continue
                        if not any(x in href for x in ['/events/', '/activities/', '/play/', 'buy-tickets']):
                            continue
                        if href.rstrip('/') in ['/events', '/activities', '/play']:
                            continue

                        full_url = href.split("&usg=")[0] if "&usg=" in href else href
                        full_url = full_url.split("?")[0].split("#")[0]

                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)

                        link_text = link.inner_text().strip()
                        if not link_text or len(link_text) < 5:
                            continue

                        # Clean name
                        event_name = link_text.split(' - District')[0].split(' | District')[0].strip()
                        event_name = re.sub(r'(?i)\s*buy\s+tickets?\s*', '', event_name).strip()
                        # Fix parsing for "Book tickets to..."
                        event_name = re.sub(r'(?i)^(?:book\s+tickets?(?:\s+to)?|buy\s+tickets?(?:\s+for)?)\s+', '', event_name).strip()
                        event_name = event_name.rstrip(' |').rstrip(' -').strip()

                        if not event_name or len(event_name) < 3:
                            continue

                        events.append({
                            'name': event_name,
                            'url': full_url,
                            'event_link': full_url,
                            'location': 'N/A', # Strict: Will be dropped if not verified in L3
                            'platform': 'District',
                            'price': 'N/A',
                            'date': 'TBD',
                            'venue': 'N/A', 
                            'source': 'google-district',
                            'is_enriched': False
                        })

                    except Exception:
                        continue

            except Exception as search_err:
                logger.debug(f"District L2: Search error for '{query}': {search_err}")
                continue

        logger.info(f"District L2: Found {len(events)} candidate URLs via Google")
        return events

    # ─────────────────────────────────────────────────────────
    # District Helper Methods
    # ─────────────────────────────────────────────────────────
    def _extract_district_organizer(self, page, next_data=None) -> str:
        """Extract organizer from District event detail page."""
        org = "District"
        try:
            # Method 1: __NEXT_DATA__
            if not next_data:
                next_data = self._extract_window_object(page, "__NEXT_DATA__")
            
            if next_data:
                def find_organizer(obj, depth=0):
                    if depth > 10: return None
                    if isinstance(obj, dict):
                        # Prioritize artist/host over corporate 'organizer' names
                        for key in ['artistName', 'artist', 'host', 'promoter', 'organiserName', 'organizer']:
                            val = obj.get(key)
                            if val:
                                if isinstance(val, dict):
                                    name = val.get('name') or val.get('title')
                                    if name and len(str(name).strip()) > 2:
                                        return str(name).strip()
                                elif isinstance(val, str) and len(val.strip()) > 2:
                                    return val.strip()
                                elif isinstance(val, list) and val:
                                    for item in val:
                                        if isinstance(item, dict):
                                            name = item.get('name') or item.get('title')
                                            if name: return str(name).strip()
                                        elif isinstance(item, str) and len(item.strip()) > 2:
                                            return item.strip()
                        for v in obj.values():
                            r = find_organizer(v, depth + 1)
                            if r: return r
                    elif isinstance(obj, list):
                        for it in obj:
                            r = find_organizer(it, depth + 1)
                            if r: return r
                    return None

                found = find_organizer(next_data)
                if found: org = found

            # Method 2: JSON-LD
            if org == "District":
                for ld in self._extract_json_ld(page):
                    if 'event' in str(ld.get('@type', '')).lower():
                        o = ld.get('organizer') or {}
                        if isinstance(o, dict):
                            name = o.get('name')
                            if name and len(str(name).strip()) > 2:
                                org = str(name).strip()
                                break
                        elif isinstance(o, str) and len(o.strip()) > 2:
                            org = o.strip()
                            break

            # Method 3: DOM
            if org == "District":
                body = page.inner_text("body")
                m = re.search(r'(?:Organized by|Organizer|Organiser|Presented by|Hosted by|By)\s*[:\-]?\s*([^\n]{3,60})', body, re.I)
                if m:
                    extracted = re.sub(r'[<>]', '', m.group(1)).strip()
                    if extracted: org = extracted

        except Exception: pass

        # Cleanup spam/corporate suffixes
        if org and org != "District":
            cleaned = re.sub(r'(?i)\s+(?:LLP|Pvt\.?\s*Ltd\.?|Private\s+Limited|Ltd|Inc|Limited)(?:\s*\(.*?\))?$', '', org).strip()
            if cleaned and len(cleaned) > 2: org = cleaned
        
        return org

    def _extract_district_description(self, page, next_data) -> str:
        """Extract event description from District detail page."""
        try:
            # 1. Try __NEXT_DATA__
            if next_data:
                def find_desc(obj, depth=0):
                    if depth > 10: return None
                    if isinstance(obj, dict):
                        for k in ['description', 'about', 'synopsis', 'content', 'eventDescription']:
                            val = obj.get(k)
                            if val and isinstance(val, str) and len(val.strip()) > 15:
                                return val.strip()
                        for v in obj.values():
                            res = find_desc(v, depth + 1)
                            if res: return res
                    elif isinstance(obj, list):
                        for it in obj:
                            res = find_desc(it, depth + 1)
                            if res: return res
                    return None
                
                desc = find_desc(next_data)
                if desc: return re.sub(r'<[^>]*>', '', desc).strip()

            # 2. Try JSON-LD
            for ld in self._extract_json_ld(page):
                if 'event' in str(ld.get('@type', '')).lower():
                    desc = ld.get('description')
                    if desc and len(desc.strip()) > 10:
                        return re.sub(r'<[^>]*>', '', desc).strip()

            # 3. Try DOM
            selectors = [
                "meta[name='description']", "meta[property='og:description']",
                "[class*='description']", "[class*='about']", "section p", 
                ".event-details", "#event-description"
            ]
            for sel in selectors:
                el = page.query_selector(sel)
                if el:
                    val = el.get_attribute("content") if sel.startswith("meta") else el.inner_text()
                    if val and len(val.strip()) > 20:
                        return val.strip()
        except Exception: pass
        return "N/A"

    def _extract_district_duration(self, page, next_data) -> str:
        """Extract event duration from District detail page."""
        try:
            if next_data:
                def find_duration(obj, depth=0):
                    if depth > 10: return None
                    if isinstance(obj, dict):
                        for k in ['duration', 'eventDuration', 'timeDuration']:
                            val = obj.get(k)
                            if val and isinstance(val, (str, int)) and len(str(val).strip()) > 1:
                                return str(val).strip()
                        for v in obj.values():
                            res = find_duration(v, depth + 1)
                            if res: return res
                    elif isinstance(obj, list):
                        for item in obj:
                            res = find_duration(item, depth + 1)
                            if res: return res
                    return None
                dur = find_duration(next_data)
                if dur: return dur

            # DOM search
            body = page.inner_text("body")
            match = re.search(r'(?:Duration|Time):\s*([^\n|]{3,40})', body, re.I)
            if match:
                return match.group(1).strip()
        except Exception: pass
        return "N/A"

    def _extract_district_name(self, page, next_data) -> str:
        """Extract full event name from District detail page."""
        try:
            # 1. Try __NEXT_DATA__
            if next_data:
                def find_name(obj, depth=0):
                    if depth > 10: return None
                    if isinstance(obj, dict):
                        # District specifically uses 'name' or 'eventName' in props
                        for k in ['eventName', 'name', 'title', 'eventTitle']:
                            val = obj.get(k)
                            if val and isinstance(val, str) and len(val.strip()) > 3:
                                # Avoid generic strings
                                if val.lower() not in ['district', 'event', 'tickets', 'buy tickets', 'home', 'onwards', 'book now']:
                                    return val.strip()
                        for v in obj.values():
                            res = find_name(v, depth + 1)
                            if res: return res
                    elif isinstance(obj, list):
                        for it in obj:
                            res = find_name(it, depth + 1)
                            if res: return res
                    return None
                
                name = find_name(next_data)
                if name: return name

            # 2. Try JSON-LD
            for ld in self._extract_json_ld(page):
                if 'event' in str(ld.get('@type', '')).lower():
                    name = ld.get('name')
                    if name and len(name.strip()) > 3:
                        return name.strip()

            # 3. Try DOM H1
            h1 = page.query_selector("h1")
            if h1:
                name = h1.inner_text().strip()
                if name and len(name) > 3:
                    # Clean "Book tickets to..."
                    name = re.sub(r'(?i)^(?:book\s+tickets?(?:\s+to)?|buy\s+tickets?(?:\s+for)?)\s+', '', name).strip()
                    return name
        except Exception: pass
        return ""

    # ─────────────────────────────────────────────────────────
    # L3: Organizer enrichment & STRICT City Validation
    # ─────────────────────────────────────────────────────────
    def _l3_enrich_organizers(self, page, events: List[Dict], city: str, city_terms: list) -> List[Dict]:
        """
        Visit each event detail page to extract correct organizer,
        description, duration and FILL AND VALIDATE the location. 
        Drop events that don't match the city!
        """
        valid_events = []
        
        for i, ev in enumerate(events):
            url = ev.get('url', '')
            if not url or 'google' in url:
                continue

            try:
                if page.is_closed() or not page.context or not page.context.browser or not page.context.browser.is_connected():
                    logger.warning("District L3: Browser closed, stopping enrichment")
                    break

                # Speed optimization: significantly reduce wait times for enrichment
                # NEXT_DATA is usually available very quickly.
                page.goto(url, wait_until="domcontentloaded", timeout=6000)
                page.wait_for_timeout(50)
                
                # Fetch NEXT_DATA once for all enrichment helpers
                next_data = self._extract_window_object(page, "__NEXT_DATA__")
                
                # 0. Correct Event Name (Google sometimes gives truncated names)
                full_name = self._extract_district_name(page, next_data)
                if full_name and len(full_name.strip()) > 3:
                    # Clean it one more time to be safe
                    full_name = re.sub(r'(?i)\s*(?:\|| -)\s*District\s*$', '', full_name).strip()
                    # Final clean for "onwards" leaks
                    full_name = re.sub(r'(?i)^(onwards|buy tickets|book now)\b\s*', '', full_name).strip()
                    
                    # Update name
                    ev['name'] = full_name

                # 1. Organizer
                if ev.get('organizer') in ('District', 'N/A', 'Unknown', '', None):
                    ev['organizer'] = self._extract_district_organizer(page)

                # 2. Description
                if not ev.get('about_event') or ev.get('about_event') == 'N/A':
                    ev['about_event'] = self._extract_district_description(page, next_data)

                # 3. Duration
                if not ev.get('duration') or ev.get('duration') == 'N/A':
                    ev['duration'] = self._extract_district_duration(page, next_data)

                # 4. Strict City Extraction & Validation
                page_city = ""
                # Use page.content() for faster access than inner_text("body")
                page_html_lower = page.content().lower()
                page_text_lower = page_html_lower # Alias for existing code compatibility
                
                # Check JSON-LD for venue/city
                for ld in self._extract_json_ld(page):
                    loc = ld.get('location') or {}
                    if isinstance(loc, dict):
                        addr = loc.get('address') or {}
                        if isinstance(addr, dict):
                            page_city = addr.get('addressLocality', '') or addr.get('addressRegion', '')
                        elif isinstance(addr, str):
                            page_city = addr
                        if not page_city:
                            page_city = loc.get('name', '')
                
                # If page_city is still unknown and the text contains our city, assume it's valid
                matched_city = False
                if page_city and self._city_matches(page_city, city_terms):
                    matched_city = True
                elif any(t in page_text_lower for t in city_terms):
                    matched_city = True
                
                # Special check for specific areas in Hyderabad
                if not matched_city and 'hyderabad' in city.lower():
                    if any(area in page_text_lower for area in ['gachibowli', 'boulder hills', 'hitech city', 'madhapur']):
                        matched_city = True
                    
                if not matched_city:
                    logger.debug(f"District L3: REJECTED - City mismatch. URL: {url[:50]}")
                    continue

                # 5. Fill missing fields (Price, Date, Venue)
                if ev.get('price', 'N/A') in ('N/A', 'TBD', '', 'Coming soon'):
                    try:
                        # Try NEXT_DATA for price
                        if next_data:
                            def find_price(obj, depth=0):
                                if depth > 10: return None
                                if isinstance(obj, dict):
                                    for k in ['price', 'startingPrice', 'minPrice', 'amount']:
                                        val = obj.get(k)
                                        if val and (isinstance(val, (int, float)) or (isinstance(val, str) and val.isdigit())):
                                            return str(val)
                                    for v in obj.values():
                                        res = find_price(v, depth + 1)
                                        if res: return res
                                return None
                            p = find_price(next_data)
                            if p: ev['price'] = p
                        
                        if ev.get('price', 'N/A') == 'N/A':
                            price_m = re.search(r'₹\s*([\d,]+)', page.content())
                            if price_m:
                                ev['price'] = price_m.group(1).replace(',', '')
                    except: pass

                if ev.get('date', 'TBD') in ('TBD', '', 'N/A'):
                    try:
                        for ld in self._extract_json_ld(page):
                            d = ld.get('startDate') or ld.get('startDateTime')
                            if d:
                                ev['date'] = str(d)
                                break
                    except: pass

                # 6. Improved Venue Extraction
                if ev.get('venue', 'N/A') in ('N/A', '', city):
                    v_extracted = False
                    # Try JSON-LD first
                    for ld in self._extract_json_ld(page):
                        loc = ld.get('location') or {}
                        if isinstance(loc, dict):
                            v_name = loc.get('name', '')
                            addr = loc.get('address')
                            full_addr = ""
                            if isinstance(addr, dict):
                                full_addr = addr.get('streetAddress') or addr.get('name') or ""
                            elif isinstance(addr, str):
                                full_addr = addr
                            
                            if v_name:
                                ev['venue'] = f"{v_name}, {full_addr}" if full_addr and full_addr.lower() not in v_name.lower() else v_name
                                if city.lower() not in ev['venue'].lower():
                                    ev['venue'] += f", {city}"
                                v_extracted = True
                                break
                    
                    if not v_extracted and next_data:
                        # Try NEXT_DATA for venue
                        def find_venue(obj, depth=0):
                            if depth > 10: return None
                            if isinstance(obj, dict):
                                if 'venueName' in obj or 'venue' in obj:
                                    v = obj.get('venueName') or obj.get('venue')
                                    if isinstance(v, str) and len(v) > 2: return v
                                    if isinstance(v, dict): return v.get('name') or v.get('address')
                                for v in obj.values():
                                    res = find_venue(v, depth + 1)
                                    if res: return res
                            return None
                        vn = find_venue(next_data)
                        if vn:
                            ev['venue'] = f"{vn}, {city}"
                            v_extracted = True

                # Fix venue to ensure it passes BaseAgent Validation
                if not ev.get('venue') or ev.get('venue') == 'N/A':
                    ev['venue'] = f"Event Location in {city}"
                    
                ev['location'] = city
                ev['is_enriched'] = True
                
                valid_events.append(ev)
                logger.debug(f"District L3: Enriched & Validated [{len(valid_events)}] {ev.get('name', '?')[:40]}")

            except Exception as e:
                logger.debug(f"District L3: Enrichment failed for {url[:50]}: {e}")
                pass

        return valid_events


# ══════════════════════════════════════════════════════════════
# MERA EVENTS — API-based scraping with deep pagination (FIXED)
# ══════════════════════════════════════════════════════════════
class MeraEventsAgent(BaseAgent):
    def __init__(self):
        super().__init__("Mera Events", "https://www.meraevents.com")

    def _perform_scraping_sync(self, page, location: str, target_count: int, max_price: Optional[int]) -> List[Dict]:
        try:
            # Handle city slug logic
            city_slug = location.lower().replace(" ", "-")
            # Special cases for MeraEvents city URLs
            city_map = {
                "bangalore": "bengaluru",
                "delhi": "delhi-ncr",
                "gurgaon": "delhi-ncr",
                "noida": "delhi-ncr",
                "chennai": "chennai",
                "mumbai": "mumbai",
                "pune": "pune",
                "ahmedabad": "ahmedabad",
                "jaipur": "jaipur",
                "kolkata": "kolkata",
                "goa": "goa",
                "hyderabad": "hyderabad"
            }
            city_slug = city_map.get(city_slug, city_slug)
            
            # If the city_slug is not in the map, we just use the slugified version
            # which is already calculated as location.lower().replace(" ", "-")
            
            url = f"https://www.meraevents.com/{city_slug}-events"
            logger.info(f"MeraEvents: Navigating to {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for event cards
            try:
                page.wait_for_selector("a[href*='/event/']", timeout=15000)
            except:
                logger.debug("MeraEvents: No event links found initially.")
                return []

            # "More Events" button selector
            more_button_selector = "a:has-text('More Events'), a:has-text('View more events'), a:has-text('View more'), a[href*='#viewMore'], a[href*='#popularEvents'], a.viewMoreBtn, #viewMore"
            
            candidates = []
            seen_urls = set()
            
            # Use Target Count or 50 as default
            target_count = target_count or 50

            # Initial extraction
            def extract_from_page():
                new_found = 0
                # Try to find the event container cards
                cards = page.query_selector_all("a[href*='/event/']")
                for card in cards:
                    try:
                        href = card.get_attribute("href") or ""
                        if not href or "/event/" not in href or any(x in href for x in ["/search", "/category", "/explore", "/dashboard"]): 
                            continue
                        
                        full_url = f"https://www.meraevents.com{href}" if href.startswith("/") else href
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            
                            # Get full inner text for detailed parsing
                            full_text = card.inner_text().replace("\n", " ").strip()
                            # Clean up multiple spaces
                            full_text = re.sub(r'\s+', ' ', full_text)
                            
                            # Try to parse name, date, venue from full_text
                            # Sample: "-Healthcare Summit 2026 Friday, 12th Jun 2026 - Saturday, 13th Jun 2026 | 09:00 AM to 06:00 AM IST Sevalal Banjara Bhavan..."
                            
                            # Initial name is just the first line or before the date
                            name = full_text.split("   ")[0].strip() # Often there's a big gap
                            if name.startswith("-"): name = name[1:].strip()
                            
                            # Fallback parsing
                            date_str = ""
                            venue_str = ""
                            format_str = "Offline"
                            
                            # Look for "Online" or "Virtual"
                            if any(x in full_text.lower() for x in ["online", "virtual", "zoom", "webinar"]):
                                format_str = "Online"
                                venue_str = "Online Event"
                            
                            # Try to extract date (e.g., "May 17, 2026" or "Friday, 12th Jun...")
                            date_match = re.search(r'([A-Za-z]+,?\s+\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})', full_text)
                            if not date_match:
                                # Try simpler format like "May 17, 2026"
                                date_match = re.search(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})', full_text)
                            
                            if date_match:
                                date_str = date_match.group(1)
                                # The name is usually before the date
                                if not name or len(name) < 5:
                                    potential_name = full_text[:date_match.start()].strip()
                                    if potential_name.startswith("-"): potential_name = potential_name[1:].strip()
                                    if potential_name: name = potential_name

                            # Venue is often after the date/time
                            # Search for city in the end of string
                            city_match = re.search(rf'([A-Za-z\s,]+{location}[A-Za-z\s,]*)', full_text, re.I)
                            if city_match:
                                venue_str = city_match.group(1).strip()
                            
                            candidates.append({
                                "url": full_url, 
                                "name": name or "MeraEvents Event",
                                "location": location,
                                "platform": self.platform_name,
                                "raw_card_text": full_text,
                                "parsed_date": date_str,
                                "parsed_venue": venue_str,
                                "event_format": format_str
                            })
                            new_found += 1
                    except:
                        continue
                return new_found

            extract_from_page()
            
            # Load more loop
            max_clicks = 15 # Reduced from 40 to avoid hanging on empty lists
            click_count = 0
            while len(candidates) < target_count and click_count < max_clicks:
                # Early exit if we have a healthy amount of events (60+) to avoid long enrichment hangs
                if len(candidates) >= 60:
                    logger.info(f"MeraEvents: Reached 60+ events, proceeding to enrichment.")
                    break
                    
                # Re-query the button as it might have changed
                more_btn = page.query_selector(more_button_selector)
                if more_btn and more_btn.is_visible():
                    logger.info(f"MeraEvents: Clicking pagination button (Current: {len(candidates)}, Target: {target_count})")
                    try:
                        # Scroll to button and click via JS to avoid being blocked
                        more_btn.scroll_into_view_if_needed()
                        page.evaluate("el => el.click()", more_btn)
                        
                        # Wait for load - use a dynamic wait if possible
                        time.sleep(3.5) 
                        click_count += 1
                        
                        # Scroll a bit more to trigger any lazy loads
                        page.evaluate("window.scrollBy(0, 500)")
                        time.sleep(0.5)
                        
                        new_found = extract_from_page()
                        if new_found == 0:
                            # Try one more deep scroll and wait
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(1.5)
                            new_found = extract_from_page()
                            if new_found == 0:
                                break
                    except Exception:
                        break
                else:
                    # Avoid infinite scrolling if button is not present
                    break
            
            logger.info(f"MeraEvents: Found {len(candidates)} candidates for {location}")
            return candidates[:target_count]
            
        except Exception as exc:
            logger.error(f"MeraEvents L1 error: {exc}")
            # If context was destroyed but we have candidates, return what we found!
            if 'candidates' in locals() and candidates:
                return candidates[:target_count]
            return []

    def _enrich_event_details(self, page, raw_event: dict) -> dict:
        url = raw_event.get("url")
        if not url: return raw_event
        
        try:
            # Use a shorter timeout and faster wait for enrichment
            resp = page.goto(url, wait_until="domcontentloaded", timeout=20000)
            if not resp or resp.status >= 400:
                return raw_event
            time.sleep(0.5) # Reduced from 1.5s
            
            # 1. JSON-LD extraction
            ld_items = self._extract_json_ld(page)
            ld_event = next((it for it in ld_items if "event" in str(it.get("@type", "")).lower()), {})
            
            # 2. Extract Event ID
            body_text = page.inner_text("body") or ""
            id_match = re.search(r"Event ID\s*[:\-]?\s*(\d+)", body_text, re.I)
            raw_event["event_id"] = id_match.group(1) if id_match else "N/A"
            if raw_event["event_id"] == "N/A" and url:
                # Fallback: some URLs might have ID at the end like /event/name-12345
                url_id_match = re.search(r"-(\d{4,8})$", url)
                if url_id_match:
                    raw_event["event_id"] = url_id_match.group(1)
            
            # 3. Basic Metadata
            raw_event["name"] = ld_event.get("name") or self._self_healing_extract(page, "title") or raw_event.get("name")
            raw_event["date"] = ld_event.get("startDate") or ld_event.get("startDateTime") or ""
            raw_event["about_event"] = ld_event.get("description") or ""
            
            # 4. Organizer & Artist
            # Try to find organizer from specific section if possible
            org_el = page.query_selector(".organizerName, [class*='organizer-name']")
            if org_el:
                raw_event["organizer"] = org_el.inner_text().strip()
            else:
                org_match = re.search(r"(?:Organized by|Hosted by|Organizer\s*[:\-])\s*([^\n]{3,80})", body_text, re.I)
                org_name = org_match.group(1).strip() if org_match else ""
                if org_name and len(org_name) < 50 and org_name.lower() != "features":
                    raw_event["organizer"] = org_name
                else:
                    # Look at JSON-LD or fallback
                    org_ld = ld_event.get("organizer", {})
                    if isinstance(org_ld, dict):
                        raw_event["organizer"] = org_ld.get("name") or "MeraEvents"
                    else:
                        raw_event["organizer"] = "MeraEvents"
            
            # 6. Venue, Address & Format (Online/Offline)
            raw_event["event_format"] = raw_event.get("event_format") or "Offline"
            raw_event["venue"] = raw_event.get("parsed_venue") or "N/A"
            raw_event["venue_address"] = "N/A"
            
            loc_data = ld_event.get("location")
            if isinstance(loc_data, dict):
                ld_venue = loc_data.get("name") or "N/A"
                if ld_venue != "N/A":
                    raw_event["venue"] = ld_venue
                addr = loc_data.get("address")
                if isinstance(addr, dict):
                    raw_event["venue_address"] = addr.get("streetAddress") or addr.get("name") or "N/A"
            
            if not raw_event.get("venue") or raw_event["venue"] == "N/A":
                v_match = re.search(r"(?:Venue|Location|At)\s*[:\-]?\s*([^\n]{3,100})", body_text, re.I)
                raw_event["venue"] = v_match.group(1).strip() if v_match else raw_event.get("location", "N/A")

            # Detect Virtual/Online events (Check both card and page)
            venue_str = str(raw_event.get("venue", "")).lower() + " " + str(raw_event.get("venue_address", "")).lower()
            if any(x in venue_str for x in ["online", "virtual", "zoom", "webinar", "webcast"]) or \
               "virtual" in body_text.lower()[:500] or \
               raw_event.get("event_format") == "Online":
                raw_event["event_format"] = "Online"
                raw_event["venue"] = "Online Event"
                raw_event["venue_address"] = "Online"

            # Append city to organizer if offline event
            display_city = raw_event.get("location", "").title()
            if raw_event["event_format"] == "Offline" and display_city and raw_event["organizer"] != "MeraEvents" and display_city not in raw_event["organizer"]:
                raw_event["organizer"] = f"{raw_event['organizer']} ({display_city})"
            
            artist_match = re.search(r"(?:Artist|Performer|Featuring|ft\.?)\s*[:\-]?\s*([^\n]{3,100})", body_text, re.I)
            raw_event["artist"] = artist_match.group(1).strip() if artist_match else ""
            
            # 5. Price & Tiers
            price_tiers = []
            try:
                # Look for ticket rows in the DOM
                ticket_els = page.query_selector_all(".ticketRow, [class*='ticket-row'], [class*='ticketRow']")
                for el in ticket_els:
                    txt = el.inner_text().replace("\n", " ").strip()
                    # Try to find name and price
                    p_match = re.search(r"(.*?)(?:INR|Rs\.?|₹)\s*([\d,]+)", txt, re.I)
                    if p_match:
                        t_name = p_match.group(1).strip()
                        t_price = p_match.group(2).replace(",", "")
                        if t_name and t_price:
                            price_tiers.append({"name": t_name, "price": t_price})
            except: pass

            if price_tiers:
                raw_event["price_tiers"] = price_tiers
                raw_event["price"] = price_tiers[0]["price"]
            else:
                # Fallback to JSON-LD or Text search
                offers = ld_event.get("offers")
                if isinstance(offers, dict):
                    raw_event["price"] = str(offers.get("price", ""))
                elif isinstance(offers, list) and offers:
                    raw_event["price"] = str(offers[0].get("price", ""))
            

            # 7. Event Type
            type_match = re.search(r"Category\s*[:\-]\s*([^\n]+)", body_text, re.I)
            raw_event["event_type"] = type_match.group(1).strip() if type_match else "Event"

            
            raw_event["is_enriched"] = True
            
        except Exception as e:
            logger.debug(f"MeraEvents enrichment failed for {url}: {e}")
            raw_event["is_enriched"] = True
            
        return raw_event

    def _format_event(self, raw_event: dict) -> Optional[dict]:
        formatted = super()._format_event(raw_event)
        if formatted:
            # Map extra fields into the formatted dict
            formatted["event_id"] = raw_event.get("event_id", "N/A")
            formatted["price_tiers"] = raw_event.get("price_tiers", [])
            formatted["organizer_name"] = raw_event.get("organizer", "MeraEvents")
            formatted["artist_name"] = raw_event.get("artist", "")
            if "event_type" in raw_event:
                formatted["event_type"] = raw_event["event_type"]
            if "event_format" in raw_event:
                formatted["event_format"] = raw_event["event_format"]
        return formatted


# ══════════════════════════════════════════════════════════════
# SKILLBOX — Direct scraping from skillboxes.com with city selection
# ══════════════════════════════════════════════════════════════
# SkillboxAgent is now imported from .skillbox_agent


# ══════════════════════════════════════════════════════════════════════
# SWIGGY SCENES — Fallback-first extraction for blocked direct page
# ══════════════════════════════════════════════════════════════════════
class SwiggyScenesAgent(BaseAgent):
    def __init__(self):
        super().__init__("Swiggy Scenes", "https://www.swiggy.com/scenes")

    def _bing_search_fallback(
        self, page, location: str, count_needed: int
    ) -> List[Dict]:
        results = []
        try:
            from urllib.parse import quote, urlparse, parse_qs, unquote

            # Use multiple queries for higher yield
            queries = [
                f"\"Swiggy Scenes\" {location} events",
                f"site:swiggy.com/scenes {location}",
                f"inurl:swiggy.com/scenes {location} experiences",
                f"Swiggy Dineout {location} events"
            ]
            
            seen = set()
            for query in queries:
                if len(results) >= count_needed * 4:
                    break
                    
                # Paginate through 3 pages
                for page_num in range(3):
                    first = page_num * 10 + 1
                    search_url = f"https://www.bing.com/search?q={quote(query)}&first={first}"
                    logger.info(f"Swiggy Scenes: Running fallback query: {query} (Page {page_num+1})")
                    try:
                        page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                        time.sleep(4.0) # Increased delay for Bing

                        query_results_count = 0
                        anchors = page.query_selector_all("a[href]")
                        if not anchors:
                            break # No more results

                        for a in anchors:
                            if len(results) >= count_needed * 5:
                                break

                            href = a.get_attribute("href") or ""
                            if not href:
                                continue

                            if "bing.com/ck/a" in href or "bing.com/ck?" in href:
                                qs = parse_qs(urlparse(href).query)
                                if qs.get("u"):
                                    href = unquote(qs["u"][0])

                            # More inclusive check
                            if "swiggy.com" not in href.lower():
                                continue

                            href = href.split("?")[0].split("#")[0]
                            if href in seen or "/scenes/" not in href.lower() or href.endswith("/scenes") or href.endswith("/scenes/"):
                                continue
                            seen.add(href)

                            name = (a.inner_text() or "").strip().split("\n")[0]
                            if not name or len(name) < 3:
                                name = "Swiggy Scenes event"

                            results.append({
                                "name": name,
                                "url": href,
                                "location": location,
                            })
                            query_results_count += 1
                        
                        logger.info(f"Swiggy Scenes: Found {query_results_count} results for query: {query} (Page {page_num+1})")
                        if query_results_count == 0:
                            break # No results on this page, skip pagination
                    except Exception as e:
                        logger.debug(f"Pass failed for query {query} page {page_num+1}: {e}")
                        break
                    
                    time.sleep(1)
                
        except Exception as exc:
            logger.debug(f"Swiggy Scenes Bing fallback failed: {exc}")
        return results

    def _fetch_sitemap_urls(self, location: str) -> List[Dict]:
        """Official Swiggy Scenes Sitemap discovery."""
        import requests
        import gzip
        import io
        import xml.etree.ElementTree as ET
        
        results = []
        city = location.lower().split(",")[0].strip()
        aliases = [city]
        if city == "bangalore": aliases.append("bengaluru")
        if city == "bengaluru": aliases.append("bangalore")
        
        sitemap_url = "https://www.swiggy.com/scenes/sitemap/sitemap-0.xml.gz"
        logger.info(f"Swiggy Scenes: Fetching official sitemap for {location}...")
        
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            r = requests.get(sitemap_url, headers=headers, timeout=15)
            if r.status_code == 200:
                with gzip.open(io.BytesIO(r.content), 'rb') as f:
                    content = f.read()
                
                root = ET.fromstring(content)
                ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                for url_node in root.findall('ns:url', ns):
                    loc_text = url_node.find('ns:loc', ns).text
                    if not loc_text or "/scenes/" not in loc_text.lower():
                        continue
                        
                    # Check if city matches any alias
                    matched_alias = next((a for a in aliases if f"/{a}/" in loc_text.lower()), None)
                    if matched_alias:
                        # URL format is typically: /scenes/{category}/{slug}/{city}/{id}
                        # We can extract the slug by looking at the segment before the city
                        try:
                            parts = loc_text.lower().split(f"/{matched_alias}/")[0].split("/")
                            slug = parts[-1]
                            name = slug.replace("-", " ").title()
                        except Exception:
                            name = "Swiggy Scenes Event"
                            
                        results.append({
                            "name": name,
                            "url": loc_text,
                            "location": location
                        })
                logger.info(f"Swiggy Scenes: Found {len(results)} events in sitemap for {location}")
            else:
                logger.warning(f"Swiggy Scenes: Sitemap fetch failed (HTTP {r.status_code})")
        except Exception as e:
            logger.debug(f"Swiggy Scenes: Sitemap error: {e}")
            
        return results

    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        candidates = []
        
        # Strategy 1: Sitemap (The "Bestest" Solution)
        candidates.extend(self._fetch_sitemap_urls(location))
        
        # Strategy 2: Direct URL construction (Fallback)
        if len(candidates) < target_count:
            city = location.lower().split(",")[0].strip()
            urls = [
                f"https://www.swiggy.com/scenes?city={city}",
                f"https://www.swiggy.com/scenes",
            ]
            
            seen_urls = {c["url"] for c in candidates}
            for url in urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)
                    
                    for a in page.query_selector_all("a[href*='/experiences/']"):
                        href = a.get_attribute("href") or ""
                        if href.startswith("/"): href = f"https://www.swiggy.com{href}"
                        
                        href_clean = href.split("?")[0].split("#")[0]
                        if href_clean and href_clean not in seen_urls:
                            name = (a.inner_text() or "").strip() or "Swiggy Scenes event"
                            candidates.append({
                                "name": name,
                                "url": href_clean,
                                "location": location
                            })
                            seen_urls.add(href_clean)
                except:
                    continue

        if len(candidates) < target_count:
            logger.info(f"Swiggy Scenes: Yield low ({len(candidates)}), relying on BaseAgent Google fallback...")

        return candidates

    def _enrich_event_details(self, page, raw_event: dict) -> dict:
        """
        Custom enrichment for Swiggy Scenes to fix the 'City as Venue' issue.
        Swiggy's JSON-LD often lists the city name (e.g., 'Mumbai') as the location name,
        which is incorrect. We need to extract the actual venue from the page widgets.
        """
        # Call base enrichment first (gets JSON-LD, price, date)
        raw_event = super()._enrich_event_details(page, raw_event)
        
        # Check if venue is just the city or missing
        venue = raw_event.get("venue")
        venue_name = ""
        if isinstance(venue, dict):
            venue_name = venue.get("name", "")
        else:
            venue_name = str(venue or "")
            
        city = str(raw_event.get("location") or "Hyderabad").split(",")[0].strip()
        
        # If venue is just the city name or generic, try to find the real venue name
        if not venue_name or venue_name.lower() == city.lower() or venue_name == "N/A":
            try:
                # ── Robust Wait for dynamic widgets ──
                # Swiggy often loads these via client-side JS after DOMContentLoaded
                try:
                    page.wait_for_selector("div[class*='EventMastheadWidget__InfoContent']", timeout=5000)
                except:
                    pass
                
                # 1. Targeted extraction from Swiggy's 'Location' widget
                # Try finding by class partial match
                venue_el = page.query_selector("div[class*='EventMastheadWidget__InfoTextWrapper'] div")
                
                # Fallback: Find by "Location" text anchor
                if not venue_el:
                    try:
                        # Find the div that says "Location" and get the next section
                        loc_section = page.query_selector("div:has-text('Location') + div")
                        if loc_section:
                            venue_el = loc_section.query_selector("div")
                    except: pass
                
                if venue_el:
                    real_venue = venue_el.inner_text().strip()
                    if real_venue and real_venue.lower() != city.lower():
                        logger.info(f"Swiggy Scenes: Corrected venue '{venue_name}' -> '{real_venue}'")
                        if isinstance(venue, dict):
                            venue["name"] = real_venue
                        else:
                            raw_event["venue"] = real_venue
                        venue_name = real_venue
                
                # 2. Extract Area/Locality
                area_el = page.query_selector("div[class*='EventMastheadWidget__InfoContent'] > div:nth-child(2)")
                if area_el:
                    area = area_el.inner_text().strip()
                    if area:
                        if isinstance(venue, dict):
                            venue["street_address"] = area
                        else:
                            raw_event["venue_address"] = area
                            
                # 3. Final Fallback: Extract from 'Venue & seating' section
                if not raw_event.get("venue") or str(raw_event.get("venue")).lower() == city.lower():
                    # The venue info is often in a div with "Venue & seating" text
                    vs_el = page.query_selector("div:has-text('Venue & seating')")
                    if vs_el:
                        vs_text = vs_el.inner_text()
                        if "•" in vs_text:
                            parts = [p.strip() for p in vs_text.split("•")]
                            # Format: "623.3 km • Venue Name • Area, City"
                            if len(parts) >= 2:
                                candidate = parts[1]
                                if candidate.lower() != city.lower():
                                    if isinstance(venue, dict):
                                        venue["name"] = candidate
                                    else:
                                        raw_event["venue"] = candidate
            except Exception as e:
                logger.debug(f"Swiggy Scenes: Custom venue extraction failed: {e}")
                
        return raw_event


# ══════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════
# SORT MY SCENE — Dynamic city-based events scraper
# ══════════════════════════════════════════════════════════════
class SortMySceneAgent(BaseAgent):
    def __init__(self):
        super().__init__("Sort My Scene", "https://sortmyscene.com")

    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        """
        Scrape events directly from the SortMyScene listing page.
        Uses the events listing URL with dynamic city parameter.
        Extracts data from event cards using dedicated CSS class selectors.
        """
        try:
            candidates = []
            seen_urls = set()

            # ── Dynamic city parameter from user input ──
            # IMPORTANT: City param is CASE-SENSITIVE on SortMyScene — must be Title Case
            # Also, SortMyScene uses "Bengaluru" instead of "Bangalore"
            display_city = location.strip().title()
            url_city = display_city
            if url_city.lower() == "bangalore":
                url_city = "Bengaluru"

            listing_url = f"https://sortmyscene.com/events?tab=events&city={url_city}"

            logger.info(f"Sort My Scene: Loading events for '{display_city}' (URL: {url_city}) -> {listing_url}")
            page.goto(listing_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(10)  # Increased wait for stable React rendering

            # ── Controlled scrolling to load more events ──
            prev_count = 0
            no_new_rounds = 0
            max_scroll_rounds = 15

            for scroll_round in range(max_scroll_rounds):
                if len(candidates) >= target_count:
                    break

                # Count current event cards using multiple possible selectors
                current_count = page.evaluate("""() => {
                    return document.querySelectorAll('[class*="Events_event__"], a[href*="/event/"]').length;
                }""")
                
                logger.debug(f"Sort My Scene: Scroll round {scroll_round + 1}, cards visible: {current_count}")

                if current_count == prev_count:
                    no_new_rounds += 1
                    if no_new_rounds >= 3:
                        logger.info(f"Sort My Scene: No new events after {no_new_rounds} scrolls, stopping")
                        break
                else:
                    no_new_rounds = 0

                prev_count = current_count

                # Scroll down gradually
                page.evaluate("window.scrollBy(0, 800)")
                time.sleep(2)

            # ── Extract data from all visible event cards via robust JS evaluation ──
            extracted_data = page.evaluate("""(city) => {
                const cards = document.querySelectorAll('[class*="Events_event__"], a[href*="/event/"]');
                const results = [];
                const searchTerms = [city.toLowerCase(), "india"];
                
                cards.forEach(card => {
                    const href = card.getAttribute('href') || '';
                    if (!href.includes('/event/')) return;
                    
                    // Direct selectors
                    const nameEl = card.querySelector('[class*="Events_name__"]');
                    const dateEl = card.querySelector('[class*="Events_date__"]');
                    const locEl = card.querySelector('[class*="Events_location__"]');
                    const priceEl = card.querySelector('[class*="Events_price__"]');
                    
                    let name = nameEl ? nameEl.innerText.trim() : "";
                    const dateText = dateEl ? dateEl.innerText.trim() : "";
                    const locText = locEl ? locEl.innerText.trim() : "";
                    const priceText = priceEl ? priceEl.innerText.trim() : "";
                    
                    // Robust Name Fallback
                    if (!name) {
                        const h = card.querySelector('h1, h2, h3, h4, [class*="title"]');
                        name = h ? h.innerText.trim() : "";
                    }
                    if (!name) {
                        const lines = card.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 2);
                        for (let line of lines) {
                            if (!/Mon|Tue|Wed|Thu|Fri|Sat|Sun|₹|Free/i.test(line)) {
                                name = line;
                                break;
                            }
                        }
                    }
                    
                    if (name) {
                        results.push({
                            url: href,
                            name: name,
                            dateText: dateText,
                            locText: locText,
                            priceText: priceText,
                            innerText: card.innerText
                        });
                    }
                });
                return results;
            }""", display_city)

            logger.info(f"Sort My Scene: JS evaluation found {len(extracted_data)} candidates for {display_city}")

            for data in extracted_data:
                if len(candidates) >= target_count * 2:
                    break

                try:
                    full_url = f"https://sortmyscene.com{data['url']}" if data['url'].startswith("/") else data['url']
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    event_name = data['name']
                    event_timing = data['dateText']
                    location_text = data['locText']
                    price_text = data['priceText']

                    # ── Parse venue and city ──
                    venue_name = ""
                    venue_city = display_city
                    if location_text:
                        location_clean = location_text.replace("\n", ", ").strip()
                        location_clean = re.sub(r",\s*,", ",", location_clean).strip(", ")
                        if "," in location_clean:
                            parts = location_clean.rsplit(",", 1)
                            venue_name = parts[0].strip()
                            raw_city = parts[1].strip()
                            venue_city = raw_city.title() if raw_city else display_city
                        else:
                            venue_name = location_clean

                    # ── City Alias Matching ──
                    search_terms = get_city_aliases(display_city.lower())
                    city_matched = any(term in venue_city.lower() or term in venue_name.lower() or term in data['innerText'].lower() for term in search_terms)
                    
                    if not city_matched:
                        continue

                    # ── Parse price ──
                    parsed_price = None
                    if price_text:
                        price_lower = price_text.lower()
                        if "free" in price_lower:
                            parsed_price = "0"
                        else:
                            price_match = re.search(r"₹\s?([\d,]+)", price_text)
                            if price_match:
                                parsed_price = price_match.group(1).replace(",", "")
                            else:
                                price_match = re.search(r"(\d[\d,]+)", price_text)
                                if price_match:
                                    parsed_price = price_match.group(1).replace(",", "")

                    # ── Parse date ──
                    parsed_date = None
                    if event_timing:
                        try:
                            date_part = event_timing.split("-")[0].strip()
                            date_part = re.sub(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+", "", date_part, flags=re.I)
                            if date_part:
                                from datetime import datetime as _dt
                                current_year = _dt.now().year
                                try:
                                    dt_obj = _dt.strptime(f"{date_part} {current_year}", "%b %d %Y")
                                    parsed_date = dt_obj.strftime("%Y-%m-%d")
                                except ValueError:
                                    try:
                                        dt_obj = _dt.strptime(f"{date_part} {current_year}", "%B %d %Y")
                                        parsed_date = dt_obj.strftime("%Y-%m-%d")
                                    except ValueError:
                                        parsed_date = None
                        except Exception:
                            pass

                    # ── Build candidate ──
                    cand = {
                        "url": full_url,
                        "name": event_name,
                        "date": parsed_date,
                        "price": parsed_price if parsed_price is not None else "N/A",
                        "location": venue_city,
                        "venue": {"name": venue_name} if venue_name else {"name": display_city},
                        "venue_address": location_text or None,
                        "organizer": None,
                        "hashtags": None,
                        "event_time": event_timing or None,
                        "description": f"{event_name} at {venue_name}, {venue_city}" if venue_name else event_name,
                        "is_enriched": False,
                    }

                    candidates.append(cand)
                    logger.info(f"Sort My Scene: Extracted '{event_name}' | {price_text} | {venue_name}")

                except Exception as e:
                    logger.debug(f"Sort My Scene: Card extraction error: {e}")
                    continue

            logger.info(f"Sort My Scene: Collected {len(candidates)} events from listing for {display_city}")
            return candidates

        except Exception as exc:
            logger.error(f"Sort My Scene: L1 pipeline error: {exc}")
            return []

    def _enrich_event_details(self, page, raw_event: dict) -> dict:
        """Enrich with detail page data (specifically looking for collaborations, dates, and prices)."""
        try:
            # Basic enrichment first (description, etc.)
            raw_event = super()._enrich_event_details(page, raw_event)
            
            # Wait for content to render
            time.sleep(4)
            
            # Extract entire body text for pattern matching
            body_text = page.evaluate("document.body.innerText")

            # ── 1. Collaboration / Organizer Extraction ──
            collab_info = page.evaluate("""() => {
                const searchPatterns = [
                    /In Collaboration With\\s+([^\\n,]{2,60})/i,
                    /Collaborating With\\s+([^\\n,]{2,60})/i,
                    /Presented By\\s+([^\\n,]{2,60})/i,
                    /Collab With\\s+([^\\n,]{2,60})/i,
                    /Organized By\\s+([^\\n,]{2,60})/i
                ];
                
                const allElements = document.querySelectorAll('div, span, p, h1, h2, h3');
                for (const el of allElements) {
                    const text = el.innerText;
                    if (!text || text.length > 200) continue;
                    
                    for (const pattern of searchPatterns) {
                        const match = text.match(pattern);
                        if (match) return match[1].trim();
                    }
                }
                return null;
            }""")

            if collab_info:
                raw_event["organizer"] = f"Sort My Scene with {collab_info.title()}"
            elif not raw_event.get("organizer") or raw_event.get("organizer") == "Sort My Scene":
                raw_event["organizer"] = "Sort My Scene"

            # ── 2. Missing Date / Time Extraction ──
            # Pattern: "Fri May 08, 08:00 PM to 00:30 AM"
            if not raw_event.get("date") or raw_event.get("date") == "Unknown" or not raw_event.get("event_time"):
                # Try to find specific date/time pattern
                time_match = re.search(r"([A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d{1,2}),\s*(\d{1,2}:\d{2}\s*[AP]M)", body_text)
                if time_match:
                    if not raw_event.get("date") or raw_event.get("date") == "Unknown":
                        raw_event["date"] = time_match.group(1)
                    raw_event["event_time"] = time_match.group(2)
                    logger.debug(f"Sort My Scene: Recovered date/time from detail page: {raw_event['date']} {raw_event['event_time']}")

            # ── 3. Missing Price Extraction ──
            if not raw_event.get("price") or raw_event.get("price") in ("0", "N/A", "-1"):
                price_match = re.search(r"(?:From|Starting at|Price:?|₹)\\s?([\\d,]+)", body_text, re.I)
                if price_match:
                    raw_event["price"] = price_match.group(1).replace(",", "")
                    logger.debug(f"Sort My Scene: Recovered missing price '{raw_event['price']}' from detail page")

            return raw_event
        except Exception as e:
            logger.debug(f"Sort My Scene: Enrichment error for {raw_event.get('name')}: {e}")
            return raw_event


# ══════════════════════════════════════════════════════════════
# URBANAUT — Discover local experiences (with detail page scraping)
# ══════════════════════════════════════════════════════════════
class UrbanautAgent(BaseAgent):
    def __init__(self):
        super().__init__("Urbanaut", "https://urbanaut.app")

    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        """
        Scrape events from Urbanaut for the given city.
        """
        try:
            city_param = location.split(",")[0].strip().lower()
            
            # Alias matching as requested
            if city_param in ["bombay", "mumbai"]:
                city_param = "mumbai"
            elif city_param in ["bangalore", "bengaluru"]:
                city_param = "bengaluru"
            elif city_param in ["gurgaram", "gurugram", "gurgaon", "gurgoramam"]:
                city_param = "gurugram"
                
            display_city = city_param.title()
            candidates = []
            seen_urls = set()

            url = f"https://urbanaut.app/experience-{city_param}/events"
            logger.info(f"Urbanaut: Trying {url}")
            
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(1000)

            # Scroll to load cards
            for _ in range(5):
                page.evaluate("window.scrollBy(0, 1500)")
                page.wait_for_timeout(600)

            # Collect experience/event card links
            cards = page.query_selector_all("a[href*='/spot/']")
            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href: continue
                    full_url = f"https://urbanaut.app{href}" if href.startswith("/") else href
                    full_url = full_url.split("?")[0].split("#")[0]

                    if full_url in seen_urls: continue
                    seen_urls.add(full_url)

                    # Get title from card for preview
                    card_text = card.inner_text().strip()
                    lines = card_text.split('\n')
                    card_title = lines[0] if lines else ""

                    candidates.append({
                        "name": card_title,
                        "url": full_url,
                        "location": display_city,
                        "city": display_city,
                        "platform": "Urbanaut",
                        "is_enriched": False
                    })
                except:
                    continue

            logger.info(f"Urbanaut: Found {len(candidates)} event links from {url}")

            # ── Google search fallback if not enough events found on site ──
            if len(candidates) < target_count:
                try:
                    search_query = f"site:urbanaut.app {display_city} experiences events"
                    google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                    logger.info(f"Urbanaut: Google fallback search for {display_city}")
                    page.goto(google_url, wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(2000)

                    for _ in range(2):
                        page.evaluate("window.scrollBy(0, 800)")
                        page.wait_for_timeout(500)

                    google_links = page.query_selector_all('a[href*="urbanaut.app"]')
                    for gl in google_links:
                        try:
                            href = gl.get_attribute("href") or ""
                            if "urbanaut.app" not in href or "google" in href:
                                continue
                            if "&sa=" in href:
                                href = href.split("&sa=")[0]
                            if href.startswith("/url?q="):
                                href = href.split("/url?q=")[1].split("&")[0]

                            clean_url = href.split("?")[0].split("#")[0]
                            if clean_url in seen_urls:
                                continue

                            if ("/experience/" in clean_url or "/event/" in clean_url or "/spot/" in clean_url) and not clean_url.endswith("/events"):
                                seen_urls.add(clean_url)
                                link_text = gl.inner_text().strip().split("\n")[0]
                                candidates.append({
                                    "name": link_text,
                                    "url": clean_url,
                                    "location": display_city,
                                    "city": display_city,
                                    "platform": "Urbanaut",
                                    "is_enriched": False
                                })
                        except:
                            continue
                    logger.info(f"Urbanaut: Total {len(candidates)} event URLs after Google fallback")
                except Exception as gf_err:
                    logger.debug(f"Urbanaut: Google fallback failed: {gf_err}")

            return candidates

        except Exception as exc:
            logger.debug(f"Urbanaut L1 error: {exc}")
            return []

    def _enrich_event_details(self, page, raw_event: dict) -> dict:
        url = raw_event.get("url", "")
        if not url or "urbanaut.app" not in url:
            return raw_event

        display_city = str(raw_event.get("city") or raw_event.get("location") or "Hyderabad").split(",")[0].strip().title()

        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            if not resp or resp.status >= 400:
                raw_event["is_enriched"] = True
                return raw_event
            page.wait_for_timeout(2000)


            event_data = raw_event.copy()
            event_data.setdefault("about_event", "N/A")
            event_data.setdefault("price", "Not Specified")
            event_data.setdefault("organizer", "Urbanaut Host")
            event_data.setdefault("hashtags", "")

            # Hashtags DOM
            body_text = page.inner_text("body") or ""
            clean_tags = [
                "Couples", "Solo-Friendly", "Great For Groups", "local", "festival", "art & culture", 
                "Must do", "Nature", "Entertainment", "Live Gig", "Food", "Drink", "Wellness",
                "Family-Friendly", "For All Ages", "Premium", "Workshops", "Nightlife"
            ]
            
            hashtags = []
            if event_data.get("hashtags") and event_data["hashtags"] != "N/A":
                hashtags.extend([h.strip() for h in event_data["hashtags"].split(',')])
                
            for tag in clean_tags:
                if tag.lower() in body_text.lower() and tag not in hashtags:
                    hashtags.append(tag)
            
            if hashtags:
                event_data["hashtags"] = ", ".join(hashtags)

            # Try NEXT_DATA
            next_data_script = page.query_selector("script#__NEXT_DATA__")
            if next_data_script:
                import json
                try:
                    next_data = json.loads(next_data_script.inner_text())
                    def extract_from_json(obj, depth=0):
                        if depth > 8: return
                        if isinstance(obj, dict):
                            if not event_data.get("about_event") or event_data["about_event"] == "N/A":
                                for k in ["description", "about", "content"]:
                                    if k in obj and isinstance(obj[k], str) and len(obj[k]) > 20:
                                        import re
                                        event_data["about_event"] = re.sub(r'<[^>]*>', '', obj[k][:800])
                            for k in ["host", "organizer", "organiserName", "brand"]:
                                if k in obj:
                                    val = obj[k]
                                    if isinstance(val, dict) and val.get("name"):
                                        event_data["organizer"] = val["name"]
                                    elif isinstance(val, str) and len(val) > 2:
                                        event_data["organizer"] = val
                            if "venue" in obj and isinstance(obj["venue"], dict) and "name" in obj["venue"]:
                                event_data["venue"] = obj["venue"]["name"]
                            if "price" in obj and isinstance(obj["price"], (int, float, str)) and str(obj["price"]).isdigit():
                                event_data["price"] = str(obj["price"])
                            for v in obj.values():
                                extract_from_json(v, depth+1)
                        elif isinstance(obj, list):
                            for item in obj:
                                extract_from_json(item, depth+1)
                    extract_from_json(next_data)
                except: pass

            # JSON-LD
            for ld in self._extract_json_ld(page):
                if "event" in str(ld.get("@type", "")).lower() or "place" in str(ld.get("@type", "")).lower():
                    sd = ld.get("startDate") or ld.get("startDateTime")
                    if sd: event_data["date"] = sd

                    offer = ld.get("offers") or {}
                    if isinstance(offer, list) and offer: offer = offer[0]
                    if isinstance(offer, dict):
                        p = offer.get("price")
                        if p: event_data["price"] = str(p)

                    loc = ld.get("location")
                    if isinstance(loc, dict):
                        vn = loc.get("name", "")
                        if vn: event_data["venue"] = vn

                    org = ld.get("organizer")
                    if isinstance(org, dict):
                        on = org.get("name", "")
                        if on: event_data["organizer"] = on
                    elif isinstance(org, str):
                        event_data["organizer"] = org
                    break

            # Fallbacks
            if not event_data.get("name") or len(event_data["name"]) < 3:
                h1 = page.query_selector("h1")
                if h1: event_data["name"] = h1.inner_text().strip()

            if not event_data.get("date"):
                date_el = page.query_selector("time, [class*='date']")
                if date_el: event_data["date"] = (date_el.get_attribute("datetime") or date_el.inner_text()).strip()

            import re
            time_m = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))", body_text)
            if time_m: event_data["event_time"] = time_m.group(1)

            # 1. DESCRIPTION fallback (Moved before price so price regex can scan it)
            if not event_data.get("about_event") or event_data["about_event"] == "N/A":
                desc = self._self_healing_extract(page, "description")
                if desc: event_data["about_event"] = desc[:500]

            # 2. PRICE fallback
            if event_data["price"] == "Not Specified" or event_data["price"] == "Free":
                pm1 = re.search(r"Book at[\s\n]+(?:INR|Rs\.?|₹)?[\s\n]*(\d+(?:,\d+)*(?:\.\d+)?)", event_data.get("about_event", ""), re.I)
                if pm1:
                    event_data["price"] = pm1.group(1).replace(",", "")
                else:
                    pm = re.search(r"(?:₹|INR|Rs\.?)[\s\n]*(\d+(?:,\d+)*(?:\.\d+)?)", body_text, re.I)
                    if pm: event_data["price"] = pm.group(1).replace(",", "")
                    elif "free" in body_text.lower(): event_data["price"] = "Free"
                    else: event_data["price"] = "Free"

            if not event_data.get("venue"):
                v_m = re.search(r"(?:Venue|Location|At)\s*[:\-]?\s*([^\n]{3,60})", body_text, re.I)
                if v_m: event_data["venue"] = v_m.group(1).strip()
                else: event_data["venue"] = display_city

            # Filter cross city leaks
            extracted_venue_lower = event_data["venue"].lower()
            OTHER_CITIES = {
                "mumbai", "bombay", "delhi", "new delhi", "noida", "gurugram", "gurgaon", 
                "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "kolkata", 
                "ahmedabad", "jaipur", "chandigarh", "kochi", "goa"
            }
            city_param = display_city.lower()
            OTHER_CITIES.discard(city_param)
            if city_param in ["bangalore", "bengaluru"]:
                OTHER_CITIES.discard("bangalore")
                OTHER_CITIES.discard("bengaluru")
            if city_param in ["mumbai", "bombay"]:
                OTHER_CITIES.discard("mumbai")
                OTHER_CITIES.discard("bombay")
            if city_param in ["gurugram", "gurgaon"]:
                OTHER_CITIES.discard("gurugram")
                OTHER_CITIES.discard("gurgaon")
            
            if any(oc in extracted_venue_lower for oc in OTHER_CITIES):
                logger.info(f"Urbanaut: REJECTED cross-city leak: {event_data['venue']}")
                event_data["is_enriched"] = True
                return event_data # Allow BaseAgent validation to officially reject it

            if display_city.lower() not in extracted_venue_lower:
                if city_param == "bangalore" and "bengaluru" in extracted_venue_lower:
                    pass # Already matches
                else:
                    event_data["venue"] = f"{event_data['venue']}, {display_city}"

            if event_data["organizer"] == "Urbanaut Host":
                org_m = re.search(r"(?:Organized by|Organizer|Hosted by|By)\s*[:\-]?\s*([^\n.]{3,100})", body_text, re.I)
                if org_m: event_data["organizer"] = org_m.group(1).strip()

            event_data["is_enriched"] = True
            return event_data

        except Exception as e:
            logger.debug(f"Urbanaut L4 detail error: {e}")
            raw_event["is_enriched"] = True
            return raw_event


# ══════════════════════════════════════════════════════════════
# MEETUP — Global community events (ALL events, no topic filter)
# ══════════════════════════════════════════════════════════════
class MeetupAgent(BaseAgent):
    def __init__(self):
        super().__init__("Meetup", "https://www.meetup.com")

    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        """
        Scrape ALL events from Meetup for the given city.
        - Robust extraction for Price, Venue, Format, Organizer
        - Extract Ratings and Review Counts
        - Optimized performance with aggressive scrolling and API sniffing
        """
        try:
            city = location.lower().split(",")[0].strip()
            formatted_city = city.replace(" ", "-")
            
            candidates = []
            seen = set()

            # ── Navigation with retries ──
            def safe_goto(url, retries=3):
                for i in range(retries):
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=40000)
                        return True
                    except Exception as e:
                        if i == retries - 1: return False
                        logger.warning(f"Meetup: Retry {i+1} for {url}...")
                        page.wait_for_timeout(3000)
                return False

            # ── Intercept GraphQL API responses for rich data ──
            events_json = []
            def handle_response(response):
                try:
                    if "graphql" in response.url and response.request.method == "POST":
                        events_json.append(response.json())
                except: pass
            page.on("response", handle_response)

            # ── Single city URL — NO keyword filtering ──
            urls_to_try = [
                f"https://www.meetup.com/find/?location=in--{formatted_city}&source=EVENTS",
                f"https://www.meetup.com/find/?location={city}&source=EVENTS",
                f"https://www.meetup.com/find/?location=in--{formatted_city}&source=GROUPS", # Sometimes groups page has better event links
            ]

            for url in urls_to_try:
                logger.info(f"Meetup: Loading events for '{city}' → {url}")
                if not safe_goto(url): continue
                page.wait_for_timeout(3000)

                # ── Aggressive scroll to load ALL event cards ──
                # Rule 8: Use deeper scroll for higher yields
                scroll_passes = 30 if target_count > 50 else 20
                last_count = 0
                stale_rounds = 0
                for scroll_round in range(scroll_passes):
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(1500)
                    current_count = len(page.query_selector_all("a[href*='/events/']"))
                    if current_count == last_count:
                        stale_rounds += 1
                        if stale_rounds >= 4: break
                    else:
                        stale_rounds = 0
                    last_count = current_count
                    if current_count >= target_count * 2.5: break

                logger.info(f"Meetup: Found {last_count} event links after scrolling")

                # ── Merge GraphQL API data (best quality) ──
                for data in events_json:
                    try:
                        for e in self._parse_api_json(data, location):
                            if e["url"] not in seen:
                                candidates.append(e)
                                seen.add(e["url"])
                    except: pass
                events_json = []

                # ── Extract from DOM cards ──
                potential_cards = page.query_selector_all("[data-testid='event-card'], a[href*='/events/']")
                for card in potential_cards:
                    try:
                        href = card.get_attribute("href") or ""
                        if not href or href in seen: continue
                        if any(x in href for x in ["/find/", "/topics/", "/groups/"]): continue

                        title_el = card.query_selector("h3")
                        if not title_el: continue
                        title = title_el.inner_text().strip()
                        if not self._is_valid_meetup_title(title): continue

                        # ── Extract ALL details from the card DOM ──
                        organizer = "Meetup Group"
                        date_text = "TBD"
                        venue_text = location
                        price = -1 # Not Mentioned
                        event_format = "Offline"
                        rating = "-"
                        review_count = "-"
                        attending = "0"

                        try:
                            card_text = card.inner_text()
                            card_text_lower = card_text.lower()

                            # --- ORGANIZER ---
                            # Priority: div/span with 'by ' text
                            org_el = card.query_selector('div:has-text("by "), span:has-text("by ")')
                            if org_el:
                                txt = org_el.inner_text().strip()
                                # Only take the part after 'by '
                                m = re.search(r"(?i)by\s+(.+)", txt)
                                if m:
                                    organizer = m.group(1).split("\n")[0].strip()
                            
                            # Fallback to groupName classes
                            if organizer == "Meetup Group":
                                for org_sel in ['[class*="groupName"]', '[data-testid*="host-name"]', '[class*="organizer"]', '[data-testid="event-group-name"]']:
                                    el = card.query_selector(org_sel)
                                    if el:
                                        txt = el.inner_text().strip()
                                        if txt and 2 < len(txt) < 100 and txt.lower() != title.lower():
                                            organizer = txt.replace("by ", "").replace("By ", "").strip()
                                            break

                            # --- RATING & REVIEWS ---
                            # Look for star icon
                            star_el = card.query_selector(".lucide-star, svg[class*='star']")
                            if star_el:
                                r_parent = star_el.evaluate_handle("el => el.parentElement")
                                if r_parent:
                                    r_txt = r_parent.as_element().inner_text().strip()
                                    rm = re.search(r"(\d\.\d|\d)", r_txt)
                                    if rm: rating = rm.group(1)
                            
                            # Attendees as Reviews proxy
                            att_el = card.query_selector("span:has-text('attendees')")
                            if att_el:
                                att_m = re.search(r"(\d[\d,]*)", att_el.inner_text())
                                if att_m: 
                                    attending = att_m.group(1).replace(",", "")
                                    review_count = attending

                            # --- DATE ---
                            date_el = card.query_selector('time, [class*="dateTime"], [class*="date"]')
                            if date_el:
                                date_text = (date_el.get_attribute("datetime") or date_el.inner_text()).strip()

                            # --- VENUE & FORMAT ---
                            # Priority 1: Check for explicit venue name
                            venue_el = card.query_selector('[data-testid*="venue-name"], [class*="venueName"], [class*="venue"], [class*="location"]')
                            venue_txt = venue_el.inner_text().strip() if venue_el else ""
                            
                            # Priority 2: Check for online badge
                            online_badge = card.query_selector("[data-testid='online-badge'], [class*='onlineBadge'], [class*='virtual']")
                            
                            if venue_txt and "online" not in venue_txt.lower():
                                venue_text = venue_txt
                                event_format = "Offline"
                            elif online_badge:
                                venue_text = "Online Event"
                                event_format = "Online"
                            elif "online event" in card_text_lower:
                                venue_text = "Online Event"
                                event_format = "Online"
                            elif venue_txt:
                                venue_text = venue_txt
                                event_format = "Offline" if "online" not in venue_txt.lower() else "Online"
                            else:
                                venue_text = location
                                event_format = "Offline"

                            # --- PRICE ---
                            p_el = card.query_selector('span:has-text("₹"), span:has-text("$"), span:has-text("INR"), span:has-text("Rs")')
                            if p_el:
                                p_txt = p_el.inner_text().strip()
                                price_match = re.search(r'(?:₹|Rs\.?|INR|\$)\s*(\d[\d,]*\.?\d*)', p_txt, re.I)
                                if price_match:
                                    price = float(price_match.group(1).replace(",", ""))
                            elif "free" in card_text_lower:
                                price = 0
                            else:
                                # Deep search for price patterns in card text
                                price_m = re.search(r'(?:₹|Rs\.?|INR|\$)\s*(\d{1,5})', card_text, re.I)
                                if price_m:
                                    price = float(price_m.group(1))

                        except Exception as card_err:
                            logger.debug(f"Meetup Card extraction error: {card_err}")

                        seen.add(href)
                        candidates.append({
                            "url":          href,
                            "name":         title,
                            "organizer":    organizer,
                            "date":         date_text,
                            "venue":        venue_text,
                            "price":        price,
                            "location":     location,
                            "event_format": event_format,
                            "rating":       rating,
                            "review_count": review_count,
                            "attending":    attending,
                            "is_enriched":  False,
                        })
                    except: continue

                if len(candidates) >= target_count * 2: break

            logger.info(f"Meetup: Total {len(candidates)} candidates found")
            return candidates[:target_count * 5]

        except Exception as exc:
            logger.debug(f"Meetup L1 error: {exc}")
            return []

    def _enrich_event_details(self, page, raw_event: dict) -> dict:
        """Meetup enrichment — visits detail page for missing data, ratings, and reviews."""
        # If already highly enriched from API, skip
        if raw_event.get("is_enriched") and raw_event.get("rating") != "-":
            return raw_event

        raw_event = super()._enrich_event_details(page, raw_event)

        try:
            # ── Organizer, Ratings & Reviews from detail page ──
            try:
                # 1. Organization/Group Info & Person Host
                group_el = page.query_selector("a[href*='/groups/'], [data-testid='group-info'], [data-testid='group-card']")
                host_person = ""
                
                # Try to get the person hosting
                for host_sel in ["[data-testid='event-host-name']", ".event-host-name", "[data-testid='organizer-name']", "span:has-text('Hosted by')", "div[id='event-hosts-links']"]:
                    el = page.query_selector(host_sel)
                    if el:
                        txt = el.inner_text().replace("Hosted by", "").replace("by ", "").strip()
                        if txt and len(txt) > 2:
                            # Clean up multi-line host names
                            host_person = txt.split("\n")[0].strip()
                            break
                
                if group_el:
                    group_name = group_el.inner_text().strip().split("\n")[0]
                    # Rating below group name - improved selectors
                    r_el = page.query_selector("[class*='rating'], [data-testid='group-rating'], [data-testid='group-card'] span:has-text('.')")
                    if r_el:
                        r_txt = r_el.inner_text().strip()
                        rm = re.search(r"(\d\.\d)", r_txt)
                        if rm: raw_event["rating"] = rm.group(1)
                        
                        # Count of reviews - search for digits + "reviews"
                        rev_m = re.search(r"(\d[\d,]*)\s*reviews", r_txt, re.I)
                        if not rev_m:
                            # Try searching sibling text
                            rev_m = re.search(r"(\d[\d,]*)\s*reviews", page.inner_text("body"), re.I)
                        if rev_m: raw_event["review_count"] = rev_m.group(1).replace(",", "")

                    if host_person and host_person.lower() not in group_name.lower():
                        raw_event["organizer"] = f"{host_person} ({group_name})"
                    else:
                        raw_event["organizer"] = group_name or host_person or raw_event.get("organizer")

                elif host_person:
                    raw_event["organizer"] = host_person

                # 2. Description (About Event)
                desc_el = page.query_selector("[data-testid='event-description'], .event-description, #event-details")
                if desc_el:
                    raw_event["about_event"] = desc_el.inner_text().strip()
                else:
                    # Fallback to self-healing
                    desc = self._self_healing_extract(page, "description")
                    if desc: raw_event["about_event"] = desc

                # 3. Venue & Format (Deep check)
                body_text = page.inner_text("body")
                body_text_lower = body_text.lower()
                
                # Priority: Physical venue selectors for full address
                v_name_el = page.query_selector("[data-testid='venue-name-link'], [data-testid='location-info'] h3")
                v_addr_el = page.query_selector("[data-testid='venue-display-name']")
                
                if v_name_el or v_addr_el:
                    v_name = v_name_el.inner_text().strip() if v_name_el else ""
                    v_addr = v_addr_el.inner_text().strip() if v_addr_el else ""
                    
                    # Combine name and address for "Exact Venue Detail"
                    full_venue = f"{v_name}, {v_addr}".strip(", ")
                    
                    if full_venue and "online" not in full_venue.lower():
                        raw_event["venue"] = full_venue
                        raw_event["event_format"] = "Offline"
                    else:
                        raw_event["venue"] = "Online Event"
                        raw_event["event_format"] = "Online"
                elif any(x in body_text_lower for x in ["online event", "zoom", "google meet", "virtual"]):
                    raw_event["venue"] = "Online Event"
                    raw_event["event_format"] = "Online"
                else:
                    # Fallback to general location selectors
                    v_el = page.query_selector("[class*='venueName'], [class*='venue-name']")
                    if v_el:
                        raw_event["venue"] = v_el.inner_text().strip()
                        raw_event["event_format"] = "Offline"

                # 4. Time Extraction
                time_el = page.query_selector("[data-testid='event-date-info'] time, .event-date-time")
                if time_el:
                    t_txt = time_el.inner_text().strip()
                    # Pattern for time like "6:30 PM" or "18:30"
                    tm = re.search(r"(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)", t_txt)
                    if tm:
                        raw_event["event_time"] = tm.group(1)
                
                if not raw_event.get("event_time"):
                    # Regex fallback from body
                    tm = re.search(r"\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)\b", body_text)
                    if tm:
                        raw_event["event_time"] = tm.group(1)

                # 5. Price (Detailed check)
                if raw_event.get("price") in (-1, None, "", "Not Mentioned", "0", 0):
                    # Check sticky footer first (most reliable for paid events)
                    footer_el = page.query_selector("[data-testid='event-info-footer']")
                    if footer_el:
                        f_txt = footer_el.inner_text().strip()
                        pm = re.search(r"(?i)(?:₹|INR|Rs\.?|\$)\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)", f_txt)
                        if pm:
                            raw_event["price"] = float(pm.group(1).replace(",", ""))
                        elif "free" in f_txt.lower():
                            raw_event["price"] = 0

                    # Fallback to body regex if still not found
                    if raw_event.get("price") in (-1, None, "", "Not Mentioned"):
                        price_m = re.search(r"(?i)(?:₹|INR|Rs\.?|\$)\s?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)", body_text)
                        if price_m:
                            raw_event["price"] = float(price_m.group(1).replace(",", ""))
                        elif "free" in body_text_lower:
                            raw_event["price"] = 0
                        else:
                            # Try to find ticket info in specific sections
                            tix_el = page.query_selector("[class*='ticket'], [class*='price'], [data-testid='event-fee'], [class*='fee']")
                            if tix_el:
                                t_txt = tix_el.inner_text().strip()
                                tm = re.search(r"(?:₹|Rs\.?|INR|\$)\s*(\d[\d,]*\.?\d*)", t_txt)
                                if tm:
                                    raw_event["price"] = float(tm.group(1).replace(",", ""))
                                elif "free" in t_txt.lower():
                                    raw_event["price"] = 0
                            else:
                                raw_event["price"] = -1 # Explicitly Not Mentioned

            except Exception as e:
                logger.debug(f"Meetup detail extraction error: {e}")

        except Exception as e:
            logger.debug(f"Meetup enrichment error: {e}")

        raw_event["is_enriched"] = True
        return raw_event

    def _parse_api_json(self, data, location: str = "") -> List[Dict]:
        """Parse Meetup GraphQL responses with full metadata."""
        results = []
        try:
            def _recurse(obj):
                if isinstance(obj, dict):
                    if "name" in obj and ("link" in obj or "eventUrl" in obj):
                        url = obj.get("link") or obj.get("eventUrl", "")
                        if "meetup.com" in str(url):
                            # Date
                            date_val = None
                            ts = obj.get("time") or obj.get("dateTime") or obj.get("startTime")
                            if ts:
                                try:
                                    import datetime as _dt
                                    ts_f = float(ts)
                                    if ts_f > 1e11: ts_f /= 1000
                                    dt_obj = _dt.datetime.fromtimestamp(ts_f)
                                    date_val = dt_obj.strftime("%Y-%m-%d")
                                    event_time = dt_obj.strftime("%I:%M %p")
                                except: 
                                    event_time = None

                            # Price
                            fee = obj.get("fee") or obj.get("eventFee") or {}
                            price = str(fee.get("amount") or fee.get("value") or "")
                            if not price:
                                price = "Free" if obj.get("isFree") else "Not Mentioned"

                            # Venue & Format
                            v_data = obj.get("venue")
                            v_name = v_data.get("name") if v_data else "Not Mentioned"
                            fmt = "Offline"
                            if obj.get("isVirtual") or obj.get("eventAttendanceMode") == "ONLINE":
                                v_name = "Online Event"
                                fmt = "Online"

                            # Group/Organizer & Rating
                            group = obj.get("group") or {}
                            organizer = group.get("name") or "Meetup Group"
                            rating = "-"
                            review_count = "-"
                            
                            # Meetup GraphQL often has ratings in group object
                            if group.get("rating"): rating = str(group["rating"])
                            if group.get("reviewCount"): review_count = str(group["reviewCount"])

                            results.append({
                                "name":         obj.get("name"),
                                "url":          url,
                                "date":         date_val,
                                "price":        price,
                                "description":  obj.get("description", ""),
                                "about_event":  obj.get("description", ""),
                                "organizer":    organizer,
                                "venue":        v_name,
                                "location":     location,
                                "event_format": fmt,
                                "event_time":   event_time,
                                "rating":       rating,
                                "review_count": review_count,
                                "is_enriched":  True,
                            })
                    for v in obj.values(): _recurse(v)
                elif isinstance(obj, list):
                    for item in obj: _recurse(item)
            _recurse(data)
        except: pass
        return results


# ══════════════════════════════════════════════════════════════
# TOWNSCRIPT — Dynamic city-based events scraper
# ══════════════════════════════════════════════════════════════
class TownscriptAgent(BaseAgent):
    def __init__(self):
        super().__init__("Townscript", "https://www.townscript.com")

    def _perform_scraping_sync(
        self, page, location: str, target_count: int, max_price: Optional[int]
    ) -> List[Dict]:
        """
        Scrape events directly from the Townscript listing page.
        Uses the /in/<city> pattern.
        """
        try:
            candidates = []
            seen_urls = set()
            
            # ── Normalise city for Townscript URL ──
            url_city = location.strip().lower().replace(" ", "-")
            home_url = f"https://www.townscript.com/in/{url_city}"
            
            logger.info(f"Townscript: Loading home page for '{location}' -> {home_url}")
            page.goto(home_url, wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            # ── Level 1 & 2: Category Discovery + Expansion ──
            # Extract category "VIEW ALL" links
            category_links = page.evaluate("""() => {
                const links = [];
                document.querySelectorAll('a[href*="/in/"]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && href.split('/').length >= 4) {
                        links.push(new URL(href, window.location.origin).href);
                    }
                });
                return [...new Set(links)];
            }""")
            
            logger.info(f"Townscript: Found {len(category_links)} potential category links")
            
            # ── Level 3: Scroll to discover more categories ──
            # Townscript home page uses a digest view. Scrolling can reveal a "Load More Categories" button.
            for _ in range(3): # Scroll a few times
                page.mouse.wheel(0, 2000)
                time.sleep(2)
                load_more = page.locator("button:has-text('Load More'), span:has-text('Load More')").first
                if load_more.is_visible():
                    try:
                        load_more.click()
                        logger.info("Townscript: Clicked 'Load More Categories'")
                        time.sleep(3)
                    except: pass

            # Re-collect category links after scrolling
            category_links = page.evaluate("""() => {
                const links = [];
                document.querySelectorAll('a[href*="/in/"]').forEach(a => {
                    const href = a.getAttribute('href');
                    if (href && href.split('/').length >= 4) {
                        links.push(new URL(href, window.location.origin).href);
                    }
                });
                return [...new Set(links)];
            }""")

            # Filter category links to ensure they match the city and are category listing pages
            # Category pattern: /in/city/category-name
            valid_categories = [
                l for l in category_links 
                if f"/in/{url_city}/" in l.lower() 
                and not any(x in l.lower() for x in ["/e/", "google", "facebook", "twitter"])
            ]
            
            logger.info(f"Townscript: Validated {len(valid_categories)} categories for enrichment")
            
            # Visit categories until we hit target_count * 3 (discovery phase)
            for cat_url in valid_categories:
                if len(candidates) >= target_count * 3:
                    break
                    
                logger.info(f"Townscript: Visiting category -> {cat_url}")
                try:
                    page.goto(cat_url, wait_until="networkidle", timeout=45000)
                    time.sleep(5)
                    
                    # Scroll within category to load events
                    for _ in range(5):
                        page.mouse.wheel(0, 1500)
                        time.sleep(1.5)
                        if len(page.query_selector_all('a[href^="/e/"]')) >= target_count:
                            break

                    # Extract event cards
                    event_links = page.evaluate("""() => {
                        return [...new Set([...document.querySelectorAll('a[href^="/e/"]')].map(a => a.href))];
                    }""")
                    
                    for link in event_links:
                        if link not in seen_urls:
                            candidates.append({
                                "url": link,
                                "location": location,
                                "platform": "Townscript"
                            })
                            seen_urls.add(link)
                            
                    logger.info(f"Townscript: Category {cat_url} yielded {len(event_links)} candidates")
                except Exception as e:
                    logger.warning(f"Townscript: Failed to scrape category {cat_url}: {e}")
                    continue

            # If still low, check the home page for any individual cards
            if len(candidates) < target_count:
                page.goto(home_url, wait_until="networkidle")
                time.sleep(3)
                event_links = page.evaluate("""() => {
                    return [...new Set([...document.querySelectorAll('a[href^="/e/"]')].map(a => a.href))];
                }""")
                for link in event_links:
                    if link not in seen_urls:
                        candidates.append({
                            "url": link,
                            "location": location,
                            "platform": "Townscript"
                        })
                        seen_urls.add(link)

            return candidates

        except Exception as exc:
            logger.error(f"Townscript: Discovery failed: {exc}")
            return []

    def _enrich_event_details(self, page, event: Dict) -> Optional[Dict]:
        """
        Layer 4: Deep enrichment for Townscript.
        Extracts: Name, Date, Venue, Organizer (Name, Joined, Bio), Hashtags, Price.
        """
        url = event.get("url")
        if not url: return None

        try:
            logger.info(f"Townscript: Enriching -> {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5) # Wait for Angular/React to hydrate
            
            # 1. Primary extraction via JSON-LD
            enriched = event.copy()
            json_ld_data = {}
            try:
                scripts = page.query_selector_all("script[type='application/ld+json']")
                for s in scripts:
                    try:
                        data = json.loads(s.inner_text().strip())
                        if isinstance(data, list):
                            for item in data:
                                if item.get("@type") == "Event":
                                    json_ld_data = item
                                    break
                        elif data.get("@type") == "Event":
                            json_ld_data = data
                    except: continue
                    if json_ld_data: break
            except: pass

            # Map JSON-LD fields
            if json_ld_data:
                enriched["event_name"] = json_ld_data.get("name") or enriched.get("name")
                enriched["description"] = json_ld_data.get("description")
                enriched["about_event"] = json_ld_data.get("description")
                
                # Date parsing
                start_date = json_ld_data.get("startDate")
                if start_date:
                    try:
                        dt_obj = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                        enriched["event_date"] = dt_obj.strftime("%Y-%m-%d")
                        enriched["event_time"] = dt_obj.strftime("%I:%M %p")
                    except:
                        enriched["event_date"] = start_date.split("T")[0]
                
                # Venue
                loc = json_ld_data.get("location") or {}
                if loc:
                    addr = loc.get("address") or {}
                    v_name = loc.get("name") or addr.get("addressLocality") or "Online"
                    enriched["venue"] = v_name
                    enriched["venue_address"] = addr.get("streetAddress") or addr.get("addressLocality") or v_name
                
                # Organizer
                performer = json_ld_data.get("performer") or {}
                if performer:
                    enriched["organizer"] = performer.get("name")
                
                # Price
                offers = json_ld_data.get("offers") or {}
                if isinstance(offers, dict):
                    price = offers.get("price") or offers.get("lowPrice")
                    if price is not None:
                        enriched["price"] = float(price)
                elif isinstance(offers, list) and offers:
                    price = offers[0].get("price")
                    if price is not None:
                        enriched["price"] = float(price)

            # 2. DOM Fallback + Supplemental Data (Organizer Joined, Bio, Hashtags)
            try:
                # Wait for the organizer section to be visible
                try:
                    page.wait_for_selector(".event-organizer-body", timeout=10000)
                except:
                    # Scroll down to trigger lazy loading of organizer section
                    page.mouse.wheel(0, 2000)
                    time.sleep(2)

                # Name fallback
                if not enriched.get("event_name"):
                    h1 = page.query_selector("h1")
                    if h1: enriched["event_name"] = h1.inner_text().strip()
                
                # Date fallback
                if not enriched.get("event_date"):
                    date_div = page.query_selector(".date-time")
                    if date_div:
                        text = date_div.inner_text().strip()
                        enriched["event_date"] = text
                
                # Venue fallback
                if not enriched.get("venue"):
                    venue_div = page.query_selector(".location")
                    if venue_div: enriched["venue"] = venue_div.inner_text().strip()

                # Organizer Joined Date - More robust selector
                joined_el = page.locator(".basic-data small, .organizer-info small").first
                if joined_el.count() > 0:
                    joined_text = joined_el.inner_text().strip()
                    if "Joined on" in joined_text:
                        enriched["organizer_joined"] = joined_text.replace("Joined on", "").strip()
                    else:
                        enriched["organizer_joined"] = joined_text

                # Organizer Bio/About
                # Try multiple common selectors for Townscript about section
                bio_selectors = [
                    ".organizer-about .px-0",
                    "#organizer-about-content",
                    ".organizer-about div"
                ]
                for sel in bio_selectors:
                    bio_el = page.query_selector(sel)
                    if bio_el:
                        bio_text = bio_el.inner_text().strip()
                        if bio_text and bio_text.lower() not in ["undefined", "about", ""]:
                            enriched["organizer_description"] = bio_text
                            break
                
                # Hashtags
                tags = page.evaluate("""() => {
                    return [...document.querySelectorAll('.tags a span')].map(s => s.innerText.trim());
                }""")
                if tags:
                    enriched["hashtags"] = tags

                # Final fallback for Price if still missing
                if "price" not in enriched:
                    price_btn = page.query_selector("primary-action-info .font-semibold")
                    if price_btn:
                        price_text = price_btn.inner_text().strip()
                        from utils.price_extractor import extract_price
                        enriched["price"] = extract_price(price_text)

            except Exception as dom_err:
                logger.debug(f"Townscript: DOM fallback error: {dom_err}")

            # 3. Clean up and set defaults
            enriched["is_enriched"] = True
            enriched["platform"] = "Townscript"
            if not enriched.get("organizer"): enriched["organizer"] = "Townscript Organizer"
            
            return enriched

        except Exception as exc:
            logger.warning(f"Townscript: Enrichment failed for {url}: {exc}")
            return None


# ══════════════════════════════════════════════════════════════
# Factory
# ══════════════════════════════════════════════════════════════
def get_platform_agent(platform_name: str, location: str = "Hyderabad") -> Optional[BaseAgent]:
    mapping = {
        "BookMyShow":   BookMyShowAgent,
        "District":     DistrictAgent,
        "Swiggy Scenes": SwiggyScenesAgent,
        "Skillbox":     SkillboxAgent,
        "Sort My Scene": SortMySceneAgent,
        "Mera Events":  MeraEventsAgent,
        "MeraEvents":   MeraEventsAgent,  # dashboard alias
        "Urbanaut":     UrbanautAgent,
        "Urbanot":      UrbanautAgent,   # alias
        "Meetup":       MeetupAgent,
        "Townscript":   TownscriptAgent,
    }
    cls = mapping.get(platform_name)
    return cls() if cls else None
