import requests
import datetime
import os
import re
import time

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

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

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 2048}
    }

    for attempt in range(5):
        print(f"Attempt {attempt + 1}...")
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Unexpected response: {data}")
                raise Exception("No candidates in response")

        elif response.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"Rate limited. Waiting {wait} seconds...")
            time.sleep(wait)

        else:
            print(f"Error {response.status_code}: {response.text}")
            response.raise_for_status()

    raise Exception("All retry attempts failed due to rate limiting.")

def generate_post(topic_offset=0):
    today = datetime.date.today()
    index = (today.timetuple().tm_yday * 2 + topic_offset) % len(TOPICS)
    topic = TOPICS[index]
    print(f"Topic: {topic}")

    prompt = f"""Write a high-quality, engaging blog post about: "{topic}"

Format in Markdown:
- Start with a single # Title
- Write 4-5 sections using ## headings
- Include bullet points and practical tips
- End with a ## Conclusion
- Length: 700-900 words
- Tone: friendly, helpful, conversational

Only return the Markdown content. No extra explanations."""

    content = call_gemini(prompt)

    # Extract title
    title_match = re.search(r'^# (.+)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else topic.title()

    # Build slug
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:50]
    date_str = today.strftime('%Y-%m-%d')
    hour = "07" if topic_offset == 0 else "19"

    post = f"""---
layout: post
title: "{title}"
date: {date_str} {hour}:00:00 +0000
categories: [blog]
description: "A blog post about {topic}"
---

{content}
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
