"""Trader Agent — synthesizes the investment plan into a concrete trading decision."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_trader(llm, memory):
    system_message = (
        "You are a crypto trader on a quantitative trading desk. The Research Manager "
        "has handed you an investment plan. Your job is to translate it into a concrete "
        "trading decision with specific parameters.\n\n"

        "## Your Process\n"
        "1. Review the investment plan from the Research Manager\n"
        "2. Consider current market conditions from the analyst reports\n"
        "3. Reference past trading memories for similar setups\n"
        "4. Produce a trading decision:\n"
        "   - **Action:** BUY / SELL / HOLD\n"
        "   - **Conviction:** Low / Medium / High\n"
        "   - **Position Size:** Conservative / Moderate / Aggressive (% of portfolio)\n"
        "   - **Entry Strategy:** Market / Limit at specific levels\n"
        "   - **Stop Loss:** Price level or percentage\n"
        "   - **Take Profit Targets:** Multiple TP levels if applicable\n"
        "   - **Timeframe:** Expected holding period\n"
        "   - **Key Trigger:** What would change your mind\n\n"

        "## Crypto Trading Rules\n"
        "- Never go all-in — max 25% position size even at highest conviction\n"
        "- Always define a stop loss before entry\n"
        "- Consider gas fees and slippage for smaller caps\n"
        "- Account for market hours — crypto is 24/7 but volume varies\n"
        "- Size inversely proportional to volatility\n"
        "- In extreme fear: consider scaling in\n"
        "- In extreme greed: consider scaling out\n\n"

        "Prefix your final decision with: "
        "FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**"
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful AI assistant, collaborating with other assistants."
            " {system_message}"
            "Here are relevant past memories:\n{memories}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    prompt = prompt.partial(system_message=system_message)

    def trader_node(state):
        memories = memory.get_memories(state.get("crypto_of_interest", ""))

        context = []
        if state.get("investment_plan"):
            context.append(f"## Investment Plan\n{state['investment_plan']}")
        if state.get("market_report"):
            context.append(f"## Market Conditions\n{state['market_report'][:500]}")

        context_text = "\n\n".join(context)

        messages = state["messages"] + [
            ("human", f"{context_text}\n\n{memories}\n\n"
             "Based on the investment plan and current conditions, what is your trading decision?")
        ]

        prompt_partial = prompt.partial(memories=memories)
        chain = prompt_partial | llm
        result = chain.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
        }

    return trader_node
