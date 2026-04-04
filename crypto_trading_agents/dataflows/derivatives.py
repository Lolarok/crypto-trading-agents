"""
Derivatives data — funding rates, open interest, liquidations.

Uses CoinGecko derivatives endpoints + free public APIs.
"""

import time
import requests
from typing import Optional

BASE_URL = "https://api.coingecko.com/api/v3"

_last_request_time = 0.0
MIN_INTERVAL = 2.5


def _throttled_get(url: str, params: dict = None) -> dict:
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    resp = requests.get(url, params=params or {}, timeout=30)
    _last_request_time = time.time()

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        return _throttled_get(url, params)

    resp.raise_for_status()
    return resp.json()


def get_derivatives_exchanges() -> list:
    """Get derivatives exchange data including open interest and volumes."""
    return _throttled_get(f"{BASE_URL}/derivatives/exchanges")


def get_derivatives_exchange(exchange_id: str) -> dict:
    """Get specific derivatives exchange data."""
    return _throttled_get(f"{BASE_URL}/derivatives/exchanges/{exchange_id}")


def get_derivatives_tickers(coin_id: str = "bitcoin") -> list:
    """Get derivative tickers for a coin (perpetuals, futures)."""
    return _throttled_get(
        f"{BASE_URL}/derivatives",
        params={"include_tickers": "unexpired"},
    )


def format_derivatives_report(coin_id: str = "bitcoin") -> str:
    """Format derivatives data into a readable report."""
    try:
        exchanges = get_derivatives_exchanges()

        lines = ["## Derivatives Market Overview\n"]

        # Top exchanges by open interest
        sorted_by_oi = sorted(
            exchanges,
            key=lambda x: x.get("open_interest_btc", 0) or 0,
            reverse=True,
        )

        lines.append("**Top Exchanges by Open Interest:**")
        total_oi = 0
        for ex in sorted_by_oi[:10]:
            oi = ex.get("open_interest_btc", 0) or 0
            total_oi += oi
            name = ex.get("name", "?")
            vol = ex.get("trade_volume_24h_btc", 0) or 0
            lines.append(f"  {name}: OI {oi:,.0f} BTC | 24h Vol {vol:,.0f} BTC")

        lines.append(f"\n**Total tracked OI (top 10):** {total_oi:,.0f} BTC")

        # Perpetuals info
        perp_count = sum(1 for e in exchanges if e.get("open_interest_btc"))
        lines.append(f"**Active derivatives exchanges:** {perp_count}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching derivatives data: {e}"
