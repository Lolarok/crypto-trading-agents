"""Neutral Risk Debator — balanced view, risk-adjusted perspective."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_neutral_debator(llm):
    system_message = (
        "You are the Neutral Risk Analyst. You take a balanced, risk-adjusted approach "
        "to evaluating trading decisions.\n\n"

        "## Your Stance\n"
        "- Weigh risk and reward objectively — neither reckless nor paralyzed\n"
        "- Focus on: risk/reward ratios, position sizing math, probability-weighted outcomes\n"
        "- Find the middle ground between Aggressive and Conservative views\n"
        "- Advocate for: Kelly criterion-style sizing, diversified approaches\n"
        "- Point out when either extreme is irrational\n"
        "- Consider: market regime, volatility state, correlation risks\n"
        "- Suggest: if both sides have merit, reduce size rather than abandon the trade\n\n"

        "You mediate between the Aggressive and Conservative analysts. Your role is to "
        "bring rational balance to the debate."
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

    def neutral_debator_node(state):
        trader_plan = state.get("trader_investment_plan", "No trader plan available.")

        risk_state = state["risk_debate_state"]
        context = f"## Trader's Plan\n{trader_plan}\n\n"

        if risk_state.get("aggressive_history"):
            context += f"## Aggressive Analyst says:\n{risk_state['aggressive_history'][-500:]}\n\n"
        if risk_state.get("conservative_history"):
            context += f"## Conservative Analyst says:\n{risk_state['conservative_history'][-500:]}\n\n"

        messages = state["messages"] + [
            ("human", f"{context}Provide your balanced risk assessment.")
        ]

        chain = prompt | llm
        result = chain.invoke(messages)

        new_risk_state = {
            **risk_state,
            "neutral_history": risk_state.get("neutral_history", "") + "\n" + result.content,
            "history": risk_state.get("history", "") + "\n" + result.content,
            "current_neutral_response": result.content,
            "latest_speaker": "neutral",
            "count": risk_state.get("count", 0) + 1,
        }

        return {
            "messages": [result],
            "risk_debate_state": new_risk_state,
        }

    return neutral_debator_node
