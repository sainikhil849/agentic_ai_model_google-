"""
Canonical city names and platform-specific URL slugs for multi-city scraping.
"""
from __future__ import annotations

from typing import Tuple


def parse_city(location: str) -> str:
    """First segment of location string, title-cased for display."""
    if not location or not str(location).strip():
        return "Hyderabad"
    part = str(location).split(",")[0].strip()
    if not part:
        return "Hyderabad"
    return part[:1].upper() + part[1:].lower() if len(part) > 1 else part.upper()


def bookmyshow_explore_slug(location: str) -> str:
    """
    BookMyShow uses paths like /explore/events-hyderabad, events-bengaluru, events-mumbai.
    """
    key = str(location).lower().split(",")[0].strip()
    SLUG_MAP = {
        "mumbai": "mumbai", "bombay": "mumbai",
        "bangalore": "bengaluru", "bengaluru": "bengaluru",
        "hyderabad": "hyderabad", "hyd": "hyderabad",
        "delhi": "delhi-ncr", "new delhi": "delhi-ncr",
        "pune": "pune", "chennai": "chennai",
        "kolkata": "kolkata", "calcutta": "kolkata",
        "ahmedabad": "ahmedabad",
        "goa": "goa",
        "jaipur": "jaipur",
        "kochi": "kochi", "cochin": "kochi",
        "noida": "noida",
        "gurgaon": "gurugram", "gurugram": "gurugram",
    }
    if key in SLUG_MAP:
        return SLUG_MAP[key]
    # default: slugify simple ascii
    return re_slug(key)


def urbanaut_city_query(location: str) -> str:
    """Query param for urbanaut.app experiences listing (?city=...)."""
    key = str(location).lower().split(",")[0].strip()
    CITY_MAP = {
        "mumbai": "mumbai", "bombay": "mumbai",
        "bangalore": "bengaluru", "bengaluru": "bengaluru",
        "hyderabad": "hyderabad", "hyd": "hyderabad",
        "delhi": "delhi", "new delhi": "delhi",
        "pune": "pune", "chennai": "chennai",
        "kolkata": "kolkata", "calcutta": "kolkata",
        "ahmedabad": "ahmedabad",
        "goa": "goa",
        "jaipur": "jaipur",
        "kochi": "kochi", "cochin": "kochi",
    }
    if key in CITY_MAP:
        return CITY_MAP[key]
    return re_slug(key)


def district_city_slug(location: str) -> str:
    """
    District.in uses paths like /events/hyderabad-ticket-booking.
    """
    key = str(location).lower().split(",")[0].strip()
    
    # Expanded city mapping for District
    CITY_MAP = {
        "bangalore": "bengaluru",
        "bengaluru": "bengaluru",
        "mumbai": "mumbai",
        "hyderabad": "hyderabad",
        "hyd": "hyderabad",
        "delhi ncr": "delhi-ncr",
        "delhi": "delhi",
        "noida": "noida",
        "gurgaon": "gurgaon",
        "gurugram": "gurgaon"
    }
    
    if key in CITY_MAP:
        return CITY_MAP[key]
        
    return re_slug(key)


