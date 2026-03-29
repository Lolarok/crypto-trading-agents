"""Bear Researcher — argues AGAINST investing in the target crypto."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_bear_researcher(llm, memory):
    system_message = (
        "You are a bearish crypto researcher. Your role is to make the strongest possible "
        "case AGAINST investing in the target cryptocurrency. You are skeptical and focus on "
        "risks, overvaluation, and downside potential.\n\n"

        "## Your Approach\n"
        "- Synthesize the analyst reports and find weaknesses\n"
        "- Build a compelling bear case with specific evidence\n"
        "- Counter bull arguments point by point — don't dismiss them, but poke holes\n"
        "- Focus on: overvaluation, declining metrics, competitive threats, "
        "regulatory risks, technical breakdowns, bubble signals\n"
        "- Use past memories to reference similar situations that ended in losses\n\n"

        "## Crypto Bear Arguments\n"
        "- Token inflation and upcoming unlock schedules\n"
        "- Declining TVL or user activity\n"
        "- Concentrated ownership / whale dumps\n"
        "- Regulatory crackdown risk\n"
        "- Competitive displacement by newer protocols\n"
        "- Market cycle exhaustion signals\n"
        "- Over-leveraged market (funding rates, liquidation cascades)\n"
        "- Narrative exhaustion — priced-in catalysts\n"
        "- Low real revenue vs valuation (high P/E equivalent)\n\n"

        "Be cautious but evidence-based. Make the bear case that demands a response."
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
            " {system_message}"
            "Here are relevant past memories for context:\n{memories}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])
    prompt = prompt.partial(system_message=system_message)

    def bear_researcher_node(state):
        memories = memory.get_memories(state.get("crypto_of_interest", ""))

        analysis = []
        if state.get("market_report"):
            analysis.append(f"## Market Analyst Report\n{state['market_report']}")
        if state.get("sentiment_report"):
            analysis.append(f"## Sentiment Analyst Report\n{state['sentiment_report']}")
        if state.get("fundamentals_report"):
            analysis.append(f"## Fundamentals Analyst Report\n{state['fundamentals_report']}")
        if state.get("onchain_report"):
            analysis.append(f"## On-Chain Analyst Report\n{state['onchain_report']}")

        analysis_text = "\n\n".join(analysis) if analysis else "No analyst reports available."

        debate_context = ""
        if state["investment_debate_state"].get("bull_history"):
            debate_context = (
                f"\n\nThe Bull Researcher's latest argument to counter:\n"
                f"{state['investment_debate_state']['bull_history']}"
            )

        messages = state["messages"] + [
            ("human", f"Here are the analyst reports:\n\n{analysis_text}{debate_context}\n\n"
             f"{memories}\n\nMake your bear case.")
        ]

        prompt_partial = prompt.partial(memories=memories)
        chain = prompt_partial | llm
        result = chain.invoke(messages)

        new_invest_debate_state = {
            **state["investment_debate_state"],
            "bear_history": state["investment_debate_state"].get("bear_history", "") + "\n" + result.content,
            "history": state["investment_debate_state"].get("history", "") + "\n" + result.content,
            "current_response": result.content,
            "count": state["investment_debate_state"].get("count", 0) + 1,
        }

        return {
            "messages": [result],
            "investment_debate_state": new_invest_debate_state,
        }

    return bear_researcher_node
