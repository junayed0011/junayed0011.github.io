import requests
import datetime
import os
import re
import time
import json
import markdown
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import trends_researcher
import social_share

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")

# Load Blogger service account securely
SERVICE_ACCOUNT_JSON = None
if "BLOGGER_SERVICE_ACCOUNT" in os.environ:
    try:
        SERVICE_ACCOUNT_JSON = json.loads(os.environ["BLOGGER_SERVICE_ACCOUNT"])
    except Exception as e:
        print(f"[ERROR] Failed to parse service account JSON environment variable: {e}")

# ─────────────────────────────────────────────
# DUPLICATE POST GUARD
# ─────────────────────────────────────────────

PUBLISHED_LOG = os.path.join(os.path.dirname(__file__), "published_titles.json")

# Stop-words to ignore in similarity comparison
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "as", "are", "was",
    "be", "that", "this", "how", "why", "what", "who", "just", "amid",
    "into", "up", "now", "new", "amid", "time", "says", "amid"
}

def _title_keywords(title):
    """Return significant lowercase words from a title (no stop-words, len>2)."""
    words = re.findall(r'[a-z]+', title.lower())
    return {w for w in words if w not in _STOP_WORDS and len(w) > 2}

def load_published_titles():
    """Load previously published post titles from the local log file."""
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"[DUPLICATE] Warning: could not read published log: {e}")
    return set()

def save_published_title(title):
    """Append a title to the published log so it's never reused."""
    titles = load_published_titles()
    titles.add(title.strip().lower())
    try:
        with open(PUBLISHED_LOG, "w", encoding="utf-8") as f:
            json.dump(list(titles), f, indent=2)
        print(f"[DUPLICATE] Title logged: {title}")
    except Exception as e:
        print(f"[DUPLICATE] Warning: could not save published log: {e}")

def is_duplicate(title):
    """Return True if an identical OR near-duplicate title was already published.
    
    Near-duplicate: ≥60% of the significant keywords in the candidate title
    already appear in any previously published title.
    """
    published = load_published_titles()
    norm = title.strip().lower()

    # Exact match
    if norm in published:
        return True

    # Fuzzy keyword-overlap check
    candidate_kw = _title_keywords(title)
    if not candidate_kw:
        return False
    for pub_title in published:
        pub_kw = _title_keywords(pub_title)
        if not pub_kw:
            continue
        overlap = len(candidate_kw & pub_kw) / len(candidate_kw)
        if overlap >= 0.60:
            print(f"[DUPLICATE] Near-duplicate detected ({overlap:.0%} overlap) with: '{pub_title}'")
            return True
    return False


# ─────────────────────────────────────────────
def get_unsplash_image(topic):
    """Fetch a high-quality landscape image from Unsplash."""
    try:
        query = topic[:50]
        url = "https://api.unsplash.com/photos/random"
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        params = {"query": query, "orientation": "landscape", "content_filter": "high"}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Use full-size image at 1200px width for quality
            img_url = data["urls"]["regular"].replace("w=1080", "w=1200")
            alt = data["alt_description"] or topic
            credit_name = data["user"]["name"]
            credit_link = data["user"]["links"]["html"]
            print(f"[IMAGE] Unsplash image found: {img_url}")
            return img_url, alt, credit_name, credit_link
    except Exception as e:
        print(f"[IMAGE] Unsplash query failed: {e}")
    return None, None, None, None

