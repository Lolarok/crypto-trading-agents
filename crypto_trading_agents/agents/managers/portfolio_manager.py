"""Portfolio Manager — final decision maker after risk debate."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_portfolio_manager(llm, memory):
    system_message = (
        "You are the Portfolio Manager of a crypto trading desk. The risk management team "
        "(Aggressive, Conservative, and Neutral analysts) has debated the trader's plan. "
        "You make the FINAL decision.\n\n"

        "## Your Process\n"
        "1. Review the trader's investment plan\n"
        "2. Review the full risk debate from all three perspectives\n"
        "3. Reference past portfolio decisions and their outcomes\n"
        "4. Make a final decision with:\n"
        "   - **Decision:** BUY / SELL / HOLD — with FINAL TRANSACTION PROPOSAL prefix\n"
        "   - **Confidence:** 1-10\n"
        "   - **Position Size:** Percentage of portfolio\n"
        "   - **Risk Management:** Stop loss, take profit levels\n"
        "   - **Conditions to Re-evaluate:** What would trigger a reassessment\n"
        "   - **Portfolio Context:** How this fits with overall crypto exposure\n\n"

        "## Crypto Portfolio Rules\n"
        "- Never risk more than 2% of portfolio on a single trade\n"
        "- Maintain minimum 20% stablecoin reserve in bear markets\n"
        "- Correlation risk: don't stack similar bets (e.g., all L1s or all DeFi)\n"
        "- Account for gas costs and tax implications\n"
        "- Weekend trades need wider stops (lower liquidity)\n\n"

        "Your word is final. Be decisive and clear. "
        "Prefix your final decision with: FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**"
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

    def portfolio_manager_node(state):
        memories = memory.get_memories(state.get("crypto_of_interest", ""))

        risk_state = state["risk_debate_state"]
        context = (
            f"## Trader's Plan\n{state.get('trader_investment_plan', 'N/A')}\n\n"
            f"## Risk Debate ({risk_state.get('count', 0)} rounds)\n"
            f"### Aggressive\n{risk_state.get('aggressive_history', 'N/A')[-500:]}\n\n"
            f"### Conservative\n{risk_state.get('conservative_history', 'N/A')[-500:]}\n\n"
            f"### Neutral\n{risk_state.get('neutral_history', 'N/A')[-500:]}"
        )

        messages = state["messages"] + [
            ("human", f"{context}\n\n{memories}\n\n"
             "Make your final portfolio decision.")
        ]

        prompt_partial = prompt.partial(memories=memories)
        chain = prompt_partial | llm
        result = chain.invoke(messages)

        return {
            "messages": [result],
            "final_trade_decision": result.content,
        }

    return portfolio_manager_node
