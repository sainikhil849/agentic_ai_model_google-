from typing import Optional
from urllib.parse import urlparse
from datetime import date as date_type


INVALID_LINK_PATTERNS = [
    "/events",
    "/explore",
    "/category",
    "/search",
    "/home",
    "/index",
    "/?",
]


def is_valid_event(event: dict) -> tuple[bool, str]:
    """
    Validate a scraped event dict against all mandatory field rules.
    Returns (True, "") if valid, or (False, reason) if invalid.
    """
    required_fields = ["event_name", "event_date", "price", "organizer", "platform", "event_url", "description"]

    for field in required_fields:
        val = event.get(field)
        # For description, we allow "Not available"
        if field == "description" and (val is None or str(val).strip() == ""):
             return False, "Missing description"
        elif field != "description" and (val is None or str(val).strip() == "" or str(val).strip().lower() in ["none", "n/a", "tba", "tbd"]):
            if field == "event_date" and event.get("platform") in ["Urbanaut", "Sort My Scene", "Swiggy Scenes"] and val == "Unknown":
                # Special allowance for platforms with enrichment recovery
                continue
            if field == "price" and event.get("platform") in ["Sort My Scene", "Swiggy Scenes"] and (val == "N/A" or val == -1 or val == "-1"):
                # Sort My Scene and Swiggy Scenes price recovery allowance
                continue
            return False, f"Missing required field: {field}"

    # Price must be a valid integer >= -1 (0 = Free, -1 = Unavailable)
    try:
        price_val = int(event["price"])
        if price_val < -1:
            return False, "Negative price (less than -1)"
    except (ValueError, TypeError):
        return False, f"Invalid price value: {event['price']}"

    # Date must be YYYY-MM-DD or Unknown
    import re
    date_val = str(event["event_date"])
    if date_val != "Unknown" and not re.match(r"^\d{4}-\d{2}-\d{2}$", date_val):
        return False, f"Invalid date format: {date_val}"

    # Event URL must be a real page (not homepage/category)
    url = str(event["event_url"]).strip()
    if not url.startswith("http"):
        return False, "Event URL does not start with http"

    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if not path or path in ["", "/"]:
        return False, "Event URL appears to be a homepage"

    # Only block if the path is EXACTLY a known listing page or very short
    for pattern in INVALID_LINK_PATTERNS:
        clean_p = pattern.rstrip("/")
        if path == clean_p:
            return False, f"Event URL is a category/listing page: {url}"

    # Verify link has enough 'depth' to be an event (at least 2 path segments)
    path_parts = [p for p in path.split("/") if p]
    if len(path_parts) < 1 or (len(path_parts) == 1 and len(path_parts[0]) < 5):
        return False, f"Event URL too shallow to be an event: {url}"


    # Description must have substance
    desc = str(event["description"]).strip()
    if len(desc) < 2:
        return False, "Description too short"

    # Title must have substance
    title = str(event["event_name"]).strip()
    if len(title) < 2:
        return False, "Title too short"

    return True, ""


def filter_upcoming_events(events: list[dict]) -> list[dict]:
    """
    Keep events with event_date >= today. Drops parseable past dates.
    Unknown dates are kept (handled per-platform upstream where possible).
    """
    today = date_type.today()
    out: list[dict] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        ds = str(ev.get("event_date", "")).strip()
        if ds == "Unknown":
            out.append(ev)
            continue
        try:
            y, m, d = int(ds[:4]), int(ds[5:7]), int(ds[8:10])
            ed = date_type(y, m, d)
            if ed >= today:
                out.append(ev)
        except (ValueError, TypeError, IndexError):
            out.append(ev)
    return out


def normalize_pipeline_events(events: list[dict], location: str) -> list[dict]:
    """
    Ensure every event has safe defaults for the existing API schema (no None fields).
    Does not rename keys (event_date, platform, event_url stay as-is).
    """
    try:
        from utils.city_config import parse_city
    except Exception:
        def parse_city(loc: str) -> str:
            return (loc or "Hyderabad").split(",")[0].strip() or "Hyderabad"

    city = parse_city(location or "Hyderabad")
    out: list[dict] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        row = dict(ev)
        row["event_name"] = str(row.get("event_name") or "").strip() or "Untitled Event"
        row["event_date"] = str(row.get("event_date") or "").strip()
        row["venue"] = str(row.get("venue") or "").strip() or "Not specified"
        row["city"] = str(row.get("city") or "").strip() or city
        row["organizer"] = str(row.get("organizer") or "").strip() or "Unknown"
        row["platform"] = str(row.get("platform") or "").strip() or "Unknown"
        row["event_url"] = str(row.get("event_url") or "").strip()
        row["description"] = str(row.get("description") or "").strip() or "Not available"
        try:
            row["price"] = int(row["price"])
        except (TypeError, ValueError):
            row["price"] = -1
        if not row["event_url"]:
            continue
        out.append(row)
    return out


def deduplicate(events: list[dict]) -> list[dict]:
    """Remove duplicate events by (event_name, event_date, venue)."""
    seen = set()
    unique = []
    for ev in events:
        key = (
            str(ev.get("event_name", "")).lower().strip(),
            str(ev.get("event_date", "")).strip(),
            str(ev.get("venue", "")).lower().strip(),
        )

        if key not in seen:
            seen.add(key)
            unique.append(ev)
    return unique
