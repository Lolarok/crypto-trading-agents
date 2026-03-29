"""
DeFiLlama data fetcher — free, no API key required.

Endpoints used:
  /tvl/{protocol}             — TVL for a specific protocol
  /v2/chains                  — TVL by chain
  /overview/dexs              — DEX volumes
  /overview/fees              — Protocol fees/revenue
  /stablecoins                — Stablecoin market caps
"""

import time
import requests

BASE_URL = "https://api.llama.fi"

_last_request_time = 0.0
MIN_INTERVAL = 1.5


def _throttled_get(url: str, params: dict = None) -> dict:
    """Rate-limited GET request to DeFiLlama."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    resp = requests.get(url, params=params or {}, timeout=30)
    _last_request_time = time.time()
    resp.raise_for_status()
    return resp.json()


def get_protocol_tvl(protocol: str) -> dict:
    """Get TVL data for a specific protocol (slug from defillama.com)."""
    return _throttled_get(f"{BASE_URL}/tvl/{protocol}")


def get_protocol_data(protocol: str) -> dict:
    """Get full protocol data including TVL history, chain breakdown, etc."""
    return _throttled_get(f"{BASE_URL}/protocol/{protocol}")


def get_chains_tvl() -> list:
    """Get TVL ranking by blockchain."""
    return _throttled_get(f"{BASE_URL}/v2/chains")


def get_dex_volumes() -> dict:
    """Get DEX volume overview."""
    return _throttled_get(f"{BASE_URL}/overview/dexs")


def get_protocol_fees() -> dict:
    """Get protocol fees and revenue overview."""
    return _throttled_get(f"{BASE_URL}/overview/fees")


def get_stablecoins() -> dict:
    """Get stablecoin market data."""
    return _throttled_get(f"{BASE_URL}/stablecoins?includePrices=false")


def get_yields() -> dict:
    """Get yield farming data."""
    return _throttled_get(f"{BASE_URL}/pools")


def format_tvl(tvl_value) -> str:
    """Format TVL value to human-readable string."""
    if isinstance(tvl_value, (int, float)):
        if tvl_value >= 1e9:
            return f"${tvl_value / 1e9:.2f}B"
        elif tvl_value >= 1e6:
            return f"${tvl_value / 1e6:.2f}M"
        elif tvl_value >= 1e3:
            return f"${tvl_value / 1e3:.2f}K"
        return f"${tvl_value:.2f}"
    return str(tvl_value)
