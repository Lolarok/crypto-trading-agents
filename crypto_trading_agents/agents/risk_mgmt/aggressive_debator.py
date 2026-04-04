"""Aggressive Risk Debator — high risk tolerance, advocates for action."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_aggressive_debator(llm):
    system_message = (
        "You are the Aggressive Risk Analyst. You have a high risk tolerance and believe "
        "in taking decisive action when opportunities present themselves.\n\n"

        "## Your Stance\n"
        "- Favor action over inaction — sitting on the sidelines has opportunity cost\n"
        "- Accept higher volatility for higher potential returns\n"
        "- Focus on: momentum, trend strength, asymmetric risk/reward setups\n"
        "- Argue that conservative approaches miss the biggest moves in crypto\n"
        "- Point out that crypto's best days often follow its worst days\n"
        "- Advocate for: larger positions, tighter stops, earlier entries\n\n"

        "You respond to the Conservative and Neutral analysts. Counter their caution "
        "with evidence of why the opportunity outweighs the risk."
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

    def aggressive_debator_node(state):
        trader_plan = state.get("trader_investment_plan", "No trader plan available.")

        risk_state = state["risk_debate_state"]
        context = f"## Trader's Plan\n{trader_plan}\n\n"

        if risk_state.get("conservative_history"):
            context += f"## Conservative Analyst says:\n{risk_state['conservative_history'][-500:]}\n\n"
        if risk_state.get("neutral_history"):
            context += f"## Neutral Analyst says:\n{risk_state['neutral_history'][-500:]}\n\n"

        messages = state["messages"] + [
            ("human", f"{context}Make your aggressive risk argument.")
        ]

        chain = prompt | llm
        result = chain.invoke(messages)

        new_risk_state = {
            **risk_state,
            "aggressive_history": risk_state.get("aggressive_history", "") + "\n" + result.content,
            "history": risk_state.get("history", "") + "\n" + result.content,
            "current_aggressive_response": result.content,
            "latest_speaker": "aggressive",
            "count": risk_state.get("count", 0) + 1,
        }

        return {
            "messages": [result],
            "risk_debate_state": new_risk_state,
        }

    return aggressive_debator_node
