"""
Venue Data Validator and Formatter
Handles JSON-LD Place schema extraction and formats venue details for display
"""
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# ================================================================
# KNOWN VENUES DATABASE
# For venues that don't explicitly mention their city in the name
# ================================================================

KNOWN_VENUES = {
    "shilpakala vedika": {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "display_name": "Shilpakala Vedika: Hyderabad"
    },
    "boulder hills": {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "display_name": "Boulder Hills, Hyderabad"
    },
    "hitech city": {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India"
    },
    "madhapur": {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India"
    },
    "gachibowli": {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India"
    },
    "kondapur": {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India"
    },
    "jubilee enclave": {
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India"
    },
    "indiranagar": {
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India"
    },
    "koramangala": {
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India"
    },
    "whitefield": {
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India"
    },
    "jayanagar": {
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India"
    },
    "bandra": {
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India"
    },
    "andheri": {
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India"
    },
    "fort kochi": {
        "city": "Kochi",
        "state": "Kerala",
        "country": "India"
    },
    "cyber hub": {
        "city": "Gurugram",
        "state": "Haryana",
        "country": "India"
    }
}


def enhance_venue_with_location(venue_data: Optional[Dict], scraping_location: Optional[str] = "Hyderabad") -> Optional[Dict]:
    """
    Enhance venue data with location information.
    If venue name matches known venues, add city/state/country information.
    If venue lacks city info but we're scraping from a specific location, use that location.
    
    Args:
        venue_data: Venue dictionary to enhance
        scraping_location: Location we're scraping from (default: "Hyderabad")
    
    Returns:
        Enhanced venue dict or original if no enhancement needed
    """
    if not venue_data or not isinstance(venue_data, dict):
        return venue_data
    
    try:
        venue_name = str(venue_data.get("name", "")).strip()
        if not venue_name:
            return venue_data
        
        # Check against known venues database
        venue_name_lower = venue_name.lower()
        for known_venue_key, known_venue_info in KNOWN_VENUES.items():
            if known_venue_key in venue_name_lower:
                # Update venue with known location info
                if not venue_data.get("city"):
                    venue_data["city"] = known_venue_info.get("city", scraping_location or "Hyderabad")
                if not venue_data.get("state"):
                    venue_data["state"] = known_venue_info.get("state", "Telangana")
                if not venue_data.get("country"):
                    venue_data["country"] = known_venue_info.get("country", "India")
                
                logger.debug(f"Enhanced venue '{venue_name}' with known location: {venue_data.get('city')}")
                return venue_data
        
        # If no known venue match but city is missing and we have scraping location
        if not venue_data.get("city") and scraping_location:
            venue_data["city"] = scraping_location
            logger.debug(f"Enhanced venue '{venue_name}' with scraping location: {scraping_location}")
        
        return venue_data
    except Exception as e:
        logger.debug(f"Error enhancing venue with location: {e}")
        return venue_data


def validate_venue_data(venue_data: Optional[Dict]) -> Tuple[bool, str]:
    """
    Validate venue data structure from JSON-LD Place schema.
    
    Returns:
        (is_valid: bool, reason: str)
    """
    if not venue_data:
        return False, "No venue data provided"
    
    if not isinstance(venue_data, dict):
        return False, "Venue data must be a dictionary"
    
    # Check if it's a valid Place schema
    venue_type = venue_data.get("@type", "").lower()
    if venue_type and "place" not in venue_type:
        return False, f"Invalid @type: {venue_type}, expected Place"
    
    # Venue name is required
    venue_name = venue_data.get("name", "").strip()
    if not venue_name:
        return False, "Venue name is required"
    
    return True, "Valid venue data"


