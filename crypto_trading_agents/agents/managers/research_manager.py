"""Research Manager — judges the Bull/Bear debate and creates an investment plan."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_research_manager(llm, memory):
    system_message = (
        "You are the Research Manager of a crypto trading desk. You've been listening to "
        "the Bull and Bear researchers debate. Your job is to synthesize both sides into "
        "a clear investment plan.\n\n"

        "## Your Process\n"
        "1. Review the full debate history between Bull and Bear researchers\n"
        "2. Weigh the evidence from both sides objectively\n"
        "3. Reference past memories for context on similar situations\n"
        "4. Create a structured investment plan with:\n"
        "   - **Verdict:** BULLISH, BEARISH, or NEUTRAL\n"
        "   - **Confidence Level:** Low / Medium / High\n"
        "   - **Key Bull Arguments:** Top 3 strongest points\n"
        "   - **Key Bear Arguments:** Top 3 strongest concerns\n"
        "   - **Decision Rationale:** Why you lean one way\n"
        "   - **Suggested Action:** BUY / SELL / HOLD with size recommendation\n"
        "   - **Key Risks:** What could invalidate this thesis\n"
        "   - **Timeline:** Short-term (1-7d) / Medium-term (1-4w) / Long-term (1-6m)\n\n"

        "Be decisive. Your plan will be handed to the Trader, who needs clear direction."
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

    def research_manager_node(state):
        memories = memory.get_memories(state.get("crypto_of_interest", ""))

        debate = state["investment_debate_state"]
        debate_history = (
            f"## Bull Arguments\n{debate.get('bull_history', 'None')}\n\n"
            f"## Bear Arguments\n{debate.get('bear_history', 'None')}\n\n"
            f"## Debate Count: {debate.get('count', 0)} rounds"
        )

        messages = state["messages"] + [
            ("human", f"Here is the full debate:\n\n{debate_history}\n\n"
             f"{memories}\n\nJudge the debate and create your investment plan.")
        ]

        prompt_partial = prompt.partial(memories=memories)
        chain = prompt_partial | llm
        result = chain.invoke(messages)

        return {
            "messages": [result],
            "investment_plan": result.content,
        }

    return research_manager_node
