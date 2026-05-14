# District.in API Endpoints & Network Call Analysis

## Summary

This document details all District.in API endpoints, network calls, and data structures found in the workspace through debug files and platform agents.

---

## 1. KNOWN API ENDPOINTS

### 1.1 Primary District.in Endpoints

#### Base URLs
```
https://www.district.in/events/
https://www.district.in/events/{city-slug}
https://www.district.in/events-in-{city}/
https://www.district.in/activities/
```

#### City-Specific URLs (URL-based routing)
```
https://www.district.in/events/hyderabad
https://www.district.in/events/bengaluru
https://www.district.in/events/delhi-ncr
https://www.district.in/events/mumbai
https://www.district.in/events/delhi
https://www.district.in/events/bangalore
https://www.district.in/events/pune
https://www.district.in/events/goa
https://www.district.in/events/chennai
```

**City Slug Mapping:**
```
bangalore     → bengaluru
delhi         → delhi-ncr
Other cities  → lowercase with hyphens for spaces
```

#### Event Detail URLs (Pattern-based)
```
https://www.district.in/event/{event-slug}
https://www.district.in/events/{city}-ticket-booking
https://www.district.in/activities/{activity-slug}
```

### 1.2 API Endpoints (Inferred from Network Interception)

#### Search/Events API
```
https://www.district.in/api/events?city={city_name}
```
**Note:** This endpoint is referenced in `_debug_district_urls.py` but effectiveness is unclear. Current implementation relies on DOM scraping instead.

#### Third-party/Proxy API (Referenced)
```
https://mpc-prod-24-s6uit34pua-uw.a.run.app/events?cee=no
```
**Source:** `_debug_district_api.py`
**Status:** Unknown purpose, possibly a Google Cloud Run endpoint for aggregated data.

#### Sitemap Discovery
```
https://www.district.in/events/search-sitemap/sitemap-events.xml
```
**Use:** Can be used to discover event URLs programmatically.

---

## 2. API RESPONSE PATTERNS & DATA STRUCTURES

### 2.1 API Response Interception (Network Listener)

The implementation uses Playwright's response listener to intercept API calls:

```python
def handle_response(response):
    if response.request.method == "GET" and "events" in response.url:
        try:
            data = response.json()
            if isinstance(data, dict):
                api_events.extend(data.get("events", []))
        except Exception:
            pass

page.on("response", handle_response)
```

**Filters Applied:**
- Method: `GET` requests only
- URL contains: `"events"` keyword
- Content-Type: Should be JSON

### 2.2 Expected API Response Structure

Based on the handler code, expected format:
```json
{
  "events": [
    {
      "name": "Event Name",
      "url": "https://www.district.in/event/slug",
      "date": "Date String",
      "price": "Price Value",
      "city": "City Name",
      "venue": "Venue Name"
    }
  ]
}
```

### 2.3 Embedded Data Structures

District.in loads event data via **`__NEXT_DATA__`** (Next.js JSON embedded in HTML):

```javascript
// Accessed via JavaScript:
window.__NEXT_DATA__
```

This contains nested event objects with structure:
```javascript
{
  "slug": "/events/event-name-slug",
  "name": "Event Name",
  "props": {
    "pageProps": {
      "event": {
        "name": "Event Name",
        "startDate": "2025-01-15T19:00:00",
        "description": "Event description",
        "location": {
          "name": "Venue Name",
          "address": "Full Address"
        },
        "price": "₹500 - ₹1000"
      }
    }
  }
}
```

---

## 3. HOW EVENTS ARE FETCHED/LOADED

### 3.1 Current Implementation Strategy (Multi-Layer)

The codebase uses a 4-layer approach:

#### Layer 1: Direct DOM Scraping
- Navigate to city-specific URL: `https://www.district.in/events/{city_slug}`
- Use Playwright to wait for `networkidle` (full page load)
- Extract event links from anchor tags:
  ```css
  a[href*='/event/'], a[href*='/events/'], a[href*='/activities/']
  ```
- Filter out false positives (search, policies, terms pages)

#### Layer 2: API Interception
- Register `page.on("response")` listener
- Capture JSON responses containing "events" keyword
- Extract event data from `data.get("events", [])`

#### Layer 3: Google Stealth Fallback
- If insufficient events from Layers 1-2
- Use Google Search API: `site:district.in {city} events`
- Extract event URLs from Google snippets

#### Layer 4: Detail Page Enrichment
- Navigate to each event URL
- Extract additional details from event page:
  - Event name (from `<h1>`)
  - Price (search for `₹` symbol)
  - Date (regex pattern: `\d{1,2}\s+[A-Za-z]{3,}`)
  - Time (regex pattern: `\d{1,2}:\d{2}\s*(?:AM|PM)`)
  - Venue (from "Venue:" label, location section, or JSON-LD schema)

### 3.2 Scroll-Loading Pattern

District uses infinite scroll to load more events:

