"""
RSS Feed collector — fetches articles from curated free sources.
"""

import feedparser
import requests
from datetime import datetime, timedelta, timezone

# ── Feed configuration ────────────────────────────────────────────────
# Each section maps to a topic block in the final digest.
FEED_SOURCES = {
    # ━━ 时事板块 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "国际经济政治": [
        {"name": "BBC World",       "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
        {"name": "BBC Business",    "url": "http://feeds.bbci.co.uk/news/business/rss.xml"},
        {"name": "Reuters World",   "url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"},
        {"name": "经济学人",         "url": "https://www.economist.com/international/rss.xml"},
        {"name": "FT",              "url": "https://www.ft.com/rss/home/uk"},
    ],
    "AI动态": [
        {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
        {"name": "The Verge AI",       "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
        {"name": "OpenAI Blog",        "url": "https://openai.com/blog/rss.xml"},
        {"name": "Google AI Blog",     "url": "https://blog.google/technology/ai/rss/"},
        {"name": "Hacker News",        "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT&points=50"},
    ],
    "商业与金融": [
        {"name": "Bloomberg",      "url": "https://feeds.bloomberg.com/markets/news.rss"},
        {"name": "CNBC",           "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147"},
        {"name": "WSJ Markets",    "url": "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain.xml"},
        {"name": "36氪",           "url": "https://36kr.com/feed"},
    ],
    "科技动态": [
        {"name": "TechCrunch",     "url": "https://techcrunch.com/feed/"},
        {"name": "The Verge",      "url": "https://www.theverge.com/rss/index.xml"},
        {"name": "Ars Technica",   "url": "https://feeds.arstechnica.com/arstechnica/index"},
        {"name": "Wired",          "url": "https://www.wired.com/feed/rss"},
    ],

    # ━━ 学习板块 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "经济金融分析": [
        {"name": "Economist Finance",  "url": "https://www.economist.com/finance-and-economics/rss.xml"},
        {"name": "Project Syndicate",  "url": "https://www.project-syndicate.org/rss"},
        {"name": "VOX EU",            "url": "https://cepr.org/rss/columns/feed"},
        {"name": "FT Alphaville",     "url": "https://www.ft.com/alphaville?format=rss"},
    ],
    "互联网产品分析": [
        {"name": "人人都是产品经理",    "url": "https://www.woshipm.com/feed"},
        {"name": "少数派",             "url": "https://sspai.com/feed"},
        {"name": "Product Hunt",      "url": "https://www.producthunt.com/feed"},
        {"name": "Stratechery",       "url": "https://stratechery.com/feed/"},
        {"name": "a16z Blog",         "url": "https://a16z.com/feed/"},
        {"name": "虎嗅",              "url": "https://www.huxiu.com/rss/0.xml"},
        {"name": "极客公园",           "url": "https://www.geekpark.net/rss"},
        {"name": "Lenny's Newsletter", "url": "https://www.lennysnewsletter.com/feed"},
        {"name": "Mind the Product",  "url": "https://www.mindtheproduct.com/feed/"},
        {"name": "Intercom Blog",     "url": "https://www.intercom.com/blog/feed/"},
        {"name": "First Round Review", "url": "https://review.firstround.com/feed.xml"},
    ],
}

# YouTube channels (via RSS — no API key needed)
YOUTUBE_CHANNELS = {
    "国际经济政治": [
        {"name": "BBC News",          "channel_id": "UC16niRr50-MSBwiO3YDb3RA"},
        {"name": "Al Jazeera",        "channel_id": "UCNye-wNBqNL5ZzHSJj3l8Bg"},
        {"name": "DW News",           "channel_id": "UCknLrEdhRCp1aegoMqRaCZg"},
    ],
    "AI动态": [
        {"name": "Two Minute Papers",  "channel_id": "UCbfYPyITQ-7l4upoX8nvctg"},
        {"name": "Matt Wolfe",         "channel_id": "UCJMQEbKsmRYAMpYHBbMEv2g"},
        {"name": "AI Explained",       "channel_id": "UCNJ1Ymd5yFuUPtn21xtRbbw"},
    ],
    "商业与金融": [
        {"name": "Bloomberg TV",       "channel_id": "UCIALMKvObZNtJ68-rmFhsGQ"},
        {"name": "CNBC",               "channel_id": "UCvJJ_dzjViJCoLf5uKUTwoA"},
    ],
    "科技动态": [
        {"name": "MKBHD",             "channel_id": "UCBcRF18a7Qf58cCRy5xuWwQ"},
        {"name": "Linus Tech Tips",   "channel_id": "UCXuqSBlHAE6Xw-yeJA0Tunw"},
    ],
}

YOUTUBE_RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={}"

# Sections where we fetch full article content (not just RSS summary)
FULL_CONTENT_SECTIONS = {"互联网产品分析"}

# Product section gets a longer time window (30 days) to ensure
# there's always enough material for the daily product deep-dive.
EXTENDED_HOURS_SECTIONS = {"互联网产品分析": 30 * 24}  # 30 days

# Wikipedia API (completely free, no key needed)
WIKI_API = "https://zh.wikipedia.org/w/api.php"
WIKI_EN_API = "https://en.wikipedia.org/w/api.php"


def _parse_feed(url: str, max_items: int = 5, hours: int = 48) -> list[dict]:
    """Parse a single RSS feed, return recent entries."""
    try:
        feed = feedparser.parse(url)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        items = []
        for entry in feed.entries[:max_items * 2]:  # fetch extra, filter by date
            published = None
            for date_field in ("published_parsed", "updated_parsed"):
                t = getattr(entry, date_field, None)
                if t:
                    from calendar import timegm
                    published = datetime.fromtimestamp(timegm(t), tz=timezone.utc)
                    break
            # If no date, include it anyway (some feeds omit dates)
            if published and published < cutoff:
                continue

            # Some feeds put full HTML in "content", use it if available
            content_text = ""
            if hasattr(entry, "content") and entry.content:
                content_text = entry.content[0].get("value", "")[:2000]

            items.append({
                "title": getattr(entry, "title", ""),
                "link": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", "")[:500],
                "content": content_text,
                "published": published.isoformat() if published else "",
            })
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return []


def _fetch_full_text(url: str) -> str:
    """Fetch the full text of a web page (best effort, for product articles)."""
    try:
        import re
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AIDigestBot/1.0)"
        })
        resp.raise_for_status()
        # Strip HTML tags for a rough plain-text extraction
        text = re.sub(r"<script[^>]*>.*?</script>", "", resp.text, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:3000]  # Cap at 3000 chars to stay within token limits
    except Exception as e:
        print(f"  [WARN] Failed to fetch full text from {url}: {e}")
        return ""


