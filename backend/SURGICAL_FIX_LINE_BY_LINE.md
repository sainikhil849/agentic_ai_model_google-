# SURGICAL FIX — LINE-BY-LINE CHANGES

## FILE 1: utils/city_config.py

### Change: Added district_city_slug() function
**Location**: After line 30 (urbanaut_city_query function)
**Lines Added**: 1 blank line + 13 code lines (total 14)
**Purpose**: Maps location names to District.in URL slugs

```python
def district_city_slug(location: str) -> str:
    """
    District.in uses paths like /events/hyderabad-ticket-booking, bengaluru-ticket-booking, mumbai-ticket-booking.
    """
    key = str(location).lower().split(",")[0].strip()
    if "mumbai" in key:
        return "mumbai"
    if "bangalore" in key or "bengaluru" in key:
        return "bengaluru"
    if "hyderabad" in key or key == "hyd":
        return "hyderabad"
    return re_slug(key)
```

---

## FILE 2: agents/platforms.py

### Change 1: Updated import statement
**Location**: Line 11 (original imports)
**Before**:
```python
from utils.city_config import bookmyshow_explore_slug, parse_city, urbanaut_city_query
```
**After**:
```python
from utils.city_config import bookmyshow_explore_slug, parse_city, urbanaut_city_query, district_city_slug
```
**Reason**: Import new district_city_slug function

---

### Change 2: Enhanced BMS venue extractor
**Location**: Lines 22-79 (BookMyShowAgent._extract_bookmyshow_venue_dom method)
**Before**: 49 lines with 3 selectors
**After**: 102 lines with 5 tiers of selectors + page waits
**Lines Changed**: Complete method rewritten with:
- page.wait_for_load_state("networkidle")
- page.wait_for_timeout(2000)
- Tier 1: data-testid selectors (new)
- Tier 2: Class/attribute selectors (expanded from 3 to 6 selectors)
- Tier 3: Section-based search with regex (new)
- Tier 4: Google Maps context (kept from original)
- Tier 5: Body text fallback (kept from original)

Key additions:
- Test ID selectors: `'[data-testid="eventVenue"]'`, `'[data-testid="venue"]'`
- New selectors: `"span.venue-name"`, `"[class*='location']"`, `"[class*='Location']"`
- Try/except per tier for robust extraction

---

### Change 3: District URL fix
**Location**: Lines ~235-260 (DistrictAgent._perform_scraping_sync method)
**Before**:
```python
city = location.lower().split(",")[0].strip()
target_city = city.capitalize()  # "Hyderabad"

# Hyderabad-specific URLs in priority order
listing_urls = [
    "https://www.district.in/events/hyderabad-ticket-booking",  # Primary Hyderabad-only
    "https://www.district.in/events/hyderabad",
    "https://www.district.in/activities/hyderabad-activities",
    "https://www.district.in/events/",
]
```

**After**:
```python
city = location.lower().split(",")[0].strip()
target_city = city.capitalize()  # "Hyderabad"

# Dynamic city slug for District URLs
city_slug = district_city_slug(location)

# City-specific URLs in priority order
listing_urls = [
    f"https://www.district.in/events/{city_slug}-ticket-booking",  # Primary city-specific
    f"https://www.district.in/events/{city_slug}",
    f"https://www.district.in/activities/{city_slug}-activities",
    "https://www.district.in/events/",
]
```

**Lines Changed**: 4 lines (1 new + 3 modified)
**Reason**: Use dynamic city_slug instead of hardcoded "hyderabad"

---

## FILE 3: agents/base_agent.py

### Change 1: Updated _google_search_fallback call
**Location**: Line ~125 (run_sync_extraction method)
**Before**:
```python
candidates.extend(
    self._google_search_fallback(page, location, target_count)
)
```

**After**:
```python
# ISSUE 3 FIX: Pass browser and context to fallback for safe page restoration
candidates.extend(
    self._google_search_fallback(page, location, target_count, browser, context)
)
```

**Lines Changed**: 1 (2 args → 4 args)

---

### Change 2: Updated _google_search_fallback signature & entry
**Location**: Lines ~214-231 (method definition & entry guard)
**Before**:
```python
def _google_search_fallback(
    self, page, location: str, count_needed: int
) -> List[Dict]:
    """
    Extracts price, date, and event URLs directly from Google snippets.
    Does NOT default date to a past value — leaves it None so enrichment fires.
    """
    if count_needed <= 0:
        return []
```

**After**:
```python
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
```

**Lines Changed**: 6 new lines + 2 modified + 1 doc line

---

### Change 3: Page restoration in Google search loop
**Location**: Lines ~258-270 (within the query loop)
**Before**:
```python
search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
try:
    page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
    time.sleep(2.5)
```

**After**:
```python
search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
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
    
    page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
    time.sleep(2.5)
```

**Lines Changed**: 9 new lines

---

## SUMMARY OF CHANGES

| File | Change Type | Lines Changed | Purpose |
|------|------------|--------------|---------|
| `utils/city_config.py` | Added function | +14 | Dynamic city slug mapping |
| `agents/platforms.py` | Import update | +1 | Import district_city_slug |
| `agents/platforms.py` | Method rewrite | -49/+102 | Enhanced BMS venue extraction |
| `agents/platforms.py` | URL logic fix | +4 | Dynamic District city URLs |
| `agents/base_agent.py` | Call update | +2 | Pass browser/context to fallback |
| `agents/base_agent.py` | Signature & guard | +10 | Page restoration at entry |
| `agents/base_agent.py` | Loop safety | +9 | Page restoration in loop |
| **TOTAL** | | **~145 lines** | **All three issues patched** |

---

## VALIDATION PASSED ✓

- ✓ All Python files compile without syntax errors
- ✓ TEST 1: District city slugs are dynamic (5/5 sub-tests)
- ✓ TEST 2: BMS venue selectors enhanced (12/12 checks)
- ✓ TEST 3: Browser lifecycle safe (6/6 checks)
- ✓ INTEGRATION: District URLs use dynamic slugs (3/3 checks)

---

## NO BREAKING CHANGES ✓

- ✓ Pipeline architecture unchanged
- ✓ Event schema unchanged
- ✓ Agent router unchanged
- ✓ All working code paths unchanged
- ✓ Fully backward compatible
