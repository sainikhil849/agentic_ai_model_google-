#!/usr/bin/env python
"""
Consolidate All Events into ONE Master Excel File
Merges all events_export_*.xlsx into a single file with deduplication
"""

import pandas as pd
import glob
import os
from datetime import datetime
import openpyxl

def consolidate_events():
    print("\n" + "="*80)
    print("CONSOLIDATING ALL EVENTS INTO MASTER FILE")
    print("="*80)
    
    exports_dir = "exports"
    
    # Get all event export files
    excel_files = glob.glob(os.path.join(exports_dir, "events_export_*.xlsx"))
    
    if not excel_files:
        print("✗ No event exports found")
        return None
    
    print(f"\n✓ Found {len(excel_files)} export files\n")
    
    all_events = []
    file_summary = []
    
    # Read all Excel files
    for i, filepath in enumerate(sorted(excel_files), 1):
        try:
            filename = os.path.basename(filepath)
            df = pd.read_excel(filepath)
            
            event_count = len(df)
            file_summary.append({
                'file': filename,
                'events': event_count
            })
            
            print(f"{i}. {filename}")
            print(f"   → Loaded {event_count} events")
            
            all_events.append(df)
            
        except Exception as e:
            print(f"   ✗ Error reading {filename}: {e}")
    
    if not all_events:
        print("\n✗ No events could be loaded")
        return None
    
    # Combine all DataFrames
    print(f"\n✓ Combining {len(all_events)} files...")
    combined_df = pd.concat(all_events, ignore_index=True)
    
    total_before = len(combined_df)
    print(f"   → Total before dedup: {total_before} events")
    
    # Deduplicate by event name + date + venue
    dedup_columns = ['Event Name', 'Date', 'Venue']
    if all(col in combined_df.columns for col in dedup_columns):
        combined_df = combined_df.drop_duplicates(
            subset=dedup_columns,
            keep='first'
        )
        total_after = len(combined_df)
        duplicates = total_before - total_after
        print(f"   → After removing duplicates: {total_after} events")
        print(f"   → Removed: {duplicates} duplicates")
    else:
        print(f"   → No deduplication (columns not found)")
        total_after = total_before
    
    # Sort by date (newest first)
    if 'Date' in combined_df.columns:
        try:
            combined_df['Date'] = pd.to_datetime(combined_df['Date'], errors='coerce')
            combined_df = combined_df.sort_values('Date', ascending=False, na_position='last')
        except:
            pass
    
    # Create output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(exports_dir, f"MASTER_ALL_EVENTS_{total_after}_{timestamp}.xlsx")
    
    print(f"\n✓ Creating master file: {os.path.basename(output_file)}")
    
    # Write to Excel with formatting
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        combined_df.to_excel(writer, sheet_name='All Events', index=False)
        
        # Format the Excel file
        workbook = writer.book
        worksheet = writer.sheets['All Events']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Add header formatting
        from openpyxl.styles import Font, PatternFill
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
    
    print(f"   ✓ Saved: {output_file}")
    print(f"   ✓ Rows: {len(combined_df)}")
    print(f"   ✓ Columns: {len(combined_df.columns)}")
    
    print("\n" + "="*80)
    print("CONSOLIDATION COMPLETE!")
    print("="*80)
    
    print(f"""
✓ Master file created with {total_after} unique events

Summary:
  • Input files: {len(all_events)}
  • Total events before dedup: {total_before}
  • Unique events: {total_after}
  • Duplicates removed: {total_before - total_after}

File: {os.path.basename(output_file)}
Location: {exports_dir}/

""")
    
    # Show file statistics
    print("Events by Platform:")
    if 'Platform' in combined_df.columns:
        platform_counts = combined_df['Platform'].value_counts()
        for platform, count in platform_counts.items():
            print(f"  • {platform}: {count} events")
    
    print(f"\nEvents by Location:")
    if 'Location' in combined_df.columns:
        location_counts = combined_df['Location'].value_counts().head(10)
        for location, count in location_counts.items():
            print(f"  • {location}: {count} events")
    
    print("\n" + "="*80)
    print("✓ Your master file is ready!")
    print(f"  Open: {os.path.abspath(output_file)}")
    print("="*80 + "\n")
    
    return output_file

if __name__ == "__main__":
    consolidate_events()
