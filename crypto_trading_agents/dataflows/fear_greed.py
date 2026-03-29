"""
Crypto Fear & Greed Index — free, no API key required.

Endpoint: https://api.alternative.me/fng/
"""

import time
import requests

BASE_URL = "https://api.alternative.me"

_last_request_time = 0.0
MIN_INTERVAL = 1.0


def _throttled_get(url: str, params: dict = None) -> dict:
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    resp = requests.get(url, params=params or {}, timeout=30)
    _last_request_time = time.time()
    resp.raise_for_status()
    return resp.json()


def get_fear_greed(limit: int = 30) -> dict:
    """
    Get Fear & Greed index data.
    Returns dict with 'data' key containing list of {value, value_classification, timestamp}.
    """
    data = _throttled_get(
        f"{BASE_URL}/fng/",
        params={"limit": limit},
    )
    return data


def get_current_fear_greed() -> dict:
    """Get just the current Fear & Greed value."""
    data = get_fear_greed(limit=1)
    if data.get("data"):
        entry = data["data"][0]
        return {
            "value": int(entry["value"]),
            "classification": entry["value_classification"],
            "timestamp": entry["timestamp"],
        }
    return {"value": 0, "classification": "Unknown", "timestamp": "0"}


def format_fear_greed(value: int) -> str:
    """Format Fear & Greed value with emoji."""
    if value <= 25:
        return f"😱 {value} — Extreme Fear"
    elif value <= 45:
        return f"😟 {value} — Fear"
    elif value <= 55:
        return f"😐 {value} — Neutral"
    elif value <= 75:
        return f"😊 {value} — Greed"
    else:
        return f"🤑 {value} — Extreme Greed"
