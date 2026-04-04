"""
LangChain @tool functions for crypto data retrieval.
These are the tools that analyst agents bind to their LLM calls.
"""

from langchain_core.tools import tool
from typing import Annotated
from crypto_trading_agents.dataflows import coingecko, defillama, fear_greed, indicators


@tool
def get_crypto_price(
    coin_id: Annotated[str, "CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'solana')"],
    vs_currency: Annotated[str, "Quote currency (default: usd)"] = "usd",
    days: Annotated[int, "Number of days of OHLC data (1/7/14/30/91/181/365)"] = 30,
) -> str:
    """
    Get OHLC price data for a cryptocurrency. Returns candle data formatted as CSV.
    Call this first before computing indicators.
    """
    try:
        ohlc = coingecko.get_ohlc(coin_id, vs_currency, days)
        df = coingecko.ohlc_to_dataframe(ohlc)
        return (
            f"OHLC data for {coin_id} ({days} days, {len(df)} candles):\n"
            f"Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}\n\n"
            f"{df.to_csv()}"
        )
    except Exception as e:
        return f"Error fetching price data for {coin_id}: {e}"


@tool
def get_crypto_indicators(
    coin_id: Annotated[str, "CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'solana')"],
    vs_currency: Annotated[str, "Quote currency (default: usd)"] = "usd",
    days: Annotated[int, "Number of days of data (1/7/14/30/91/181/365)"] = 30,
) -> str:
    """
    Compute technical indicators (RSI, MACD, Bollinger Bands, ATR, SMAs, EMAs)
    for a cryptocurrency. Returns a summary with current values and signals.
    """
    try:
        ohlc = coingecko.get_ohlc(coin_id, vs_currency, days)
        df = coingecko.ohlc_to_dataframe(ohlc)
        df = indicators.compute_all_indicators(df)
        summary = indicators.generate_indicator_summary(df)
        return f"Technical Indicators for {coin_id} ({days}d):\n\n{summary}"
    except Exception as e:
        return f"Error computing indicators for {coin_id}: {e}"


@tool
def get_crypto_market_data(
    coin_id: Annotated[str, "CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'solana')"],
) -> str:
    """
    Get comprehensive market data for a crypto: price, market cap, volume,
    supply, ATH/ATL, developer activity, community data, and description.
    """
    try:
        data = coingecko.get_coin_data(coin_id)
        md = data.get("market_data", {})

        lines = [
            f"## {data.get('name', coin_id)} ({data.get('symbol', '').upper()})",
            f"**Rank:** #{data.get('market_cap_rank', 'N/A')}",
            f"**Price:** ${md.get('current_price', {}).get('usd', 'N/A'):,}",
            f"**Market Cap:** ${md.get('market_cap', {}).get('usd', 'N/A'):,.0f}",
            f"**24h Volume:** ${md.get('total_volume', {}).get('usd', 'N/A'):,.0f}",
            f"**24h Change:** {md.get('price_change_percentage_24h', 'N/A'):.2f}%",
            f"**7d Change:** {md.get('price_change_percentage_7d', 'N/A'):.2f}%",
            f"**30d Change:** {md.get('price_change_percentage_30d', 'N/A'):.2f}%",
            f"**ATH:** ${md.get('ath', {}).get('usd', 'N/A'):,} ({md.get('ath_date', {}).get('usd', 'N/A')[:10]})",
            f"**ATL:** ${md.get('atl', {}).get('usd', 'N/A'):,} ({md.get('atl_date', {}).get('usd', 'N/A')[:10]})",
            "",
            "### Supply",
            f"Circulating: {md.get('circulating_supply', 'N/A'):,.0f}",
            f"Total: {md.get('total_supply', 'N/A'):,.0f}" if md.get('total_supply') else "Total: ∞",
            f"Max: {md.get('max_supply', 'N/A'):,.0f}" if md.get('max_supply') else "Max: ∞",
        ]

        # Developer data
        dd = data.get("developer_data", {})
        if dd:
            lines.extend([
                "",
                "### Developer Activity",
                f"GitHub Stars: {dd.get('stars', 'N/A')}",
                f"Forks: {dd.get('forks', 'N/A')}",
                f"Subscribers: {dd.get('subscribers', 'N/A')}",
                f"Commits (4 weeks): {dd.get('commit_count_4_weeks', 'N/A')}",
                f"PRs merged (4 weeks): {dd.get('pull_requests_merged', 'N/A')}",
            ])

        # Community data
        cd = data.get("community_data", {})
        if cd:
            lines.extend([
                "",
                "### Community",
                f"Twitter Followers: {cd.get('twitter_followers', 'N/A'):,}",
                f"Reddit Subscribers: {cd.get('reddit_subscribers', 'N/A'):,}",
                f"Reddit Active (48h): {cd.get('reddit_accounts_active_48h', 'N/A')}",
            ])

        # Description snippet
        desc = data.get("description", {}).get("en", "")
        if desc:
            snippet = desc[:500] + ("..." if len(desc) > 500 else "")
            lines.extend(["", f"### Description", snippet])

        return "\n".join(str(l) for l in lines)
    except Exception as e:
        return f"Error fetching market data for {coin_id}: {e}"


