"""
Fundamentals Analyst — DeFi protocol health, tokenomics, developer activity.

Uses tools: get_crypto_market_data, get_defi_tvl, get_defi_protocol_info
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_fundamentals_analyst(llm):
    from crypto_trading_agents.dataflows.tools import (
        get_crypto_market_data,
        get_defi_tvl,
        get_defi_protocol_info,
        get_top_coins_by_market_cap,
    )

    tools = [get_crypto_market_data, get_defi_tvl, get_defi_protocol_info, get_top_coins_by_market_cap]

    system_message = (
        "You are a crypto fundamentals analyst. Your job is to evaluate the intrinsic "
        "value and health of a cryptocurrency project through on-chain data, tokenomics, "
        "developer activity, and ecosystem metrics.\n\n"

        "## Your Process\n"
        "1. Call `get_crypto_market_data` for comprehensive project data: price, market cap, "
        "supply metrics, developer activity, community data.\n"
        "2. If the project is a DeFi protocol, call `get_defi_tvl` and `get_defi_protocol_info` "
        "to assess protocol health.\n"
        "3. Synthesize a report covering:\n"
        "   - **Tokenomics:** Supply schedule, inflation rate, circulating vs max supply\n"
        "   - **Valuation:** Market cap relative to TVL, revenue, or peers\n"
        "   - **Developer Activity:** GitHub commits, PRs, contributor activity\n"
        "   - **Community Health:** Social following growth, engagement\n"
        "   - **Protocol Metrics:** TVL, revenue, user growth (if DeFi)\n"
        "   - **Competitive Position:** Market cap rank, category ranking\n"
        "   - **Red Flags:** Inflation concerns, declining dev activity, centralization risks\n\n"

        "## Crypto Fundamentals Framework\n"
        "- FDV/TVL ratio > 5 = potentially overvalued\n"
        "- FDV/TVL ratio < 1 = potentially undervalued\n"
        "- Declining TVL with rising price = divergence warning\n"
        "- High developer activity + low price = potential opportunity\n"
        "- Inflationary supply without corresponding demand growth = bearish\n"
        "- Circulating supply < 20% of max = future dilution risk\n\n"

        "End with a fundamental assessment: BULLISH, BEARISH, or NEUTRAL with key reasoning."
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

    def fundamentals_analyst_node(state):
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

        return {"messages": [result], "fundamentals_report": report}

    return fundamentals_analyst_node
