"""
Final integration test: Verify that scraping works end-to-end with optional fields.
"""
import asyncio
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from pipeline_controller import PipelineController

async def final_integration_test():
    """Run a quick pipeline test to verify everything works together."""
    print("\n" + "="*70)
    print("FINAL INTEGRATION TEST: Full Pipeline with Optional Fields")
    print("="*70 + "\n")
    
    controller = PipelineController()
    
    # Test with a small subset to keep test time reasonable
    result = await controller.run_pipeline(
        location="Hyderabad",
        max_events=5,
        target_platforms=["District"],  # Use just one fast platform
        category=None,
        max_price=None,
    )
    
    print(f"Pipeline returned {len(result)} events\n")
    
    if not result:
        print("WARNING: No events returned from pipeline")
        return
    
    # Display first event with all fields
    ev = result[0]
    print("Sample Event with all fields:")
    print("-" * 70)
    print(f"Event Name: {ev.get('event_name', 'N/A')}")
    print(f"Date: {ev.get('event_date', 'N/A')}")
    print(f"Price: INR {ev.get('price', 'N/A')}")
    print(f"Organizer: {ev.get('organizer', 'N/A')}")
    print(f"Platform: {ev.get('platform', 'N/A')}")
    print(f"Venue: {ev.get('venue', 'N/A')}")
    print(f"URL: {ev.get('event_url', 'N/A')[:60]}...")
    print(f"City: {ev.get('city', 'N/A')}")
    print(f"Description: {ev.get('description', 'N/A')[:60]}...")
    
    # Show optional fields
    optional_fields = ['event_language', 'event_type', 'duration', 'event_time', 'event_format', 'attending', 'rating']
    optional_found = 0
    print("\nOptional Fields:")
    for field in optional_fields:
        if field in ev and ev[field]:
            print(f"  ✓ {field}: {ev[field]}")
            optional_found += 1
        else:
            print(f"  - {field}")
    
    print(f"\nOptional fields: {optional_found}/{len(optional_fields)} found")
    print("="*70)
    print("✓ INTEGRATION TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(final_integration_test())
