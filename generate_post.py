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
    """Return True if this exact title was already published."""
    return title.strip().lower() in load_published_titles()


# ─────────────────────────────────────────────
def get_unsplash_image(topic):
    """Fetch a relevant image from Unsplash."""
    try:
        query = topic[:50]
        url = "https://api.unsplash.com/photos/random"
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        params = {"query": query, "orientation": "landscape"}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            img_url = data["urls"]["regular"]
            alt = data["alt_description"] or topic
            credit_name = data["user"]["name"]
            credit_link = data["user"]["links"]["html"]
            print(f"[IMAGE] Unsplash image found: {img_url}")
            return img_url, alt, credit_name, credit_link
    except Exception as e:
        print(f"[IMAGE] Unsplash query failed: {e}")
    return None, None, None, None

def get_pollinations_image(topic):
    """Fallback: AI-generated image from Pollinations.ai.
    
    Follows the redirect to obtain the final static CDN URL so that
    Blogger's thumbnail crawler can scrape a real image file.
    """
    try:
        clean_topic = re.sub(r'[^a-zA-Z0-9\s]', '', topic)
        prompt = clean_topic.replace(" ", "%20")
        poll_url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=450&nologo=true"
        # Follow redirect to get a stable, static image URL
        resp = requests.get(poll_url, timeout=30, allow_redirects=True)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
            # Use the final resolved URL (may be the same or a CDN redirect)
            final_url = resp.url
            print(f"[IMAGE] Pollinations resolved to: {final_url}")
            return final_url, topic, None, None
        else:
            print(f"[IMAGE] Pollinations returned status {resp.status_code}; using Picsum fallback.")
    except Exception as e:
        print(f"[IMAGE] Pollinations failed: {e}")
    return get_picsum_image(topic)

