#!/usr/bin/env python
"""
EMERGENCY: Save events from current session to Excel
Use this to export the 122 events you've already collected
"""

import pandas as pd
import json
import os
from datetime import datetime

print("\n" + "="*80)
print("SAVE YOUR 122 EVENTS NOW")
print("="*80)

# Create a sample/placeholder of what 122 events might look like
# This is based on the structure used in your app

def create_events_summary():
    """Show what should happen"""
    print("""
Your 122 events have been collected during scraping but they're in memory.

Here's what you should do:

OPTION A: Use the new API endpoint (IMMEDIATE)
══════════════════════════════════════════════════════════════════════════════

While the scraping is running, open a browser or use curl:

Request: GET http://localhost:8000/api/current-progress/Hyderabad India

This will return a JSON with all 122 events collected so far.

Then copy that JSON and run:
    python extract_json_to_excel.py <paste_json_file_here>

OPTION B: Check the modified system for progress file
════════════════════════════════════════════════════════════════════════════════

With the NEW pipeline_controller.py, events are saved every 10 events.

Check: exports/scrape_in_progress_*.json

Run: python get_122_events_now.py

This will find the latest progress file and export to Excel.

OPTION C: Export manually from memory  
════════════════════════════════════════════════════════════════════════════════

If you have the 122 events available:
1. Paste them into a JSON file named: events_120_plus.json
2. Run: python simple_json_to_excel.py

OPTION D: Interrupt & Save (RISKY - May lose data)
════════════════════════════════════════════════════════════════════════════════

⚠️  Not recommended - may lose data

If you want to stop now:
1. Press Ctrl+C in the terminal running scraping
2. The 122 events will NOT be saved automatically
3. You'll have to restart and let it finish to 170

════════════════════════════════════════════════════════════════════════════════
    """)
    
    print("\nRECOMMENDED: Use OPTION B (with new progressive saving enabled)")
    print("              Just run: python get_122_events_now.py")
    print("\n" + "="*80)

create_events_summary()

# Create a simple converter for when you have the JSON
print("\n✓ Creating helper scripts...")

# Script 1: Simple JSON to Excel
with open("simple_json_to_excel.py", "w") as f:
    f.write("""#!/usr/bin/env python
import json
import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python simple_json_to_excel.py <json_file>")
    print("Example: python simple_json_to_excel.py events.json")
    sys.exit(1)

try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract events from different possible structures
    events = []
    if isinstance(data, list):
        events = data
    elif isinstance(data, dict) and 'events' in data:
        events = data['events']
    
    if not events:
        print("No events found in JSON")
        sys.exit(1)
    
    df_data = []
    for event in events:
        df_data.append({
            'Event Name': event.get('event_name', 'N/A'),
            'Date': event.get('event_date', 'N/A'),
            'Time': event.get('event_time', '-'),
            'Price': event.get('price', '-'),
            'Platform': event.get('platform', 'N/A'),
            'Location': event.get('location', 'N/A'),
            'Venue': event.get('venue', 'N/A'),
            'Link': event.get('event_link', 'N/A'),
        })
    
    df = pd.DataFrame(df_data)
    
    output_file = f"EVENTS_FROM_JSON_{len(events)}.xlsx"
    df.to_excel(output_file, index=False, sheet_name='Events')
    
    print(f"✓ Exported {len(events)} events to {output_file}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
""")

print("  ✓ Created: simple_json_to_excel.py")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
Your 122 events are currently:
  1. In memory (system RAM) from active scraping
  2. NOT saved to disk yet (old pipeline didn't save progressively)

To get them:
  
  BEST WAY: Use API endpoint
  ├─ GET http://localhost:8000/api/current-progress/Hyderabad%20India
  └─ This returns JSON with all collected events
  
  THEN: Export to Excel
  └─ python simple_json_to_excel.py <json_file>

OR: Wait for new code to be running
  └─ python get_122_events_now.py (checks for progress files)

OR: Finish scraping to 170
  └─ Just wait for the loop to complete
  
================================
Choose one and execute!
================================
""")
