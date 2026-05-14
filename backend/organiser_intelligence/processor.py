import os
import pandas as pd
import glob
import re
import time
from datetime import datetime

class OrganizerProcessor:
    def __init__(self, exports_dir=None):
        if exports_dir is None:
            self.exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        else:
            self.exports_dir = exports_dir
        self.master_path = os.path.join(self.exports_dir, 'organizers_master.xlsx')

        # Words that indicate this is NOT an organizer name
        self.reject_words = [
            'guide', 'instructions', 'exclusions', 'terms', 'policy', 'policies',
            'book now', 'limited seats', 'unknown', 'admin', 'tba', 'not available',
            'seats left', 'per person', 'only rs', 'per head', 'description',
            'overview', 'highlights', 'inclusions', 'itinerary', 'schedule',
            'disclaimer', 'refund', 'cancellation', 'check-in', 'check in',
            'please note', 'important note', 'note:', 'terms and conditions',
            'bookmyshow', 'meetup', 'swiggy', 'sortmyscene', 'skillbox', 'district', 
            'urbanaut', 'meraevents', 'insider'
        ]
        
        # Characters / patterns that indicate garbage
        self.reject_chars = ['###', '***', '---', '❌', '📅', '🕔', '📍', '✅', '⚠']

    def is_valid_organizer(self, name):
        """Strict validation: only accept strings that look like company/brand/person names."""
        if not isinstance(name, str):
            return False
        name = name.strip()
        
        # Length filters
        if len(name) < 3 or len(name) > 60:
            return False
        
        # Max 6 words — real organizer names are short
        if len(name.split()) > 6:
            return False

        # Reject if starts with special chars like ( or contains emoji/symbols
        if name[0] in '([{<!"\'':
            return False
        
        # Reject garbage characters
        for char in self.reject_chars:
            if char in name:
                return False
        
        # Reject currency / price patterns ($19.00, Rs 500, etc.)
        if re.search(r'[\$£€₹]|^Rs\.?\s*\d|^\d+\.\d{2}$', name):
            return False
        
        # Reject if it's just a number
        if re.match(r'^\d+$', name):
            return False

        # Reject known bad keywords or platform names
        name_lower = name.lower()
        for word in self.reject_words:
            if word in name_lower:
                return False
        
        # Stricter platform check (catches "Sort My Scene", "Skill Box", etc.)
        platforms_regex = r'book\s*my\s*show|meet\s*up|swiggy|sort\s*my\s*scene|skill\s*box|district|urbanaut|mera\s*events|insider'
        if re.search(platforms_regex, name_lower):
            return False
        
        # Reject double commas (e.g. "Actor,,Anchor")
        if ',,' in name:
            return False
            
        # Reject if more than 2 commas (likely a list/description)
        if name.count(',') > 2:
            return False
        
        return True

    def normalize_name(self, name):
        """Clean and standardize organizer name."""
        if not isinstance(name, str):
            return ""
        name = name.strip()
        
        # Remove leading numbers + separator (e.g. "145 - SKY HOSPITALITY")
        name = re.sub(r'^\d+\s*[-–—:]\s*', '', name)
        
        # Remove trailing suffixes
        name = re.sub(r'\s+(India|Pvt\.?\s*Ltd\.?|Private\s+Limited|LLP|Inc\.?)$', '', name, flags=re.IGNORECASE)
        
        # Remove HTML
        name = re.sub(r'<[^>]*>', '', name)
        
        # Collapse whitespace
        name = ' '.join(name.split())
        
        # Title case
        name = name.title()
        
        return name

    def extract_organizers(self):
        """Phase 1: Aggregate data from all excel files in exports folder."""
        organizers = {}
        files = [f for f in os.listdir(self.exports_dir) if f.endswith('.xlsx') and not f.startswith('~$') and 'organizers_master' not in f]
        
        # Try to load existing data from master to avoid re-scanning everything
        if os.path.exists(self.master_path):
            try:
                master_df = pd.read_excel(self.master_path)
                for _, row in master_df.iterrows():
                    name = str(row['Organizer Name'])
                    # Apply strict validation even to existing rows to clean up junk
                    if not self.is_valid_organizer(name):
                        continue
                        
                    organizers[name] = {
                        'Total Events': row.get('Total Events Organized', row.get('Total Events', 0)),
                        'Cities Active': set(str(row.get('Cities Active In', row.get('Cities Active', ''))).split(', ')) if pd.notna(row.get('Cities Active In', row.get('Cities Active'))) else set(),
                        'Platforms Used': set(str(row.get('Platforms Used', '')).split(', ')) if pd.notna(row.get('Platforms Used')) else set(),
                        'Timeline': row.get('Timeline', datetime.now().strftime('%Y-%m')),
                        'Verification Status': row.get('Verification Status', 'Unverified'),
                        'Instagram URL': row.get('Instagram URL', 'Pending'),
                        'LinkedIn URL': row.get('LinkedIn URL', 'Pending'),
                        'Website': row.get('Official Website', row.get('Website', 'Pending')),
                        'Email': row.get('Contact Email', row.get('Email', 'Pending')),
                        'Phone': row.get('Phone Number', row.get('Phone', 'Pending')),
                        'Discovery Method': row.get('Discovery Method', 'Initial Extraction'),
                        'Confidence Score': row.get('Confidence Score', 10)
                    }
                print(f"  Loaded and cleaned {len(organizers)} existing organizers from master.")
                
                # Filter files to only process those newer than the master file
                mtime_master = os.path.getmtime(self.master_path)
                files = [f for f in files if os.path.getmtime(os.path.join(self.exports_dir, f)) > mtime_master]
            except Exception as e:
                print(f"  Could not load master for optimization: {e}")

        print(f"  Scanning {len(files)} new/updated export files...")
        
        for file in files:
            file_path = os.path.join(self.exports_dir, file)
            try:
                # Detect platform from filename
                platform = "Unknown"
                f_lower = file.lower()
                if "bookmyshow" in f_lower: platform = "BookMyShow"
                elif "meetup" in f_lower: platform = "Meetup"
                elif "district" in f_lower: platform = "District"
                elif "skillbox" in f_lower: platform = "SkillBox"
                elif "swiggy" in f_lower: platform = "Swiggy"
                elif "mera" in f_lower and "events" in f_lower: platform = "MeraEvents"
                elif "sort" in f_lower and "scene" in f_lower: platform = "SortMyScene"
                elif "urbanaut" in f_lower: platform = "Urbanaut"

                df = pd.read_excel(file_path)
                
                # Case insensitive column mapping
                cols = {c.lower(): c for c in df.columns}
                target_col = None
                if 'organizer' in cols: target_col = cols['organizer']
                elif 'artist' in cols: target_col = cols['artist']
                
                city_col = cols.get('city')
                
                if target_col:
                    # Get common city for this file
                    file_city = "Unknown"
                    if city_col and not df[city_col].dropna().empty:
                        file_city = df[city_col].dropna().iloc[0]

                    for name in df[target_col].dropna():
                        if self.is_valid_organizer(str(name)):
                            clean_name = self.normalize_name(str(name))
                            if clean_name not in organizers:
                                organizers[clean_name] = {
                                    'Total Events': 0,
                                    'Cities Active': set(),
                                    'Platforms Used': set(),
                                    'Timeline': f"{time.strftime('%Y-%m')}",
                                    'Verification Status': 'Unverified',
                                    'Instagram URL': 'Pending',
                                    'LinkedIn URL': 'Pending',
                                    'Website': 'Pending',
                                    'Email': 'Pending',
                                    'Phone': 'Pending',
                                    'Discovery Method': 'Initial Extraction',
                                    'Confidence Score': 10
                                }
                            
                            organizers[clean_name]['Total Events'] += 1
                            if file_city != "Unknown": organizers[clean_name]['Cities Active'].add(str(file_city))
                            if platform != "Unknown": organizers[clean_name]['Platforms Used'].add(platform)
            except Exception:
                continue

        # Convert sets to strings for Excel
        master_data = []
        for name, data in organizers.items():
            row = {
                'Organizer Name': name,
                'Total Events Organized': data['Total Events'],
                'Cities Active In': ", ".join(sorted([c for c in data['Cities Active'] if c != 'Unknown'])),
                'Platforms Used': ", ".join(sorted([p for p in data['Platforms Used'] if p != 'Unknown'])),
                'Timeline': data['Timeline'],
                'Verification Status': data['Verification Status'],
                'Instagram URL': data['Instagram URL'],
                'LinkedIn URL': data['LinkedIn URL'],
                'Official Website': data['Website'],
                'Contact Email': data['Email'],
                'Phone Number': data['Phone'],
                'Discovery Method': data['Discovery Method'],
                'Confidence Score': data['Confidence Score']
            }
            master_data.append(row)

        final_df = pd.DataFrame(master_data)
        if not final_df.empty:
            final_df = final_df.sort_values(by='Total Events Organized', ascending=False)
        return final_df

    def run(self):
        print("[PHASE 1] Scanning exports and extracting organizers...")
        master_df = self.extract_organizers()
        if master_df.empty:
            print("No valid organizers found.")
            return
        
        print(f"  Consolidated {len(master_df)} unique organizers.")
        
        # Save results
        try:
            master_df.to_excel(self.master_path, index=False)
            print(f"  Master database updated: {self.master_path}")
        except PermissionError:
            ts = datetime.now().strftime("%H%M%S")
            fallback = self.master_path.replace('.xlsx', f'_{ts}.xlsx')
            master_df.to_excel(fallback, index=False)
            self.master_path = fallback
            print(f"  Permission denied. Saved to: {fallback}")

if __name__ == "__main__":
    OrganizerProcessor().run()