def extract_venue_from_json_ld(
    place_obj: Optional[Dict], scraping_location: Optional[str] = None
) -> Optional[Dict]:
    """
    Extract venue details from JSON-LD Place schema.
    
    Expected format:
    {
        "@type": "Place",
        "name": "Venue Name",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "India",
            "addressLocality": "Hyderabad",
            "streetAddress": "..."
        }
    }
    
    Returns:
        Formatted venue dict or None if invalid
    """
    if not place_obj or not isinstance(place_obj, dict):
        return None
    
    try:
        # Extract venue name
        venue_name = place_obj.get("name", "").strip()
        if not venue_name:
            return None
        
        # Extract address details
        address = place_obj.get("address", {})
        if isinstance(address, dict):
            street_address = address.get("streetAddress", "").strip()
            locality = address.get("addressLocality", "").strip()
            city = address.get("addressCity", "").strip() or locality
            state = address.get("addressRegion", "").strip()
            country = address.get("addressCountry", "").strip()
            postal_code = address.get("postalCode", "").strip()
            
            # If postal code not found in separate field, try to extract from streetAddress
            if not postal_code and street_address:
                import re
                # Match patterns like "500081" or "500081, India"
                postal_match = re.search(r'\b(\d{6})\b', street_address)
                if postal_match:
                    postal_code = postal_match.group(1)
        else:
            # Handle case where address is a string
            address_str = str(address).strip()
            return {
                "name": venue_name,
                "address": address_str,
                "full_display": f"{venue_name}, {address_str}"
            }
        
        # Build formatted venue dict
        venue_dict = {
            "name": venue_name,
            "street_address": street_address,
            "locality": locality,
            "city": city,
            "state": state,
            "country": country,
            "postal_code": postal_code,
            "address": address  # Keep original address object
        }
        
        # Build full display string
        display_parts = [venue_name]
        if street_address:
            display_parts.append(street_address)
        if state and state != city:
            display_parts.append(state)
        if postal_code:
            display_parts.append(postal_code)
        if country and country not in street_address:
            display_parts.append(country)
        
        venue_dict["full_display"] = ", ".join(display_parts)
        
        # Enhance with location information (handle venues without explicit city)
        scrape = scraping_location or "Hyderabad"
        venue_dict = enhance_venue_with_location(venue_dict, scraping_location=scrape)
        
        # Return the extracted venue dict if it has a name
        # (Don't validate the original place_obj here as it has different structure)
        if venue_dict.get("name"):
            return venue_dict
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting venue from JSON-LD: {e}")
        return None


def format_venue_for_display(venue_data: Optional[Dict], compact: bool = False) -> str:
    """
    Format venue data for clear dashboard and table display.
    
    Args:
        venue_data: Venue dictionary (from extract_venue_from_json_ld)
        compact: If True, return single-line format; if False, return multi-line
    
    Returns:
        Formatted venue string
    """
    if not venue_data:
        return "Not specified"
    
    if isinstance(venue_data, str):
        return venue_data.strip() or "Not specified"
    
    if not isinstance(venue_data, dict):
        return "Not specified"
    
    # Use full_display if available
    if venue_data.get("full_display"):
        display = venue_data.get("full_display", "")
        if compact:
            return display.replace(", ", " | ")
        return display
    
    # Fallback: build from components
    name = venue_data.get("name", "")
    street = venue_data.get("street_address", "")
    city = venue_data.get("city") or venue_data.get("locality", "")
    state = venue_data.get("state", "")
    postal = venue_data.get("postal_code", "")
    
    parts = [p for p in [name, street, city, state, postal] if p]
    
    if compact:
        return " | ".join(parts) if parts else "Not specified"
    else:
        # Multi-line format for display
        result = name
        if street:
            result += f"\n{street}"
        location_parts = [city, state, postal]
        location_parts = [p for p in location_parts if p]
        if location_parts:
            result += f"\n{', '.join(location_parts)}"
        return result if result else "Not specified"


def format_venue_for_excel(venue_data: Optional[Dict]) -> str:
    """
    Format venue data for Excel export (single line with clear structure).
    
    Returns:
        Single-line formatted venue string
    """
    return format_venue_for_display(venue_data, compact=True)


def get_venue_summary(venue_data: Optional[Dict]) -> str:
    """
    Get a one-line summary of venue for quick reference.
    
    Returns:
        Venue name and city in format: "Name, City"
    """
    if not venue_data:
        return "Not specified"
    
    if isinstance(venue_data, str):
        return venue_data.strip() or "Not specified"
    
    if isinstance(venue_data, dict):
        name = venue_data.get("name", "")
        city = venue_data.get("city") or venue_data.get("locality", "")
        
        if name and city:
            return f"{name}, {city}"
        elif name:
            return name
    
    return "Not specified"