def generate_image_prompt(topic, category="lifestyle"):
    """Generates a highly detailed cinematic visual prompt for AI image generation."""
    if not GROQ_API_KEY:
        return topic  # Fallback to topic if no LLM key
    
    style_map = {
        "tech": "sleek futuristic interface, neon blue glow, dark studio, 8k ultra detailed",
        "finance": "premium financial charts, golden hour light, modern glass office, professional",
        "lifestyle": "warm golden hour, healthy vibrant colors, modern lifestyle photography",
        "mindset": "serene minimalist workspace, soft morning light, focused atmosphere, motivational"
    }
    style_hint = style_map.get(category, "cinematic lighting, photorealistic, professional photography")

    prompt = f"""You are a professional art director for a premium editorial magazine. Write a concise, vivid visual prompt for an AI image generator (Stable Diffusion) to illustrate the article topic below.

Topic: "{topic}"
Category: {category.upper()}
Style guidance: {style_hint}

Rules:
- Describe ONE concrete, photorealistic visual scene with specific objects, lighting, and color palette
- Do NOT include text, letters, logos, or people's faces in the description
- Include camera style: "wide angle shot" or "close-up" or "aerial view"
- Use: "photorealistic, cinematic lighting, 4k, sharp focus, editorial photography"
- Maximum 30 words
- Return ONLY the prompt text, no quotes, no preamble"""

    try:
        response = call_groq(prompt, model="llama-3.1-8b-instant", max_tokens=100, temp=0.7)
        cleaned = response.strip().strip('"').strip("'")
        print(f"[IMAGE] Generated visual prompt: {cleaned}")
        return cleaned
    except Exception as e:
        print(f"[IMAGE] Failed to generate visual prompt: {e}")
        return topic

def get_pollinations_image(topic, category="lifestyle"):
    """AI-generated high-res image from Pollinations.ai.
    
    Uses seed for determinism, 1200x675 for landscape quality.
    """
    try:
        visual_prompt = generate_image_prompt(topic, category)
        # Clean and encode prompt
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s,.-]', '', visual_prompt)
        prompt_encoded = clean_prompt.replace(" ", "%20")
        # Use seed from topic hash for consistent per-topic images
        seed = abs(hash(topic)) % 9999
        poll_url = (
            f"https://image.pollinations.ai/prompt/{prompt_encoded}"
            f"?width=1200&height=675&seed={seed}&nologo=true&enhance=true"
        )
        # Follow redirect to get a stable, static image URL
        resp = requests.get(poll_url, timeout=45, allow_redirects=True)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
            final_url = resp.url
            print(f"[IMAGE] Pollinations resolved to: {final_url}")
            return final_url, visual_prompt, None, None
        else:
            print(f"[IMAGE] Pollinations returned status {resp.status_code}; using Picsum fallback.")
    except Exception as e:
        print(f"[IMAGE] Pollinations failed: {e}")
    return get_picsum_image(topic)

def get_picsum_image(topic):
    """Last-resort fallback: deterministic landscape photo from Picsum Photos at 1200px."""
    try:
        seed = abs(hash(topic)) % 1000
        img_url = f"https://picsum.photos/seed/{seed}/1200/675"
        resp = requests.get(img_url, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            final_url = resp.url
            print(f"[IMAGE] Picsum fallback resolved to: {final_url}")
            return final_url, topic, None, None
    except Exception as e:
        print(f"[IMAGE] Picsum fallback failed: {e}")
    return None, None, None, None

def get_image(topic, category="lifestyle"):
    """Try Pollinations AI first, then Unsplash, then Picsum."""
    img_url, alt, credit_name, credit_link = get_pollinations_image(topic, category)
    if img_url and "picsum.photos" not in img_url:
        return img_url, alt, credit_name, credit_link
        
    if UNSPLASH_ACCESS_KEY:
        u_url, u_alt, u_name, u_link = get_unsplash_image(topic)
        if u_url:
            return u_url, u_alt, u_name, u_link
            
    return img_url, alt, credit_name, credit_link

def call_groq(prompt, model="llama-3.3-70b-versatile", max_tokens=4096, temp=0.75):
    """Executes call to Groq with rate limit retries. Uses 70B model for premium content quality."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temp,
        "max_tokens": max_tokens
    }

    for attempt in range(3):
        print(f"[LLM] Dispatching request to Groq {model} (Attempt {attempt + 1})...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"[LLM] Rate limit hit. Cooling down {wait}s...")
            time.sleep(wait)
        elif response.status_code == 400 and "model" in response.text.lower():
            # Model not available, fall back to 8B
            print(f"[LLM] Model {model} unavailable, falling back to llama-3.1-8b-instant")
            payload["model"] = "llama-3.1-8b-instant"
            payload["max_tokens"] = 2048
        else:
            print(f"[LLM] Error {response.status_code}: {response.text}")
            response.raise_for_status()

    raise Exception("All Groq API retries failed.")

def load_monetization_offer(category):
    """Loads matching contextual affiliate campaign from configuration file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "monetization_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["offers"].get(category)
    except Exception as e:
        print(f"[ERROR] Failed to load monetization config: {e}")
    return None

def get_blogger_service():
    """Dynamically authenticates with Blogger API using either OAuth Refresh Token or Service Account."""
    client_id = os.environ.get("BLOGGER_CLIENT_ID", "")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET", "")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN", "")

    # Method A: OAuth 2.0 Client Credentials with Refresh Token
    if client_id and client_secret and refresh_token:
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret
            )
            creds.refresh(Request())
            service = build("blogger", "v3", credentials=creds)
            print("[AUTH] Successfully authenticated using OAuth 2.0 Refresh Token.")
            return service
        except Exception as e:
            print(f"[AUTH] OAuth 2.0 Refresh Token authentication failed: {e}")

    # Method B: Google Cloud Service Account
    if SERVICE_ACCOUNT_JSON:
        try:
            creds = service_account.Credentials.from_service_account_info(
                SERVICE_ACCOUNT_JSON,
                scopes=["https://www.googleapis.com/auth/blogger"]
            )
            service = build("blogger", "v3", credentials=creds)
            print("[AUTH] Successfully authenticated using Service Account.")
            return service
        except Exception as e:
            print(f"[AUTH] Service Account authentication failed: {e}")

    return None

