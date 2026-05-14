"""Debug venue format for Test 1"""
from utils.venue_validator import format_venue_for_bookmyshow, extract_venue_from_json_ld

venue_data = {
    "@type": "Place",
    "name": "Heart Cup Coffee: Gachibowli",
    "address": {
        "@type": "PostalAddress",
        "addressCountry": "India",
        "addressLocality": "Hyderabad",
        "streetAddress": "Old Mumbai Highway, Gachibowli, Hyderabad, Telangana 500032, India"
    }
}

# Extract venue
extracted = extract_venue_from_json_ld(venue_data)
print(f"Extracted venue: {extracted}")
print(f"\nVenue components:")
print(f"  name: {extracted.get('name')}")
print(f"  locality: {extracted.get('locality')}")
print(f"  city: {extracted.get('city')}")

# Format for BookMyShow
formatted = format_venue_for_bookmyshow(extracted)
print(f"\nFormatted for BookMyShow: {formatted}")
print(f"Expected: Heart Cup Coffee, Gachibowli, Hyderabad")
print(f"Match: {formatted == 'Heart Cup Coffee, Gachibowli, Hyderabad'}")
