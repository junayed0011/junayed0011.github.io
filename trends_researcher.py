import urllib.request
import xml.etree.ElementTree as ET
import random
import re

# ─────────────────────────────────────────────────────────────────────────────
# RSS FEED SOURCES — Multiple feeds per category for better topic diversity
# ─────────────────────────────────────────────────────────────────────────────
FEEDS = {
    "tech": [
        "https://techcrunch.com/feed/",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss",
    ],
    "finance": [
        "https://finance.yahoo.com/news/rssindex",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.investing.com/rss/news.rss",
    ],
    "lifestyle": [
        "https://www.health.com/feed",
        "https://feeds.feedburner.com/MindBodyGreen",
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
        "https://feeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
    ],
    "mindset": [
        "https://feeds.hbr.org/harvardbusiness",
        "https://www.psychologytoday.com/us/front/feed",
        "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US",
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD FILTERS — Must match these to be considered "on-topic"
# ─────────────────────────────────────────────────────────────────────────────
KEYWORDS = {
    "tech": [
        "ai", "artificial intelligence", "machine learning", "llm", "chatgpt", "openai",
        "automation", "saas", "software", "developer", "cybersecurity", "cloud", "startup",
        "coding", "nvidia", "robot", "data", "chip", "semiconductor", "tech"
    ],
    "finance": [
        "stock", "invest", "market", "fund", "crypto", "bitcoin", "economy", "inflation",
        "dividend", "interest rate", "federal reserve", "retirement", "savings", "portfolio",
        "wealth", "passive income", "real estate", "side hustle", "budget", "financial"
    ],
    "lifestyle": [
        "health", "wellness", "sleep", "diet", "nutrition", "exercise", "workout", "mental health",
        "habit", "routine", "stress", "weight", "skin", "supplement", "vitamin", "longevity",
        "fitness", "mindfulness", "gut health", "immune"
    ],
    "mindset": [
        "productivity", "focus", "discipline", "motivation", "habit", "mindset", "success",
        "procrastination", "goal", "performance", "leadership", "learning", "growth",
        "resilience", "confidence", "decision", "cognitive", "brain", "psychology"
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# HIGH-QUALITY STATIC FALLBACKS — Used when all network sources fail
# These are evergreen, high-search-volume topics per category
# ─────────────────────────────────────────────────────────────────────────────
STATIC_FALLBACKS = {
    "tech": [
        {
            "title": "How AI Agents Are Replacing Traditional Software in 2025",
            "description": "Agentic AI systems can now browse the web, write code, and execute multi-step tasks autonomously — changing how businesses operate.",
            "link": ""
        },
        {
            "title": "The Best Cybersecurity Practices Every Remote Worker Must Follow",
            "description": "With remote work now standard, cybersecurity threats have multiplied. Here's what security experts recommend to stay protected.",
            "link": ""
        },
        {
            "title": "Nvidia's Latest GPU Architecture Is Changing AI Development Forever",
            "description": "Nvidia's dominance in AI chips continues with breakthroughs in VRAM efficiency, throughput, and edge inference capabilities.",
            "link": ""
        }
    ],
    "finance": [
        {
            "title": "7 Proven Investing Strategies to Build Wealth in Any Market",
            "description": "From index fund laddering to dividend reinvestment plans, these time-tested strategies work regardless of market conditions.",
            "link": ""
        },
        {
            "title": "How to Pay Off Debt Fast: A Step-by-Step Financial Freedom Plan",
            "description": "The avalanche and snowball methods compared with real data on which approach saves more money in the long run.",
            "link": ""
        },
        {
            "title": "Passive Income Ideas That Actually Work in 2025 (With Real Numbers)",
            "description": "From dividend ETFs to digital products and rental income — the honest numbers behind popular passive income streams.",
            "link": ""
        }
    ],
    "lifestyle": [
        {
            "title": "Science-Backed Sleep Optimization: How to Wake Up Energized Every Morning",
            "description": "Sleep researchers at Stanford reveal the five evidence-based techniques that dramatically improve sleep quality and daytime performance.",
            "link": ""
        },
        {
            "title": "The Truth About Ultra-Processed Foods and Your Long-Term Health",
            "description": "A landmark study tracking 100,000 participants reveals what eating ultra-processed foods does to your brain and body over time.",
            "link": ""
        },
        {
            "title": "Biohacking Your Morning Routine: What Top Performers Do Before 9AM",
            "description": "Cold exposure, light therapy, and targeted nutrition — what the science actually says about high-performance morning protocols.",
            "link": ""
        }
    ],
    "mindset": [
        {
            "title": "The Power of Micro-Habits: Why Small Actions Beat Big Goals Every Time",
            "description": "Behavioral scientist BJ Fogg's research proves that tiny habits, not willpower, are the foundation of lasting behavioral change.",
            "link": ""
        },
        {
            "title": "Deep Work vs. Shallow Work: How to Protect Your Most Valuable Hours",
            "description": "Cal Newport's principles applied to modern remote work — with concrete scheduling frameworks to triple focused output.",
            "link": ""
        },
        {
            "title": "Why Your Brain Resists Change (And 5 Ways to Overcome It)",
            "description": "Neuroscience explains why new habits feel painful and how to rewire your prefrontal cortex for growth mindset.",
            "link": ""
        }
    ]
}


def fetch_feed_data(url):
    """Fetch raw XML data from RSS feed using standard library with timeout."""
    try:
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            return response.read()
    except Exception as e:
        print(f"[RSS] Error fetching feed {url}: {e}")
        return None

def parse_rss_items(xml_data):
    """Parse XML and extract clean title, description, and links."""
    items = []
    if not xml_data:
        return items
    try:
        root = ET.fromstring(xml_data)
        # Handle both RSS 2.0 and Atom formats
        for item in root.findall('.//item'):
            title_el = item.find('title')
            desc_el = item.find('description')
            link_el = item.find('link')
            
            title_text = title_el.text.strip() if title_el is not None and title_el.text else ""
            desc_text = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
            link_text = link_el.text.strip() if link_el is not None and link_el.text else ""
            
            # Strip CDATA/HTML from description
            desc_text = re.sub(r'<[^<]+?>', '', desc_text)
            desc_text = re.sub(r'\s+', ' ', desc_text).strip()
            
            # Skip very short or empty titles
            if title_text and len(title_text) > 10:
                items.append({
                    "title": title_text,
                    "description": desc_text[:500],  # Cap description length
                    "link": link_text
                })
    except Exception as e:
        print(f"[RSS] XML parsing error: {e}")
    return items

def score_item(item, keywords):
    """Score an item by how many category keywords it contains. Higher = better match."""
    combined = (item["title"] + " " + item["description"]).lower()
    return sum(1 for kw in keywords if kw in combined)

def get_trending_topic(category):
    """
    Fetch trending headlines for a specific category from multiple RSS sources.
    
    Priority:
    1. Best keyword-matched item from any live RSS feed
    2. Random item from any live feed (if no keyword match)
    3. Random high-quality static fallback
    """
    print(f"[NICHE] Researching real-time trending topics for: {category.upper()}...")
    urls = FEEDS.get(category, [])
    category_keywords = KEYWORDS.get(category, [])
    
    all_matched = []  # (score, item) tuples from all feeds
    all_items = []    # fallback pool

    # Try all feeds in parallel-ish (sequential with early exit)
    for url in urls:
        raw_xml = fetch_feed_data(url)
        if not raw_xml:
            continue
        parsed_items = parse_rss_items(raw_xml)
        if not parsed_items:
            continue
        
        all_items.extend(parsed_items)
        for item in parsed_items:
            score = score_item(item, category_keywords)
            if score > 0:
                all_matched.append((score, item))
    
    # Return the highest-scoring keyword match
    if all_matched:
        all_matched.sort(key=lambda x: x[0], reverse=True)
        selected = all_matched[0][1]
        print(f"[LIVE TREND] Best match (score={all_matched[0][0]}): {selected['title']}")
        return selected
    
    # No keyword match — return random from any feed
    if all_items:
        selected = random.choice(all_items)
        print(f"[FEED ITEM] Random feed item (no keyword match): {selected['title']}")
        return selected
    
    # All network sources offline — use a random high-quality static fallback
    fallbacks = STATIC_FALLBACKS.get(category, list(STATIC_FALLBACKS.values())[0])
    selected = random.choice(fallbacks)
    print(f"[STATIC FALLBACK] All feeds offline — using: {selected['title']}")
    return selected


if __name__ == "__main__":
    # Test execution — run each category and print the selected topic
    for cat in ["tech", "finance", "lifestyle", "mindset"]:
        topic = get_trending_topic(cat)
        print(f"\nCategory: {cat}")
        print(f"  Title: {topic['title']}")
        print(f"  Desc:  {topic['description'][:100]}...")
