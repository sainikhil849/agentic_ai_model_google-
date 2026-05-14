import pandas as pd
import os
import re

class OrganizerDiscoverer:
    def __init__(self, exports_dir=r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend\exports'):
        self.exports_dir = exports_dir

    def discover_from_description(self, description):
        if not isinstance(description, str):
            return None
        
        # Look for "Presented by", "Organized by", etc.
        patterns = [
            r'Presented by\s+([^,\.\n]+)',
            r'Organized by\s+([^,\.\n]+)',
            r'Hosted by\s+([^,\.\n]+)',
            r'Powered by\s+([^,\.\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def run(self):
        # This will be called on events with missing organizers
        pass

if __name__ == "__main__":
    discoverer = OrganizerDiscoverer()
    # Test
    print(discoverer.discover_from_description("This event is Presented by Bangalore Comedy Club and hosted at..."))
