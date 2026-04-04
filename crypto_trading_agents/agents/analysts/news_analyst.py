"""
News Analyst — Crypto news from RSS feeds (CoinDesk, CoinTelegraph, Decrypt, The Block).

Uses tools: get_crypto_news
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_news_analyst(llm):
    from crypto_trading_agents.dataflows.tools import get_crypto_news

    tools = [get_crypto_news]

    system_message = (
        "You are a crypto news analyst. You monitor major crypto news outlets "
        "and identify news events that could impact the target cryptocurrency.\n\n"

        "## Your Process\n"
        "1. Call `get_crypto_news` to fetch the latest headlines from all sources.\n"
        "2. Optionally call it again with a keyword filter for the specific crypto.\n"
        "3. Synthesize a report covering:\n"
        "   - **Major Headlines:** Top 5-10 most impactful stories\n"
        "   - **Regulatory News:** SEC, CFTC, EU MiCA, or country-specific regulations\n"
        "   - **Protocol Updates:** Upgrades, partnerships, launches for the target crypto\n"
        "   - **Market Events:** Exchange issues, hacks, major fund flows, ETF news\n"
        "   - **Macro Context:** Fed policy, inflation data, geopolitical events affecting crypto\n"
        "   - **Sentiment Reading:** Is the news overall positive, negative, or mixed?\n\n"

        "## News Impact Framework\n"
        "- Regulatory crackdown → Short-term bearish, long-term bullish (clarity)\n"
        "- Major partnership/adoption → Bullish\n"
        "- Exchange hack/exploit → Bearish for ecosystem, specific to affected protocol\n"
        "- ETF inflows/outflows → Direct impact on BTC/ETH price\n"
        "- Protocol upgrade → Bullish if smooth, bearish if contentious/hard fork\n"
        "- Whale movements → Context-dependent (accumulation vs distribution)\n\n"

        "Focus on actionable news, not filler content. Distinguish signal from noise. "
        "End with an overall news sentiment: BULLISH, BEARISH, or NEUTRAL."
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
            "The crypto to analyze is: {crypto_name} (CoinGecko ID: {coin_id}). "
            "Use the keyword '{coin_id}' to filter news for this specific crypto.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])

    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([t.name for t in tools]))

    def news_analyst_node(state):
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

        return {"messages": [result], "news_report": report}

    return news_analyst_node