```python
for i in range(6):  # Max scroll attempts
    page.evaluate("window.scrollBy(0, 1500)")  # Scroll down
    page.wait_for_timeout(1000)  # Wait 1 second
    
    new_height = page.evaluate("document.body.scrollHeight")
    if new_height == previous_height:
        break  # No new content loaded
    previous_height = new_height
```

---

## 4. SEARCH-RELATED API CALLS

### 4.1 URL-Based Search/City Filtering

```python
# City routing (most reliable)
city_slug = city.lower().replace(" ", "-")
if city_slug == "bangalore": city_slug = "bengaluru"
if city_slug == "delhi": city_slug = "delhi-ncr"

city_url = f"https://www.district.in/events/{city_slug}"
page.goto(city_url, wait_until="networkidle", timeout=30000)
```

### 4.2 Google Search Fallback (For Discovery)

```python
queries = [
    f"site:district.in {location} district events tickets",
    f"site:district.in {location} district upcoming events",
    f"site:district.in {location} events",
    f"site:district.in {location} things to do",
]
```

### 4.3 Alternative Search URLs Tested

From `_debug_district_urls.py`:
```
https://www.district.in/
https://www.district.in/events-in-hyderabad/
https://www.district.in/hyderabad-events
https://www.district.in/events/hyderabad
https://www.district.in/hyderabad
https://www.district.in/api/events?city=hyderabad
```

---

## 5. RESPONSE INTERCEPTION PATTERNS

### 5.1 Network Monitoring Filters

From `_debug_district_network.py` and `_debug_district_network_home.py`:

```python
def log_response(response):
    url = response.url
    status = response.status
    ct = response.headers.get('content-type', '')
    
    # Capture responses matching:
    if any(x in url.lower() for x in ['api', 'search', 'event', 'browse', 'hyderabad', 'activities', 'promotions']):
        print('RESP', status, ct, url)
    
    # Log JSON responses
    if 'application/json' in ct and 'district.in' in url:
        try:
            body = response.json()
            print('JSON keys:', list(body.keys()) if isinstance(body, dict) else type(body))
        except Exception:
            print('JSON parse failed')

page.on('response', log_response)
```

### 5.2 Response Handler Implementation

```python
def _handle_response(self, response: Response):
    try:
        ct = response.headers.get("content-type", "")
        if "application/json" not in ct:
            return
        url = response.url.lower()
        
        # Only intercept event-relevant endpoints
        if not any(x in url for x in ["/api/", "graphql", "events", "search", "activities"]):
            return
        
        data = response.json()
        extracted = self._parse_api_json(data)
        if extracted:
            self.intercepted_api_data.extend(extracted)
    except Exception:
        pass
```

---

## 6. EVENT DATA EXTRACTION METHODS

### 6.1 DOM-Based Extraction

**Event Cards Selector:**
```css
a[href*='/event/']
a[href*='/events/']
a[href*='/activities/']
a:has(h3)
a[class*='dds-h-full']
```

**Event Name:** From `<h1>` first element
```javascript
page.locator("h1").first.inner_text()
```

**Price:** Search for ₹ symbol
```javascript
page.locator("text=₹").first.inner_text()
```

**Date:** Regex pattern matching
```javascript
page.locator("text=/\\d{1,2}\\s+[A-Za-z]{3,}/").first
```

**Time:** Time pattern matching
```javascript
page.locator("text=/\\d{1,2}:\\d{2}\\s*(?:AM|PM|am|pm)/").first
```

**Venue:** Multiple fallback sources
```javascript
page.locator("text=Venue").locator("..").first
page.locator("text=Location").locator("..").first
page.locator("[class*=venue]").first
page.locator("section:has-text('Where') p").first
```

### 6.2 JSON-LD Schema Extraction (Structured Data)

```javascript
// Fallback for missing data
for ld in self._extract_json_ld(page):
    if "event" in str(ld.get("@type", "")).lower():
        name = ld.get("name")
        startDate = ld.get("startDate")
        description = ld.get("description")
        location = ld.get("location", {}).get("name")
```

---

## 7. EXTRACTED EVENT DATA STRUCTURE

### 7.1 Raw Event Object (From Scraping)

```python
{
    "name": "Event Name",
    "url": "https://www.district.in/event/slug",
    "event_link": "https://www.district.in/event/slug",
    "platform": "District",
    "city": "Hyderabad",
    "location": "Hyderabad",
    "date": "15 Jan 2025",
    "event_time": "7:00 PM",
    "price": "₹500",
    "venue": "Venue Name",
    "description": "Event description",
    "organizer": "District",
    "event_language": "-",
    "event_type": "-",
    "event_format": "-",
    "rating": "-"
}
```

### 7.2 Final Normalized Event (Global Schema)

```python
{
    'Event Name': "Event Name",
    'Date': "15 Jan 2025",
    'Time': "7:00 PM",
    'Price': "₹500",
    'Platform': "District",
    'Organizer': "District",
    'Language': "-",
    'Type': "-",
    'Format': "-",
    'City': "Hyderabad",
    'Venue': "Venue Name",
    'Rating': "-",
    'View Link': "https://www.district.in/event/slug"
}
```

---

## 8. VALIDATION & FILTERING

