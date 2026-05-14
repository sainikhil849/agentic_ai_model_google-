"""
Consolidate and Export District Multi-City Events to Excel
Combines results from all 4 cities and provides city-based filtering
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import openpyxl for Excel export
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    logger.warning("openpyxl not installed, will use CSV fallback")
    HAS_OPENPYXL = False
    import csv

def load_city_events(city_name: str) -> List[Dict]:
    """Load events from temporary JSON files for each city"""
    temp_file = rf'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_{city_name.lower()}_temp.json'
    
    if not os.path.exists(temp_file):
        logger.warning(f"File not found: {temp_file}")
        return []
    
    try:
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(city_name, [])
    except Exception as e:
        logger.error(f"Error loading {city_name} events: {e}")
        return []

def create_excel_export(all_events: Dict[str, List[Dict]], output_file: str, selected_city: Optional[str] = None):
    """Create Excel file with proper formatting"""
    
    if not HAS_OPENPYXL:
        logger.error("openpyxl required for Excel export. Install: pip install openpyxl")
        return
    
    wb = Workbook()
    
    # Remove default sheet
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])
    
    # Create summary sheet
    ws_summary = wb.create_sheet("Summary", 0)
    
    # Summary headers
    ws_summary['A1'] = "District Events Summary"
    ws_summary['A1'].font = Font(bold=True, size=14)
    
    row = 3
    ws_summary['A' + str(row)] = "City"
    ws_summary['B' + str(row)] = "Events Count"
    ws_summary['A' + str(row)].font = Font(bold=True)
    ws_summary['B' + str(row)].font = Font(bold=True)
    
    row += 1
    total_events = 0
    for city, events in all_events.items():
        count = len(events)
        total_events += count
        ws_summary['A' + str(row)] = city
        ws_summary['B' + str(row)] = count
        row += 1
    
    ws_summary['A' + str(row)] = "TOTAL"
    ws_summary['A' + str(row)].font = Font(bold=True)
    ws_summary['B' + str(row)] = total_events
    ws_summary['B' + str(row)].font = Font(bold=True)
    
    ws_summary.column_dimensions['A'].width = 20
    ws_summary.column_dimensions['B'].width = 15
    
    # Create sheets for each city or selected city
    cities_to_export = [selected_city] if selected_city and selected_city in all_events else list(all_events.keys())
    
    for city in cities_to_export:
        events = all_events.get(city, [])
        if not events:
            continue
        
        ws = wb.create_sheet(city)
        
        # Headers
        headers = [
            "Event Name",
            "Price (₹)",
            "Venue Location",
            "Event Date",
            "Event Time",
            "Description",
            "Event URL",
            "City",
            "Platform"
        ]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = header
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Data rows
        for row_idx, event in enumerate(events, 2):
            ws.cell(row=row_idx, column=1).value = event.get('event_name', '')
            ws.cell(row=row_idx, column=2).value = event.get('price', 0)
            ws.cell(row=row_idx, column=3).value = event.get('venue_location', '')
            ws.cell(row=row_idx, column=4).value = event.get('event_date', '')
            ws.cell(row=row_idx, column=5).value = event.get('event_time', '')
            ws.cell(row=row_idx, column=6).value = event.get('description', '')[:100]  # Truncate description
            ws.cell(row=row_idx, column=7).value = event.get('event_url', '')
            ws.cell(row=row_idx, column=8).value = event.get('city', '')
            ws.cell(row=row_idx, column=9).value = event.get('platform', '')
            
            # Alignment
            for col_idx in range(1, 10):
                ws.cell(row=row_idx, column=col_idx).alignment = Alignment(wrap_text=True, vertical="top")
        
        # Column widths
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 40
        ws.column_dimensions['G'].width = 50
        ws.column_dimensions['H'].width = 15
        ws.column_dimensions['I'].width = 15
    
    # Save
    wb.save(output_file)
    logger.info(f"✓ Excel file saved: {output_file}")
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("EXCEL EXPORT SUMMARY")
    logger.info("="*80)
    for city in cities_to_export:
        count = len(all_events.get(city, []))
        logger.info(f"{city}: {count} events")
    logger.info("="*80 + "\n")

def consolidate_and_export(selected_city: Optional[str] = None):
    """Main consolidation function"""
    logger.info("\n" + "="*80)
    logger.info("CONSOLIDATING DISTRICT EVENTS FROM ALL CITIES")
    logger.info("="*80 + "\n")
    
    # Load all city events
    cities = ["Mumbai", "Delhi", "Chennai", "Pune"]
    all_events = {}
    
    for city in cities:
        events = load_city_events(city)
        all_events[city] = events
        logger.info(f"{city}: {len(events)} events loaded")
    
    # Export to Excel
    if selected_city:
        output_file = rf'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_events_{selected_city}.xlsx'
        logger.info(f"\nExporting only {selected_city}...")
    else:
        output_file = r'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_events_all_cities.xlsx'
        logger.info(f"\nExporting all cities...")
    
    create_excel_export(all_events, output_file, selected_city)
    
    # Also save consolidated JSON
    json_output = r'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_consolidated.json'
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ JSON file saved: {json_output}")

if __name__ == "__main__":
    # Example: consolidate_and_export() for all cities
    # Or: consolidate_and_export("Mumbai") for specific city
    consolidate_and_export()
