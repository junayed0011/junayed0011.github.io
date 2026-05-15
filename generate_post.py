import requests
import datetime
import os
import re
import time

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

TOPICS = [
    "how artificial intelligence is changing everyday life",
    "best free tools for developers in 2025",
    "cybersecurity tips for beginners",
    "how to learn programming from scratch",
    "top productivity apps for remote workers",
    "simple morning routines that change your life",
    "healthy meal prep ideas for busy people",
    "how to improve sleep quality naturally",
    "beginner home workout routines no equipment",
    "mindfulness habits for reducing stress",
    "how to save money on a tight budget",
    "beginner's guide to investing in 2025",
    "best free tools to track your expenses",
    "how to build an emergency fund fast",
    "side hustles you can start with no money",
    "tips for learning any new skill faster",
    "how to stay motivated every day",
    "best habits for a more organized life",
    "how to travel on a very tight budget",
    "simple ways to improve your focus daily",
]

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
            print(f"✅ Unsplash image found: {img_url}")
            return img_url, alt, credit_name, credit_link
    except Exception as e:
        print(f"Unsplash failed: {e}")
    return None, None, None, None

def get_pollinations_image(topic):
    """Fallback: AI-generated image from Pollinations.ai."""
    try:
        prompt = topic.replace(" ", "%20")
        img_url = f"https://image.pollinations.ai/prompt/{prompt}?width=800&height=450&nologo=true"
        print(f"✅ Using Pollinations fallback: {img_url}")
        return img_url, topic, None, None
    except Exception as e:
        print(f"Pollinations failed: {e}")
    return None, None, None, None

def get_image(topic):
    """Try Unsplash first, fallback to Pollinations."""
    if UNSPLASH_ACCESS_KEY:
        img_url, alt, credit_name, credit_link = get_unsplash_image(topic)
        if img_url:
            return img_url, alt, credit_name, credit_link
    return get_pollinations_image(topic)

def call_groq(prompt):
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
        print(f"Attempt {attempt + 1}...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            wait = 20 * (attempt + 1)
            print(f"Rate limited. Waiting {wait} seconds...")
            time.sleep(wait)
        else:
            print(f"Error {response.status_code}: {response.text}")
            response.raise_for_status()

    raise Exception("All retry attempts failed.")

def generate_post(topic_offset=0):
    today = datetime.date.today()
    index = (today.timetuple().tm_yday * 2 + topic_offset) % len(TOPICS)
    topic = TOPICS[index]
    print(f"Topic: {topic}")

    # Get image
    img_url, alt, credit_name, credit_link = get_image(topic)

    # Build image markdown
    if img_url:
        if credit_name and credit_link:
            image_md = f'![{alt}]({img_url})\n*Photo by [{credit_name}]({credit_link}) on Unsplash*\n'
        else:
            image_md = f'![{alt}]({img_url})\n'
    else:
        image_md = ""

    prompt = f"""Write a high-quality, engaging blog post about: "{topic}"

Format in Markdown:
- Start with a single # Title
- Write 4-5 sections using ## headings
- Include bullet points and practical tips
- End with a ## Conclusion
- Length: 700-900 words
- Tone: friendly, helpful, conversational

Only return the Markdown content. No extra explanations."""

    content = call_groq(prompt)

    # Extract title
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else topic.title()

    # Remove # title line from content body
    body = re.sub(r'^# .+\n', '', content, count=1).strip()

    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
    date_str = today.strftime('%Y-%m-%d')
    hour = "07" if topic_offset == 0 else "19"

    post = f"""---
layout: post
title: "{title}"
date: {date_str} {hour}:00:00 +0000
categories: [blog]
description: "A blog post about {topic}"
image: {img_url or ''}
---

{image_md}
{body}
"""

    os.makedirs('_posts', exist_ok=True)
    suffix = "am" if topic_offset == 0 else "pm"
    filepath = f"_posts/{date_str}-{suffix}-{slug}.md"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(post)

    print(f"✅ Generated: {filepath}")

if __name__ == "__main__":
    offset = int(os.environ.get("POST_OFFSET", "0"))
    generate_post(offset)
