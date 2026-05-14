#!/usr/bin/env python
"""
District Agent - Live Excel Saving Documentation
Saves events to Excel every 10 events during scraping
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    DISTRICT AGENT - LIVE EXCEL SAVING                     ║
╚════════════════════════════════════════════════════════════════════════════╝

🎯 WHAT'S NEW:

While District agent is scraping, it NOW automatically saves events to Excel:
  ✓ Every 10 events collected → Saved to Excel
  ✓ If process stops → Keep all saved events
  ✓ Real-time tracking → See progress in file
  ✓ No data loss → Always have current progress

════════════════════════════════════════════════════════════════════════════════

📊 HOW IT WORKS:

1. Start District scraping
   POST /api/scrape
   {
     "location": "Hyderabad, India",
     "max_events": 170,
     "platforms": ["District"]
   }

2. Events collected → Every 10 events automatically saved

3. Excel file created in: exports/DISTRICT_LIVE_<timestamp>.xlsx

4. Check progress anytime:
   • Open file from exports/
   • Refresh to see latest
   • All columns populated

5. If stops by mistake:
   • All collected events are in the Excel file
   • No data lost!
   • Can restart from where it stopped

════════════════════════════════════════════════════════════════════════════════

📈 EXAMPLE TIMELINE:

Event 1 collected    → Stored in memory
Event 2 collected    → Stored in memory
...
Event 9 collected    → Stored in memory
Event 10 collected   → ✓ SAVED TO EXCEL (DISTRICT_LIVE_*.xlsx)

Event 11 collected   → Stored in memory
...
Event 19 collected   → Stored in memory
Event 20 collected   → ✓ SAVED TO EXCEL (Excel updated)

...

Event 165 collected  → Stored in memory
...
Event 170 collected  → ✓ FINAL SAVE (All events saved)

════════════════════════════════════════════════════════════════════════════════

✅ FILE DETAILS:

Location: backend/exports/DISTRICT_LIVE_<TIMESTAMP>.xlsx

Columns:
  • Event Name
  • Date
  • Time
  • Price
  • Platform (District)
  • Location (Hyderabad)
  • Venue
  • Description
  • Link
  • Organizer
  • Language
  • Type
  • Format
  • Duration
  • Attending
  • Rating

════════════════════════════════════════════════════════════════════════════════

🔄 USAGE SCENARIOS:

SCENARIO 1: Normal Completion
   1. Start scraping: POST /api/scrape for 170 events
   2. Wait ~2-3 hours
   3. All 170 events auto-saved to Excel every 10
   4. Check: exports/DISTRICT_LIVE_*.xlsx has 170 rows

SCENARIO 2: Accidental Stop (Power loss, crash, etc.)
   1. Started scraping for 170 events
   2. After collecting 75 events, system crashed
   3. ✓ 70 events are already in Excel (saved when hit 70)
   4. ✓ 5 more events in memory (not yet saved)
   5. Use the 70 saved events, restart for remaining 100

SCENARIO 3: Manual Stop (Ctrl+C)
   1. Started scraping for 170 events
   2. After collecting 45 events, user pressed Ctrl+C
   3. ✓ 40 events already saved in Excel
   4. ✓ 5 events in memory (lost on stop)
   5. Restart and get remaining 125 events
   6. Consolidate both runs to get all unique events

SCENARIO 4: Check Progress While Running
   1. Started scraping at 15:00
   2. At 17:30, open: exports/DISTRICT_LIVE_*.xlsx
   3. Can see current events (last saved at 17:28)
   4. Know exactly how many collected
   5. Estimate when will finish

════════════════════════════════════════════════════════════════════════════════

⚙️  TECHNICAL DETAILS:

Saving Logic:
   • After each event is enriched and validated
   • Check if (total_saved) % 10 == 0
   • If yes → Write all events to Excel
   • Uses pandas for formatting and efficiency

Excel Format:
   • Sheet name: "District Events"
   • Headers: Event Name, Date, Time, Price, Platform, etc.
   • Auto-formatted columns (width adjusted)
   • UTF-8 encoding for special characters

Error Handling:
   • If save fails → Continues scraping (no crash)
   • Only logs warning, doesn't stop collection
   • Next 10 events trigger save again

════════════════════════════════════════════════════════════════════════════════

💡 BEST PRACTICES:

1. Monitor during long runs
   • Don't start 170-event scrape and leave for 3 hours
   • Check progress every 30 mins
   • If it stops, know immediately

2. Use this with consolidate script
   • After District completes: python consolidate_all_events.py
   • This merges DISTRICT_LIVE_*.xlsx with other platforms
   • Creates MASTER_ALL_EVENTS_*.xlsx

3. Check file size
   • Growing file = Scraping working
   • Static file = Might be stuck
   • ~10KB per 10 events (approximate)

4. Keep multiple runs organized
   • Each scrape creates new DISTRICT_LIVE_*.xlsx
   • Use timestamps to track
   • Can compare runs side-by-side

════════════════════════════════════════════════════════════════════════════════

📋 COMMANDS FOR NEXT STEPS:

After District finishes:

1. Verify saved file:
   $ ls -lh exports/DISTRICT_LIVE_*.xlsx

2. Check row count:
   $ python count_excel_rows.py exports/DISTRICT_LIVE_*.xlsx

3. Consolidate with other platforms:
   $ python consolidate_all_events.py

4. Clean up old files:
   $ python cleanup_old_exports.py

════════════════════════════════════════════════════════════════════════════════

✨ BENEFITS:

✓ No more lost data during long scrapes
✓ Real-time progress tracking
✓ Safe recovery if process crashes
✓ Excel file grows as scraping progresses
✓ Each 10 events = checkpoint
✓ Can analyze partial results while scraping continues
✓ Better reliability for production

════════════════════════════════════════════════════════════════════════════════

🎯 YOUR WORKFLOW:

BEFORE (Old):
  1. Start scraping
  2. Wait 2-3 hours
  3. Hope nothing crashes
  4. Get all or nothing
  5. Lost if interrupted

NOW (New - with live saving):
  1. Start scraping
  2. Every 10 events → auto-saved
  3. Can check progress anytime
  4. If crash → keep what's saved
  5. Never lose all data!

════════════════════════════════════════════════════════════════════════════════

Ready to use! Start District scraping and watch the Excel file grow! 📈

When you make the request: POST /api/scrape for District with 170 events
Check: exports/DISTRICT_LIVE_*.xlsx after ~30 seconds
Should see first 10 events saved!

════════════════════════════════════════════════════════════════════════════════
""")
