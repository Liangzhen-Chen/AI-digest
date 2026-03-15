"""
AI Digest — daily information assistant.
Collects news → AI summarizes → sends email.
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env for local development

from feeds import fetch_all_feeds
from summarizer import summarize_digest
from mailer import send_digest


def main():
    print("=" * 50)
    print("🚀 AI Digest — Starting daily run")
    print("=" * 50)

    # Step 1: Collect feeds
    print("\n📡 Step 1: Fetching RSS feeds ...")
    feeds = fetch_all_feeds()
    total = sum(len(v) for v in feeds.values())
    print(f"   Collected {total} articles across {len(feeds)} sections")

    if total == 0:
        print("⚠️  No articles fetched. Skipping digest.")
        sys.exit(0)

    # Step 2: AI Summarize
    print("\n🧠 Step 2: Generating AI summary ...")
    digest = summarize_digest(feeds)
    print(f"   Generated digest ({len(digest)} chars)")

    # Step 3: Send email
    print("\n📧 Step 3: Sending email ...")
    send_digest(digest)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