def re_slug(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_"):
            out.append("-")
    slug = "".join(out).strip("-")
    return slug or "hyderabad"


def get_city_aliases(city: str) -> list[str]:
    """Returns a list of search aliases for a given canonical city name."""
    sel = str(city).lower().split(",")[0].strip()
    
    ALIAS_MAP = {
        "hyderabad": ["hyderabad", "secunderabad", "telangana", "cyberabad", "gachibowli", "hitech city", "madhapur", "kondapur", "nanakramguda", "financial district", "kokapet", "manikonda", "jubilee hills", "banjara hills", "begumpet", "somajiguda", "kukatpally", "miyapur", "tellapur", "nallagandla", "ameerpet", "tarnaka", "uppal", "dilsukhnagar", "l.b. nagar", "kothapet", "nagole", "hafeezpet", "chandanagar"],
        "hyd": ["hyderabad", "secunderabad", "telangana", "cyberabad", "gachibowli", "hitech city", "madhapur", "kondapur", "nanakramguda", "financial district", "kokapet", "manikonda", "jubilee hills", "banjara hills", "begumpet", "somajiguda", "kukatpally", "miyapur", "tellapur", "nallagandla", "ameerpet", "tarnaka", "uppal", "dilsukhnagar", "l.b. nagar", "kothapet", "nagole", "hafeezpet", "chandanagar"],
        "mumbai": ["mumbai", "bombay", "navi mumbai", "bandra", "andheri", "juhu", "powai", "worli", "colaba", "borivali", "malad", "thane", "lower parel", "dadar", "chembur", "vashi", "belapur", "nerul", "kharghar", "dahisar", "kandivali", "goregaon", "jogeshwari", "vile parle", "santacruz", "khar", "mahim", "sion", "mulund", "ghatkopar", "vikhroli"],
        "bombay": ["mumbai", "bombay", "navi mumbai", "bandra", "andheri", "juhu", "powai", "worli", "colaba", "borivali", "malad", "thane", "lower parel", "dadar", "chembur", "vashi", "belapur", "nerul", "kharghar", "dahisar", "kandivali", "goregaon", "jogeshwari", "vile parle", "santacruz", "khar", "mahim", "sion", "mulund", "ghatkopar", "vikhroli"],
        "bangalore": ["bangalore", "bengaluru", "whitefield", "koramangala", "indiranagar", "karnataka", "hsr layout", "bellandur", "marathahalli", "electronic city", "sarjapur", "jayanagar", "jp nagar", "mg road", "hebbal", "yelahanka", "bannerghatta", "rajajinagar", "malleshwaram", "basavanagudi", "btm layout", "kammanahalli", "kalyan nagar", "hennur", "thanisandra", "bagmane tech park", "outer ring road", "domlur", "cv raman nagar"],
        "bengaluru": ["bangalore", "bengaluru", "whitefield", "koramangala", "indiranagar", "karnataka", "hsr layout", "bellandur", "marathahalli", "electronic city", "sarjapur", "jayanagar", "jp nagar", "mg road", "hebbal", "yelahanka", "bannerghatta", "rajajinagar", "malleshwaram", "basavanagudi", "btm layout", "kammanahalli", "kalyan nagar", "hennur", "thanisandra", "bagmane tech park", "outer ring road", "domlur", "cv raman nagar"],
        "delhi": ["delhi", "new delhi", "ncr", "dwarka", "rohini", "saket", "connaught place", "hauz khas", "gurgaon", "noida", "okhla", "chanakyapuri", "vasant kunj", "lajpat nagar", "karol bagh", "pitampura"],
        "kolkata": ["kolkata", "calcutta", "salt lake", "new town", "park street", "behala", "tollygunge", "kasba", "dum dum"],
        "calcutta": ["kolkata", "calcutta", "salt lake", "new town", "park street", "behala", "tollygunge", "kasba", "dum dum"],
        "kochi": ["kochi", "cochin", "ernakulam", "kakkanad", "edappally", "vytilla", "aluva"],
        "cochin": ["kochi", "cochin", "ernakulam", "kakkanad", "edappally", "vytilla", "aluva"],
        "gurgaon": ["gurgaon", "gurugram", "cyber city", "sector", "sohna road", "dlf phase"],
        "gurugram": ["gurgaon", "gurugram", "cyber city", "sector", "sohna road", "dlf phase"],
        "ahmedabad": ["ahmedabad", "gandhinagar", "satellite", "prahlad nagar", "vastrapur", "bodakdev"],
        "goa": ["goa", "panjim", "panaji", "margao", "calangute", "candolim", "anjuna", "vagator", "arambol", "morjim", "assagao"],
        "jaipur": ["jaipur", "rajasthan", "rajastan", "malviya nagar", "vaishali nagar", "mansarovar", "c-scheme"],
        "chennai": ["chennai", "madras", "t-nagar", "adyar", "velachery", "mylapore", "anna nagar", "guindy", "omr", "ecr", "perungudi", "thoraipakkam", "sholinganallur", "karapakkam", "neelankarai", "akkarai", "injambakkam", "porur", "poonamallee", "ambattur"],
        "pune": ["pune", "koregaon park", "viman nagar", "baner", "hinjewadi", "magarpatta", "kothrud", "kalyani nagar", "pimple saudagar", "wakad", "pimpri", "chinchwad", "hadapsar", "kharadi", "kondhwa", "wanowrie", "pashan", "bavdhan"],
        "noida": ["noida", "greater noida", "sector", "indrapuram"],
    }
    
    return ALIAS_MAP.get(sel, [sel])


def venue_city_matches_selection(venue_city: str, selected_location: str) -> bool:
    """
    Returns True if venue_city is unknown/not specified or matches selected city
    (handles Hyderabad / Mumbai / Bangalore / Bengaluru aliases).
    """
    if not venue_city or str(venue_city).strip().lower() in ("not specified", "n/a", ""):
        return True

    vc = str(venue_city).lower()
    aliases = get_city_aliases(selected_location)
    sel = str(selected_location).lower().split(",")[0].strip()

    return any(x in vc for x in aliases) or sel in vc or vc in sel
