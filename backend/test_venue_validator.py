"""
Test Venue Validator and Formatter for BookMyShow

This script tests the venue extraction, validation, and formatting functionality
for proper display in dashboard and Excel sheets.
"""
import logging
from utils.venue_validator import (
    validate_venue_data,
    extract_venue_from_json_ld,
    format_venue_for_display,
    format_venue_for_excel,
    get_venue_summary,
    format_event_with_venue,
    enhance_venue_with_location
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_venue_validator():
    """Test venue data validation"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Venue Data Validation")
    logger.info("="*80)
    
    # Test case 1: Valid venue data from BookMyShow
    shilpakala_venue = {
        '@type': 'Place',
        'address': {
            '@type': 'PostalAddress',
            'addressCountry': 'India',
            'addressLocality': 'Hyderabad',
            'streetAddress': 'Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana 500081, India'
        },
        'name': 'Shilpakala Vedika: Hyderabad'
    }
    
    is_valid, reason = validate_venue_data(shilpakala_venue)
    logger.info(f"Shilpakala Venue Valid: {is_valid} | Reason: {reason}")
    assert is_valid, "Shilpakala venue should be valid"
    
    # Test case 2: Invalid venue - missing name
    invalid_venue = {
        '@type': 'Place',
        'address': {'streetAddress': 'Some Address'}
    }
    is_valid, reason = validate_venue_data(invalid_venue)
    logger.info(f"Invalid Venue (no name) Valid: {is_valid} | Reason: {reason}")
    assert not is_valid, "Venue without name should be invalid"
    
    # Test case 3: None venue
    is_valid, reason = validate_venue_data(None)
    logger.info(f"None Venue Valid: {is_valid} | Reason: {reason}")
    assert not is_valid, "None venue should be invalid"
    
    logger.info("✓ Venue validation tests passed!")


def test_venue_extraction():
    """Test JSON-LD venue extraction"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: JSON-LD Venue Extraction")
    logger.info("="*80)
    
    # Test case 1: BookMyShow Shilpakala Vedika
    shilpakala_venue = {
        '@type': 'Place',
        'address': {
            '@type': 'PostalAddress',
            'addressCountry': 'India',
            'addressLocality': 'Hyderabad',
            'streetAddress': 'Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana 500081, India'
        },
        'name': 'Shilpakala Vedika: Hyderabad'
    }
    
    extracted = extract_venue_from_json_ld(shilpakala_venue)
    logger.info(f"Extracted Venue: {extracted}")
    
    assert extracted is not None, "Should extract venue data"
    assert extracted['name'] == 'Shilpakala Vedika: Hyderabad', "Name should match"
    assert extracted['city'] == 'Hyderabad', "City should be extracted"
    assert extracted['postal_code'] == '500081', f"Postal code should be extracted, got: {extracted['postal_code']}"
    assert 'full_display' in extracted, "Full display should be generated"
    
    logger.info(f"  Name: {extracted['name']}")
    logger.info(f"  City: {extracted['city']}")
    logger.info(f"  Postal Code: {extracted['postal_code']}")
    logger.info(f"  Full Display: {extracted['full_display']}")
    
    logger.info("✓ Venue extraction tests passed!")


def test_venue_formatting():
    """Test venue formatting for display"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Venue Formatting for Display")
    logger.info("="*80)
    
    shilpakala_venue = {
        '@type': 'Place',
        'address': {
            '@type': 'PostalAddress',
            'addressCountry': 'India',
            'addressLocality': 'Hyderabad',
            'streetAddress': 'Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana 500081, India'
        },
        'name': 'Shilpakala Vedika: Hyderabad'
    }
    
    extracted = extract_venue_from_json_ld(shilpakala_venue)
    
    # Test compact format (for Excel)
    compact = format_venue_for_display(extracted, compact=True)
    logger.info(f"Compact Format (for Excel):\n{compact}\n")
    
    # Test full format (for dashboard)
    full = format_venue_for_display(extracted, compact=False)
    logger.info(f"Full Format (for Dashboard):\n{full}\n")
    
    # Test summary format
    summary = get_venue_summary(extracted)
    logger.info(f"Summary Format: {summary}\n")
    
    # Test Excel format
    excel = format_venue_for_excel(extracted)
    logger.info(f"Excel Format: {excel}\n")
    
    assert compact, "Compact format should not be empty"
    assert full, "Full format should not be empty"
    assert summary, "Summary should not be empty"
    assert excel, "Excel format should not be empty"
    
    logger.info("✓ Venue formatting tests passed!")


def test_event_formatting():
    """Test full event formatting with venue"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Event Formatting with Venue")
    logger.info("="*80)
    
    # Sample event with structured venue
    event = {
        "event_name": "Live Concert Event",
        "event_date": "2026-04-20",
        "price": 500,
        "platform": "BookMyShow",
        "city": "Hyderabad",
        "venue": {
            '@type': 'Place',
            'address': {
                '@type': 'PostalAddress',
                'addressCountry': 'India',
                'addressLocality': 'Hyderabad',
                'streetAddress': 'Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana 500081, India'
            },
            'name': 'Shilpakala Vedika: Hyderabad'
        },
        "description": "An exciting live concert event",
        "event_url": "https://in.bookmyshow.com/events/test-concert"
    }
    
    formatted = format_event_with_venue(event)
    
    logger.info(f"Original Venue Type: {type(event.get('venue'))}")
    logger.info(f"Venue Name: {formatted.get('venue_name')}")
    logger.info(f"Venue Full: {formatted.get('venue_full')}")
    logger.info(f"Venue City: {formatted.get('venue_city')}")
    logger.info(f"Venue Summary: {formatted.get('venue_summary')}")
    
    assert formatted['venue_name'] == 'Shilpakala Vedika: Hyderabad'
    assert formatted['venue_city'] == 'Hyderabad'
    # Summary format: "Name, City"
    assert formatted['venue_summary'] == 'Shilpakala Vedika: Hyderabad, Hyderabad', f"Expected 'Shilpakala Vedika: Hyderabad, Hyderabad', got: {formatted['venue_summary']}"
    
    logger.info("✓ Event formatting tests passed!")


