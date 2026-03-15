"""
Tracks which products have been featured in the daily deep-dive,
so we never repeat the same product.
"""

import json
import os
from datetime import datetime, timezone

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "product_history.json")


def load_history() -> list[dict]:
    """Load the history of previously featured products."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_featured_titles() -> set[str]:
    """Return a set of product/topic titles that have already been featured."""
    return {entry["title"] for entry in load_history()}


def record_featured(title: str) -> None:
    """Record a product as featured today."""
    history = load_history()
    history.append({
        "title": title,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    })
    # Keep last 365 entries to avoid unbounded growth
    history = history[-365:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
