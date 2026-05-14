import re
from datetime import datetime, date
from typing import Optional
import dateutil.parser as dparser


MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}


def extract_date(raw: str) -> Optional[str]:
    """
    Parse any date string to YYYY-MM-DD.
    If multiple dates exist, return the nearest upcoming one.
    Returns None if no date can be parsed.
    """
    if not raw:
        return None

    raw = raw.strip()
    today = date.today()
    found_dates = []

    # Try direct ISO
    iso_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", raw)
    if iso_match:
        try:
            d = datetime.strptime(iso_match.group(1).replace("/", "-"), "%Y-%m-%d").date()
            found_dates.append(d)
        except ValueError:
            pass

    # Try natural language with ordinals and optional year: "14th April 2026", "April 14th", "14 Apr"
    # m[0]=DD, m[1]=Ordinal, m[2]=Month, m[3]=Year, m[4]=Month, m[5]=DD, m[6]=Ordinal, m[7]=Year
    natural = re.findall(
        r"(\d{1,2})(st|nd|rd|th)?\s+([A-Za-z]{3,9})(?:\s+,?\s*(\d{4}))?|"
        r"([A-Za-z]{3,9})\s+(\d{1,2})(st|nd|rd|th)?(?:\s+,?\s*(\d{4}))?",
        raw, re.I
    )
    for m in natural:
        try:
            current_year = today.year
            if m[0]:  # DD Mon [YYYY]
                d, mon, y = m[0], m[2].lower()[:3], m[3]
                year = int(y) if y else current_year
                month = MONTHS.get(mon)
                if month:
                    parsed_date = date(year, month, int(d))
                    # If year is missing, do not assume next year for past dates.
                    found_dates.append(parsed_date)
            else:  # Mon DD [YYYY]
                mon, d, y = m[4].lower()[:3], m[5], m[7]
                year = int(y) if y else current_year
                month = MONTHS.get(mon)
                if month:
                    parsed_date = date(year, month, int(d))
                    found_dates.append(parsed_date)
        except (ValueError, KeyError):
            continue

    # Try dateutil as fallback
    if not found_dates:
        try:
            parsed = dparser.parse(raw, fuzzy=True)
            found_dates.append(parsed.date())
        except Exception:
            pass

    if not found_dates:
        return None

    # Filter to upcoming dates, take nearest; if all past, return closest future
    upcoming = [d for d in found_dates if d >= today]
    if upcoming:
        return str(min(upcoming))

    # If all dates are past, still return nearest
    return str(max(found_dates))
