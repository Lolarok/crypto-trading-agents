"""Conservative Risk Debator — risk-averse, advocates for caution."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_conservative_debator(llm):
    system_message = (
        "You are the Conservative Risk Analyst. You have a low risk tolerance and prioritize "
        "capital preservation over aggressive gains.\n\n"

        "## Your Stance\n"
        "- Capital preservation is the #1 rule — you can't compound if you're blown out\n"
        "- Favor smaller position sizes and wider stops\n"
        "- Focus on: downside scenarios, tail risks, black swan events\n"
        "- Argue that crypto volatility can destroy portfolios quickly\n"
        "- Point out survivorship bias in crypto success stories\n"
        "- Advocate for: partial positions, scaling in, hedging, stablecoin reserves\n"
        "- Cite: exchange hacks, regulatory surprises, stablecoin depegs, rug pulls\n\n"

        "You respond to the Aggressive and Neutral analysts. Counter their enthusiasm "
        "with risk-first reasoning."
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful AI assistant collaborating in a risk management debate."
            " {system_message}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    prompt = prompt.partial(system_message=system_message)

    def conservative_debator_node(state):
        trader_plan = state.get("trader_investment_plan", "No trader plan available.")

        risk_state = state["risk_debate_state"]
        context = f"## Trader's Plan\n{trader_plan}\n\n"

        if risk_state.get("aggressive_history"):
            context += f"## Aggressive Analyst says:\n{risk_state['aggressive_history'][-500:]}\n\n"
        if risk_state.get("neutral_history"):
            context += f"## Neutral Analyst says:\n{risk_state['neutral_history'][-500:]}\n\n"

        messages = state["messages"] + [
            ("human", f"{context}Make your conservative risk argument.")
        ]

        chain = prompt | llm
        result = chain.invoke(messages)

        new_risk_state = {
            **risk_state,
            "conservative_history": risk_state.get("conservative_history", "") + "\n" + result.content,
            "history": risk_state.get("history", "") + "\n" + result.content,
            "current_conservative_response": result.content,
            "latest_speaker": "conservative",
            "count": risk_state.get("count", 0) + 1,
        }

        return {
            "messages": [result],
            "risk_debate_state": new_risk_state,
        }

    return conservative_debator_node
