"""Live cricket news RSS feed reader with timeouts, sanitization, and graceful fallback."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import feedparser
import requests

from cricintel.ingestion.preprocessor import clean_html, clean_text, enrich_article_metadata
from cricintel.ingestion.sample_loader import load_sample_articles

# Accessible cricket RSS feeds from top international and domestic outlets
DEFAULT_RSS_FEEDS = [
    {
        "name": "ESPNcricinfo",
        "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
        "category": "International",
    },
    {
        "name": "BBC Sport Cricket",
        "url": "https://feeds.bbci.co.uk/sport/cricket/rss.xml",
        "category": "International",
    },
    {
        "name": "NDTV Sports Cricket",
        "url": "https://feeds.feedburner.com/ndtvsports-cricket",
        "category": "International",
    },
    {
        "name": "Sky Sports Cricket",
        "url": "https://www.skysports.com/rss/12123",
        "category": "International",
    },
    {
        "name": "The Guardian Cricket",
        "url": "https://www.theguardian.com/sport/cricket/rss",
        "category": "International",
    },
    {
        "name": "Hindustan Times Cricket",
        "url": "https://www.hindustantimes.com/feeds/rss/cricket/rssfeed.xml",
        "category": "International",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 (CricIntel-AI/1.0)"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def fetch_feed_articles(
    feed_meta: Dict[str, str], timeout_seconds: int = 5, max_articles: int = 20
) -> List[Dict[str, Any]]:
    """Fetch and parse articles from a single RSS feed."""
    articles: List[Dict[str, Any]] = []
    feed_url = feed_meta["url"]
    feed_name = feed_meta["name"]

    try:
        response = requests.get(feed_url, headers=HEADERS, timeout=timeout_seconds)
        if response.status_code != 200:
            return []

        parsed = feedparser.parse(response.content)
        for entry in parsed.entries[:max_articles]:
            title = clean_text(entry.get("title", ""))
            if not title or len(title) < 10:
                continue

            # Extract content from summary or content fields
            summary = entry.get("summary", "") or entry.get("description", "")
            if entry.get("content") and len(entry["content"]) > 0:
                summary = entry["content"][0].get("value", summary)

            cleaned_content = clean_text(summary)
            if not cleaned_content or len(cleaned_content) < 20:
                cleaned_content = title

            link = entry.get("link", "")
            # Generate deterministic ID
            art_id = "rss_" + hashlib.md5(f"{feed_name}_{title}".encode("utf-8")).hexdigest()[:10]

            # Parse published date
            published_str = entry.get("published", "") or entry.get("updated", "")
            if not published_str:
                published_str = datetime.now(timezone.utc).isoformat()

            author = entry.get("author", feed_name)

            raw_article = {
                "id": art_id,
                "title": title,
                "source": feed_name,
                "url": link,
                "published_at": published_str,
                "author": author,
                "category": feed_meta.get("category", "International"),
                "tournament": "International",
                "teams": [],
                "players": [],
                "content": cleaned_content,
            }

            enriched = enrich_article_metadata(raw_article)
            articles.append(enriched)

    except Exception:
        # Feeds can time out or fail; return whatever we successfully collected
        return []

    return articles


def fetch_all_cricket_news(
    feeds: Optional[List[Dict[str, str]]] = None,
    timeout_per_feed: int = 4,
    max_articles_per_feed: int = 20,
    include_sample_if_low: bool = True,
    min_articles_threshold: int = 15,
) -> Dict[str, Any]:
    """Fetch live cricket articles across all configured feeds with automatic offline fallback."""
    target_feeds = feeds or DEFAULT_RSS_FEEDS
    collected_articles: List[Dict[str, Any]] = []
    feed_statuses: Dict[str, str] = {}
    start_time = time.time()

    for feed in target_feeds:
        feed_name = feed["name"]
        try:
            articles = fetch_feed_articles(
                feed, timeout_seconds=timeout_per_feed, max_articles=max_articles_per_feed
            )
            if articles:
                collected_articles.extend(articles)
                feed_statuses[feed_name] = f"Success ({len(articles)} articles)"
            else:
                feed_statuses[feed_name] = "No articles returned (fallback ready)"
        except Exception as e:
            feed_statuses[feed_name] = f"Error: {type(e).__name__}"

    # Deduplicate by URL and title
    unique_articles: List[Dict[str, Any]] = []
    seen_titles = set()
    for art in collected_articles:
        title_key = art["title"].lower()[:45]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(art)

    used_fallback = False
    if len(unique_articles) < min_articles_threshold and include_sample_if_low:
        sample_articles = load_sample_articles()
        # Merge sample articles while avoiding duplicate titles
        for s_art in sample_articles:
            t_key = s_art["title"].lower()[:45]
            if t_key not in seen_titles:
                seen_titles.add(t_key)
                unique_articles.append(s_art)
        used_fallback = True

    duration = round(time.time() - start_time, 2)

    return {
        "articles": unique_articles,
        "total_count": len(unique_articles),
        "feed_statuses": feed_statuses,
        "duration_seconds": duration,
        "used_fallback": used_fallback,
    }
