"""
social_share.py
───────────────
Auto-shares published blog posts to Twitter/X and Pinterest
immediately after each Blogger post is created.

Required environment secrets:
  Twitter/X:
    TWITTER_API_KEY, TWITTER_API_SECRET
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET

  Pinterest:
    PINTEREST_ACCESS_TOKEN
    PINTEREST_BOARD_ID
"""

import os
import json
import hmac
import hashlib
import base64
import time
import random
import string
import urllib.parse
import urllib.request


# ─────────────────────────────────────────────
# TWITTER / X
# ─────────────────────────────────────────────

def _oauth1_header(method, url, params, api_key, api_secret, token, token_secret):
    """Builds a valid OAuth 1.0a Authorization header for Twitter API v2."""
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": "".join(random.choices(string.ascii_letters + string.digits, k=32)),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": token,
        "oauth_version": "1.0",
    }

    # Merge all params for signature base string
    all_params = {**params, **oauth_params}
    sorted_params = "&".join(
        f"{urllib.parse.quote(k, safe='')}" f"={urllib.parse.quote(str(v), safe='')}"
        for k, v in sorted(all_params.items())
    )

    base_string = "&".join([
        method.upper(),
        urllib.parse.quote(url, safe=""),
        urllib.parse.quote(sorted_params, safe=""),
    ])

    signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()

    oauth_params["oauth_signature"] = signature
    header = "OAuth " + ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(str(v), safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return header


def tweet_post(title, url, category):
    """
    Posts a tweet to Twitter/X with the blog post title, URL, and hashtags.
    Uses Twitter API v2 free tier (1,500 tweets/month).
    """
    api_key          = os.environ.get("TWITTER_API_KEY", "")
    api_secret       = os.environ.get("TWITTER_API_SECRET", "")
    access_token     = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("[TWITTER] Skipping — credentials not configured.")
        return False

    # Build hashtags by category
    tag_map = {
        "tech":      "#Tech #AI #Technology",
        "finance":   "#Finance #Investing #Money",
        "lifestyle": "#Lifestyle #Wellness #Health",
        "mindset":   "#Mindset #Productivity #Habits",
    }
    hashtags = tag_map.get(category.lower(), "#Blog #Trending")

    tweet_text = f"📰 {title}\n\n{hashtags}\n\n🔗 {url}"

    # Twitter API v2 endpoint
    endpoint = "https://api.twitter.com/2/tweets"
    body = json.dumps({"text": tweet_text}).encode("utf-8")

    auth_header = _oauth1_header(
        "POST", endpoint, {}, api_key, api_secret, access_token, access_token_secret
    )

    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            tweet_id = result.get("data", {}).get("id", "unknown")
            print(f"[TWITTER] ✅ Tweet published! ID: {tweet_id}")
            return True
    except urllib.request.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"[TWITTER] ❌ Failed ({e.code}): {body_text}")
        return False
    except Exception as e:
        print(f"[TWITTER] ❌ Error: {e}")
        return False


# ─────────────────────────────────────────────
# PINTEREST
# ─────────────────────────────────────────────

def pin_post(title, url, image_url, category):
    """
    Creates a Pinterest Pin linking back to the blog post.
    Uses Pinterest API v5. Requires a business account access token.
    """
    access_token = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
    board_id     = os.environ.get("PINTEREST_BOARD_ID", "")

    if not all([access_token, board_id]):
        print("[PINTEREST] Skipping — credentials not configured.")
        return False

    description_map = {
        "tech":      "🔥 Must-read tech & AI insights — stay ahead of the curve!",
        "finance":   "💰 Smart money moves & investing strategies for 2025.",
        "lifestyle": "✨ Life-changing wellness & lifestyle tips you need to know.",
        "mindset":   "🧠 Boost your productivity & mindset with these proven habits.",
    }
    description = description_map.get(category.lower(), "📰 Trending blog post — click to read more!")

    endpoint = "https://api.pinterest.com/v5/pins"
    payload = {
        "board_id": board_id,
        "title": title[:100],
        "description": description,
        "link": url,
        "media_source": {
            "source_type": "image_url",
            "url": image_url or "https://via.placeholder.com/800x450?text=The+Daily+Pulse"
        }
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            pin_id = result.get("id", "unknown")
            print(f"[PINTEREST] ✅ Pin created! ID: {pin_id}")
            return True
    except urllib.request.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"[PINTEREST] ❌ Failed ({e.code}): {body_text}")
        return False
    except Exception as e:
        print(f"[PINTEREST] ❌ Error: {e}")
        return False


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def share_post(title, post_url, image_url, category):
    """
    Shares a newly published post to all configured social platforms.
    Called from generate_post.py after a successful Blogger publish.
    """
    print(f"\n[SOCIAL] Sharing: {title}")
    tweet_post(title, post_url, category)
    pin_post(title, post_url, image_url, category)
    print("[SOCIAL] Social sharing complete.\n")
