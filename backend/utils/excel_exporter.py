import pandas as pd
import logging
import os
import datetime as dt
from .venue_validator import get_venue_summary
from .price_extractor import format_price

logger = logging.getLogger(__name__)

def export_to_excel(events: list, filepath: str):
    """
    Comprehensive Excel export with expanded columns.
    """
    if not events:
        logger.warning("No events to export.")
        return

    try:
        # Excel Permission Error Fix: If file is open, use a fallback path
        if os.path.exists(filepath):
            try:
                # Test if we can open for writing
                with open(filepath, 'a'):
                    pass
            except PermissionError:
                target_dir = os.path.dirname(filepath)
                base_name = os.path.basename(filepath).replace(".xlsx", "")
                ts = dt.datetime.now().strftime("%H%M%S")
                filepath = os.path.join(target_dir, f"{base_name}_{ts}.xlsx")
                logger.info(f"Original file locked, using fallback path: {filepath}")

        data = []
        for ev in events:
            # Format price
            price_str = format_price(ev.get("price"))
            
            # Format artist details robustly
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

            data.append({
                "Event Name":        ev.get("event_name", "N/A"),
                "Date":              ev.get("event_date", "N/A"),
                "Time":              ev.get("event_time", "-"),
                "Price":             price_str,
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
                "City":              ev.get("city", "N/A"),
                "Venue":             get_venue_summary(ev.get("venue")),
                "Rating":            ev.get("rating", "-"),
                "Reviews":           ev.get("review_count", "-"),
                "View Link":         ev.get("event_url", "N/A"),
            })

        df = pd.DataFrame(data)
        
        # Consistent column order
        columns_order = [
            "Event Name", "Date", "Time", "Price", "Platform", "Organizer",
            "Description", "Duration", "Hashtags", "Artist Name", "Artist Details", 
            "Interests", "Venue Address", "Language", "Type", "Format", "City", 
            "Venue", "Rating", "Reviews", "View Link"
        ]
        available_cols = [c for c in columns_order if c in df.columns]
        df = df[available_cols]
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        logger.info(f"Excel export successful: {filepath}")
        return filepath # Return the final path used
        
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        raise e