def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for a product/company and return a factual summary.
    Tries Chinese Wikipedia first, falls back to English.
    Completely free, no API key needed.
    """
    for api_url in [WIKI_API, WIKI_EN_API]:
        try:
            # Step 1: Search for the page
            search_resp = requests.get(api_url, params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": 1,
                "format": "json",
            }, timeout=10)
            results = search_resp.json().get("query", {}).get("search", [])
            if not results:
                continue

            page_title = results[0]["title"]

            # Step 2: Get the extract (plain text summary)
            extract_resp = requests.get(api_url, params={
                "action": "query",
                "titles": page_title,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "format": "json",
            }, timeout=10)
            pages = extract_resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                extract = page.get("extract", "")
                if extract:
                    lang = "zh" if api_url == WIKI_API else "en"
                    print(f"  [Wiki-{lang}] Found: {page_title}")
                    return f"[Wikipedia: {page_title}] {extract[:1500]}"
        except Exception as e:
            print(f"  [WARN] Wikipedia search failed ({api_url}): {e}")
            continue

    return ""


def fetch_all_feeds() -> dict[str, list[dict]]:
    """
    Returns {section_name: [article_dicts]} for every configured section.
    """
    result: dict[str, list[dict]] = {}

    for section, feeds in FEED_SOURCES.items():
        articles = []
        need_full_content = section in FULL_CONTENT_SECTIONS
        hours = EXTENDED_HOURS_SECTIONS.get(section, 48)
        for feed_cfg in feeds:
            print(f"  Fetching [{feed_cfg['name']}] ...")
            items = _parse_feed(feed_cfg["url"],
                                max_items=8 if need_full_content else 5,
                                hours=hours)
            for item in items:
                item["source"] = feed_cfg["name"]
                # For product sections: fetch full article text if RSS content is thin
                if need_full_content and len(item.get("content", "")) < 200:
                    full = _fetch_full_text(item["link"])
                    if full:
                        item["content"] = full
            articles.extend(items)
        result[section] = articles

    # YouTube channels
    for section, channels in YOUTUBE_CHANNELS.items():
        if section not in result:
            result[section] = []
        for ch in channels:
            url = YOUTUBE_RSS_TEMPLATE.format(ch["channel_id"])
            print(f"  Fetching YouTube [{ch['name']}] ...")
            items = _parse_feed(url, max_items=3, hours=48)
            for item in items:
                item["source"] = f"YouTube: {ch['name']}"
            result[section].extend(items)

    # Fetch Wikipedia context for product deep-dive grounding
    print("\n📖 Fetching Wikipedia context for product grounding ...")
    product_articles = result.get("互联网产品分析", [])
    wiki_contexts = []
    # Pick up to 3 product-related titles to look up
    seen = set()
    for article in product_articles[:10]:
        # Extract likely product/company name from title
        title = article.get("title", "")
        if title and title not in seen:
            seen.add(title)
            wiki_text = search_wikipedia(title)
            if wiki_text:
                wiki_contexts.append(wiki_text)
            if len(wiki_contexts) >= 3:
                break

    if wiki_contexts:
        result["_wiki_product_context"] = [
            {"title": "Wikipedia 产品背景资料",
             "link": "",
             "summary": "\n\n".join(wiki_contexts),
             "content": "\n\n".join(wiki_contexts),
             "source": "Wikipedia",
             "published": ""}
        ]

    return result
