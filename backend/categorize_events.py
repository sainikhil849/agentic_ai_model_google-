import pandas as pd
import os
import glob
import logging
import re
from openpyxl import load_workbook

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expanded Category definitions with comprehensive keywords
CATEGORIES = {
    'AI': [
        r'\bai\b', 'artificial intelligence', 'machine learning', r'\bml\b', 'deep learning', 
        r'\bllm\b', 'gpt', 'neural network', 'nlp', 'computer vision', 'robotics', 
        'automation', 'openai', 'midjourney', 'stable diffusion', 'generative ai', 'chatbot'
    ],
    'Tech': [
        'tech', 'technology', 'coding', 'programming', 'developer', 'software', 'hardware', 
        'blockchain', 'crypto', 'web3', 'cloud', 'devops', 'data science', 'python', 
        'javascript', 'react', 'node', 'java', 'cybersecurity', 'digital', 'mobile app', 
        'api', 'saas', 'infrastructure', 'it', 'hacker', 'encryption', 'metaverse'
    ],
    'Startup': [
        'startup', 'founder', r'\bvc\b', 'venture capital', 'pitch', 'entrepreneur', 
        'incubation', 'accelerator', 'equity', 'angel investor', 'seed funding', 
        'series a', 'unicorn', 'growth hack', 'scaleup', 'business model'
    ],
    'Business': [
        'business', 'finance', 'management', 'corporate', 'strategy', 'marketing', 
        'sales', 'leadership', r'\bceo\b', r'\bcfo\b', 'economic', 'investment', 
        'real estate', 'trading', 'stock market', 'professional', 'career', 'job', 
        'enterprise', 'b2b', 'consulting', 'networking'
    ],
    'Workshop': [
        'workshop', 'masterclass', 'class', 'tutorial', 'training', 'boot camp', 
        'coaching', 'learning', 'session', 'course', 'certification', 'skill', 
        'learn', 'teaching', 'education', 'academy', 'seminar', 'webinar'
    ],
    'Networking': [
        'networking', 'meetup', 'mixer', 'social', 'connect', 'community gathering', 
        'circle', 'club', 'membership', 'referral', 'interaction', 'partnership', 
        'collab', 'meet & greet', 'mingle'
    ],
    'Comedy': [
        'comedy', 'standup', 'stand-up', 'funny', 'laughter', 'comic', 'jokes', 
        'open mic', 'improv', 'roast', 'satire', 'humor', 'gag'
    ],
    'Music': [
        'music', 'concert', 'gig', r'\bdj\b', 'band', 'singer', 'musical', 
        'live performance', 'karaoke', 'acoustic', 'bollywood night', r'\bedm\b', 
        'jazz', 'rock', 'pop', 'hip hop', 'symphony', 'orchestra', 'ghazal', 'sufi', 
        'unplugged', 'rhythm', 'beat', 'remix', 'playback'
    ],
    'Nightlife': [
        'nightlife', 'club', 'party', 'pub', 'bar', 'lounge', 'disco', 'dance floor', 
        'social house', 'afterparty', 'ladies night', 'happy hour', 'soiree', 'ball', 
        'prom', 'gala', 'rave', 'vibe'
    ],
    'Food': [
        'food', 'wine', 'tasting', 'culinary', 'cooking', 'brunch', 'dinner', 
        'festival food', 'beer', 'restaurant', 'chef', 'pizza', 'coffee', 'cafe', 
        'cocktail', 'whiskey', 'beverage', 'cuisine', 'bakery', 'dessert'
    ],
    'Art': [
        'art', 'painting', 'sketch', 'drawing', 'exhibition', 'gallery', 'craft', 
        'pottery', 'photography', 'theater', 'drama', 'play', 'creative', 'design', 
        'fashion', 'jewelry', 'sculpture', 'poetry', 'literature', 'book', 'author', 
        'movie', 'cinema', 'film', 'acting'
    ],
    'Fitness': [
        'fitness', 'yoga', 'gym', 'marathon', 'run', 'cycling', 'sports', 
        'badminton', 'cricket', 'football', 'workout', 'health', 'pilates', 'zumba', 
        'trekking', 'camping', 'hiking', 'adventure', 'wellness', 'aerobics'
    ],
    'Spiritual': [
        'spiritual', 'meditation', 'soul', 'peace', 'divine', 'temple', 'puja', 
        'satsang', 'healing', 'wellness', 'inner peace', 'astrology', 'tarot', 
        'god', 'prayer', 'zen', 'consciousness'
    ],
    'Education': [
        'education', 'school', 'college', 'university', 'student', 'research', 
        'science', 'history', 'lecture', 'talk', 'seminar', 'upskilling', 'career', 
        'scholarship', 'academic', 'study', 'exam'
    ],
    'Festival': [
        'festival', 'fest', 'mela', 'carnival', 'celebration', 'annual meet', 
        'expo', 'fair', 'parade', 'bazaar', 'gathering'
    ],
    'Community': [
        'community', 'volunteer', 'charity', 'cause', 'awareness', r'\bngo\b', 
        'social work', 'group', 'initiative', 'donation', 'support', 'help', 
        'fundraiser', 'environment'
    ],
}

