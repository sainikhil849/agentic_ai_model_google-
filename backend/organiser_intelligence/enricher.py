import os
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class OrganizerEnricher:
    def __init__(self, exports_dir=None, master_path=None, batch_size=20):
        if exports_dir is None:
            self.exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
        else:
            self.exports_dir = exports_dir
        if master_path:
            self.master_path = master_path
        else:
            self.master_path = os.path.join(self.exports_dir, 'organizers_master.xlsx')
        # How many organizers to enrich per run
        self.batch_size = batch_size

    def _search_google(self, page, query):
        """Use Playwright to search DuckDuckGo (more reliable for scraping than Google)."""
        links = []
        try:
            # DuckDuckGo doesn't block headless as much and has a simple layout
            search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
            print(f"    Searching: {query}")
            page.goto(search_url, timeout=20000)
            
            # Wait for results to appear
            try:
                page.wait_for_selector('a[data-testid="result-title-a"]', timeout=10000)
            except:
                pass
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # DuckDuckGo result titles/links
            for a_tag in soup.select('a[data-testid="result-title-a"]'):
                href = a_tag.get('href', '')
                if href.startswith('http') and not any(x in href.lower() for x in ['duckduckgo.com', 'google.com']):
                    if href not in links:
                        links.append(href)
                if len(links) >= 5:
                    break
                    
            if not links:
                # Fallback: check all links on page that look like external links
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if href.startswith('http') and not any(x in href.lower() for x in ['duckduckgo.com', 'google.com', 'bing.com', 'apple.com']):
                        if href not in links:
                            links.append(href)
                    if len(links) >= 5:
                        break

            if not links:
                print("    Warning: No links found for query.")
        except Exception as e:
            print(f"    Search error: {e}")
        return links

    def _is_valid_page(self, soup, organizer_name, city):
        """Check if the page content actually belongs to the organizer."""
        text = soup.get_text(separator=' ').lower()
        title = soup.title.string.lower() if soup.title else ""
        name_lower = organizer_name.lower()
        
        # Must contain organizer name in text or title
        if name_lower not in text and name_lower not in title:
            # Check for partial match if name is long
            words = name_lower.split()
            if len(words) > 2:
                partial = " ".join(words[:2])
                if partial not in text and partial not in title:
                    return False, 0
            else:
                return False, 0
            
        score = 30 # Base score for having the name
        
        # Bonus for city name
        if city and city.lower() in text:
            score += 20
            
        # Bonus for event-related keywords
        keywords = ['event', 'workshop', 'ticket', 'booking', 'contact', 'about us', 'follow', 'organizer', 'host', 'artist', 'show']
        matches = [kw for kw in keywords if kw in text]
        score += min(len(matches) * 5, 25)
        
        # High confidence if name is in the title
        if name_lower in title:
            score += 30
            
        # Bonus for having social links on the page
        if soup.find('a', href=re.compile(r'instagram\.com|linkedin\.com|facebook\.com')):
            score += 15
            
        return score >= 45, score

    def _extract_page_data(self, page, url, organizer_name, city):
        """Visit a URL and extract emails, phones, and social links with validation."""
        data = {'emails': [], 'phones': [], 'instagram': None, 'linkedin': None, 'is_valid': False, 'score': 0}
        try:
            print(f"    Visiting: {url}")
            # Increased timeout and wait_until to handle slower/complex sites
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(2) # Wait for dynamic content
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            is_valid, score = self._is_valid_page(soup, organizer_name, city)
            data['is_valid'] = is_valid
            data['score'] = score
            
            if not is_valid:
                print(f"      Validation failed (Score: {score}). Skipping content extraction.")
                return data

            text = soup.get_text(separator=' ')
            
            # Also check meta description/keywords
            meta_desc = ""
            desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            if desc_tag:
                meta_desc = desc_tag.get('content', '')
                text += " " + meta_desc

            # Extract emails
            email_matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', text)
            for match in email_matches:
                if not any(x in match.lower() for x in ['png', 'jpg', 'gif', 'sentry', 'wixpress', 'example', 'domain', 'email.com']):
                    if match not in data['emails']:
                        data['emails'].append(match)

            # Extract phones (+91 format or 10-digit)
            phone_matches = re.findall(r'\+91[\s\-]?\d{5}[\s\-]?\d{5}|\b\d{10}\b', text)
            for match in phone_matches:
                if match not in data['phones']:
                    data['phones'].append(match.strip())

            # Extract social links from all anchor tags
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].lower()
                if 'instagram.com/' in href and not data['instagram']:
                    if not any(x in href for x in ['/explore/', '/p/', '/reels/', '/direct/']):
                        data['instagram'] = a_tag['href']
                elif 'linkedin.com/company/' in href and not data['linkedin']:
                    data['linkedin'] = a_tag['href']
                elif 'linkedin.com/in/' in href and not data['linkedin']:
                    data['linkedin'] = a_tag['href']
                    
        except Exception as e:
            print(f"      Visit failed: {e}")
        return data

    def enrich_organizer(self, row, page):
        """STEP 7-10: Active discovery for a single organizer."""
        row_copy = row.copy()
        name = row_copy['Organizer Name']
        city = str(row_copy.get('Cities Active In', '')).split(',')[0].strip()

        print(f"  Enriching: {name} ({city})")

        # Better queries to find specific social profiles
        queries = [
            f'"{name}" official website {city}',
            f'"{name}" instagram profile {city}',
            f'"{name}" linkedin page {city}',
            f'"{name}" contact email phone',
        ]

        all_links = []
        for q in queries:
            results = self._search_google(page, q)
            all_links.extend(results)
            time.sleep(2)

        unique_links = []
        seen = set()
        
        # Platforms to avoid for the "Website" field but allow for social extraction
        junk_domains = [
            'duckduckgo.com', 'google.com', 'bing.com', 'apple.com', 'internshala.com', 
            'justdial.com', 'indiamart.com', 'bookmyshow.com', 'insider.in', 'skillbox.co',
            'townscript.com', 'meetup.com', 'facebook.com', 'youtube.com', 'twitter.com',
            'pinterest.com', 'yelp.com', 'mapsofindia.com', 'zaubacorp.com', 'tofler.in'
        ]

        for link in all_links:
            link_lower = link.lower()
            if link not in seen:
                # Direct match for social profiles from URL
                if 'instagram.com/' in link_lower and name.lower().replace(" ", "") in link_lower.replace("-", "").replace("_", ""):
                    if row_copy.get('Instagram URL') == 'Pending':
                        row_copy['Instagram URL'] = link
                elif 'linkedin.com/' in link_lower and name.lower().replace(" ", "") in link_lower.replace("-", "").replace("_", ""):
                    if row_copy.get('LinkedIn URL') == 'Pending':
                        row_copy['LinkedIn URL'] = link
                
                # Add to unique links for visiting if not a platform or if it's a potential official site
                if not any(jd in link_lower for jd in junk_domains) or 'instagram.com/' in link_lower or 'linkedin.com/' in link_lower:
                    seen.add(link)
                    unique_links.append(link)

        # Visit top results (limit to 5)
        for url in unique_links[:5]:
            data = self._extract_page_data(page, url, name, city)

            if not data['is_valid']:
                continue

            if data['instagram'] and row_copy.get('Instagram URL') == 'Pending':
                row_copy['Instagram URL'] = data['instagram']
            if data['linkedin'] and row_copy.get('LinkedIn URL') == 'Pending':
                row_copy['LinkedIn URL'] = data['linkedin']
            if data['emails'] and row_copy.get('Contact Email') == 'Pending':
                row_copy['Contact Email'] = data['emails'][0]
            if data['phones'] and row_copy.get('Phone Number') == 'Pending':
                row_copy['Phone Number'] = data['phones'][0]

            if row_copy.get('Official Website') == 'Pending':
                # Only set as website if it's not a major platform
                if not any(x in url.lower() for x in ['instagram.com', 'linkedin.com', 'facebook.com', 'youtube.com', 'meetup.com', 'bookmyshow.com']):
                    row_copy['Official Website'] = url

        # STEP 10: Set verification status
        found_something = any(row_copy.get(col) != 'Pending' for col in ['Instagram URL', 'LinkedIn URL', 'Official Website', 'Contact Email'])
        if found_something:
            row_copy['Verification Status'] = 'Verified'
            row_copy['Discovery Method'] = 'Web Discovery (High Accuracy)'
            
            # Scoring logic
            score = 40
            if row_copy.get('Instagram URL') != 'Pending': score += 20
            if row_copy.get('Official Website') != 'Pending': score += 20
            if row_copy.get('LinkedIn URL') != 'Pending': score += 10
            if row_copy.get('Contact Email') != 'Pending': score += 10
            if row_copy.get('Phone Number') != 'Pending': score += 5
            row_copy['Confidence Score'] = min(score, 100)
        else:
            row_copy['Verification Status'] = 'Unverified'
            row_copy['Discovery Method'] = 'Web Discovery (No Verified Matches)'
            row_copy['Confidence Score'] = 20

        return row_copy

    def _safe_save(self, df):
        """Save Excel with retries and fallback naming."""
        max_retries = 5
        for i in range(max_retries):
            try:
                df.to_excel(self.master_path, index=False)
                return True
            except PermissionError:
                time.sleep(1)
                continue
        
        # Fallback to timestamped version
        ts = datetime.now().strftime("%H%M%S")
        dir_name = os.path.dirname(self.master_path)
        base_name = os.path.basename(self.master_path).replace('.xlsx', f'_{ts}.xlsx')
        fallback_path = os.path.join(dir_name, base_name)
        df.to_excel(fallback_path, index=False)
        print(f"  Saved to fallback: {fallback_path}")
        return True

    def run(self, start_row=None, end_row=None):
        if not os.path.exists(self.master_path):
            print("  Master file not found. Run processor first.")
            return

        df = pd.read_excel(self.master_path)

        # Allow user to specify row range
        unverified = df[df['Verification Status'].isin(['Unverified', 'Pending'])]
        if unverified.empty:
            print("  No organizers to enrich.")
            return

        if start_row is not None and end_row is not None:
            batch = df.iloc[start_row:end_row]
        else:
            batch = unverified.head(self.batch_size)
            
        print(f"  Enriching {len(batch)} organizers via browser...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            ctx = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            )
            # Increase default navigation timeout
            ctx.set_default_navigation_timeout(45000)
            page = ctx.new_page()

            for idx in batch.index:
                # If already verified, skip unless it's a re-run
                if df.loc[idx, 'Verification Status'] == 'Verified' and start_row is None:
                    continue
                    
                df.loc[idx] = self.enrich_organizer(df.loc[idx], page)
                self._safe_save(df)

            browser.close()

        verified = len(df[df['Verification Status'] == 'Verified'])
        print(f"  Done. {verified}/{len(df)} total organizers verified.")

if __name__ == "__main__":
    OrganizerEnricher().run()
