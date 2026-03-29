"""
RSS News fetcher for crypto news sources.

Fetches headlines and snippets from major crypto news outlets.
Uses stdlib xml.etree + requests — no extra dependencies.
"""

import time
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime

# Crypto RSS feeds (verified working as of 2026)
RSS_FEEDS = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt": "https://decrypt.co/feed",
    "theblock": "https://www.theblock.co/rss.xml",
    "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
    "cryptoslate": "https://cryptoslate.com/feed/",
}

_last_request_time = 0.0
MIN_INTERVAL = 2.0


def _throttled_get(url: str, timeout: int = 15) -> Optional[str]:
    """Rate-limited GET for RSS feeds."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    try:
        headers = {"User-Agent": "CryptoTradingAgents/0.1 (RSS Reader)"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        _last_request_time = time.time()
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"[RSS] Error fetching {url}: {e}")
    return None


def _parse_rss(xml_text: str, source: str, limit: int = 10) -> List[Dict]:
    """Parse RSS XML into list of article dicts."""
    articles = []
    try:
        root = ET.fromstring(xml_text)

        # Handle both RSS 2.0 and Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        # RSS 2.0
        items = root.findall(".//item")
        if not items:
            # Atom
            items = root.findall(".//atom:entry", ns)

        for item in items[:limit]:
            title = item.findtext("title") or item.findtext("atom:title", namespaces=ns) or ""
            link = item.findtext("link") or ""
            if not link:
                link_el = item.find("atom:link", ns)
                if link_el is not None:
                    link = link_el.get("href", "")

            pub_date = item.findtext("pubDate") or item.findtext("atom:published", namespaces=ns) or ""
            description = item.findtext("description") or item.findtext("atom:summary", namespaces=ns) or ""

            # Clean HTML tags from description
            import re
            description = re.sub(r"<[^>]+>", "", description).strip()
            if len(description) > 300:
                description = description[:300] + "..."

            articles.append({
                "source": source,
                "title": title.strip(),
                "link": link.strip(),
                "date": pub_date.strip(),
                "description": description,
            })
    except ET.ParseError as e:
        print(f"[RSS] Parse error for {source}: {e}")

    return articles


def fetch_crypto_news(
    sources: Optional[List[str]] = None,
    limit_per_source: int = 10,
) -> List[Dict]:
    """
    Fetch crypto news from RSS feeds.

    Args:
        sources: List of source names (default: all)
        limit_per_source: Max articles per source

    Returns:
        List of article dicts sorted by source
    """
    if sources is None:
        sources = list(RSS_FEEDS.keys())

    all_articles = []
    for source in sources:
        url = RSS_FEEDS.get(source)
        if not url:
            print(f"[RSS] Unknown source: {source}")
            continue

        xml_text = _throttled_get(url)
        if xml_text:
            articles = _parse_rss(xml_text, source, limit_per_source)
            all_articles.extend(articles)
            print(f"[RSS] {source}: {len(articles)} articles")

    return all_articles


def format_news_report(articles: List[Dict], max_articles: int = 20) -> str:
    """Format articles into a readable news report."""
    if not articles:
        return "No news articles available."

    lines = [f"## Crypto News ({len(articles[:max_articles])} articles)\n"]

    for i, article in enumerate(articles[:max_articles], 1):
        lines.append(f"**{i}. [{article['source']}] {article['title']}**")
        if article["description"]:
            lines.append(f"   {article['description']}")
        if article["link"]:
            lines.append(f"   🔗 {article['link']}")
        lines.append("")

    return "\n".join(lines)


def search_news(articles: List[Dict], keyword: str) -> List[Dict]:
    """Filter articles by keyword in title or description."""
    keyword_lower = keyword.lower()
    return [
        a for a in articles
        if keyword_lower in a.get("title", "").lower()
        or keyword_lower in a.get("description", "").lower()
    ]
