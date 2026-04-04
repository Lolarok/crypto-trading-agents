"""
CryptoTradingAgentsGraph — Main orchestrator for the crypto multi-agent trading framework.

Adapted from TradingAgents (TauricResearch) for crypto markets.
Key differences from the original:
  - CoinGecko + DeFiLlama data sources (free, no API keys)
  - On-Chain Analyst (new role)
  - Sentiment Analyst replaces Social Media Analyst (Fear & Greed + trending)
  - Crypto-specific prompts, rules, and risk management
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from langgraph.prebuilt import ToolNode

from crypto_trading_agents.llm_clients import create_llm
from crypto_trading_agents.default_config import DEFAULT_CONFIG
from crypto_trading_agents.agents.utils.memory import CryptoSituationMemory
from crypto_trading_agents.agents.utils.agent_states import AgentState
from crypto_trading_agents.agents.utils.agent_utils import create_msg_delete
from crypto_trading_agents.dataflows.tools import (
    get_crypto_price,
    get_crypto_indicators,
    get_crypto_market_data,
    get_crypto_fear_greed,
    get_defi_tvl,
    get_defi_protocol_info,
    get_trending_coins,
    get_global_crypto_market,
    get_top_coins_by_market_cap,
    get_crypto_news,
    get_derivatives_data,
    cmc_get_quote,
    cmc_get_global,
    cmc_get_top_coins,
    cmc_get_coin_info,
    cmc_get_fear_greed,
)

from crypto_trading_agents.agents import (
    create_market_analyst,
    create_sentiment_analyst,
    create_news_analyst,
    create_fundamentals_analyst,
    create_onchain_analyst,
    create_bull_researcher,
    create_bear_researcher,
    create_research_manager,
    create_trader,
    create_aggressive_debator,
    create_conservative_debator,
    create_neutral_debator,
    create_portfolio_manager,
)

from crypto_trading_agents.graph.conditional_logic import ConditionalLogic
from crypto_trading_agents.graph.propagation import Propagator
from crypto_trading_agents.graph.signal_processing import SignalProcessor

from langgraph.graph import END, StateGraph, START


class CryptoTradingAgentsGraph:
    """
    Main class that orchestrates the crypto trading agents framework.
    
    Flow: Analysts → Bull/Bear Debate → Research Manager → Trader → Risk Debate → Portfolio Manager
    
    Crypto-specific analysts:
      - Market: technical analysis (OHLCV, indicators)
      - Sentiment: Fear & Greed, trending, global market mood
      - Fundamentals: DeFi TVL, tokenomics, developer activity
      - On-Chain: supply dynamics, market structure, relative strength
    """

    def __init__(
        self,
        selected_analysts: List[str] = None,
        debug: bool = False,
        config: Dict[str, Any] = None,
    ):
        self.debug = debug
        self.config = config or DEFAULT_CONFIG.copy()
        if selected_analysts is not None:
            self.config["selected_analysts"] = selected_analysts

        # Create results directories
        os.makedirs(self.config.get("results_dir", "./results"), exist_ok=True)

        # Initialize LLMs
        llm_kwargs = self._get_provider_kwargs()

        self.deep_thinking_llm = create_llm(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )
        self.quick_thinking_llm = create_llm(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )

        # Initialize memories
        self.bull_memory = CryptoSituationMemory("bull_memory", self.config)
        self.bear_memory = CryptoSituationMemory("bear_memory", self.config)
        self.trader_memory = CryptoSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = CryptoSituationMemory("invest_judge_memory", self.config)
        self.portfolio_manager_memory = CryptoSituationMemory("portfolio_manager_memory", self.config)

        # Create tool nodes for analysts that use tools
        self.tool_nodes = {
            "market": ToolNode([get_crypto_price, get_crypto_indicators, cmc_get_quote]),
            "sentiment": ToolNode([
                get_crypto_fear_greed, get_trending_coins,
                get_global_crypto_market, get_top_coins_by_market_cap,
                get_derivatives_data, cmc_get_global, cmc_get_fear_greed,
            ]),
            "news": ToolNode([get_crypto_news]),
            "fundamentals": ToolNode([
                get_crypto_market_data, get_defi_tvl,
                get_defi_protocol_info, get_top_coins_by_market_cap,
                cmc_get_coin_info, cmc_get_quote,
            ]),
            "onchain": ToolNode([
                get_crypto_market_data, get_global_crypto_market,
                get_crypto_fear_greed, get_top_coins_by_market_cap,
                cmc_get_quote, cmc_get_global,
            ]),
        }

        # Initialize components
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config["max_debate_rounds"],
            max_risk_discuss_rounds=self.config["max_risk_discuss_rounds"],
        )
        self.propagator = Propagator(max_recur_limit=self.config["max_recur_limit"])
        self.signal_processor = SignalProcessor()

        # State tracking
        self.curr_state = None
        self.log_states_dict = {}

        # Build the graph
        self.graph = self._setup_graph()

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        kwargs = {}
        provider = self.config.get("llm_provider", "").lower()
        if provider == "openai" and self.config.get("openai_reasoning_effort"):
            kwargs["reasoning_effort"] = self.config["openai_reasoning_effort"]
        elif provider == "anthropic" and self.config.get("anthropic_effort"):
            kwargs["effort"] = self.config["anthropic_effort"]
        elif provider == "google" and self.config.get("google_thinking_level"):
            kwargs["thinking_level"] = self.config["google_thinking_level"]
        return kwargs

    def _setup_graph(self):
        """Build and compile the LangGraph agent workflow."""
        selected = self.config["selected_analysts"]

        if not selected:
            raise ValueError("No analysts selected!")

        # Create analyst nodes
        analyst_factories = {
            "market": create_market_analyst,
            "sentiment": create_sentiment_analyst,
            "news": create_news_analyst,
            "fundamentals": create_fundamentals_analyst,
            "onchain": create_onchain_analyst,
        }

        analyst_nodes = {}
        delete_nodes = {}

        for analyst_type in selected:
            if analyst_type not in analyst_factories:
                raise ValueError(f"Unknown analyst type: {analyst_type}")
            analyst_nodes[analyst_type] = analyst_factories[analyst_type](self.quick_thinking_llm)
            delete_nodes[analyst_type] = create_msg_delete()

        # Create researcher/manager/trader/risk nodes
        bull_researcher = create_bull_researcher(self.quick_thinking_llm, self.bull_memory)
        bear_researcher = create_bear_researcher(self.quick_thinking_llm, self.bear_memory)
        research_manager = create_research_manager(self.deep_thinking_llm, self.invest_judge_memory)
        trader = create_trader(self.quick_thinking_llm, self.trader_memory)
        aggressive = create_aggressive_debator(self.quick_thinking_llm)
        conservative = create_conservative_debator(self.quick_thinking_llm)
        neutral = create_neutral_debator(self.quick_thinking_llm)
        portfolio_manager = create_portfolio_manager(self.deep_thinking_llm, self.portfolio_manager_memory)

        # Build the graph
        workflow = StateGraph(AgentState)

        # Add analyst nodes
        for analyst_type in selected:
            name = analyst_type.capitalize()
            workflow.add_node(f"{name} Analyst", analyst_nodes[analyst_type])
            workflow.add_node(f"Msg Clear {name}", delete_nodes[analyst_type])
            workflow.add_node(f"tools_{analyst_type}", self.tool_nodes[analyst_type])

        # Add other nodes
        workflow.add_node("Bull Researcher", bull_researcher)
        workflow.add_node("Bear Researcher", bear_researcher)
        workflow.add_node("Research Manager", research_manager)
        workflow.add_node("Trader", trader)
        workflow.add_node("Aggressive Analyst", aggressive)
        workflow.add_node("Conservative Analyst", conservative)
        workflow.add_node("Neutral Analyst", neutral)
        workflow.add_node("Portfolio Manager", portfolio_manager)

        # Wire edges: Analyst chain
        first_analyst = selected[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        for i, analyst_type in enumerate(selected):
            name = analyst_type.capitalize()
            current_analyst = f"{name} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {name}"

            # Analyst → tools or clear
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Clear → next analyst or Bull Researcher
            if i < len(selected) - 1:
                next_name = selected[i + 1].capitalize()
                workflow.add_edge(current_clear, f"{next_name} Analyst")
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # Wire: Bull ↔ Bear debate → Research Manager
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )

        # Wire: Research Manager → Trader → Risk chain
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")

        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Conservative Analyst": "Conservative Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Neutral Analyst": "Neutral Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Neutral Analyst": "Neutral Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )

        workflow.add_edge("Portfolio Manager", END)

        return workflow.compile()

    def propagate(self, crypto_name: str, coin_id: str, trade_date: str):
        """
        Run the full multi-agent analysis for a cryptocurrency.

        Args:
            crypto_name: Human-readable name (e.g., "Bitcoin")
            coin_id: CoinGecko coin ID (e.g., "bitcoin")
            trade_date: Analysis date string

        Returns:
            (final_state, decision_signal) tuple
        """
        self.ticker = coin_id

        init_state = self.propagator.create_initial_state(crypto_name, coin_id, trade_date)
        args = self.propagator.get_graph_args()

        if self.debug:
            trace = []
            for chunk in self.graph.stream(init_state, **args):
                if chunk.get("messages"):
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)
            final_state = trace[-1] if trace else init_state
        else:
            final_state = self.graph.invoke(init_state, **args)

        self.curr_state = final_state
        self._log_state(trade_date, final_state)

        return final_state, self.signal_processor.process_signal(
            final_state.get("final_trade_decision", "")
        )

    def _log_state(self, trade_date, final_state):
        """Log the final analysis state to JSON."""
        self.log_states_dict[str(trade_date)] = {
            "crypto_of_interest": final_state.get("crypto_of_interest"),
            "coin_id": final_state.get("coin_id"),
            "trade_date": final_state.get("trade_date"),
            "market_report": final_state.get("market_report"),
            "sentiment_report": final_state.get("sentiment_report"),
            "fundamentals_report": final_state.get("fundamentals_report"),
            "onchain_report": final_state.get("onchain_report"),
            "investment_debate_state": {
                k: final_state.get("investment_debate_state", {}).get(k, "")
                for k in ["bull_history", "bear_history", "history", "current_response", "judge_decision"]
            },
            "trader_investment_plan": final_state.get("trader_investment_plan"),
            "risk_debate_state": {
                k: final_state.get("risk_debate_state", {}).get(k, "")
                for k in ["aggressive_history", "conservative_history", "neutral_history", "history", "judge_decision"]
            },
            "investment_plan": final_state.get("investment_plan"),
            "final_trade_decision": final_state.get("final_trade_decision"),
        }

        directory = Path(self.config.get("results_dir", "./results")) / self.ticker
        directory.mkdir(parents=True, exist_ok=True)

        with open(directory / f"analysis_{trade_date}.json", "w", encoding="utf-8") as f:
            json.dump(self.log_states_dict, f, indent=2, default=str)

    def reflect_and_remember(self, returns_losses: float):
        """Reflect on decisions and update memory based on actual returns."""
        if not self.curr_state:
            return

        crypto = self.curr_state.get("crypto_of_interest", "unknown")
        decision = self.signal_processor.process_signal(
            self.curr_state.get("final_trade_decision", "")
        )

        self.bull_memory.add_memory(f"{crypto} analysis", decision, returns_losses)
        self.bear_memory.add_memory(f"{crypto} analysis", decision, returns_losses)
        self.trader_memory.add_memory(f"{crypto} trade", decision, returns_losses)
        self.invest_judge_memory.add_memory(f"{crypto} judgment", decision, returns_losses)
        self.portfolio_manager_memory.add_memory(f"{crypto} portfolio decision", decision, returns_losses)
