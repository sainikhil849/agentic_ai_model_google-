import re
from datetime import datetime, date
from typing import Optional


def extract_price(raw: str) -> Optional[int]:
    """
    Normalize price strings to the minimum integer INR value.
    - 'Free', 'RSVP', 'No Charge'  -> 0
    - 'Rs.499', 'Rs 499', 'INR 499'  -> 499
    - 'Rs.499 - Rs.1999'              -> 499  (minimum)
    - 'Starting from Rs.999'         -> 999
    Returns None if price cannot be determined.
    """
    if not raw:
        return None

    raw_lower = raw.lower().strip()

    # Free / RSVP patterns
    free_keywords = ["free", "rsvp", "no charge", "complimentary", "Rs.0", "rs 0", "inr 0"]
    if any(k in raw_lower for k in free_keywords):
        return 0

    # Extract all numbers from the string
    numbers = re.findall(r"[\d,]+", raw.replace(",", ""))
    if not numbers:
        return None

    values = []
    for n in numbers:
        try:
            values.append(int(n.replace(",", "")))
        except ValueError:
            continue

    if not values:
        return None

    return min(values)


def format_price(amount: Optional[int]) -> str:
    """Point 8: Standardize price extraction."""
    if amount is None or amount == -1:
        return "Not Mentioned"
    if amount == 0:
        return "Free"
    return f"Rs.{amount:,}"
