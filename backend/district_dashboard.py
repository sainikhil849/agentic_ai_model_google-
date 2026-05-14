"""
District Events Dashboard - Multi-City Support
Provides API endpoints for filtering events by city
"""

import sys
import json
import os
import logging
from typing import List, Dict, Optional

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DistrictDashboard:
    """Dashboard for multi-city event filtering"""
    
    def __init__(self):
        self.consolidated_file = r'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_consolidated.json'
        self.all_events = self._load_events()
        self.cities = list(self.all_events.keys())
    
    def _load_events(self) -> Dict[str, List[Dict]]:
        """Load all events from consolidated JSON"""
        try:
            with open(self.consolidated_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading events: {e}")
            return {}
    
    def get_all_cities(self) -> List[str]:
        """Return list of all available cities"""
        return self.cities
    
    def get_city_events(self, city: str) -> List[Dict]:
        """Get events for a specific city"""
        if city not in self.all_events:
            logger.warning(f"City not found: {city}")
            return []
        return self.all_events[city]
    
    def get_city_count(self, city: str) -> int:
        """Get event count for a city"""
        return len(self.all_events.get(city, []))
    
    def get_summary(self) -> Dict:
        """Get summary of all events across cities"""
        summary = {
            "total_events": sum(len(events) for events in self.all_events.values()),
            "cities": {}
        }
        
        for city in self.cities:
            events = self.all_events.get(city, [])
            summary["cities"][city] = {
                "count": len(events),
                "price_range": self._get_price_range(events) if events else (0, 0),
                "venues": len(set(e.get('venue_location', '') for e in events))
            }
        
        return summary
    
    def _get_price_range(self, events: List[Dict]) -> tuple:
        """Get min and max price from events"""
        prices = [e.get('price', 0) for e in events if e.get('price')]
        if not prices:
            return (0, 0)
        return (min(prices), max(prices))
    
    def filter_events(self, city: str, min_price: int = 0, max_price: int = 99999) -> List[Dict]:
        """Filter events by city and price range"""
        events = self.get_city_events(city)
        return [e for e in events if min_price <= e.get('price', 0) <= max_price]
    
    def search_events(self, city: str, keyword: str) -> List[Dict]:
        """Search events by keyword in city"""
        events = self.get_city_events(city)
        keyword_lower = keyword.lower()
        return [
            e for e in events
            if keyword_lower in e.get('event_name', '').lower() or
               keyword_lower in e.get('description', '').lower()
        ]
    
    def export_dashboard_json(self, city: str = None) -> Dict:
        """Export dashboard data as JSON"""
        if city and city in self.cities:
            return {
                "selected_city": city,
                "events": self.get_city_events(city),
                "summary": {
                    "total": self.get_city_count(city),
                    "city_name": city
                }
            }
        else:
            return {
                "selected_city": "all",
                "summary": self.get_summary(),
                "available_cities": self.cities
            }
    
    def print_dashboard(self, city: str = None):
        """Print dashboard summary"""
        print("\n" + "="*80)
        print("DISTRICT EVENTS DASHBOARD")
        print("="*80)
        
        summary = self.get_summary()
        print(f"\nTotal Events: {summary['total_events']}")
        print(f"\nAvailable Cities: {len(self.cities)}")
        
        for city_name in self.cities:
            city_info = summary['cities'][city_name]
            print(f"\n{city_name}:")
            print(f"  Events: {city_info['count']}")
            print(f"  Price Range: ₹{city_info['price_range'][0]} - ₹{city_info['price_range'][1]}")
            print(f"  Unique Venues: {city_info['venues']}")
        
        if city and city in self.cities:
            print(f"\n{'='*80}")
            print(f"EVENTS IN {city.upper()}")
            print(f"{'='*80}")
            events = self.get_city_events(city)[:5]  # Show first 5
            for i, event in enumerate(events, 1):
                print(f"\n{i}. {event['event_name']}")
                print(f"   Price: ₹{event['price']}")
                print(f"   Venue: {event['venue_location']}")
                print(f"   Date: {event['event_date']} at {event['event_time']}")
                print(f"   Description: {event['description'][:60]}...")
        
        print("\n" + "="*80 + "\n")

def main():
    """Demo dashboard usage"""
    dashboard = DistrictDashboard()
    
    # Print general dashboard
    dashboard.print_dashboard()
    
    # Print dashboard for specific city
    dashboard.print_dashboard("Mumbai")
    
    # Export data
    logger.info("\nCities available for filtering:")
    for city in dashboard.get_all_cities():
        count = dashboard.get_city_count(city)
        logger.info(f"  ✓ {city}: {count} events")
    
    # Export JSON
    json_data = dashboard.export_dashboard_json("Delhi")
    logger.info(f"\nDelhia Data: {len(json_data['events'])} events loaded")
    logger.info(f"Sample event: {json_data['events'][0]['event_name']}")

if __name__ == "__main__":
    main()
