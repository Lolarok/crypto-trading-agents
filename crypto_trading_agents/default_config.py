"""Default configuration for crypto-trading-agents."""

import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "results_dir": os.getenv("CRYPTOAGENTS_RESULTS_DIR", "./results"),
    # LLM settings
    "llm_provider": os.getenv("CRYPTO_LLM_PROVIDER", "openai"),  # openai, anthropic, google, openrouter
    "deep_think_llm": os.getenv("CRYPTO_DEEP_THINK_LLM", "gpt-4o"),
    "quick_think_llm": os.getenv("CRYPTO_QUICK_THINK_LLM", "gpt-4o-mini"),
    "backend_url": os.getenv("CRYPTO_BACKEND_URL", None),
    # Provider-specific settings
    "openai_reasoning_effort": None,  # "low", "medium", "high"
    "anthropic_effort": None,         # "low", "medium", "high"
    "google_thinking_level": None,    # "high", "minimal", etc.
    # Debate settings
    "max_debate_rounds": 2,
    "max_risk_discuss_rounds": 2,
    "max_recur_limit": 100,
    # Analyst selection
    "selected_analysts": ["market", "sentiment", "news", "fundamentals", "onchain"],
}