### 8.1 Event Rejection Criteria

Events are rejected if they match:

**Artist/Musician Pages:**
- Name contains: artist, singer, dj, rapper, band, performer, musician, concert
- Description is extensive (>500 chars) with artist keywords

**Wrong City:**
- Event explicitly mentions different city in name or venue
- City mapping: Bangalore ↔ Bengaluru, Delhi ↔ Delhi-NCR

**Invalid Data:**
- No event name provided
- Duplicate event name
- Invalid venue (placeholder text like "Select Location", "TBD", "Not Specified")

### 8.2 Placeholder Keywords (Skipped Venues)

```python
placeholder_keywords = [
    "select location",
    "select city",
    "not specified",
    "tbd",
    "to be announced",
    "venue details",
    "location details"
]
```

---

## 9. IMPLEMENTATION QUIRKS & ANTI-BOT HANDLING

### 9.1 Anti-Bot Measures Used

1. **Stealth Mode:** Remove webdriver flags
   ```javascript
   Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
   ```

2. **Headless False:** Use visible browser to avoid detection
   ```python
   "headless": False
   ```

3. **Realistic User Agent:** Chrome 126 on Windows
   ```
   Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
   ```

4. **Disable Automation Detection:**
   ```python
   "args": ["--disable-blink-features=AutomationControlled"]
   ```

5. **Strategic Delays:** Avoid rapid page navigation
   ```python
   page.wait_for_timeout(700)  # 700ms between events
   ```

6. **Page Health Checks:** Every 5 events
   ```python
   if idx % 5 == 0 and page.is_closed():
       break  # Stop if page crashes
   ```

### 9.2 Known Issues & Workarounds

| Issue | Symptom | Workaround |
|-------|---------|-----------|
| Connection closing | Page closed unexpectedly | Check `page.is_closed()` before navigation |
| Cloudflare block | 403/429 errors | Use Layer 3 Google fallback |
| Venue extraction | Missing venue data | Use JSON-LD schema as fallback |
| API rate limiting | Sparse API responses | Rely on DOM scraping instead |
| Artist page false positives | Musician bios appearing as events | Check description for artist keywords |

---

## 10. RECENT DEBUGGING OUTPUT

### Debug Files & Discoveries

| File | Discovery |
|------|-----------|
| `_debug_district_api.py` | Third-party proxy endpoint: `mpc-prod-24-s6uit34pua-uw.a.run.app` |
| `_debug_district_network.py` | Network interception of district.in API calls |
| `_debug_district_urls.py` | Tested URLs including `/api/events?city=` endpoint |
| `_tmp_debug_district_api.py` | Response status monitoring for events-related URLs |
| `_tmp_debug_district_api2.py` | GraphQL and JSON content-type filtering |

---

## 11. RECOMMENDATIONS FOR DIRECT API USAGE

### 11.1 If Using Direct API Instead of Scraping

**Potential API Structure (Inferred):**
```bash
GET https://www.district.in/api/events?city=hyderabad
Content-Type: application/json

Response:
{
  "events": [
    {
      "id": "event-id",
      "name": "Event Name",
      "slug": "event-slug",
      "date": "2025-01-15T19:00:00Z",
      "location": {
        "name": "Venue Name",
        "address": "Full Address",
        "lat": 17.369,
        "lng": 78.507
      },
      "price": {
        "min": 500,
        "max": 1000,
        "currency": "INR"
      },
      "image": "https://...",
      "description": "Event description"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20
  }
}
```

### 11.2 Rate Limiting Estimates

- **DOM Scraping:** ~1-2 seconds per event page
- **Scroll Loading:** ~1 second per scroll (6 scrolls typical)
- **Google Fallback:** ~3 seconds per search query

**Total per city:** ~5-10 minutes for 100 events

---

## 12. FILES REFERENCED

**Debug/Investigation Files:**
- `/backend/_debug_district.py`
- `/backend/_debug_district_api.py`
- `/backend/_debug_district_network.py`
- `/backend/_debug_district_network_home.py`
- `/backend/_debug_district_urls.py`
- `/backend/_tmp_debug_district_api.py`
- `/backend/_tmp_debug_district_api2.py`

**Implementation Files:**
- `/backend/agents/platforms.py` (DistrictAgent class)
- `/backend/agents/base_agent.py` (Response interception, multi-layer pipeline)
- `/backend/agents/scrapers.py` (scrape_district function)

**Alternative Scrapers:**
- `/backend/scrape_district_real_data.py`
- `/backend/scrape_district_multi_city.py`
- `/backend/scrape_district_agent.py`
- `/backend/scrape_district_alternative.py`

---

## Notes

- District.in appears to **not expose a public API** (all endpoints are internal/testing only)
- Current implementation is **100% browser-based DOM scraping** with network interception fallback
- Site employs **anti-bot measures** but allows legitimate browser access
- **Sitemap available** at `/events/search-sitemap/sitemap-events.xml` for URL discovery
- **Third-party aggregator** (`mpc-prod-24-s6uit34pua-uw.a.run.app`) may exist but purpose unclear
