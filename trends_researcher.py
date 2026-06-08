import xml.etree.ElementTree as ET
import random
import re
import requests

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


# ─────────────────────────────────────────────────────────────────────────────
# DUPLICATE POST GUARD HELPERS FOR NICHE RESEARCH
# ─────────────────────────────────────────────────────────────────────────────
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "as", "are", "was",
    "be", "that", "this", "how", "why", "what", "who", "just", "amid",
    "into", "up", "now", "new", "amid", "time", "says", "amid"
}

def _title_keywords(title):
    words = re.findall(r'[a-z]+', title.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 2}

def is_duplicate_local(title, exclude_titles):
    if not exclude_titles:
        return False
    norm = title.strip().lower()
    if norm in exclude_titles:
        return True
    candidate_kw = _title_keywords(title)
    if not candidate_kw:
        return False
    for pub_title in exclude_titles:
        pub_kw = _title_keywords(pub_title)
        if not pub_kw:
            continue
        overlap = len(candidate_kw & pub_kw) / len(candidate_kw)
        if overlap >= 0.60:
            return True
    return False


def fetch_feed_data(url):
    """Fetch raw XML data from RSS feed using requests with timeout."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            return response.content
        else:
            print(f"[RSS] Error fetching feed {url}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[RSS] Error fetching feed {url}: {e}")
        return None

def parse_rss_items(xml_data):
    """Parse XML namespace-agnostically and extract clean title, description, and links.
    Supports both RSS 2.0 (<item>) and Atom (<entry>) formats.
    """
    items = []
    if not xml_data:
        return items
    try:
        root = ET.fromstring(xml_data)
        
        def local_name(tag):
            return tag.split('}')[-1] if '}' in tag else tag
            
        for el in root.iter():
            tag = local_name(el.tag)
            if tag in ('item', 'entry'):
                title_text = ""
                desc_text = ""
                link_text = ""
                
                for child in el:
                    child_tag = local_name(child.tag)
                    if child_tag == 'title':
                        title_text = child.text.strip() if child.text else ""
                    elif child_tag in ('description', 'summary', 'content'):
                        if not desc_text or child_tag == 'summary':
                            desc_text = child.text.strip() if child.text else ""
                    elif child_tag == 'link':
                        if child.text:
                            link_text = child.text.strip()
                        elif 'href' in child.attrib:
                            link_text = child.attrib['href'].strip()
                            
                # Clean description
                desc_text = re.sub(r'<[^>]+>', '', desc_text)
                desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                
                if title_text and len(title_text) > 10:
                    items.append({
                        "title": title_text,
                        "description": desc_text[:500],
                        "link": link_text
                    })
    except Exception as e:
        print(f"[RSS] XML parsing error: {e}")
    return items

# ─────────────────────────────────────────────────────────────────────────────
# QUESTION/GUIDE WORD BOOST — Titles containing these words are long-tail
# SEO goldmines for new sites. They rank faster and power FAQ rich results.
# ─────────────────────────────────────────────────────────────────────────────
QUESTION_BOOST_WORDS = [
    "how", "why", "what", "when", "which", "who",
    "best", "top", "vs", "guide", "tips", "ways",
    "steps", "secrets", "truth", "science", "proven"
]

def score_item(item, keywords):
    """Score an item by keyword relevance + long-tail question-word boost.
    
    Returns:
        int: keyword match count + 2 per question/guide word in title
    """
    combined = (item["title"] + " " + item["description"]).lower()
    base_score = sum(1 for kw in keywords if kw in combined)
    # Boost items whose TITLE contains question/guide words (better for long-tail SEO)
    question_boost = sum(2 for qw in QUESTION_BOOST_WORDS if qw in item["title"].lower())
    return base_score + question_boost

def get_trending_topic(category, exclude_titles=None):
    """
    Fetch trending headlines for a specific category from multiple RSS sources.
    
    Priority:
    1. Best keyword-matched item from any live RSS feed (excluding duplicates)
    2. Random item from any live feed (if no keyword match and not duplicate)
    3. Random high-quality static fallback (not duplicate)
    """
    if exclude_titles is None:
        exclude_titles = set()
    else:
        exclude_titles = {t.strip().lower() for t in exclude_titles}

    print(f"[NICHE] Researching real-time trending topics for: {category.upper()}...")
    urls = FEEDS.get(category, [])
    category_keywords = KEYWORDS.get(category, [])
    
    all_matched = []  # (score, item) tuples from all feeds
    all_items = []    # fallback pool

    # Try all feeds
    for url in urls:
        raw_xml = fetch_feed_data(url)
        if not raw_xml:
            continue
        parsed_items = parse_rss_items(raw_xml)
        if not parsed_items:
            continue
        
        for item in parsed_items:
            # Skip duplicates immediately
            if is_duplicate_local(item["title"], exclude_titles):
                continue
            all_items.append(item)
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
    
    # All network sources offline or all feed items are duplicates — use static fallbacks
    fallbacks = STATIC_FALLBACKS.get(category, list(STATIC_FALLBACKS.values())[0])
    non_dup_fallbacks = [f for f in fallbacks if not is_duplicate_local(f["title"], exclude_titles)]
    if non_dup_fallbacks:
        selected = random.choice(non_dup_fallbacks)
        print(f"[STATIC FALLBACK] All feeds offline — using: {selected['title']}")
        return selected
        
    # Absolute fallback (even if duplicate, to return something)
    selected = random.choice(fallbacks)
    print(f"[STATIC FALLBACK] All non-duplicate fallbacks exhausted — using: {selected['title']}")
    return selected


if __name__ == "__main__":
    # Test execution — run each category and print the selected topic
    for cat in ["tech", "finance", "lifestyle", "mindset"]:
        topic = get_trending_topic(cat)
        print(f"\nCategory: {cat}")
        print(f"  Title: {topic['title']}")
        print(f"  Desc:  {topic['description'][:100]}...")
