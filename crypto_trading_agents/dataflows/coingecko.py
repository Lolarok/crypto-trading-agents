"""
CoinGecko data fetcher — free, no API key required.

Endpoints used:
  /coins/{id}/market_chart  — price, market_cap, volume over time
  /coins/{id}/ohlc          — OHLC candles (1/7/14/30/91/181/365 days)
  /coins/{id}               — full coin data (description, links, sentiment)
  /coins/markets             — top coins by market cap
  /search/trending           — trending coins
  /global                    — total market cap, BTC dominance
"""

import time
import requests
from typing import Optional

BASE_URL = "https://api.coingecko.com/api/v3"

# Simple rate-limit: CoinGecko free = ~10-30 req/min
_last_request_time = 0.0
MIN_INTERVAL = 2.5  # seconds between requests


def _throttled_get(url: str, params: dict = None) -> dict:
    """Rate-limited GET request to CoinGecko."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    resp = requests.get(url, params=params or {}, timeout=30)
    _last_request_time = time.time()

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        print(f"[CoinGecko] Rate limited. Waiting {retry_after}s...")
        time.sleep(retry_after)
        return _throttled_get(url, params)

    resp.raise_for_status()
    return resp.json()


def get_ohlc(coin_id: str = "bitcoin", vs_currency: str = "usd", days: int = 30) -> list:
    """
    Get OHLC candles.
    days must be one of: 1, 7, 14, 30, 91, 181, 365 (CoinGecko free tier).
    Returns list of [timestamp, open, high, low, close].
    """
    # Snap to nearest valid interval
    valid_days = [1, 7, 14, 30, 91, 181, 365]
    days = min(valid_days, key=lambda x: abs(x - days))

    data = _throttled_get(
        f"{BASE_URL}/coins/{coin_id}/ohlc",
        params={"vs_currency": vs_currency, "days": days},
    )
    return data


def get_market_chart(coin_id: str = "bitcoin", vs_currency: str = "usd", days: int = 30) -> dict:
    """
    Get market chart data (prices, market_caps, total_volumes).
    """
    data = _throttled_get(
        f"{BASE_URL}/coins/{coin_id}/market_chart",
        params={"vs_currency": vs_currency, "days": days},
    )
    return data


def get_coin_data(coin_id: str = "bitcoin") -> dict:
    """
    Get full coin data: description, links, sentiment, market data,
    developer data, community data, etc.
    """
    data = _throttled_get(
        f"{BASE_URL}/coins/{coin_id}",
        params={
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true",
            "sparkline": "false",
        },
    )
    return data


def get_top_coins(
    vs_currency: str = "usd",
    order: str = "market_cap_desc",
    per_page: int = 100,
    page: int = 1,
) -> list:
    """Get top coins by market cap."""
    data = _throttled_get(
        f"{BASE_URL}/coins/markets",
        params={
            "vs_currency": vs_currency,
            "order": order,
            "per_page": per_page,
            "page": page,
            "sparkline": "false",
        },
    )
    return data


def get_trending() -> dict:
    """Get trending coins on CoinGecko."""
    return _throttled_get(f"{BASE_URL}/search/trending")


def get_global_data() -> dict:
    """Get global crypto market data: total market cap, volume, BTC dominance."""
    data = _throttled_get(f"{BASE_URL}/global")
    return data.get("data", data)


def ohlc_to_dataframe(ohlc_list: list):
    """
    Convert OHLC list [[ts, o, h, l, c], ...] to a pandas DataFrame.
    """
    import pandas as pd

    df = pd.DataFrame(ohlc_list, columns=["timestamp", "open", "high", "low", "close"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("date", inplace=True)
    df.drop("timestamp", axis=1, inplace=True)
    return df


def market_chart_to_dataframe(chart_data: dict):
    """
    Convert market_chart response to pandas DataFrames.
    Returns dict with 'prices', 'market_caps', 'volumes' DataFrames.
    """
    import pandas as pd

    result = {}
    for key in ["prices", "market_caps", "total_volumes"]:
        if key in chart_data:
            df = pd.DataFrame(chart_data[key], columns=["timestamp", key])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("date", inplace=True)
            df.drop("timestamp", axis=1, inplace=True)
            result[key] = df
    return result
