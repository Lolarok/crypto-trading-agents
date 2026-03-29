"""Conditional logic for graph routing decisions."""

from crypto_trading_agents.agents.utils.agent_states import AgentState


class ConditionalLogic:
    """Controls routing decisions in the agent graph."""

    def __init__(self, max_debate_rounds: int = 2, max_risk_discuss_rounds: int = 2):
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_market(self, state: AgentState) -> str:
        """Route market analyst: continue with tools or move on."""
        if state["messages"][-1].tool_calls:
            return "tools_market"
        return "Msg Clear Market"

    def should_continue_sentiment(self, state: AgentState) -> str:
        if state["messages"][-1].tool_calls:
            return "tools_sentiment"
        return "Msg Clear Sentiment"

    def should_continue_fundamentals(self, state: AgentState) -> str:
        if state["messages"][-1].tool_calls:
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"

    def should_continue_onchain(self, state: AgentState) -> str:
        if state["messages"][-1].tool_calls:
            return "tools_onchain"
        return "Msg Clear Onchain"

    def should_continue_debate(self, state: AgentState) -> str:
        """Continue bull/bear debate or move to research manager."""
        count = state["investment_debate_state"].get("count", 0)
        if count >= self.max_debate_rounds * 2:  # Each side gets max_debate_rounds
            return "Research Manager"
        # Alternate between bull and bear
        last_history = state["investment_debate_state"].get("history", "")
        if last_history.count("Bull") <= last_history.count("Bear"):
            return "Bull Researcher"
        return "Bear Researcher"

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Continue risk debate or move to portfolio manager."""
        count = state["risk_debate_state"].get("count", 0)
        if count >= self.max_risk_discuss_rounds * 3:  # 3 analysts × rounds
            return "Portfolio Manager"

        latest_speaker = state["risk_debate_state"].get("latest_speaker", "")
        if latest_speaker == "aggressive":
            return "Conservative Analyst"
        elif latest_speaker == "conservative":
            return "Neutral Analyst"
        else:
            return "Aggressive Analyst"
