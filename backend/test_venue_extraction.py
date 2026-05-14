"""
Test venue extraction to ensure it's not returning None when it shouldn't
"""
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from utils.venue_validator import extract_venue_from_json_ld

test_venues = [
    {
        "name": "Heart Cup Coffee: Gachibowli",
        "@type": "Place",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "India",
            "addressLocality": "Hyderabad",
            "streetAddress": "Old Mumbai Highway, Gachibowli, Hyderabad, Telangana 500032"
        }
    },
    {
        "name": "Music Academy: Kondapur",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "India",
            "addressLocality": "Hyderabad",
            "streetAddress": "3rd Floor, Sangeetha, Kondapur, Hyderabad, Telangana 500084"
        }
    },
    {
        "name": "Nirvana Music and Dance Academy: Hyderabad",
        "address": {
            "addressCountry": "India",
            "addressLocality": "Hyderabad",
            "streetAddress": "3rd Floor, Sangeetha Land Mark, Sri Ram Nagar, Kondapur, Botanical Garden Road, Above Dry Fruits Den, Opposite to Ghanshyam Super Market, Hyderabad, Telangana 500084, India"
        }
    },
]

print("\n" + "="*80)
print("VENUE EXTRACTION TEST - Checking for None returns")
print("="*80 + "\n")

for i, venue in enumerate(test_venues, 1):
    print(f"TEST {i}: {venue.get('name')}")
    print("-" * 80)
    
    extracted = extract_venue_from_json_ld(venue)
    
    if extracted is None:
        print(f"❌ ERROR: Venue extraction returned None!")
        print(f"Input venue: {venue}\n")
    elif isinstance(extracted, dict):
        print(f"✅ Extracted successfully")
        print(f"Venue name: {extracted.get('name')}")
        print(f"Venue city: {extracted.get('city')}")
        print(f"Venue address: {extracted.get('street_address')}\n")
    else:
        print(f"⚠️  Unexpected type: {type(extracted)}\n")
