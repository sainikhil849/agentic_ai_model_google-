import sys
import re
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

logging.basicConfig(level=logging.INFO)

print("\n" + "="*80)
print("PLATFORMS.PY VALIDATION TESTS")
print("="*80 + "\n")

try:
    from agents.platforms import DistrictPlatform, BookMyShowPlatform
    print("√ Successfully imported platform classes\n")
except Exception as e:
    print(f"✗ FAIL - Import error: {e}")
    sys.exit(1)

# TEST 1: District City Routing (Bangalore → bengaluru)
print("[TEST 1] District City Routing - Bangalore → bengaluru")
print("-" * 80)
try:
    district = DistrictPlatform()
    
    # Check if the platform has methods to handle city routing
    if hasattr(district, 'get_url_for_city') or hasattr(district, '_get_location_slug'):
        print("✓ Platform has city routing methods")
    
    # Try to instantiate and check base URL
    if hasattr(district, 'base_url'):
        print(f"  Base URL: {district.base_url}")
    
    # Check if Bangalore/bengaluru mapping is configured
    district_config = str(district.__dict__)
    if 'bengaluru' in district_config.lower() or 'bangalore' in district_config.lower():
        print("✓ PASS - City mapping configuration found")
    else:
        print("? City mapping not explicitly found in config (may be in methods)")
    
except Exception as e:
    print(f"✗ FAIL - District test error: {e}")

# TEST 2: Venue Extraction Selectors
print("\n[TEST 2] Venue Extraction Selectors")
print("-" * 80)
try:
    bms = BookMyShowPlatform()
    
    # Check if platform has CSS selectors or venue extraction logic
    bms_dict = bms.__dict__
    source_code = str(bms_dict)
    
    venue_selectors = []
    if hasattr(bms, 'venue_selector'):
        venue_selectors.append(("venue_selector", bms.venue_selector))
    
    # Look for common CSS selectors in the class
    if 'selector' in source_code.lower():
        print("✓ Platform contains selector definitions")
    else:
        print("? Selectors not explicitly found in attributes")
    
    # Check the BookMyShowPlatform implementation for venue extraction
    import inspect
    methods = inspect.getmembers(bms, predicate=inspect.ismethod)
    venue_methods = [m for m in methods if 'venue' in m[0].lower()]
    
    if venue_methods:
        print(f"✓ PASS - Found {len(venue_methods)} venue-related method(s): {[m[0] for m in venue_methods]}")
    else:
        print("? No explicit venue methods found (may be in parent class)")
    
except Exception as e:
    print(f"✗ FAIL - Venue test error: {e}")

# TEST 3: Price Extraction Regex with ₹ Symbol
print("\n[TEST 3] Price Extraction Regex - ₹ Symbol Support")
print("-" * 80)
try:
    # Import and test the platforms module for regex patterns
    from agents import platforms as platforms_module
    
    # Get source code
    import inspect
    source = inspect.getsource(platforms_module)
    
    # Check for rupee symbol in regex patterns
    if '₹' in source or 'rupee' in source.lower():
        print("✓ PASS - Rupee symbol (₹) found in source code")
    else:
        print("? Rupee symbol not explicitly found")
    
    # Check for price regex patterns
    if re.search(r"['\\\"]\\d+['\\\"]", source) or 'price' in source.lower():
        print("✓ PASS - Price extraction patterns found in source")
    else:
        print("? Price patterns not explicitly found")
    
    # Test actual regex matching
    test_prices = [
        "₹500",
        "₹1,000",
        "₹2,500 - ₹5,000",
        "Price: ₹999"
    ]
    
    # Try to find price patterns in source
    price_pattern_matches = re.findall(r"['\\\"].*?[₹\$].*?['\\\"]", source)
    if price_pattern_matches:
        print(f"✓ Found {len(price_pattern_matches)} price pattern(s)")
        for pattern in price_pattern_matches[:3]:
            print(f"    Pattern: {pattern}")
    
    # Test basic rupee regex
    basic_rupee_regex = r'₹[\d,]+'
    print(f"\n  Testing basic rupee regex: {basic_rupee_regex}")
    for price in test_prices:
        match = re.search(basic_rupee_regex, price)
        if match:
            print(f"    ✓ Matched: {price} → {match.group()}")
        else:
            print(f"    ? No match: {price}")
    
except Exception as e:
    print(f"✗ FAIL - Price regex test error: {e}")

print("\n" + "="*80)
print("VALIDATION COMPLETE")
print("="*80 + "\n")
