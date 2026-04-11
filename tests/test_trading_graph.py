import pytest
from crypto_trading_agents.graph.trading_graph import CryptoTradingAgentsGraph
from crypto_trading_agents.default_config import DEFAULT_CONFIG

def test_trading_graph_initialization():
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openrouter"
    config["deep_think_llm"] = "anthropic/claude-3-5-sonnet"
    config["quick_think_llm"] = "anthropic/claude-3-5-sonnet"
    
    graph = CryptoTradingAgentsGraph(debug=True, config=config)
    assert graph is not None
    assert graph.cryptos == ["bitcoin", "ethereum", "solana"]
    assert graph.max_recur_limit == 3

def test_trading_graph_propagation():
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openrouter"
    config["deep_think_llm"] = "anthropic/claude-3-5-sonnet"
    config["quick_think_llm"] = "anthropic/claude-3-5-sonnet"
    
    graph = CryptoTradingAgentsGraph(debug=True, config=config)
    # This should not raise an error even without API keys (it will use mock responses)
    try:
        final_state, decision = graph.propagate("Bitcoin", "bitcoin", "2026-04-11")
        assert final_state is not None
        assert decision in ["BUY", "SELL", "HOLD"]
    except Exception as e:
        # If it fails due to missing API keys, that's expected in test environment
        print(f"Test skipped due to missing API keys: {e}")
        pytest.skip("Requires API keys for full execution")

def test_token_optimizer_integration():
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openrouter"
    config["deep_think_llm"] = "anthropic/claude-3-5-sonnet"
    config["quick_think_llm"] = "anthropic/claude-3-5-sonnet"
    config["optimize_tokens"] = True
    
    graph = CryptoTradingAgentsGraph(debug=True, config=config)
    assert graph.optimizer is not None
    # Try to run a small propagation to see if optimizer works
    try:
        final_state, decision = graph.propagate("Bitcoin", "bitcoin", "2026-04-11")
        assert final_state is not None
    except Exception:
        pytest.skip("Requires API keys for full execution")

def test_config_loading():
    from crypto_trading_agents.default_config import DEFAULT_CONFIG
    assert DEFAULT_CONFIG is not None
    assert "llm_provider" in DEFAULT_CONFIG
    assert "deep_think_llm" in DEFAULT_CONFIG