# Google Indexing API is only for JobPosting/BroadcastEvent; removed to prevent silent site-wide search indexing penalties.

# ─────────────────────────────────────────────
# CATEGORY → BLOGGER LABEL MAPPING
# More descriptive labels improve discoverability on Blogger
# ─────────────────────────────────────────────
CATEGORY_LABELS = {
    "tech": ["Technology", "AI & Innovation", "Trending", "Blog"],
    "finance": ["Finance & Money", "Wealth Building", "Trending", "Blog"],
    "lifestyle": ["Beauty & Health Tips", "Wellness", "Trending", "Blog"],
    "mindset": ["Mindset & Productivity", "Self Improvement", "Trending", "Blog"],
}

def generate_post(topic_offset=0):
    """Orchestrates dynamic trends research, content writing, ad injection, and Blogger publishing."""
    categories = ["tech", "finance", "lifestyle", "mindset"]
    today = datetime.date.today()
    category_index = (today.timetuple().tm_yday * 2 + topic_offset) % len(categories)
    category = categories[category_index]
    
    # Query live RSS feeds via research module
    trend = trends_researcher.get_trending_topic(category)
    topic = trend["title"]
    trend_desc = trend["description"]
    
    print(f"[AUTOMATION] Pillar: {category.upper()} | Selected Live Trend: {topic}")

    # ── Duplicate post guard ──────────────────────────────────────────────────
    if is_duplicate(topic):
        print(f"[DUPLICATE] Skipping '{topic}' — already published. Fetching alternative topic...")
        for _ in range(5):
            trend = trends_researcher.get_trending_topic(category)
            topic = trend["title"]
            trend_desc = trend["description"]
            if not is_duplicate(topic):
                print(f"[DUPLICATE] Alternative selected: {topic}")
                break
        else:
            print("[DUPLICATE] All candidate topics already published. Skipping this run.")
            return
    # ─────────────────────────────────────────────────────────────────────────

    # Fetch visual header image
    img_url, alt_text, credit_name, credit_link = get_image(topic, category)

    # Build image HTML with proper dimensions for Core Web Vitals (no CLS)
    image_html = ""
    if img_url:
        alt_safe = (alt_text or topic).replace('"', "'")
        if credit_name and credit_link:
            image_html = (
                f'<figure style="margin:0 0 32px 0;">'
                f'<img src="{img_url}" alt="{alt_safe}" width="1200" height="675" '
                f'style="width:100%; height:auto; border-radius:16px; display:block;" '
                f'loading="eager" fetchpriority="high"/>'
                f'<figcaption style="text-align:center; font-style:italic; font-size:12px; '
                f'color:var(--text-secondary, #9ea2b6); margin-top:8px;">'
                f'Photo by <a href="{credit_link}" target="_blank" rel="noopener">{credit_name}</a> on Unsplash'
                f'</figcaption></figure>\n'
            )
        else:
            image_html = (
                f'<figure style="margin:0 0 32px 0;">'
                f'<img src="{img_url}" alt="{alt_safe}" width="1200" height="675" '
                f'style="width:100%; height:auto; border-radius:16px; display:block;" '
                f'loading="eager" fetchpriority="high"/>'
                f'</figure>\n'
            )

    # ─────────────────────────────────────────────────────────────────────────
    # UPGRADED CONTENT PROMPT — E-E-A-T + FAQ + Key Takeaways
    # ─────────────────────────────────────────────────────────────────────────
    prompt = f"""You are an award-winning senior journalist and SEO strategist writing for a high-authority editorial news blog with millions of readers.

Write a deeply researched, compelling, premium long-form article about: "{topic}".
Niche: {category.upper()}. Background context: "{trend_desc}".

━━━ CONTENT QUALITY RULES (Google E-E-A-T) ━━━
- EXPERIENCE: Open with one concrete real-world scenario, surprising statistic, or expert quote that immediately proves depth and first-hand knowledge.
- EXPERTISE: Include at minimum 3 specific data points (exact percentages, named studies, concrete timeframes) highly relevant to "{topic}".
- AUTHORITATIVENESS: Reference at least 2 real companies, research institutions, or named experts. Be specific — avoid vague references.
- TRUSTWORTHINESS: Include a nuanced "What to Watch Out For" or "Common Misconceptions" section that shows honest, balanced analysis.

━━━ SEO STRUCTURE ━━━
- Title: Write a title using one of these power formulas:
  * "[Number] [Power Word] Ways to [Benefit] in [Year]" 
  * "Why [Topic] Is Changing [Industry] Forever — And What You Should Do Now"
  * "The Science-Backed Truth About [Topic] (Most People Get This Wrong)"
- Use the exact phrase "{topic}" in: the title, first paragraph, at least one H2 subheading, and the conclusion.
- Use LSI/semantic keywords naturally — related phrases, synonyms — do NOT stuff keywords.
- Include 6-8 sections using ## H2 headings and 2+ ### H3 sub-sections.
- Include: one numbered list AND one bullet list in the article body.
- Target length: 1,800–2,200 words. Longer, thorough content ranks higher for competitive keywords and maximizes dwell time.

━━━ SPECIAL SECTIONS (REQUIRED) ━━━
After the conclusion, add these three mandatory sections:

**KEY TAKEAWAYS** (formatted as 4-5 bullet points prefixed with "✅"):
A section titled "## Key Takeaways" with concise, scannable action items readers can immediately apply.

**FAQ SECTION** (formatted as ### questions with short paragraph answers):
A section titled "## Frequently Asked Questions" with exactly 3 relevant questions and answers about "{topic}". These power Google's FAQ rich snippets.

**AUTHOR BIO** (required for E-E-A-T):
End with a section titled "## About the Author" containing a 2-sentence bio for "The Daily Pulse Editorial Team" that establishes specific expertise in {category} topics. Example: "The Daily Pulse Editorial Team covers [category-relevant field] with a focus on evidence-based insights and practical advice. Our writers draw on industry research, expert interviews, and data analysis to bring you actionable content."

━━━ FORMATTING ━━━
- Start with: # [Your SEO-optimized title]
- End with: [META_DESCRIPTION: a 145–160 character meta description — put primary keyword first, include a call-to-action word]

Return ONLY the Markdown content. No preamble, no sign-offs, no meta-commentary about the article."""

    # Generate content using Groq
    if not GROQ_API_KEY:
        print("[AUTOMATION] Warning: GROQ_API_KEY missing. Generating mock SEO post content.")
        content = f"""# {topic}: What You Need to Know Right Now

In today's fast-moving world, {topic} is reshaping how professionals in {category} think and operate.

## Why {topic} Matters More Than Ever

Understanding how these elements interact can reshape your daily routine, finance, or technical workflow.

### Key Data Points
- **78%** of industry leaders report significant impact from this trend
- Research from Stanford University confirms measurable productivity gains
- Companies like Google and Microsoft are investing billions in this space

## Practical Strategies for 2025

By breaking down the challenges, you can build atomic habits that yield exponential returns.

1. Start with a 30-day commitment
2. Track progress weekly with measurable metrics
3. Adjust based on what data tells you

## Common Misconceptions

Many people believe this only applies to large companies — that's false.

## What Experts Are Saying

"This is the most significant shift we've seen in a decade," says Dr. Jane Smith, Harvard Business School.

## Conclusion

Embracing {topic} will position you at the forefront of the industry.

## Key Takeaways

✅ Start implementing small changes today
✅ Track your metrics consistently
✅ Stay updated with the latest developments
✅ Connect with communities around {topic}

## Frequently Asked Questions

### What is {topic} and why does it matter?
{topic} refers to a significant trend in {category} that is changing how people and businesses operate in the modern world.

### How can beginners get started with {topic}?
Start with free resources online, join relevant communities, and implement one small change per week to build momentum.

### What are the biggest mistakes people make with {topic}?
The biggest mistake is trying to do everything at once. Start with the highest-impact change and master it before moving on.

[META_DESCRIPTION: Discover the truth about {topic} — expert-backed strategies, real data, and actionable steps to get ahead in {category} today.]"""
    else:
        content = call_groq(prompt)

    # Extract Meta Description
    meta_desc = f"Discover the latest insights on {topic} — expert analysis, key data, and actionable strategies for {category} success."
    meta_match = re.search(r'\[META_DESCRIPTION:\s*(.+?)\]', content, re.IGNORECASE)
    if meta_match:
        meta_desc = meta_match.group(1).strip()
        content = content.replace(meta_match.group(0), "")

    # Extract Title
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else topic.title()
    title = title.replace("**", "").replace("*", "").strip()

    # Remove H1 title line from body content
    body = re.sub(r'^# .+\n', '', content, count=1).strip()

    # Convert markdown body to HTML
    html_content = markdown.markdown(body, extensions=['extra', 'nl2br'])

    # Retrieve previous post details from Blogger API for internal linking (Solving referring page issues)
    prev_title = ""
    prev_url = ""
    previous_post_link = ""
    service = get_blogger_service()
    if service and BLOG_ID:
        try:
            print("[INTERNAL LINK] Fetching latest post to build internal link...")
            resp = service.posts().list(
                blogId=BLOG_ID,
                maxResults=1,
                fields="items(title,url)"
            ).execute()
            items = resp.get("items", [])
            if items:
                prev_title = items[0].get("title", "").replace("**", "").replace("*", "").strip()
                prev_url = items[0].get("url", "")
                previous_post_link = (
                    f'\n<div style="margin-top: 40px; padding: 20px 0; border-top: 1px solid var(--divider); '
                    f'font-family: \'Outfit\', sans-serif;">'
                    f'<p style="margin: 0; font-weight: 600; font-size: 15px; color: var(--text-primary);">'
                    f'🔗 Read Also: <a href="{prev_url}" style="color: #7c3aed; text-decoration: none; '
                    f'border-bottom: 1.5px solid rgba(124, 58, 237, 0.4); transition: border-color 0.2s ease;">'
                    f'{prev_title}</a></p></div>\n'
                )
                html_content += previous_post_link
                print(f"[INTERNAL LINK] Found previous post: {prev_title}")
        except Exception as e:
            print(f"[INTERNAL LINK] Could not retrieve previous post: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Wrap FAQ section with JSON-LD friendly markup for rich snippets
    # ─────────────────────────────────────────────────────────────────────────
    html_content = re.sub(
        r'<h2[^>]*>Frequently Asked Questions</h2>',
        '<h2 id="faq-section">Frequently Asked Questions</h2>',
        html_content, flags=re.IGNORECASE
    )

    # Style the Key Takeaways box
    html_content = re.sub(
        r'<h2[^>]*>Key Takeaways</h2>',
        '''<h2 id="key-takeaways" style="margin-top:48px;">Key Takeaways</h2>''',
        html_content, flags=re.IGNORECASE
    )

    # Add styling to ✅ list items in the key takeaways section
    html_content = html_content.replace(
        '<li>✅',
        '<li style="list-style:none; padding:6px 0; font-weight:500;">✅'
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Inject FAQPage JSON-LD schema for Google rich result cards
    # Extracts H3 questions + following P answers from the FAQ section
    # ─────────────────────────────────────────────────────────────────────────
    faq_pattern = re.findall(
        r'<h3[^>]*>(.*?)</h3>\s*<p>(.*?)</p>',
        html_content, re.DOTALL | re.IGNORECASE
    )
    if len(faq_pattern) >= 2:
        faq_items = []
        for q, a in faq_pattern[:5]:  # Max 5 FAQ items for schema
            q_clean = re.sub(r'<[^>]+>', '', q).strip().replace('"', "'")
            a_clean = re.sub(r'<[^>]+>', '', a).strip().replace('"', "'")[:300]
            if q_clean and a_clean:
                faq_items.append(
                    '{"@type":"Question","name":"' + q_clean +
                    '","acceptedAnswer":{"@type":"Answer","text":"' + a_clean + '"}}'
                )
        if faq_items:
            faq_jsonld = (
                '<script type="application/ld+json">\n'
                '{\n  "@context": "https://schema.org",\n'
                '  "@type": "FAQPage",\n'
                '  "mainEntity": [' + ','.join(faq_items) + ']\n}\n'
                '</script>\n'
            )
            # Prepend FAQ schema before the main Article JSON-LD
            html_content = faq_jsonld + html_content
            print(f"[SCHEMA] FAQPage JSON-LD injected with {len(faq_items)} Q&A pairs.")

    # Save markdown file to _posts directory for Jekyll
    posts_dir = os.path.join(os.path.dirname(__file__), "_posts")
    os.makedirs(posts_dir, exist_ok=True)
    
    offset_prefix = "am" if topic_offset == 0 else "pm"
    post_time_str = "07:00:00 +0000" if topic_offset == 0 else "19:00:00 +0000"
    date_str = today.strftime("%Y-%m-%d")
    
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]
    filename = f"{date_str}-{offset_prefix}-{slug}.md"
    filepath = os.path.join(posts_dir, filename)
    
    escaped_title = title.replace('"', '\\"')
    escaped_meta_desc = meta_desc.replace('"', '\\"')
    
    # Get canonical category label for Jekyll
    primary_label = CATEGORY_LABELS.get(category, ["Blog"])[0]
    
    front_matter = f"""---
layout: post
title: "{escaped_title}"
date: {date_str} {post_time_str}
categories: [{category}]
tags: {json.dumps(CATEGORY_LABELS.get(category, ["Blog"]))}
description: "{escaped_meta_desc}"
image: {img_url or ""}
author: "The Daily Pulse Editorial Team"
---

"""
    body_content = ""
    if img_url:
        body_content += f"![{title}]({img_url})\n\n"
    body_content += body
    if prev_title and prev_url:
        body_content += f"\n\n---\n\n🔗 **Read Also:** [{prev_title}]({prev_url})\n"
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(front_matter + body_content)
        print(f"[SUCCESS] Jekyll markdown post saved: {filepath}")
    except Exception as e:
        print(f"[ERROR] Failed to save Jekyll markdown post: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Load and inject affiliate offer callout box (after 2nd paragraph)
    # ─────────────────────────────────────────────────────────────────────────
    offer = load_monetization_offer(category)
    if offer:
        callout_html = f"""
<div class="editorial-callout" style="padding:24px; background:linear-gradient(135deg, rgba(124,58,237,0.04) 0%, rgba(6,182,212,0.04) 100%); border-left:4px solid #7c3aed; margin:35px 0; border-radius:16px; font-family:'Outfit',sans-serif; box-shadow:0 12px 40px rgba(0,0,0,0.04); border:1px solid rgba(124,58,237,0.1);">
  <h4 style="margin:0 0 10px 0; color:#7c3aed; font-size:15px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">{offer['callout_title']}</h4>
  <p style="margin:0 0 16px 0; font-size:14px; line-height:1.6; color:var(--text-secondary, #9ea2b6);">{offer['copywriting']}</p>
  <a href="{offer['referral_url']}" target="_blank" rel="noopener sponsored" style="display:inline-flex; align-items:center; gap:8px; padding:10px 22px; font-weight:600; font-size:13px; color:#FFFFFF; background:linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); border-radius:9999px; text-decoration:none; box-shadow:0 4px 15px rgba(124,58,237,0.35);">Get instant access &rarr;</a>
</div>
"""
        # Inject after the second paragraph
        paragraphs = html_content.split("</p>")
        if len(paragraphs) > 2:
            paragraphs[1] += "</p>\n" + callout_html
            html_content = "</p>".join(paragraphs)
        else:
            html_content += "\n" + callout_html

    # ─────────────────────────────────────────────────────────────────────────
    # Add JSON-LD Article structured data at the top for Google rich results
    # ─────────────────────────────────────────────────────────────────────────
    pub_date = today.isoformat() + "T07:00:00Z"
    img_for_schema = img_url or ""
    json_ld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title.replace('"', "'")}",
  "description": "{meta_desc.replace('"', "'")}",
  "image": {{
    "@type": "ImageObject",
    "url": "{img_for_schema}",
    "width": 1200,
    "height": 675
  }},
  "datePublished": "{pub_date}",
  "dateModified": "{pub_date}",
  "author": {{
    "@type": "Organization",
    "name": "The Daily Pulse Editorial Team",
    "url": "https://dailypulsetrends.blogspot.com"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "The Daily Pulse",
    "logo": {{
      "@type": "ImageObject",
      "url": "https://dailypulsetrends.blogspot.com/favicon.ico"
    }}
  }},
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "https://dailypulsetrends.blogspot.com/"
  }}
}}
</script>
"""

    # Combine: JSON-LD schema + hero image + HTML content
    final_html = json_ld + image_html + html_content

    # Deploy to Blogger
    service = get_blogger_service()
    if service and BLOG_ID:
        try:
            post_labels = CATEGORY_LABELS.get(category, ["Blog", "Trending"])
            post_body = {
                "title": title,
                "content": final_html,
                "labels": post_labels,
            }
            
            result = service.posts().insert(
                blogId=BLOG_ID, 
                body=post_body, 
                isDraft=False
            ).execute()
            post_url = result.get("url", "")
            print(f"[SUCCESS] Dynamic Post Published Successfully: {post_url}")
            save_published_title(title)
            # Share to social media platforms
            social_share.share_post(
                title=title,
                post_url=post_url,
                image_url=img_url,
                category=category
            )
            # Google Indexing API is removed to avoid site indexing penalties
        except Exception as e:
            print(f"[ERROR] Blogger API publishing failed: {e}")
    else:
        print("[AUTOMATION] Simulated Local Publishing Successful (Blogger Credentials Omitted).")
        drafts_dir = os.path.join(os.path.dirname(__file__), "drafts")
        os.makedirs(drafts_dir, exist_ok=True)
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]
        draft_path = os.path.join(drafts_dir, f"{slug}.html")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(f"<!--\nTitle: {title}\nMeta Description: {meta_desc}\nCategory: {category}\n-->\n" + final_html)
        print(f"[SUCCESS] Draft saved locally for review: {draft_path}")

if __name__ == "__main__":
    offset = int(os.environ.get("POST_OFFSET", "0"))
    generate_post(offset)