@tool
def get_crypto_fear_greed(
    days: Annotated[int, "Number of days of history (default: 30)"] = 30,
) -> str:
    """
    Get the Crypto Fear & Greed index. Shows market sentiment from 0 (extreme fear)
    to 100 (extreme greed). Useful for gauging overall market mood.
    """
    try:
        from crypto_trading_agents.dataflows.fear_greed import format_fear_greed
        data = fear_greed.get_fear_greed(limit=days)
        entries = data.get("data", [])

        if not entries:
            return "No Fear & Greed data available."

        current = entries[0]
        value = int(current["value"])

        lines = [
            f"**Current:** {format_fear_greed(value)}",
            "",
            f"**Last {len(entries)} days:**",
        ]

        for entry in entries[:10]:
            from datetime import datetime
            ts = datetime.fromtimestamp(int(entry["timestamp"]))
            lines.append(f"  {ts.strftime('%Y-%m-%d')}: {entry['value']} ({entry['value_classification']})")

        if len(entries) > 10:
            lines.append(f"  ... and {len(entries) - 10} more days")

        # Trend
        if len(entries) >= 7:
            week_ago = int(entries[-1]["value"])
            change = value - week_ago
            direction = "improving 📈" if change > 0 else "declining 📉" if change < 0 else "stable ➡️"
            lines.append(f"\n**7-day trend:** {direction} ({change:+d} points)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching Fear & Greed data: {e}"


@tool
def get_defi_tvl(
    protocol: Annotated[str, "Protocol slug from DeFiLlama (e.g., 'aave', 'lido', 'uniswap')"],
) -> str:
    """
    Get Total Value Locked (TVL) for a DeFi protocol.
    TVL is a key metric for protocol health and adoption.
    """
    try:
        from crypto_trading_agents.dataflows.defillama import format_tvl
        tvl = defillama.get_protocol_tvl(protocol)

        if isinstance(tvl, (int, float)):
            return f"**{protocol}** TVL: {format_tvl(tvl)}"
        return f"TVL data for {protocol}: {tvl}"
    except Exception as e:
        return f"Error fetching TVL for {protocol}: {e}"


@tool
def get_defi_protocol_info(
    protocol: Annotated[str, "Protocol slug from DeFiLlama (e.g., 'aave', 'lido', 'uniswap')"],
) -> str:
    """
    Get detailed DeFi protocol information: TVL history, chain breakdown,
    category, description, and links.
    """
    try:
        from crypto_trading_agents.dataflows.defillama import format_tvl
        data = defillama.get_protocol_data(protocol)

        lines = [
            f"## {data.get('name', protocol)}",
            f"**Category:** {data.get('category', 'N/A')}",
            f"**Chains:** {', '.join(data.get('chains', []))}",
            f"**Current TVL:** {format_tvl(data.get('tvl', 0))}",
        ]

        # Chain breakdown
        chain_tvls = data.get("chainTvls", {})
        if chain_tvls:
            lines.append("\n**TVL by Chain:**")
            for chain, tvl in sorted(chain_tvls.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)[:5]:
                if isinstance(tvl, (int, float)):
                    lines.append(f"  {chain}: {format_tvl(tvl)}")

        # Description
        desc = data.get("description", "")
        if desc:
            lines.extend(["", f"### Description", desc[:400] + ("..." if len(desc) > 400 else "")])

        return "\n".join(str(l) for l in lines)
    except Exception as e:
        return f"Error fetching protocol info for {protocol}: {e}"


@tool
def get_trending_coins() -> str:
    """
    Get currently trending cryptocurrencies on CoinGecko.
    Useful for spotting momentum and hype-driven opportunities.
    """
    try:
        data = coingecko.get_trending()
        coins = data.get("coins", [])

        lines = ["**Trending on CoinGecko (Top 15):**", ""]

        for i, entry in enumerate(coins[:15], 1):
            coin = entry.get("item", {})
            lines.append(
                f"{i}. **{coin.get('name', '?')}** ({coin.get('symbol', '?').upper()}) "
                f"— Rank #{coin.get('market_cap_rank', '?')}, "
                f"Score: {coin.get('score', '?')}"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching trending coins: {e}"


@tool
def get_global_crypto_market() -> str:
    """
    Get global crypto market overview: total market cap, 24h volume,
    BTC dominance, ETH dominance, and market cap change percentages.
    """
    try:
        data = coingecko.get_global_data()

        lines = [
            "## Global Crypto Market",
            f"**Total Market Cap:** ${data.get('total_market_cap', {}).get('usd', 0):,.0f}",
            f"**24h Volume:** ${data.get('total_volume', {}).get('usd', 0):,.0f}",
            f"**BTC Dominance:** {data.get('market_cap_percentage', {}).get('btc', 0):.1f}%",
            f"**ETH Dominance:** {data.get('market_cap_percentage', {}).get('eth', 0):.1f}%",
            f"**Active Cryptocurrencies:** {data.get('active_cryptocurrencies', 'N/A'):,}",
            f"**Markets:** {data.get('markets', 'N/A'):,}",
            "",
            f"**Market Cap Change (24h):** {data.get('market_cap_change_percentage_24h_usd', 0):.2f}%",
        ]

        return "\n".join(str(l) for l in lines)
    except Exception as e:
        return f"Error fetching global market data: {e}"


@tool
def get_top_coins_by_market_cap(
    limit: Annotated[int, "Number of top coins to return (default: 20)"] = 20,
) -> str:
    """
    Get top cryptocurrencies ranked by market cap.
    Shows price, market cap, volume, and 24h change.
    """
    try:
        coins = coingecko.get_top_coins(per_page=limit)

        lines = [f"**Top {limit} Cryptocurrencies by Market Cap:**", ""]
        lines.append(f"{'#':<4} {'Name':<20} {'Price':<15} {'MCap':<18} {'24h %':<10}")
        lines.append("-" * 75)

        for coin in coins:
            rank = coin.get("market_cap_rank", "?")
            name = coin.get("name", "?")[:18]
            symbol = coin.get("symbol", "?").upper()
            price = coin.get("current_price", 0)
            mcap = coin.get("market_cap", 0)
            change = coin.get("price_change_percentage_24h", 0)

            price_str = f"${price:,.2f}" if price < 1000 else f"${price:,.0f}"
            mcap_str = f"${mcap/1e9:.1f}B" if mcap else "N/A"
            change_str = f"{change:+.1f}%" if change else "N/A"

            lines.append(f"{rank:<4} {name} ({symbol}){'':<1} {price_str:<15} {mcap_str:<18} {change_str:<10}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching top coins: {e}"


@tool
def get_crypto_news(
    sources: Annotated[str, "Comma-separated source names: coindesk,cointelegraph,decrypt,theblock,bitcoinmagazine,cryptoslate (or 'all')"] = "all",
    limit_per_source: Annotated[int, "Max articles per source (default: 5)"] = 5,
    keyword: Annotated[str, "Optional keyword to filter articles"] = "",
) -> str:
    """
    Fetch latest crypto news from major RSS feeds (CoinDesk, CoinTelegraph, Decrypt, The Block, etc).
    Useful for sentiment and news analysis. Can filter by keyword.
    """
    try:
        from crypto_trading_agents.dataflows.rss_news import (
            fetch_crypto_news, format_news_report, search_news,
        )

        source_list = None if sources == "all" else [s.strip() for s in sources.split(",")]
        articles = fetch_crypto_news(sources=source_list, limit_per_source=limit_per_source)

        if keyword:
            articles = search_news(articles, keyword)
            if not articles:
                return f"No news articles found matching '{keyword}'."

        return format_news_report(articles)
    except Exception as e:
        return f"Error fetching crypto news: {e}"


@tool
def get_derivatives_data() -> str:
    """
    Get crypto derivatives market data: open interest, trading volumes,
    and exchange rankings. Useful for gauging leveraged market positioning.
    """
    try:
        from crypto_trading_agents.dataflows.derivatives import format_derivatives_report
        return format_derivatives_report()
    except Exception as e:
        return f"Error fetching derivatives data: {e}"


@tool
def cmc_get_quote(
    symbol: Annotated[str, "Coin symbol (e.g., BTC, ETH, SOL)"],
) -> str:
    """
    Get price quote and market data from CoinMarketCap for a specific coin.
    Includes price, market cap, volume, supply, and price changes (1h/24h/7d/30d).
    Better rate limits than CoinGecko — prefer this for quotes.
    """
    try:
        from crypto_trading_agents.dataflows.coinmarketcap import format_quote_report
        return format_quote_report(symbol.upper())
    except Exception as e:
        return f"Error fetching CMC quote for {symbol}: {e}"


@tool
def cmc_get_global() -> str:
    """
    Get global crypto market metrics from CoinMarketCap: total market cap,
    volume, BTC/ETH dominance, active cryptos and exchanges.
    """
    try:
        from crypto_trading_agents.dataflows.coinmarketcap import format_global_report
        return format_global_report()
    except Exception as e:
        return f"Error fetching CMC global data: {e}"


@tool
def cmc_get_top_coins(
    limit: Annotated[int, "Number of top coins (default: 20)"] = 20,
) -> str:
    """
    Get top cryptocurrencies by market cap from CoinMarketCap.
    Better rate limits than CoinGecko for listings.
    """
    try:
        from crypto_trading_agents.dataflows.coinmarketcap import format_listings_report
        return format_listings_report(limit)
    except Exception as e:
        return f"Error fetching CMC listings: {e}"


@tool
def cmc_get_coin_info(
    symbol: Annotated[str, "Coin symbol (e.g., BTC, ETH, SOL)"],
) -> str:
    """
    Get detailed coin metadata from CoinMarketCap: description, category,
    tags, website, explorer links, and technical details.
    """
    try:
        from crypto_trading_agents.dataflows.coinmarketcap import get_coin_info
        data = get_coin_info(symbol.upper())

        lines = [
            f"## {data.get('name', symbol)} ({data.get('symbol', symbol)})",
            f"**Category:** {data.get('category', 'N/A')}",
            f"**Slug:** {data.get('slug', 'N/A')}",
        ]

        desc = data.get("description", "")
        if desc:
            lines.extend(["", f"### Description", desc[:500] + ("..." if len(desc) > 500 else "")])

        urls = data.get("urls", {})
        if urls:
            lines.append("")
            for category, links in urls.items():
                if links:
                    lines.append(f"**{category.title()}:** {', '.join(links[:3])}")

        tags = data.get("tags", [])
        if tags:
            lines.append(f"\n**Tags:** {', '.join(tags[:10])}")

        return "\n".join(str(l) for l in lines)
    except Exception as e:
        return f"Error fetching CMC info for {symbol}: {e}"


@tool
def cmc_get_fear_greed() -> str:
    """
    Get Crypto Fear & Greed Index from CoinMarketCap.
    Value from 0 (extreme fear) to 100 (extreme greed).
    """
    try:
        from crypto_trading_agents.dataflows.coinmarketcap import get_fear_and_greed
        data = get_fear_and_greed()
        value = data.get("value", 0)
        classification = data.get("value_classification", "Unknown")

        from crypto_trading_agents.dataflows.fear_greed import format_fear_greed
        return f"**CoinMarketCap Fear & Greed:** {format_fear_greed(int(value))}"
    except Exception as e:
        return f"Error fetching CMC Fear & Greed: {e}"
