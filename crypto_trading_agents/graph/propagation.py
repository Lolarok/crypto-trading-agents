"""State initialization and graph invocation helpers."""

from typing import Dict, Any, List, Optional
from crypto_trading_agents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit: int = 100):
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, crypto_name: str, coin_id: str, trade_date: str
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph."""
        return {
            "messages": [("human", f"Analyze {crypto_name} ({coin_id}) for {trade_date}")],
            "crypto_of_interest": crypto_name,
            "coin_id": coin_id,
            "trade_date": str(trade_date),
            "investment_debate_state": InvestDebateState(
                bull_history="",
                bear_history="",
                history="",
                current_response="",
                judge_decision="",
                count=0,
            ),
            "risk_debate_state": RiskDebateState(
                aggressive_history="",
                conservative_history="",
                neutral_history="",
                history="",
                latest_speaker="",
                current_aggressive_response="",
                current_conservative_response="",
                current_neutral_response="",
                judge_decision="",
                count=0,
            ),
            "market_report": "",
            "sentiment_report": "",
            "news_report": "",
            "fundamentals_report": "",
            "onchain_report": "",
        }

    def get_graph_args(self) -> Dict[str, Any]:
        """Get arguments for the graph invocation."""
        return {
            "stream_mode": "values",
            "config": {"recursion_limit": self.max_recur_limit},
        }
