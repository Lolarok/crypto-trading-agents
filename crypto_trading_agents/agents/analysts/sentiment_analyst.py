"""
Sentiment Analyst — Market sentiment using Fear & Greed Index, trending data, and global market context.

Uses tools: get_crypto_fear_greed, get_trending_coins, get_global_crypto_market, get_top_coins_by_market_cap
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_sentiment_analyst(llm):
    from crypto_trading_agents.dataflows.tools import (
        get_crypto_fear_greed,
        get_trending_coins,
        get_global_crypto_market,
        get_top_coins_by_market_cap,
        get_derivatives_data,
        cmc_get_global,
        cmc_get_fear_greed,
    )

    tools = [get_crypto_fear_greed, get_trending_coins, get_global_crypto_market, get_top_coins_by_market_cap, get_derivatives_data, cmc_get_global, cmc_get_fear_greed]

    system_message = (
        "You are a crypto sentiment analyst. Your job is to gauge market mood "
        "and identify sentiment-driven opportunities or risks.\n\n"

        "## Your Process\n"
        "1. Call `get_crypto_fear_greed` and `cmc_get_fear_greed` to get Fear & Greed index data.\n"
        "2. Call `get_global_crypto_market` and `cmc_get_global` for total market cap, BTC dominance, and 24h change.\n"
        "3. Call `get_trending_coins` to see what the crowd is watching.\n"
        "4. Call `get_top_coins_by_market_cap` for broad market context.\n"
        "5. Call `get_derivatives_data` for open interest and leverage positioning.\n"
        "6. Synthesize a report covering:\n"
        "   - **Overall Sentiment:** Fear/Greed level and what it implies\n"
        "   - **Market Context:** BTC dominance trend, total market cap direction\n"
        "   - **Crowd Behavior:** What's trending and why — hype vs fundamentals\n"
        "   - **Contrarian Signals:** Extreme fear = potential buying opportunity, "
        "extreme greed = potential top\n"
        "   - **Specific Crypto Context:** How does sentiment relate to our target coin?\n\n"

        "## Sentiment Interpretation Guide\n"
        "- Fear & Greed 0-25 (Extreme Fear): Historically good buying zones, but watch for falling knives\n"
        "- 25-45 (Fear): Cautious optimism warranted\n"
        "- 45-55 (Neutral): Wait for clearer signals\n"
        "- 55-75 (Greed): Healthy trend but start watching for exits\n"
        "- 75-100 (Extreme Greed): Consider taking profits, reduce risk\n\n"

        "- Rising BTC dominance = risk-off (money flowing to BTC from alts)\n"
        "- Falling BTC dominance = risk-on (money flowing to altcoins)\n\n"

        "End with a clear sentiment assessment: BULLISH, BEARISH, or NEUTRAL sentiment with reasoning."
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful AI assistant collaborating with other assistants."
            " Use the provided tools to progress towards answering the question."
            " If you are unable to fully answer, that's OK; another assistant with different tools"
            " will help where you left off. Execute what you can to make progress."
            " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**"
            " or deliverable, prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**"
            " so the team knows to stop."
            " You have access to the following tools: {tool_names}.\n{system_message}"
            "For your reference, the current date is {current_date}. "
            "The crypto to analyze is: {crypto_name} (CoinGecko ID: {coin_id}).",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])

    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([t.name for t in tools]))

    def sentiment_analyst_node(state):
        prompt_partial = prompt.partial(
            current_date=state["trade_date"],
            crypto_name=state["crypto_of_interest"],
            coin_id=state["coin_id"],
        )
        chain = prompt_partial | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {"messages": [result], "sentiment_report": report}

    return sentiment_analyst_node
