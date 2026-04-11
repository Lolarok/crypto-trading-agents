import pytest
from crypto_trading_agents.optimizer import TokenOptimizer

def test_token_optimizer_initialization():
    optimizer = TokenOptimizer(verbose=False)
    assert optimizer is not None
    assert len(optimizer.stats) == 0

def test_compress_report():
    optimizer = TokenOptimizer(verbose=False)
    original_report = """
    Bitcoin is showing strong bullish signals. The RSI is at 72, which indicates overbought conditions, but the MACD histogram is turning positive, suggesting momentum is shifting. Bollinger Bands are tightening, indicating a potential breakout. Volume is above average, confirming buyer interest. Key resistance at $70,000, support at $68,000. 
    """
    compressed = optimizer.compress_report(original_report, "market")
    assert len(compressed) < len(original_report)
    assert "BUY" in compressed or "SELL" in compressed or "HOLD" in compressed

def test_token_optimizer_statistics():
    optimizer = TokenOptimizer(verbose=False)
    report = "Market is bullish with RSI 65, MACD crossover, and increasing volume."
    compressed = optimizer.compress_report(report, "market")
    assert len(optimizer.stats) == 1
    assert optimizer.stats[0].agent == "market"
    assert optimizer.stats[0].input_tokens > 0

def test_token_optimizer_multiple_agents():
    optimizer = TokenOptimizer(verbose=False)
    reports = {
        "market": "Market analysis: RSI 60, MACD bullish, volume up 20%.",
        "sentiment": "Sentiment is extremely greedy, Fear & Greed index at 85.",
        "onchain": "Large transactions detected: 50,000 BTC moved to exchange."
    }
    for agent, report in reports.items():
        compressed = optimizer.compress_report(report, agent)
    assert len(optimizer.stats) == 3
    agent_names = [s.agent for s in optimizer.stats]
    assert "market" in agent_names
    assert "sentiment" in agent_names
    assert "onchain" in agent_names

def test_token_optimizer_dedup_sections():
    optimizer = TokenOptimizer(verbose=False)
    report = """
    Bitcoin price is $70,000. Bitcoin is up 5% today. Market sentiment is bullish.
    Bitcoin price is $70,000. Bitcoin is up 5% today. Market sentiment is bullish.
    Bitcoin price is $70,000. Bitcoin is up 5% today. Market sentiment is bullish.
    """
    compressed = optimizer.compress_report(report, "market")
    # Should remove duplicates and compress
    assert "Bitcoin price is $70,000" in compressed
    assert compressed.count("Bitcoin price is $70,000") < 3
