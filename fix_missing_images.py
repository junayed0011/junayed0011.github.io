"""
fix_missing_images.py
─────────────────────
One-shot repair script: scans every post on the Blogger blog, detects posts
with no image OR with a Pollinations redirect URL (which Blogger can't
thumbnail), fetches a real static image, and patches the post via the
Blogger API.

Usage (run locally or as a manual GitHub Actions workflow_dispatch):
    python fix_missing_images.py

Required environment variables (same as generate_post.py):
    BLOGGER_BLOG_ID, BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET,
    BLOGGER_REFRESH_TOKEN  (or BLOGGER_SERVICE_ACCOUNT)
    UNSPLASH_ACCESS_KEY    (optional — used if available)
"""

import os
import re
import json
import requests
from generate_post import get_blogger_service, get_image

BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")

# ── Helpers ───────────────────────────────────────────────────────────────────

def _first_img_src(html: str) -> str | None:
    """Return the src of the very first <img> tag in the HTML, or None."""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    return m.group(1) if m else None

def _is_pollinations_url(url: str) -> bool:
    return "pollinations.ai" in url

def _is_broken_url(url: str) -> bool:
    """Return True if the URL doesn't resolve to a real image."""
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        ct = r.headers.get("content-type", "")
        return r.status_code != 200 or not ct.startswith("image/")
    except Exception:
        return True

def _build_img_tag(img_url: str, alt: str) -> str:
    return (
        f'<img src="{img_url}" alt="{alt}" '
        f'style="width:100%; border-radius:12px; margin-bottom:24px;"/>\n'
    )

def _replace_or_prepend_image(html: str, new_img_tag: str) -> str:
    """Replace the existing first <img> tag (if any) or prepend the new one."""
    replaced = re.sub(
        r'<img[^>]+>(\s*<p[^>]*>.*?</p>)?',  # img + optional caption paragraph
        new_img_tag,
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )
    if replaced == html:
        # No existing img tag — prepend
        return new_img_tag + html
    return replaced

# ── Main repair loop ──────────────────────────────────────────────────────────

def fix_all_posts():
    service = get_blogger_service()
    if not service or not BLOG_ID:
        print("[ERROR] Blogger credentials not available. Set env vars and retry.")
        return

    print(f"[REPAIR] Fetching post list for blog {BLOG_ID} …")
    posts = []
    page_token = None
    while True:
        params = {"blogId": BLOG_ID, "maxResults": 20, "fields": "items(id,title,content),nextPageToken"}
        if page_token:
            params["pageToken"] = page_token
        resp = service.posts().list(**params).execute()
        batch = resp.get("items", [])
        posts.extend(batch)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    print(f"[REPAIR] {len(posts)} posts found. Scanning for missing/broken images …\n")

    patched = 0
    skipped = 0

    for post in posts:
        post_id   = post["id"]
        title     = post.get("title", "Untitled")
        content   = post.get("content", "")

        current_src = _first_img_src(content)

        needs_fix = (
            current_src is None
            or _is_pollinations_url(current_src)
            or _is_broken_url(current_src)
        )

        if not needs_fix:
            print(f"  ✓  OK      | {title[:70]}")
            skipped += 1
            continue

        print(f"  ✗  FIXING  | {title[:70]}")
        if current_src:
            print(f"             | Bad URL: {current_src[:80]}")

        # Fetch a real image for this post's topic
        img_url, alt, credit_name, credit_link = get_image(title)
        if not img_url:
            print(f"  !  SKIP    | Could not fetch any image for: {title[:70]}\n")
            continue

        # Build the replacement img tag (with optional Unsplash credit)
        if credit_name and credit_link:
            new_img_tag = (
                f'<img src="{img_url}" alt="{alt or title}" '
                f'style="width:100%; border-radius:12px; margin-bottom:24px;"/>\n'
                f'<p style="text-align:center; font-style:italic; font-size:12px; '
                f'color:#5A5E6F; margin-top:-16px;">'
                f'Photo by <a href="{credit_link}" target="_blank">{credit_name}</a> on Unsplash</p>\n'
            )
        else:
            new_img_tag = _build_img_tag(img_url, alt or title)

        new_content = _replace_or_prepend_image(content, new_img_tag)

        # Patch via Blogger API
        try:
            service.posts().patch(
                blogId=BLOG_ID,
                postId=post_id,
                body={"content": new_content}
            ).execute()
            print(f"             | ✓ Patched with: {img_url[:80]}\n")
            patched += 1
        except Exception as e:
            print(f"             | ✗ API error: {e}\n")

    print(f"\n[REPAIR] Done. {patched} posts patched, {skipped} posts already had valid images.")


if __name__ == "__main__":
    fix_all_posts()