# Fallback mappings for broad terms that might otherwise end up in "Other"
FALLBACK_KEYWORDS = {
    'Art': ['exhibition', 'show', 'creative', 'exhibit', 'display', 'viewing', 'movie', 'film'],
    'Networking': ['meet', 'gathering', 'social', 'meetup', 'mixer', 'circle'],
    'Workshop': ['session', 'talk', 'learn', 'how to', 'guide', 'basics'],
    'Business': ['professional', 'summit', 'conference', 'forum', 'conclave'],
    'Festival': ['celebration', 'fest', 'carnival', 'mela'],
    'Community': ['group', 'people', 'friends', 'together'],
}

def get_category_v2(row):
    """
    More intelligent classification using both Event Name and Description.
    """
    event_name = str(row.get('Event Name', '')).lower()
    description = str(row.get('Description', '')).lower()
    
    # Combined text for analysis
    text = event_name + " " + (description if description != 'n/a' else "")
    
    scores = {cat: 0 for cat in CATEGORIES.keys()}
    
    # 1. Direct match with weighted scores
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.startswith(r'\b'):
                if re.search(kw, text):
                    # Higher weight for Event Name matches
                    if re.search(kw, event_name):
                        scores[category] += 5
                    else:
                        scores[category] += 2
            elif kw in text:
                if kw in event_name:
                    scores[category] += 3
                else:
                    scores[category] += 1
                    
    # 2. Check for the best score
    max_score = max(scores.values())
    if max_score > 0:
        # Get all categories with the max score and pick the first one
        best_cats = [cat for cat, score in scores.items() if score == max_score]
        return best_cats[0]
    
    # 3. Fallback logic if still 0
    for category, keywords in FALLBACK_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
                
    # 4. Default categories based on common event structures if still unknown
    if any(word in event_name for word in ['summit', 'conference', 'expo']):
        return 'Business'
    if any(word in event_name for word in ['class', 'masterclass', 'session']):
        return 'Workshop'
    if any(word in event_name for word in ['party', 'night']):
        return 'Nightlife'
    if any(word in event_name for word in ['show', 'exhibition']):
        return 'Art'
    
    return 'Other'

def process_city_file(filepath):
    """
    Process a single city Excel file: categorize, deduplicate, and organize into sheets.
    """
    logger.info(f"Processing file: {filepath}")
    
    try:
        # 1. Read the exported file
        df = pd.read_excel(filepath)
        
        if df.empty:
            logger.warning(f"File {filepath} is empty. Skipping.")
            return

        # 2. Remove duplicates (event_name + date + venue)
        dup_subset = ['Event Name', 'Date', 'Venue']
        available_cols = df.columns.tolist()
        subset_to_use = [c for c in dup_subset if c in available_cols]
        
        before_count = len(df)
        df = df.drop_duplicates(subset=subset_to_use, keep='first')
        after_count = len(df)
        logger.info(f"Deduplication: {before_count} -> {after_count} events")

        # 3. Categorize events using the enhanced logic
        logger.info("Applying intelligent categorization...")
        df['Category'] = df.apply(get_category_v2, axis=1)

        # 4. Prepare categorized data frames
        category_dfs = {}
        # Get all unique categories present in the data
        present_categories = df['Category'].unique()
        
        for category in present_categories:
            cat_df = df[df['Category'] == category].copy()
            if not cat_df.empty:
                category_dfs[category] = cat_df

        # 5. Create Category Summary
        summary_data = []
        for cat, cat_df in category_dfs.items():
            summary_data.append({'Category': cat, 'Event Count': len(cat_df)})
        
        summary_df = pd.DataFrame(summary_data).sort_values(by='Event Count', ascending=False)

        # 6. Save back to the same Excel file with multiple sheets
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Main sheet with all events
            df.to_excel(writer, sheet_name='All_Events', index=False)
            
            # Summary sheet
            summary_df.to_excel(writer, sheet_name='Category_Summary', index=False)
            
            # Individual category sheets
            # Sort categories so important ones come first
            sorted_cats = sorted(category_dfs.keys(), key=lambda x: (x == 'Other', x))
            for cat in sorted_cats:
                cat_df = category_dfs[cat]
                # Sheet names have a 31 char limit
                sheet_name = cat[:31]
                cat_df.to_excel(writer, sheet_name=sheet_name, index=False)

        logger.info(f"Successfully categorized {filepath}")

    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}")

def main():
    exports_dir = os.path.join(os.getcwd(), 'exports')
    if not os.path.exists(exports_dir):
        exports_dir = 'exports'
    
    pattern = os.path.join(exports_dir, 'Events_Database_*.xlsx')
    files = glob.glob(pattern)
    
    if not files:
        files = glob.glob('Events_Database_*.xlsx')
    
    if not files:
        logger.error("No export files found to categorize.")
        return

    logger.info(f"Found {len(files)} files to process.")
    
    for f in files:
        if os.path.basename(f).startswith('~$'):
            continue
        process_city_file(f)

    logger.info("Intelligence Categorization Layer processing complete.")

if __name__ == "__main__":
    main()
