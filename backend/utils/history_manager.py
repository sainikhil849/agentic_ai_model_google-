import os
import pandas as pd
import logging
from typing import List, Dict
from utils.excel_exporter import get_venue_summary, format_price

logger = logging.getLogger(__name__)

def update_historical_excel(city: str, new_events: List[Dict]) -> Dict:
    """
    Updates the historical Excel tracking file for the specified city.
    Prevents duplicates based on Event Name, Date, and Venue.
    Creates a secondary sheet for Organizers.
    """
    if not new_events:
        return {
            "city": city,
            "existing_events": 0,
            "new_events_found": 0,
            "added_to_excel": 0,
            "duplicates_skipped": 0
        }

    safe_city = city.replace(" ", "_").title()
    filepath = os.path.join(os.getcwd(), "exports", f"Events_Database_{safe_city}.xlsx")

    # 1. Format incoming data into a standard list of dicts (same mapping as excel_exporter)
    incoming_data = []
    for ev in new_events:
        # Format artist details robustly for history
        artists_raw = ev.get("artists", [])
        artist_names = "N/A"
        artist_details = "N/A"
        
        if isinstance(artists_raw, list) and artists_raw:
            names = []
            details = []
            for a in artists_raw:
                if isinstance(a, dict):
                    name = a.get("name") or a.get("title")
                    if name: names.append(str(name))
                    desc = a.get("description") or a.get("role")
                    if desc: details.append(f"{name}: {desc}")
                else:
                    names.append(str(a))
            
            if names: artist_names = ", ".join(names)
            if details: artist_details = " | ".join(details)
        elif isinstance(artists_raw, str):
            artist_names = artists_raw

        incoming_data.append({
            "Event Name":        ev.get("event_name", "N/A"),
            "Date":              ev.get("event_date", "N/A"),
            "Time":              ev.get("event_time", "-"),
            "Price":             format_price(ev.get("price")),
            "Platform":          ev.get("platform", "N/A"),
            "Organizer":         ev.get("organizer", "N/A"),
            "Description":       ev.get("about_event") or ev.get("description") or "N/A",
            "Duration":          ev.get("duration", "N/A"),
            "Hashtags":          ", ".join(ev.get("hashtags", [])) if isinstance(ev.get("hashtags"), list) else ev.get("hashtags", "N/A"),
            "Artist Name":       artist_names,
            "Artist Details":    artist_details,
            "Interests":         ev.get("people_interested") or ev.get("attending") or "N/A",
            "Venue Address":     ev.get("venue_address", "N/A"),
            "Language":          ev.get("event_language", "-"),
            "Type":              ev.get("event_type", "-"),
            "Format":            ev.get("event_format", "-"),
            "City":              ev.get("city", safe_city),
            "Venue":             get_venue_summary(ev.get("venue")),
            "Rating":            ev.get("rating", "-"),
            "Reviews":           ev.get("review_count", "-"),
            "View Link":         ev.get("event_url", "N/A"),
        })

    new_df = pd.DataFrame(incoming_data)
    
    columns_order = [
        "Event Name", "Date", "Time", "Price", "Platform", "Organizer",
        "Description", "Duration", "Hashtags", "Artist Name", "Artist Details", 
        "Interests", "Venue Address", "Language", "Type", "Format", "City", 
        "Venue", "Rating", "Reviews", "View Link"
    ]
    # Keep ordering consistent
    available_cols = [c for c in columns_order if c in new_df.columns]
    new_df = new_df[available_cols]

    existing_events_count = 0
    df_combined = new_df
    
    # 2. Merge with existing dataset if present
    if os.path.exists(filepath):
        try:
            # Read existing Events sheet
            old_df = pd.read_excel(filepath, sheet_name="Events")
            existing_events_count = len(old_df)
            # Concat new events to old, old comes first so we keep oldest details potentially, or keep='last' to update it.
            # We'll use keep='last' to ensure NEW ones replace old ones for conflicts.
            df_combined = pd.concat([old_df, new_df], ignore_index=True)
            
            logger.info(f"Loaded existing history for {city}. Found {existing_events_count} events.")
        except Exception as e:
            logger.error(f"Could not read existing Excel database for {city}. Overwriting. ({e})")
            existing_events_count = 0

    # 3. Deduplicate
    # Based on URL (primary) and Event Name + Date + Venue (heuristic fallback).
    # Convert them to temporary columns just for dropping duplicates.
    df_combined['_temp_name'] = df_combined['Event Name'].astype(str).str.lower().str.strip()
    df_combined['_temp_date'] = df_combined['Date'].astype(str).str.strip()
    df_combined['_temp_venue'] = df_combined['Venue'].astype(str).str.lower().str.strip()
    df_combined['_temp_url'] = df_combined['View Link'].astype(str).str.strip()

    initial_len = len(df_combined)
    
    # We keep 'last' so fresh scrapes overwrite older versions of the same event.
    # Pass 1: Deduplicate by exact URL (most reliable)
    df_combined = df_combined.drop_duplicates(subset=['_temp_url'], keep='last')
    # Pass 2: Deduplicate by Name + Date + Venue (handles same event on different platforms or slightly different URLs)
    df_combined = df_combined.drop_duplicates(subset=['_temp_name', '_temp_date', '_temp_venue'], keep='last')
    
    final_len = len(df_combined)
    added_to_excel = final_len - existing_events_count
    
    # Fix the case where the math might go negative if old DB had exact duplicates natively.
    if added_to_excel < 0:
        added_to_excel = 0
        
    duplicates_skipped = len(new_events) - added_to_excel

    # Clean temps
    df_combined = df_combined.drop(columns=['_temp_name', '_temp_date', '_temp_venue', '_temp_url'])
    
    # 4. Generate Organizers Sheet
    organizers_df = None
    if "Organizer" in df_combined.columns:
        # Group by Organizer to find count and unique platforms
        org_group = df_combined[df_combined["Organizer"] != "N/A"].groupby("Organizer")
        org_data = []
        for name, group in org_group:
            platforms = ", ".join(group["Platform"].unique().tolist())
            total_events = len(group)
            
            org_data.append({
                "Organizer Name": name,
                "Total Events": total_events,
                "Platforms Found On": platforms
            })
        
        organizers_df = pd.DataFrame(org_data)
        # Sort by total events descending
        if not organizers_df.empty:
            organizers_df = organizers_df.sort_values(by="Total Events", ascending=False)

    # 5. Write out
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_combined.to_excel(writer, sheet_name="Events", index=False)
            if organizers_df is not None and not organizers_df.empty:
                organizers_df.to_excel(writer, sheet_name="Organizers", index=False)
        logger.info(f"Saved history database to {filepath}")
    except PermissionError:
        import datetime as dt
        ts = dt.datetime.now().strftime("%H%M%S")
        filepath_fallback = os.path.join(os.getcwd(), "exports", f"Events_Database_{safe_city}_{ts}.xlsx")
        logger.warning(f"PermissionError: Original file {filepath} locked, using fallback path: {filepath_fallback}")
        try:
            with pd.ExcelWriter(filepath_fallback, engine='openpyxl') as writer:
                df_combined.to_excel(writer, sheet_name="Events", index=False)
                if organizers_df is not None and not organizers_df.empty:
                    organizers_df.to_excel(writer, sheet_name="Organizers", index=False)
            logger.info(f"Saved history database to fallback {filepath_fallback}")
        except Exception as fallback_e:
            logger.error(f"Error saving fallback historical Excel: {fallback_e}")
            raise
    except Exception as e:
        logger.error(f"Error saving historical Excel: {e}")
        raise

    stats = {
        "city": city,
        "existing_events": existing_events_count,
        "new_events_found": len(new_events),
        "added_to_excel": added_to_excel,
        "duplicates_skipped": duplicates_skipped,
        "final_total": final_len
    }

    print("\n" + "="*50)
    print(f"SCRAPE STATISTICS: {city}")
    print("="*50)
    print(f"  Existing events in DB: {stats['existing_events']}")
    print(f"  New events discovered: {stats['new_events_found']}")
    print(f"  Duplicates skipped   : {stats['duplicates_skipped']}")
    print(f"  Added to Excel DB    : {stats['added_to_excel']}")
    print("-" * 50)
    print(f"  Final Excel Total    : {stats['final_total']}")
    print("="*50 + "\n")

    return stats

def get_existing_urls(city: str) -> set:
    """
    Returns a set of all event URLs already present in the historical Excel for this city.
    Used to skip redundant enrichment of previously scraped events.
    """
    safe_city = city.replace(" ", "_").title()
    filepath = os.path.join(os.getcwd(), "exports", f"Events_Database_{safe_city}.xlsx")
    
    if not os.path.exists(filepath):
        return set()
        
    try:
        df = pd.read_excel(filepath, sheet_name="Events")
        if "View Link" in df.columns:
            # Clean and return as set
            return set(df["View Link"].astype(str).str.strip().tolist())
    except Exception as e:
        logger.debug(f"Could not read existing URLs for {city}: {e}")
        
    return set()
