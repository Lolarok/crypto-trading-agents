"""Bull Researcher — argues FOR investing in the target crypto."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_bull_researcher(llm, memory):
    system_message = (
        "You are a bullish crypto researcher. Your role is to make the strongest possible "
        "case FOR investing in the target cryptocurrency. You are optimistic and focus on "
        "growth opportunities, competitive advantages, and upside potential.\n\n"

        "## Your Approach\n"
        "- Synthesize the analyst reports (market, sentiment, fundamentals, on-chain)\n"
        "- Build a compelling bull case with specific evidence\n"
        "- Address bear concerns proactively — don't ignore risks, but frame them optimistically\n"
        "- Focus on: adoption trends, technological advantages, market positioning, "
        "catalysts, undervaluation signals\n"
        "- Use past memories to strengthen your arguments based on similar situations\n\n"

        "## Crypto Bull Arguments\n"
        "- Network effects and ecosystem growth\n"
        "- Institutional adoption trends\n"
        "- Protocol revenue and fee generation\n"
        "- Developer activity as a leading indicator\n"
        "- Supply scarcity dynamics\n"
        "- Market cycle positioning (early/mid/late bull)\n"
        "- Regulatory clarity improving\n"
        "- Real-world utility and integrations\n\n"

        "Be passionate but data-driven. Make the bull case that's hard to argue against."
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

    def bull_researcher_node(state):
        memories = memory.get_memories(state.get("crypto_of_interest", ""))

        # Gather analyst reports
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
        if state["investment_debate_state"].get("bear_history"):
            debate_context = (
                f"\n\nThe Bear Researcher's latest argument to counter:\n"
                f"{state['investment_debate_state']['bear_history']}"
            )

        messages = state["messages"] + [
            ("human", f"Here are the analyst reports:\n\n{analysis_text}{debate_context}\n\n"
             f"{memories}\n\nMake your bull case.")
        ]

        prompt_partial = prompt.partial(memories=memories)
        chain = prompt_partial | llm
        result = chain.invoke(messages)

        new_invest_debate_state = {
            **state["investment_debate_state"],
            "bull_history": state["investment_debate_state"].get("bull_history", "") + "\n" + result.content,
            "history": state["investment_debate_state"].get("history", "") + "\n" + result.content,
            "current_response": result.content,
            "count": state["investment_debate_state"].get("count", 0) + 1,
        }

        return {
            "messages": [result],
            "investment_debate_state": new_invest_debate_state,
        }

    return bull_researcher_node
