"""
CoinMarketCap API data fetcher — free tier (10,000 calls/month).

Auth: X-CMC_PRO_API_KEY header

Endpoints:
  /cryptocurrency/listings/latest     — top coins by market cap
  /cryptocurrency/quotes/latest       — price + market data for specific coins
  /cryptocurrency/info                — metadata (description, links, tags)
  /cryptocurrency/ohlcv/latest        — OHLCV candles
  /cryptocurrency/trending/latest     — trending gainers/losers
  /global-metrics/quotes/latest       — total market cap, BTC dominance
  /fear-and-greed/latest              — Fear & Greed index
  /content/post/latest                — crypto news
"""

import os
import time
import requests
from typing import Optional, List

BASE_URL = "https://pro-api.coinmarketcap.com/v1"

_last_request_time = 0.0
MIN_INTERVAL = 1.0  # 30 req/min on free tier = 2s safe interval


def _get_headers() -> dict:
    api_key = os.getenv("CMC_API_KEY", "")
    if not api_key:
        raise ValueError("CMC_API_KEY environment variable is required")
    return {
        "X-CMC_PRO_API_KEY": api_key,
        "Accept": "application/json",
    }


def _throttled_get(endpoint: str, params: dict = None) -> dict:
    """Rate-limited GET to CoinMarketCap."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    resp = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=_get_headers(),
        params=params or {},
        timeout=30,
    )
    _last_request_time = time.time()

    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        print(f"[CMC] Rate limited. Waiting {retry_after}s...")
        time.sleep(retry_after)
        return _throttled_get(endpoint, params)

    resp.raise_for_status()
    return resp.json().get("data", resp.json())


def get_listings(
    limit: int = 20,
    convert: str = "USD",
    sort: str = "market_cap",
) -> list:
    """Get top coins by market cap."""
    return _throttled_get("/cryptocurrency/listings/latest", {
        "limit": limit,
        "convert": convert,
        "sort": sort,
        "sort_dir": "desc",
    })


def get_quotes(symbol: str, convert: str = "USD") -> dict:
    """Get price quote and market data for a coin by symbol (e.g., BTC, ETH)."""
    data = _throttled_get("/cryptocurrency/quotes/latest", {
        "symbol": symbol,
        "convert": convert,
    })
    return data.get(symbol, data)


def get_coin_info(symbol: str) -> dict:
    """Get coin metadata: description, links, tags, category, etc."""
    data = _throttled_get("/cryptocurrency/info", {"symbol": symbol})
    return data.get(symbol, data)


def get_ohlcv(symbol: str, convert: str = "USD", time_period: str = "daily") -> dict:
    """
    Get OHLCV data. time_period: 'daily', 'hourly', 'weekly', 'monthly', 'yearly'.
    Returns latest + historical quotes.
    """
    data = _throttled_get("/cryptocurrency/ohlcv/latest", {
        "symbol": symbol,
        "convert": convert,
        "time_period": time_period,
    })
    return data.get(symbol, data)


def get_global_metrics(convert: str = "USD") -> dict:
    """Get global crypto market metrics."""
    return _throttled_get("/global-metrics/quotes/latest", {"convert": convert})


def get_fear_and_greed() -> dict:
    """Get Fear & Greed index from CoinMarketCap."""
    return _throttled_get("/fear-and-greed/latest")


def get_trending(limit: int = 10) -> dict:
    """Get trending gainers and losers."""
    return _throttled_get("/cryptocurrency/trending/latest", {"limit": limit})


def get_categories(limit: int = 20) -> list:
    """Get crypto categories with market data."""
    return _throttled_get("/cryptocurrency/categories", {"limit": limit})


def get_news(limit: int = 10) -> list:
    """Get latest crypto news from CoinMarketCap."""
    data = _throttled_get("/content/posts/latest", {"limit": limit})
    return data if isinstance(data, list) else data.get("data", [])


def format_quote_report(symbol: str = "BTC") -> str:
    """Format a coin quote into a readable report."""
    try:
        quote = get_quotes(symbol)
        usd = quote.get("quote", {}).get("USD", {})

        lines = [
            f"## {quote.get('name', symbol)} ({quote.get('symbol', symbol)})",
            f"**Rank:** #{quote.get('cmc_rank', 'N/A')}",
            f"**Price:** ${usd.get('price', 0):,.2f}",
            f"**Market Cap:** ${usd.get('market_cap', 0):,.0f}",
            f"**24h Volume:** ${usd.get('volume_24h', 0):,.0f}",
            f"**24h Change:** {usd.get('percent_change_24h', 0):.2f}%",
            f"**7d Change:** {usd.get('percent_change_7d', 0):.2f}%",
            f"**30d Change:** {usd.get('percent_change_30d', 0):.2f}%",
            f"**1h Change:** {usd.get('percent_change_1h', 0):.2f}%",
            "",
            f"**Circulating Supply:** {quote.get('circulating_supply', 0):,.0f}",
            f"**Total Supply:** {quote.get('total_supply', 0):,.0f}",
            f"**Max Supply:** {quote.get('max_supply', 0) or '∞':,}",
            f"**FDV:** ${quote.get('quote', {}).get('USD', {}).get('fully_diluted_market_cap', 0):,.0f}",
        ]
        return "\n".join(str(l) for l in lines)
    except Exception as e:
        return f"Error fetching quote for {symbol}: {e}"


def format_global_report() -> str:
    """Format global market metrics."""
    try:
        data = get_global_metrics()
        usd = data.get("quote", {}).get("USD", {})

        lines = [
            "## Global Crypto Market (CoinMarketCap)",
            f"**Total Market Cap:** ${usd.get('total_market_cap', 0):,.0f}",
            f"**24h Volume:** ${usd.get('total_volume_24h', 0):,.0f}",
            f"**BTC Dominance:** {data.get('btc_dominance', 0):.1f}%",
            f"**ETH Dominance:** {data.get('eth_dominance', 0):.1f}%",
            f"**Active Cryptos:** {data.get('active_cryptocurrencies', 0):,}",
            f"**Active Exchanges:** {data.get('active_exchanges', 0):,}",
            f"**Market Cap Change 24h:** {usd.get('total_market_cap_yesterday_percentage_change', 0):.2f}%",
            f"**Volume Change 24h:** {usd.get('total_volume_24h_yesterday_percentage_change', 0):.2f}%",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching global metrics: {e}"


def format_listings_report(limit: int = 20) -> str:
    """Format top coins listing."""
    try:
        coins = get_listings(limit=limit)
        lines = [f"**Top {limit} Cryptocurrencies by Market Cap (CoinMarketCap):**", ""]
        lines.append(f"{'#':<4} {'Name':<20} {'Price':<15} {'MCap':<18} {'24h %':<10}")
        lines.append("-" * 75)

        for coin in coins:
            rank = coin.get("cmc_rank", "?")
            name = coin.get("name", "?")[:18]
            symbol = coin.get("symbol", "?")
            usd = coin.get("quote", {}).get("USD", {})
            price = usd.get("price", 0)
            mcap = usd.get("market_cap", 0)
            change = usd.get("percent_change_24h", 0)

            price_str = f"${price:,.2f}" if price < 1000 else f"${price:,.0f}"
            mcap_str = f"${mcap/1e9:.1f}B" if mcap else "N/A"
            change_str = f"{change:+.1f}%" if change else "N/A"

            lines.append(f"{rank:<4} {name} ({symbol}){'':<1} {price_str:<15} {mcap_str:<18} {change_str:<10}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching listings: {e}"