def test_edge_cases():
    """Test edge cases"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Edge Cases")
    logger.info("="*80)
    
    # Test case 1: String venue (fallback)
    event = {
        "venue": "Shilpakala Vedika, Hyderabad",
        "event_name": "Test Event",
        "event_date": "2026-04-20",
        "price": 0,
        "platform": "Test",
        "city": "Hyderabad",
        "description": "Test",
        "event_url": "https://test.com"
    }
    
    formatted = format_event_with_venue(event)
    logger.info(f"String Venue - Name: {formatted['venue_name']}, City: {formatted['venue_city']}")
    assert formatted['venue_name'] == "Shilpakala Vedika, Hyderabad"
    
    # Test case 2: None venue
    event['venue'] = None
    formatted = format_event_with_venue(event)
    logger.info(f"None Venue - Name: {formatted['venue_name']}")
    assert formatted['venue_name'] == "Not specified"
    
    # Test case 3: Empty string venue
    event['venue'] = ""
    formatted = format_event_with_venue(event)
    logger.info(f"Empty Venue - Name: {formatted['venue_name']}")
    assert formatted['venue_name'] == "Not specified"
    
    logger.info("✓ Edge case tests passed!")


def test_location_enhancement():
    """Test venue location enhancement for known venues without explicit city"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Location Enhancement for Known Venues")
    logger.info("="*80)
    
    # Test case 1: Boulder Hills (known venue without explicit Hyderabad mention)
    boulder_hills = {
        "@type": "Place",
        "name": "Boulder Hills",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "India",
            "streetAddress": "Boulder Hills, Hyderabad"
        }
    }
    
    enhanced = enhance_venue_with_location(boulder_hills, scraping_location="Hyderabad")
    logger.info(f"Boulder Hills Enhanced - City: {enhanced.get('city')}")
    assert enhanced.get('city') == 'Hyderabad', "Boulder Hills should have Hyderabad as city"
    
    # Test case 2: Shilpakala Vedika variant (without Hyderabad in name)
    shilpakala_variant = {
        "@type": "Place",
        "name": "Shilpakala Vedika",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "India",
            "streetAddress": "Shilparamam, Hitech City"
        }
    }
    
    enhanced = enhance_venue_with_location(shilpakala_variant, scraping_location="Hyderabad")
    logger.info(f"Shilpakala Vedika Enhanced - City: {enhanced.get('city')}, State: {enhanced.get('state')}")
    assert enhanced.get('city') == 'Hyderabad', "Shilpakala Vedika should have Hyderabad as city"
    assert enhanced.get('state') == 'Telangana', "State should be Telangana"
    
    # Test case 3: Unknown venue with location fallback
    unknown_venue = {
        "@type": "Place",
        "name": "Some Random Venue",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "India"
        }
    }
    
    enhanced = enhance_venue_with_location(unknown_venue, scraping_location="Hyderabad")
    logger.info(f"Unknown Venue Enhanced - City: {enhanced.get('city')}")
    assert enhanced.get('city') == 'Hyderabad', "Unknown venue should fallback to scraping location"
    
    logger.info("✓ Location enhancement tests passed!")


def test_excel_export_format():
    """Test Excel export format"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Excel Export Format")
    logger.info("="*80)
    
    from utils.excel_exporter import export_to_excel
    
    # Sample events with different venue types
    events = [
        {
            "event_name": "BookMyShow Concert",
            "event_date": "2026-04-20",
            "price": 500,
            "platform": "BookMyShow",
            "city": "Hyderabad",
            "venue": {
                '@type': 'Place',
                'address': {
                    '@type': 'PostalAddress',
                    'addressCountry': 'India',
                    'addressLocality': 'Hyderabad',
                    'streetAddress': 'Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana 500081, India'
                },
                'name': 'Shilpakala Vedika: Hyderabad'
            },
            "description": "An exciting live concert",
            "event_url": "https://in.bookmyshow.com/events/concert",
            "organizer": "BookMyShow",
            "venue_name": "Shilpakala Vedika: Hyderabad",
            "venue_full": "Shilpakala Vedika: Hyderabad, Shilparamam, Hitech, Hitech City Rd, Jubilee Enclave, Hyderabad, Telangana, 500081, India",
            "venue_city": "Hyderabad",
            "venue_summary": "Shilpakala Vedika: Hyderabad, Hyderabad"
        }
    ]
    
    # Export to test file
    try:
        export_to_excel(events, "exports/test_venue_export.xlsx")
        logger.info("✓ Excel export successful!")
        logger.info("  File: exports/test_venue_export.xlsx")
    except Exception as e:
        logger.error(f"✗ Excel export failed: {e}")


if __name__ == "__main__":
    logger.info("\n" + "█"*80)
    logger.info("█ VENUE VALIDATOR & FORMATTER TESTS")
    logger.info("█"*80)
    
    try:
        test_venue_validator()
        test_venue_extraction()
        test_venue_formatting()
        test_event_formatting()
        test_edge_cases()
        test_location_enhancement()
        test_excel_export_format()
        
        logger.info("\n" + "█"*80)
        logger.info("█ ALL TESTS PASSED! ✓")
        logger.info("█"*80 + "\n")
        
    except AssertionError as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
