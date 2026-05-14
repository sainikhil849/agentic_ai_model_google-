"""
Location Validator - Normalizes and confirms user input location
Maps states/regions to cities, handles aliases, validates before scraping
"""

import logging

logger = logging.getLogger(__name__)

# State/Region to Primary City Mapping
STATE_TO_CITIES = {
    "karnataka": {
        "primary": "Bangalore",
        "aliases": ["bengaluru", "bangalore", "karnataka"]
    },
    "maharashtra": {
        "primary": "Mumbai",
        "aliases": ["mumbai", "maharashtra"]
    },
    "delhi": {
        "primary": "Delhi",
        "aliases": ["delhi", "delhi ncr", "ncr", "new delhi"]
    },
    "telangana": {
        "primary": "Hyderabad",
        "aliases": ["hyderabad", "telangana", "hyd"]
    },
    "tamil nadu": {
        "primary": "Chennai",
        "aliases": ["chennai", "tamil nadu", "madras"]
    },
    "west bengal": {
        "primary": "Kolkata",
        "aliases": ["kolkata", "west bengal", "calcutta"]
    },
    "goa": {
        "primary": "Goa",
        "aliases": ["goa"]
    },
    "punjab": {
        "primary": "Chandigarh",
        "aliases": ["chandigarh", "punjab"]
    },
    "rajasthan": {
        "primary": "Jaipur",
        "aliases": ["jaipur", "rajasthan"]
    },
    "gujarat": {
        "primary": "Ahmedabad",
        "aliases": ["ahmedabad", "gujarat", "surat"]
    },
    "kerala": {
        "primary": "Kochi",
        "aliases": ["kochi", "kerala", "cochin", "ernakulam"]
    },
}

# City Aliases (for direct city inputs)
CITY_ALIASES = {
    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "karnataka": "Bangalore",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "ncr": "Delhi",
    "delhi ncr": "Delhi",
    "pune": "Pune",
    "goa": "Goa",
    "chennai": "Chennai",
    "madras": "Chennai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "jaipur": "Jaipur",
    "rajasthan": "Jaipur",
    "rajastan": "Jaipur",
    "chandigarh": "Chandigarh",
    "ahmedabad": "Ahmedabad",
    "noida": "Noida",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "ernakulam": "Kochi",
}

SUPPORTED_CITIES = [
    "Hyderabad", "Bangalore", "Mumbai", "Delhi", "Pune", "Goa", 
    "Chennai", "Kolkata", "Jaipur", "Chandigarh", "Ahmedabad", "Noida", "Gurugram", "Kochi"
]


def normalize_location(user_input: str) -> tuple[str, bool]:
    """
    Normalize user location input to a supported city.
    
    Args:
        user_input: Raw user input (e.g., "Karnataka", "bangalore", "delhi ncr")
    
    Returns:
        tuple: (normalized_city, is_valid)
            - normalized_city: Confirmed city name (e.g., "Bangalore")
            - is_valid: Whether location is supported
    """
    if not user_input or not isinstance(user_input, str):
        return "Hyderabad", False
    
    # Clean input
    raw = user_input.strip().lower()
    
    # Remove common suffixes
    raw = raw.replace(", india", "").replace(" india", "").strip()
    
    # Try direct city alias match first
    if raw in CITY_ALIASES:
        confirmed_city = CITY_ALIASES[raw]
        logger.info(f"[OK] Location normalized: '{user_input}' -> '{confirmed_city}'")
        return confirmed_city, True
    
    # Try state/region mapping
    for state, info in STATE_TO_CITIES.items():
        if raw == state or raw in [alias.lower() for alias in info["aliases"]]:
            primary = info["primary"]
            logger.info(f"[OK] Location mapped: '{user_input}' (State) -> '{primary}' (City)")
            return primary, True
    
    # Check if it's a partial/typo match
    for city in SUPPORTED_CITIES:
        city_lower = city.lower()
        if raw.startswith(city_lower[:3]) and len(raw) >= 3:
            logger.warning(f"[WARN]  Fuzzy match: '{user_input}' -> '{city}' (assumed)")
            return city, True
    
    # Not found - return default
    logger.error(f"[X] Unsupported location: '{user_input}' (using default: Hyderabad)")
    return "Hyderabad", False


def validate_location(location: str) -> tuple[bool, str]:
    """
    Validate if location is in supported cities.
    
    Returns:
        tuple: (is_valid, message)
    """
    if not location:
        return False, "Location is empty"
    
    clean_loc = location.strip()
    
    # Extract city name (first part before comma if any)
    city = clean_loc.split(",")[0].strip()
    
    if city not in SUPPORTED_CITIES:
        supported_str = ", ".join(SUPPORTED_CITIES)
        return False, f"Location '{city}' not supported. Supported: {supported_str}"
    
    return True, f"[OK] Location confirmed: {city}"


def get_location_with_confirmation(user_input: str) -> str:
    """
    Get and confirm location from user input.
    Handles mapping and validation before returning.
    
    Args:
        user_input: Raw user location input
    
    Returns:
        Confirmed city name
    """
    # Step 1: Normalize
    normalized_city, is_valid = normalize_location(user_input)
    
    # Step 2: Validate
    is_supported, message = validate_location(normalized_city)
    
    logger.info(message)
    
    if is_supported:
        logger.info(f"[OK] LOCATION CONFIRMED: {normalized_city}")
        return normalized_city
    else:
        logger.error(f"[ERROR] LOCATION REJECTED: {message}")
        logger.info(f"Using default: Hyderabad")
        return "Hyderabad"


def print_supported_locations():
    """Print all supported locations for reference"""
    print("\n" + "="*60)
    print("SUPPORTED LOCATIONS:")
    print("="*60)
    
    print("\nDirect City Names:")
    for city in SUPPORTED_CITIES:
        print(f"  * {city}")
    
    print("\nState/Region Mappings:")
    for state, info in STATE_TO_CITIES.items():
        primary = info["primary"]
        aliases = ", ".join(info["aliases"][:2])
        print(f"  * {state.title()} -> {primary} (aliases: {aliases})")
    
    print("\n" + "="*60)
