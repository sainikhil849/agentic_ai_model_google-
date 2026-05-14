#!/usr/bin/env python
"""
Stop Infinite Scraping Loop & Keep Latest Events Only
"""

import glob
import os
from datetime import datetime

def stop_loop_keep_latest():
    print("\n" + "="*80)
    print("STOPPING LOOP - KEEPING ONLY LATEST EVENTS")
    print("="*80)
    
    exports_dir = "exports"
    
    # Get all event export files sorted by modification time
    excel_files = sorted(
        glob.glob(os.path.join(exports_dir, "events_export_*.xlsx")),
        key=os.path.getmtime,
        reverse=True
    )
    
    if not excel_files:
        print("No export files found")
        return
    
    # Keep latest 3, delete rest
    keep_files = excel_files[:3]
    delete_files = excel_files[3:]
    
    print(f"\n✓ Found {len(excel_files)} export files")
    print(f"  Keeping: {len(keep_files)} latest files")
    print(f"  Deleting: {len(delete_files)} old files")
    
    print(f"\nKEEPING (Latest 3):")
    for i, f in enumerate(keep_files, 1):
        mtime = os.path.getmtime(f)
        mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {i}. {os.path.basename(f)} ({mod_time})")
    
    print(f"\nDELETING (Old {len(delete_files)}):")
    for f in delete_files:
        try:
            os.remove(f)
            print(f"  ✓ Deleted: {os.path.basename(f)}")
        except Exception as e:
            print(f"  ✗ Error deleting {os.path.basename(f)}: {e}")
    
    print("\n" + "="*80)
    print("✓ Cleanup complete!")
    print(f"  Kept: {len(keep_files)} recent exports")
    print(f"  Removed: {len(delete_files)} old exports")
    print("="*80 + "\n")

if __name__ == "__main__":
    stop_loop_keep_latest()