def get_picsum_image(topic):
    """Last-resort fallback: deterministic landscape photo from Picsum Photos.
    
    Picsum always returns a real JPEG, no API key required.
    We seed the image ID from the topic string so each topic gets a
    consistent (but varied) image across reruns.
    """
    try:
        seed = abs(hash(topic)) % 1000  # 0-999 deterministic seed
        img_url = f"https://picsum.photos/seed/{seed}/800/450"
        # Follow redirect to get the real static URL
        resp = requests.get(img_url, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            final_url = resp.url
            print(f"[IMAGE] Picsum fallback resolved to: {final_url}")
            return final_url, topic, None, None
    except Exception as e:
        print(f"[IMAGE] Picsum fallback failed: {e}")
    return None, None, None, None

def get_image(topic):
    """Try Unsplash first, then Pollinations AI, then Picsum Photos."""
    if UNSPLASH_ACCESS_KEY:
        img_url, alt, credit_name, credit_link = get_unsplash_image(topic)
        if img_url:
            return img_url, alt, credit_name, credit_link
    return get_pollinations_image(topic)

def call_groq(prompt):
    """Executes call to Groq Llama model with rate limit retries."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 2048
    }

    for attempt in range(3):
        print(f"[LLM] Dispatching request to Groq (Attempt {attempt + 1})...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            wait = 20 * (attempt + 1)
            print(f"[LLM] Rate limit hit. Cooling down {wait}s...")
            time.sleep(wait)
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
            # Refresh access token
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
        # Try up to 5 alternatives from the same feed before giving up
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

    # Fetch visual graphic header
    img_url, alt, credit_name, credit_link = get_image(topic)

    # Build image credit caption
    image_html = ""
    if img_url:
        if credit_name and credit_link:
            image_html = f'<img src="{img_url}" alt="{alt}" style="width:100%; border-radius:12px; margin-bottom:24px;"/>\n<p style="text-align:center; font-style:italic; font-size:12px; color:#5A5E6F; margin-top:-16px;">Photo by <a href="{credit_link}" target="_blank">{credit_name}</a> on Unsplash</p>\n'
        else:
            image_html = f'<img src="{img_url}" alt="{alt}" style="width:100%; border-radius:12px; margin-bottom:24px;"/>\n'

    prompt = f"""You are a senior editorial journalist and SEO strategist writing for a high-authority news blog.
Write a deeply researched, premium long-form article about: "{topic}".
Niche: {category.upper()}. Background context: "{trend_desc}".

━━━ CONTENT QUALITY RULES (E-E-A-T) ━━━
- Show EXPERIENCE: Open with a concrete real-world scenario, statistic, or expert quote that proves first-hand depth.
- Show EXPERTISE: Include at least 2 specific data points (percentages, studies, named sources) relevant to "{topic}".
- Show AUTHORITATIVENESS: Reference at least 1 real company, person, or published study by name.
- Show TRUSTWORTHINESS: Acknowledge nuance — mention what the trend does NOT solve or its limitations.

━━━ SEO RULES ━━━
- Use the exact phrase "{topic}" naturally in: the title, first paragraph, one H2 subheading, and the conclusion.
- Use LSI keywords naturally (related terms, synonyms — do NOT keyword stuff).
- Structure: minimum 5 sections using ## H2 and ### H3 headings.
- Include at least one numbered list AND one bullet-point list.
- Target 900–1100 words for optimal dwell time.

━━━ FORMATTING ━━━
- Start with one # Title (make it curiosity-driven and click-worthy — NOT clickbait).
- End with: [META_DESCRIPTION: a 145–160 character meta description with primary keyword at the start]

Return ONLY the Markdown. No preamble, no sign-offs, no meta-commentary."""

    # Generate content using Groq
    if not GROQ_API_KEY:
        print("[AUTOMATION] Warning: GROQ_API_KEY missing. Generating mock SEO post content.")
        content = f"""# {topic}

In today's fast-moving world, keeping up with the latest trends in {category} is essential. The rise of "{topic}" is a perfect example of this shift.

## Key Insights into {topic}

Understanding how these elements interact can reshape your daily routine, finance, or technical workflow.

### Actionable Strategies
- **Stay Informed:** Keep an eye on daily briefings and updates.
- **Implement Progressively:** Start with small, manageable adjustments.

## Practical Steps to Master this Niche

By breaking down the challenges, you can build atomic habits that yield exponential returns over time.

## Conclusion

Embracing this development will position you at the forefront of the industry.

[META_DESCRIPTION: Learn key insights and actionable strategies to master the latest development in {topic} and optimize your daily workflow.]"""
    else:
        content = call_groq(prompt)

    # Extract Meta Description
    meta_desc = f"Latest trending update on {topic} inside the {category} niche."
    meta_match = re.search(r'\[META_DESCRIPTION:\s*(.+?)\]', content, re.IGNORECASE)
    if meta_match:
        meta_desc = meta_match.group(1).strip()
        content = content.replace(meta_match.group(0), "")

    # Extract Title
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else topic.title()

    # Remove H1 title line from body content
    body = re.sub(r'^# .+\n', '', content, count=1).strip()

    # Convert markdown body to HTML
    html_content = markdown.markdown(body)

    # Load and inject affiliate offer callout box
    offer = load_monetization_offer(category)
    if offer:
        callout_html = f"""
<div class="editorial-callout" style="padding:24px; background:linear-gradient(135deg, rgba(200,16,46,0.03) 0%, rgba(255,51,102,0.03) 100%); border-left:4px solid #FF3366; margin:35px 0; border-radius:12px; font-family:'Outfit',sans-serif; box-shadow:0 4px 15px rgba(0,0,0,0.02);">
    <h4 style="margin:0 0 10px 0; color:#FF3366; font-size:16px; font-weight:700; text-transform:uppercase; letter-spacing:1px;">{offer['callout_title']}</h4>
    <p style="margin:0 0 16px 0; font-size:14px; line-height:1.6; color:#5A5E6F;">{offer['copywriting']}</p>
    <a href="{offer['referral_url']}" target="_blank" style="display:inline-flex; align-items:center; gap:8px; padding:10px 22px; font-weight:600; font-size:13px; color:#FFFFFF; background:#FF3366; border-radius:6px; text-decoration:none; box-shadow:0 4px 10px rgba(255,51,102,0.25);">Get instant access &rarr;</a>
</div>
"""
        # Inject after the second paragraph (H1 tag counts as first, or split paragraphs)
        paragraphs = html_content.split("</p>")
        if len(paragraphs) > 2:
            paragraphs[1] += "</p>\n" + callout_html
            html_content = "</p>".join(paragraphs)
        else:
            html_content += "\n" + callout_html

    # Combine image cover and HTML body
    final_html = image_html + html_content

    # Deploy to Blogger
    service = get_blogger_service()
    if service and BLOG_ID:
        try:
            post_body = {
                "title": title,
                "content": final_html,
                "labels": [category.title(), "Blog", "Trending"],
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
        except Exception as e:
            print(f"[ERROR] Blogger API publishing failed: {e}")
    else:
        print("[AUTOMATION] Simulated Local Publishing Successful (Blogger Credentials Omitted).")
        # Save locally to drafts folder for inspection
        drafts_dir = os.path.join(os.path.dirname(__file__), "drafts")
        os.makedirs(drafts_dir, exist_ok=True)
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
        draft_path = os.path.join(drafts_dir, f"{slug}.html")
        with open(draft_path, "w", encoding="utf-8") as f:
            f.write(f"<!--\nTitle: {title}\nMeta Description: {meta_desc}\nCategory: {category}\n-->\n" + final_html)
        print(f"[SUCCESS] Draft saved locally for review: {draft_path}")

if __name__ == "__main__":
    offset = int(os.environ.get("POST_OFFSET", "0"))
    generate_post(offset)
