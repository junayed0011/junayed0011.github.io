import urllib.request
import xml.etree.ElementTree as ET
import random
import re

FEEDS = {
    "tech": [
        "https://techcrunch.com/feed/",
        "https://www.wired.com/feed/rss"
    ],
    "finance": [
        "https://finance.yahoo.com/news/rssindex"
    ],
    "lifestyle": [
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    ],
    "mindset": [
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    ]
}

KEYWORDS = {
    "tech": ["ai", "tech", "software", "development", "cybersecurity", "google", "apple", "app", "meta", "nvidia", "artificial intelligence", "coding", "web", "robotics"],
    "finance": ["money", "stock", "invest", "crypto", "bitcoin", "budget", "saving", "cash", "wealth", "interest", "inflation", "market", "gold", "bank"],
    "lifestyle": ["health", "workout", "sleep", "diet", "nutrition", "fitness", "wellness", "habit", "recipe", "travel", "nature", "meditation"],
    "mindset": ["mindset", "focus", "productive", "motivation", "routine", "discipline", "mindfulness", "brain", "habit", "success", "goal", "learn"]
}

def fetch_feed_data(url):
    """Fetch raw XML data from RSS feed using standard library."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"[ERROR] Error fetching RSS feed {url}: {e}")
        return None

def parse_rss_items(xml_data):
    """Parse XML and extract clean title, description, and links."""
    items = []
    if not xml_data:
        return items
    try:
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item'):
            title = item.find('title')
            description = item.find('description')
            link = item.find('link')
            
            title_text = title.text.strip() if title is not None and title.text else ""
            desc_text = description.text.strip() if description is not None and description.text else ""
            link_text = link.text.strip() if link is not None and link.text else ""
            
            # HTML tags cleanup from description
            desc_text = re.sub('<[^<]+?>', '', desc_text)
            
            if title_text:
                items.append({
                    "title": title_text,
                    "description": desc_text,
                    "link": link_text
                })
    except Exception as e:
        print(f"[ERROR] XML parsing error: {e}")
    return items

def get_trending_topic(category):
    """
    Fetch trending search queries or headlines for a specific category.
    Fallback to static popular topics if networks fail.
    """
    print(f"[NICHE] Researching real-time trending topics for niche: {category.upper()}...")
    urls = FEEDS.get(category, [])
    
    # Try fetching dynamic trends from real-time feeds
    for url in urls:
        raw_xml = fetch_feed_data(url)
        parsed_items = parse_rss_items(raw_xml)
        
        if parsed_items:
            # Filter and match items based on category keywords
            matched_items = []
            category_keywords = KEYWORDS.get(category, [])
            
            for item in parsed_items:
                combined_text = (item["title"] + " " + item["description"]).lower()
                # Check for keyword match
                for keyword in category_keywords:
                    if keyword in combined_text:
                        matched_items.append(item)
                        break
            
            # If we found matched items, return a random one
            if matched_items:
                selected = random.choice(matched_items)
                print(f"[LIVE TREND] Live Trend Found inside {url}: {selected['title']}")
                return selected
            
            # Fallback to random item from the feed if no exact match but feed exists
            selected = random.choice(parsed_items)
            print(f"[FEED ITEM] Feed item retrieved inside {url}: {selected['title']}")
            return selected
            
    # Ultimate static fallback if all network resources are offline
    static_fallbacks = {
        "tech": {
            "title": "How Artificial Intelligence is Changing Everyday Creative Work",
            "description": "Exploring how developers, designers, and writers are utilizing generative models to double creative output.",
            "link": ""
        },
        "finance": {
            "title": "Proven Investing Strategies to Outpace Rising Market Inflation",
            "description": "A beginner-friendly analysis of compound index tracking, dividend stocks, and high-yield savings cash reserves.",
            "link": ""
        },
        "lifestyle": {
            "title": "Science-Backed Sleep Habits to Optimize Daily Cognitive Energy",
            "description": "How evening blue-light blockades and temperature shifts restore natural circadian rhythm cycles.",
            "link": ""
        },
        "mindset": {
            "title": "The Power of Micro-Habits: Small Daily Routine Upgrades That Scale",
            "description": "How to beat systemic procrastination and mental blocks through progressive 5-minute atomic action chains.",
            "link": ""
        }
    }
    
    fallback = static_fallbacks.get(category)
    print(f"[STATIC FALLBACK] Returning high-converting static fallback topic: {fallback['title']}")
    return fallback

if __name__ == "__main__":
    # Test execution
    for cat in ["tech", "finance", "lifestyle", "mindset"]:
        topic = get_trending_topic(cat)
        print(f"Category: {cat} -> Title: {topic['title']}\n")
