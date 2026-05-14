import os
import argparse
import sys

# Add backend to path to support running as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from organizer_intelligence.processor import OrganizerProcessor
from organizer_intelligence.enricher import OrganizerEnricher
from organizer_intelligence.discovery import OrganizerDiscoverer

class OrganizerIntelligenceSystem:
    def __init__(self):
        self.processor = OrganizerProcessor()
        self.discoverer = OrganizerDiscoverer()

    def run(self, start_row=None, end_row=None, batch_size=20):
        print("=" * 60)
        print("  ORGANIZER INTELLIGENCE SYSTEM")
        print("=" * 60)

        # Phase 1: Extract + Build Master DB
        self.processor.run()
        
        # Pass the actual master path (may have been changed due to lock)
        actual_master = self.processor.master_path

        # Phase 2: Tier-2 Discovery (signal analysis)
        print("\n[PHASE 2] Tier-2 signal analysis...")
        self.discoverer.run()

        # Phase 3: Active Web Enrichment via Playwright
        print("\n[PHASE 3] Active web enrichment (Playwright)...")
        enricher = OrganizerEnricher(master_path=actual_master, batch_size=batch_size)
        enricher.run(start_row=start_row, end_row=end_row)

        print("\n" + "=" * 60)
        print("  ORGANIZER INTELLIGENCE RUN COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organizer Intelligence System")
    parser.add_argument("--start", type=int, help="Start row index")
    parser.add_argument("--end", type=int, help="End row index")
    parser.add_argument("--batch", type=int, default=20, help="Batch size for enrichment")
    
    args = parser.parse_args()
    
    OrganizerIntelligenceSystem().run(
        start_row=args.start, 
        end_row=args.end, 
        batch_size=args.batch
    )
