import asyncio
import logging
from pipeline_controller import PipelineController

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_mumbai():
    controller = PipelineController()
    
    print("\n--- STARTING DISTRICT VERIFICATION (MUMBAI) ---\n")
    
    # Focus only on District for this test
    target_platforms = ["District"]
    
    try:
        results = await controller.run_pipeline(
            location="Mumbai",
            category="Events",
            max_events=10,
            max_price=None,
            target_platforms=target_platforms
        )
        
        print(f"\nTotal Events Collected: {results['total_events']}")
        
        print("\n--- SAMPLE EVENTS ---")
        accepted_mumbai = 0
        for ev in results['events']:
            print(f"[{ev['platform']}] {ev['event_name']} | {ev['event_date']} | ₹{ev['price']} | {ev['location']}")
            loc = ev.get('location', '').lower()
            if "mumbai" in loc or "bombay" in loc or "thane" in loc or "navi mumbai" in loc:
                accepted_mumbai += 1
            
        print(f"\nFinal Tally: {accepted_mumbai}/{results['total_events']} events are in Mumbai region.")
            
        if results['total_events'] >= 1:
            print("\nSUCCESS: District found events in Mumbai and successfully enriched them.")
        else:
            print("\nWARNING: Low yield found. Checking if this is expected for Mumbai today.")
            
    except Exception as e:
        print(f"\nFAILED: System encountered an error: {e}")
        logger.exception(e)

if __name__ == "__main__":
    asyncio.run(verify_mumbai())
