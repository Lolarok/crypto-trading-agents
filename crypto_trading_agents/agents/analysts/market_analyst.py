"""
Market Analyst — Technical analysis using CoinGecko OHLCV data and indicators.

Uses tools: get_crypto_price, get_crypto_indicators
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_market_analyst(llm):
    from crypto_trading_agents.dataflows.tools import get_crypto_price, get_crypto_indicators

    tools = [get_crypto_price, get_crypto_indicators]

    system_message = (
        "You are a crypto market analyst specializing in technical analysis. "
        "Your job is to analyze price action and technical indicators to identify trends, "
        "support/resistance levels, and potential trade signals.\n\n"

        "## Your Process\n"
        "1. First call `get_crypto_price` to get OHLC candle data (use 30 days for short-term, "
        "91 days for medium-term context).\n"
        "2. Then call `get_crypto_indicators` to get RSI, MACD, Bollinger Bands, ATR, SMAs.\n"
        "3. Synthesize a detailed report with:\n"
        "   - **Trend Analysis:** Direction, strength, key moving average positions\n"
        "   - **Momentum:** RSI levels, MACD crossovers and divergences\n"
        "   - **Volatility:** Bollinger Band position, ATR levels, squeeze/expansion\n"
        "   - **Key Levels:** Support/resistance from MAs and BBands\n"
        "   - **Volume Context:** Any volume-price divergences\n"
        "   - **Short-term Outlook:** Expected direction and confidence level\n\n"

        "## Crypto-Specific Considerations\n"
        "- Crypto markets trend harder than stocks — don't fight strong trends\n"
        "- RSI can stay overbought/oversold longer in crypto bull/bear markets\n"
        "- Watch for BTC correlation — altcoins often follow BTC's direction\n"
        "- Weekend/volatility patterns differ from TradFi\n"
        "- Pay attention to funding rates sentiment (if available from other analysts)\n\n"

        "Provide specific price levels, indicator values, and actionable insights. "
        "End with a clear directional bias: BULLISH, BEARISH, or NEUTRAL with confidence level."
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
            "Use the coin_id '{coin_id}' for all tool calls.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])

    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([t.name for t in tools]))

    def market_analyst_node(state):
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

        return {"messages": [result], "market_report": report}

    return market_analyst_node
