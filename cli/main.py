"""
Crypto Trading Agents — CLI entry point.

Usage:
    crypto-agents                         # Interactive mode
    crypto-agents bitcoin                 # Quick analysis of Bitcoin
    crypto-agents ethereum --date 2026-03-29 --provider openai
    crypto-agents solana --analysts market sentiment onchain
"""

import argparse
import sys
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Crypto Trading Agents — Multi-Agent LLM Crypto Analysis Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  crypto-agents bitcoin                          # Analyze Bitcoin today
  crypto-agents ethereum --date 2026-03-28       # Analyze Ethereum on specific date
  crypto-agents solana --provider anthropic       # Use Anthropic Claude
  crypto-agents bitcoin --debug                   # Debug mode with trace

Analyst options: market, sentiment, fundamentals, onchain
Providers: openai, anthropic, google, openrouter
        """,
    )

    parser.add_argument(
        "crypto",
        nargs="?",
        default="bitcoin",
        help="CoinGecko coin ID (e.g., bitcoin, ethereum, solana)",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Analysis date (YYYY-MM-DD, default: today)",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("CRYPTO_LLM_PROVIDER", "openai"),
        choices=["openai", "anthropic", "google", "openrouter"],
        help="LLM provider (default: openai)",
    )
    parser.add_argument(
        "--quick-model",
        default=os.getenv("CRYPTO_QUICK_THINK_LLM"),
        help="Model for quick-thinking agents (analysts, researchers, risk)",
    )
    parser.add_argument(
        "--deep-model",
        default=os.getenv("CRYPTO_DEEP_THINK_LLM"),
        help="Model for deep-thinking agents (research manager, portfolio manager)",
    )
    parser.add_argument(
        "--analysts",
        nargs="+",
        default=["market", "sentiment", "news", "fundamentals", "onchain"],
        choices=["market", "sentiment", "news", "fundamentals", "onchain"],
        help="Analyst types to include",
    )
    parser.add_argument(
        "--debate-rounds",
        type=int,
        default=2,
        help="Number of bull/bear debate rounds (default: 2)",
    )
    parser.add_argument(
        "--risk-rounds",
        type=int,
        default=2,
        help="Number of risk management debate rounds (default: 2)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with agent trace output",
    )

    args = parser.parse_args()

    # Validate API key
    key_env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    required_key = key_env_map.get(args.provider)
    if required_key and not os.getenv(required_key):
        print(f"Error: {required_key} environment variable is required for {args.provider}")
        print(f"Set it with: export {required_key}=your-key-here")
        print(f"Or create a .env file with: {required_key}=your-key-here")
        sys.exit(1)

    # Build config
    from crypto_trading_agents.default_config import DEFAULT_CONFIG

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = args.provider
    config["selected_analysts"] = args.analysts
    config["max_debate_rounds"] = args.debate_rounds
    config["max_risk_discuss_rounds"] = args.risk_rounds

    if args.quick_model:
        config["quick_think_llm"] = args.quick_model
    if args.deep_model:
        config["deep_think_llm"] = args.deep_model

    # Resolve coin name from ID
    crypto_names = {
        "bitcoin": "Bitcoin",
        "ethereum": "Ethereum",
        "solana": "Solana",
        "cardano": "Cardano",
        "polkadot": "Polkadot",
        "avalanche-2": "Avalanche",
        "chainlink": "Chainlink",
        "polygon-ecosystem-token": "Polygon",
        "ripple": "XRP",
        "dogecoin": "Dogecoin",
        "shiba-inu": "Shiba Inu",
        "litecoin": "Litecoin",
        "uniswap": "Uniswap",
        "aave": "Aave",
        "lido-dao": "Lido",
    }
    crypto_name = crypto_names.get(args.crypto, args.crypto.replace("-", " ").title())

    # Run analysis
    print(f"\n{'='*60}")
    print(f"  Crypto Trading Agents — Multi-Agent Analysis")
    print(f"{'='*60}")
    print(f"  Crypto:    {crypto_name} ({args.crypto})")
    print(f"  Date:      {args.date}")
    print(f"  Provider:  {args.provider}")
    print(f"  Analysts:  {', '.join(args.analysts)}")
    print(f"  Debates:   {args.debate_rounds} rounds")
    print(f"  Debug:     {args.debug}")
    print(f"{'='*60}\n")

    from crypto_trading_agents.graph.trading_graph import CryptoTradingAgentsGraph

    try:
        ta = CryptoTradingAgentsGraph(
            selected_analysts=args.analysts,
            debug=args.debug,
            config=config,
        )

        print("🚀 Starting multi-agent analysis...\n")
        final_state, decision = ta.propagate(crypto_name, args.crypto, args.date)

        # Print results
        print(f"\n{'='*60}")
        print(f"  ANALYSIS COMPLETE")
        print(f"{'='*60}\n")

        # Analyst reports
        for report_key, report_name in [
            ("market_report", "📊 Market Analyst"),
            ("sentiment_report", "😊 Sentiment Analyst"),
            ("fundamentals_report", "📈 Fundamentals Analyst"),
            ("onchain_report", "🔗 On-Chain Analyst"),
        ]:
            report = final_state.get(report_key, "")
            if report:
                print(f"### {report_name}")
                print(f"{report[:500]}...")
                print()

        # Investment plan
        plan = final_state.get("investment_plan", "")
        if plan:
            print(f"### 📋 Investment Plan")
            print(plan[:800])
            print()

        # Final decision
        decision_text = final_state.get("final_trade_decision", "")
        if decision_text:
            print(f"### 🎯 Final Decision")
            print(decision_text[:800])
            print()

        print(f"\n{'='*60}")
        print(f"  SIGNAL: {decision}")
        print(f"{'='*60}\n")

        # Save location
        results_dir = config.get("results_dir", "./results")
        print(f"📁 Full results saved to: {results_dir}/{args.crypto}/")

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