def format_venue_for_bookmyshow(venue_data: Optional[Dict]) -> str:
    """
    Format venue data specifically for BookMyShow in compact form.
    Format: "Venue Name, Area, City" (e.g., "Heart Cup Coffee, Gachibowli, Hyderabad")
    
    Handles cases where:
    - Venue name includes area (e.g., "Heart Cup Coffee: Gachibowli") -> extract both
    - Venue name has colon/dash separators
    - Area needs to be extracted from street address
    
    Args:
        venue_data: Venue dictionary from extract_venue_from_json_ld
    
    Returns:
        Simple formatted venue string
    """
    if not venue_data:
        return "Not specified"
    
    if isinstance(venue_data, str):
        return venue_data.strip() or "Not specified"
    
    if not isinstance(venue_data, dict):
        return "Not specified"
    
    import re
    
    # Get venue components
    name = venue_data.get("name", "").strip()
    locality = venue_data.get("locality", "").strip()  # Area name
    city = venue_data.get("city", "").strip()
    street = venue_data.get("street_address", "").strip()
    
    # Extract area from venue name if it contains a colon or dash
    # E.g., "Heart Cup Coffee: Gachibowli" -> name="Heart Cup Coffee", area="Gachibowli"
    # But if it's "Academy: Hyderabad" (part is the city), just clean the city from name
    area = None
    if name and (":" in name or "-" in name or "-" in name):
        # Try to split by common separators
        parts = re.split(r'[\s:\-]+', name)
        if len(parts) >= 2:
            # Last part after separator
            potential_area = parts[-1].strip()
            if potential_area:
                # Check if it's the city - if so, remove it from name
                if potential_area.lower() == city.lower():
                    # Remove the city from the venue name
                    name = re.sub(rf'[\s:\-]+{re.escape(potential_area)}[\s]*$', '', name, flags=re.IGNORECASE).strip()
                # If it's a reasonable area name (not city, not all caps, has good length)
                elif (len(potential_area) > 2 and 
                      not potential_area.isupper() and
                      "floor" not in potential_area.lower() and
                      "street" not in potential_area.lower()):
                    area = potential_area
                    # Keep only the venue name part (before the separator)
                    name = re.sub(rf'[\s:\-]+{re.escape(potential_area)}[\s]*$', '', name, flags=re.IGNORECASE).strip()
    
    # If no area found yet, try to extract from street address
    if not area and street and city:
        # Look for common area keywords in the address (before city name)
        # Pattern: extract the part that comes before "Hyderabad" in the address
        # E.g., "...Sri Ram Nagar, Kondapur, Botanical Garden Road, ... Hyderabad..." -> extract "Kondapur"
        
        # Split street address by commas and look for area-like names before city
        address_parts = [p.strip() for p in street.split(",")]
        
        # Find city in the address
        city_lower = city.lower()
        city_index = -1
        for i, part in enumerate(address_parts):
            if part.lower() == city_lower or part.lower().startswith(city_lower):
                city_index = i
                break
        
        # If city found and there's something before it, that might be the area
        if city_index > 0:
            # Look backwards from city to find area-like names
            # Skip postal codes and short fragments
            for j in range(city_index - 1, -1, -1):
                part = address_parts[j].strip()
                # Skip numbers (postal codes), skip if too short or all caps (like state abbreviations)
                if part and not part.isdigit() and len(part) > 2 and not part.isupper():
                    # Check if it's not a street name or direction
                    if not any(x in part.lower() for x in ["floor", "street", "road", "lane", "avenue", "next to", "above", "opposite"]):
                        area = part
                        break
    
    # Also check if there's a known area in the locality
    if not area and locality and locality != city:
        area = locality
    
    # Build simple format: "Name, Area, City"
    parts = []
    if name:
        parts.append(name)
    if area and area != city:
        parts.append(area)
    if city:
        parts.append(city)
    
    if parts:
        return ", ".join(parts)
    
    return "Not specified"


def format_event_with_venue(event: dict) -> dict:
    """
    Update event dict to include properly formatted venue information
    for both display and storage.
    
    Modifies the event dict in-place to include:
    - venue_name: Display name only
    - venue_full: Full address display
    - venue_city: City name for filtering
    
    Returns:
        Updated event dict
    """
    venue = event.get("venue")
    platform = event.get("platform", "")
    
    if isinstance(venue, dict):
        # Check if it's a structured venue dict from extract_venue_from_json_ld (has 'name' key)
        if 'name' in venue and ('street_address' in venue or 'city' in venue):
            # Already a structured venue dict with extracted fields
            # Keep as dict for internal use, but also set formatted string for display
            event["venue_name"] = venue.get("name", "Not specified")
            event["venue_full"] = format_venue_for_display(venue, compact=False)
            event["venue_city"] = venue.get("city") or venue.get("locality", "Not specified")
            event["venue_summary"] = get_venue_summary(venue)
            # For main venue field, use BookMyShow format for better area extraction
            if not isinstance(event.get("venue"), str) or event.get("venue") == "Not specified":
                # Use BookMyShow formatter which extracts area from name and address
                event["venue"] = format_venue_for_bookmyshow(venue)
        else:
            # It's a JSON-LD Place dict (@type and address fields), extract it first
            extracted = extract_venue_from_json_ld(venue)
            if extracted:
                # Update the event's venue to be the formatted string
                # Use BookMyShow formatter which is smarter about area extraction
                event["venue"] = format_venue_for_bookmyshow(extracted)
                event["venue_name"] = extracted.get("name", "Not specified")
                event["venue_full"] = format_venue_for_display(extracted, compact=False)
                event["venue_city"] = extracted.get("city") or extracted.get("locality", "Not specified")
                event["venue_summary"] = get_venue_summary(extracted)
            else:
                event["venue"] = "Not specified"
                event["venue_name"] = "Not specified"
                event["venue_full"] = "Not specified"
                event["venue_summary"] = "Not specified"
                event["venue_city"] = "Not specified"
    else:
        # Simple string venue
        venue_str = str(venue or "").strip()
        if venue_str and venue_str.lower() != "not specified":
            # Ensure event["venue"] is always the formatted string (not dict or list)
            event["venue"] = venue_str
            event["venue_name"] = venue_str
            event["venue_full"] = venue_str
            event["venue_summary"] = venue_str
            # Try to extract city if format is "Name, City"
            if "," in venue_str:
                event["venue_city"] = venue_str.split(",")[-1].strip()
            else:
                event["venue_city"] = "Not specified"
        else:
            event["venue"] = "Not specified"
            event["venue_name"] = "Not specified"
            event["venue_full"] = "Not specified"
            event["venue_summary"] = "Not specified"
            event["venue_city"] = "Not specified"
    
    return event


