#!/usr/bin/env python3
"""
Less Clueless static site builder.

Reads content/posts.json and the raw Notion HTML exports in content/raw/,
extracts each post body, copies images, and writes:
  - index.html
  - posts/<slug>.html         (one per post)
  - assets/img/<slug>/...      (post images)

To add a new post later:
  1. Drop the Notion HTML export (and its image folder) into content/raw/
  2. Add an entry to content/posts.json (slug, title, description, date, source)
  3. Run:  python3 scripts/build.py
"""

import json
import os
import re
import shutil
import html
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "content", "raw")
IMG_OUT = os.path.join(ROOT, "assets", "img")
POSTS_OUT = os.path.join(ROOT, "posts")

with open(os.path.join(ROOT, "content", "posts.json"), encoding="utf-8") as f:
    DATA = json.load(f)

SITE = DATA["site"]
POSTS = DATA["posts"]


def fmt_date(iso):
    from datetime import datetime
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %-d, %Y")
    except Exception:
        return iso


def extract_body(src_html_path, slug):
    """Pull the Notion page-body div, rewrite image paths, return clean HTML."""
    raw = open(src_html_path, encoding="utf-8").read()
    m = re.search(r'<div class="page-body">(.*)</div>\s*</article>', raw, re.S)
    body = m.group(1) if m else ""

    # Build a lookup from Notion source .html filename -> our slug, so that
    # inter-post "link-to-page" references resolve to /posts/<slug>.html.
    src_to_slug = {os.path.basename(p["source"]): p["slug"] for p in POSTS}

    media_ext = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
                 ".mp4", ".webm", ".mov", ".pdf")

    def rewrite_src(match):
        attr, url = match.group(1), match.group(2)
        if url.startswith(("http://", "https://", "mailto:", "#", "data:")):
            return f'{attr}="{url}"'
        clean = unquote(url)
        base = os.path.basename(clean)
        low = base.lower()
        if low.endswith(media_ext):
            return f'{attr}="/assets/img/{slug}/{base}"'
        if low.endswith(".html"):
            target = src_to_slug.get(base)
            # Point at the linked post if we publish it; else drop to home.
            return f'{attr}="/posts/{target}.html"' if target else f'{attr}="/"'
        return f'{attr}="{url}"'

    body = re.sub(r'(src|href)="([^"]+)"', rewrite_src, body)

    # Convert Notion's mp4 "attachment" figures into inline <video> players.
    def video_embed(match):
        return (f'<video controls preload="metadata" src="{match.group(1)}">'
                f'</video>')
    body = re.sub(
        r'<figure[^>]*>.*?<a href="([^"]+\.mp4)"[^>]*>.*?</a>.*?</figure>',
        video_embed, body, flags=re.S)
    # Any remaining bare mp4 links -> video too
    body = re.sub(
        r'<div class="source"><a href="([^"]+\.mp4)"[^>]*>.*?</a></div>',
        video_embed, body, flags=re.S)

    # Drop Notion-only artifacts we don't need
    body = re.sub(r'\sdata-notion-[a-z-]+="[^"]*"', "", body)
    body = re.sub(r'\sid="[0-9a-f-]{36}"', "", body)
    return body


def copy_images(slug, source_filename):
    """Copy the post's Notion asset folder into assets/img/<slug>/."""
    folder_name = source_filename.rsplit(" ", 1)[0]  # strip trailing hash + .html
    src_dir = os.path.join(RAW, folder_name)
    dst_dir = os.path.join(IMG_OUT, slug)
    if os.path.isdir(src_dir):
        os.makedirs(dst_dir, exist_ok=True)
        for fn in os.listdir(src_dir):
            sp = os.path.join(src_dir, fn)
            if os.path.isfile(sp):
                shutil.copy2(sp, os.path.join(dst_dir, fn))


def head(title, description, canonical):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<header class="site-header"><div class="wrap">
  <a class="brand" href="/">{html.escape(SITE['title'])}</a>
  <nav class="nav">
    <a href="/">Writing</a>
    <a href="{SITE['socials'][3]['href']}">Substack</a>
  </nav>
</div></header>
"""


def footer():
    socials = "".join(
        f'<li><a href="{s["href"]}">{html.escape(s["label"])}</a></li>'
        for s in SITE["socials"]
    )
    return f"""
<footer class="site-footer"><div class="wrap">
  <div>— {html.escape(SITE['author'])}</div>
  <p><em>{html.escape(SITE['footer_note'])}</em></p>
  <ul class="socials">{socials}</ul>
</div></footer>
</body>
</html>
"""


def build_home():
    items = []
    for p in POSTS:
        tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in p.get("tags", []))
        items.append(f"""<li class="post-item">
  <a class="post-title" href="/posts/{p['slug']}.html">{html.escape(p['title'])}</a>
  <p class="post-desc">{html.escape(p['description'])}</p>
  <div class="post-meta"><span>{fmt_date(p['date'])}</span>{tags}</div>
</li>""")
    body = f"""
<main class="wrap">
  <section class="hero">
    <h1>{html.escape(SITE['title'])}</h1>
    <p class="tagline">{html.escape(SITE['tagline'])}</p>
    <p class="intro">{html.escape(SITE['intro'])}</p>
  </section>
  <div class="section-label">Writing</div>
  <ul class="post-list">
    {''.join(items)}
  </ul>
</main>
"""
    out = head(SITE["title"], SITE["tagline"], SITE["url"] + "/") + body + footer()
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)


def build_post(p):
    src = os.path.join(RAW, p["source"])
    copy_images(p["slug"], p["source"])
    body_html = extract_body(src, p["slug"])
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in p.get("tags", []))
    canonical = f"{SITE['url']}/posts/{p['slug']}.html"
    body = f"""
<main class="wrap">
  <article class="article">
    <div class="article-header">
      <h1>{html.escape(p['title'])}</h1>
      <div class="post-meta"><span>{fmt_date(p['date'])}</span>{tags}</div>
    </div>
    <div class="post-body">{body_html}</div>
    <a class="back-link" href="/">← All writing</a>
  </article>
</main>
"""
    out = head(p["title"], p["description"], canonical) + body + footer()
    os.makedirs(POSTS_OUT, exist_ok=True)
    with open(os.path.join(POSTS_OUT, f"{p['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(out)


def main():
    build_home()
    for p in POSTS:
        build_post(p)
    print(f"Built index.html + {len(POSTS)} posts.")


if __name__ == "__main__":
    main()