# ================================================================
# PLACEHOLDER VENUE FILTERING - Removes generic/placeholder text
# ================================================================

PLACEHOLDER_VENUES = {
    "use current location",
    "to be announced",
    "tba",
    "not specified",
    "unknown",
    "not available",
    "n/a",
    "venue tbc",
    "venue to be confirmed",
    "venue pending",
    "location pending",
    "search for events",
    "select venue",
    "choose venue",
    "will be updated",
    "coming soon",
}


def is_placeholder_venue(venue_text: Optional[str]) -> bool:
    """
    Check if venue text is a placeholder or generic/app UI text.
    
    Returns:
        True if venue is placeholder/invalid, False if it's real venue text
    """
    if not venue_text or not isinstance(venue_text, str):
        return True
    
    clean_text = venue_text.strip().lower()
    
    # Exact match with placeholder list
    if clean_text in PLACEHOLDER_VENUES:
        return True
    
    # Starts with placeholder pattern
    for placeholder in PLACEHOLDER_VENUES:
        if clean_text.startswith(placeholder):
            return True
    
    # Very short (< 3 chars)
    if len(clean_text) < 3:
        return True
    
    # Contains only common words (likely UI text)
    common_words = {"the", "in", "at", "your", "location"}
    words = set(clean_text.split())
    if len(words) <= 2 and any(w in common_words for w in words):
        return True
    
    return False


def clean_venue_text(venue_text: Optional[str]) -> str:
    """
    Clean venue text by removing placeholder markers, normalizing format.
    Returns "Not specified" if venue is placeholder/empty.
    
    Args:
        venue_text: Raw venue text from scraping
    
    Returns:
        Cleaned venue text or "Not specified"
    """
    if not venue_text or not isinstance(venue_text, str):
        return "Not specified"
    
    clean = venue_text.strip()
    
    # If it's a placeholder, return Not specified
    if is_placeholder_venue(clean):
        return "Not specified"
    
    # Remove common prefixes
    for prefix in ["Venue: ", "Location: ", "Venue Name: "]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):].strip()
    
    # Remove trailing parentheses/brackets
    import re
    clean = re.sub(r"\s*\[.*?\]\s*$", "", clean)
    clean = re.sub(r"\s*\(.*?\)\s*$", "", clean)
    clean = clean.strip()
    
    # If after cleaning it's placeholder or too short, return Not specified
    if len(clean) < 3 or is_placeholder_venue(clean):
        return "Not specified"
    
    return clean


def filter_placeholder_venues(events: list) -> list:
    """
    Filter out events with placeholder venue text.
    For events with placeholder venues, try to extract real venue or mark as "Not specified".
    
    Args:
        events: List of event dicts
    
    Returns:
        List of events with cleaned venues (placeholder events marked as "Not specified")
    """
    filtered_events = []
    
    for event in events:
        if not isinstance(event, dict):
            filtered_events.append(event)
            continue
        
        venue = event.get("venue")
        
        # If venue is placeholder, clean it
        if isinstance(venue, str):
            cleaned = clean_venue_text(venue)
            event["venue"] = cleaned
        elif isinstance(venue, dict):
            # If it's a structured venue dict, validate it
            venue_name = venue.get("name", "")
            if is_placeholder_venue(venue_name):
                # Try to use address as fallback, else mark as Not specified
                address = venue.get("street_address", "")
                if address and not is_placeholder_venue(address):
                    event["venue"] = clean_venue_text(address)
                else:
                    event["venue"] = "Not specified"
        
        filtered_events.append(event)
    
    return filtered_events
