"""
Token Optimizer — Reduce LLM token consumption in multi-agent flows.

Strategies:
1. Report Compression — Summarize analyst reports before passing downstream
2. Context Deduplication — Remove repeated data across messages
3. Structured Data Formatting — Compact market data into minimal format
4. Token Tracking — Log usage per agent per run

Usage:
    from crypto_trading_agents.optimizer import TokenOptimizer

    optimizer = TokenOptimizer()
    compressed = optimizer.compress_report(report, "market")
    optimizer.print_summary()
"""

import re
import json
import hashlib
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class TokenStats:
    """Track token estimates per agent."""
    agent: str
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0


class TokenOptimizer:
    """
    Reduces token consumption in the crypto trading agents pipeline.
    
    Core principle: analysts generate verbose reports that downstream agents
    re-read in full. By compressing reports into structured summaries, we
    cut ~40-60% of tokens while preserving signal.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats: list[TokenStats] = []
        self._seen_data: dict[str, str] = {}  # hash -> compressed form

    # ─── Report Compression ──────────────────────────────────────────────

    def compress_report(self, report: str, report_type: str) -> str:
        """
        Compress an analyst report into a structured summary.
        
        Removes:
        - Filler phrases ("In conclusion...", "Based on the analysis...")
        - Repeated data points
        - Excessive hedging language
        - Redundant section headers
        
        Preserves:
        - Specific numbers (prices, percentages, indicators)
        - Directional signals (BULLISH/BEARISH/NEUTRAL)
        - Key levels (support, resistance)
        - Confidence levels
        """
        if not report or len(report) < 100:
            return report

        original_len = len(report)

        # Step 1: Extract structured data
        structured = self._extract_signals(report)

        # Step 2: Remove filler
        cleaned = self._remove_filler(report)

        # Step 3: Deduplicate repeated data points
        cleaned = self._dedup_sections(cleaned)

        # Step 4: Build compressed output
        compressed = self._build_compressed(cleaned, structured, report_type)

        if self.verbose:
            reduction = (1 - len(compressed) / original_len) * 100
            print(f"  [optimizer] {report_type}: {original_len} → {len(compressed)} chars ({reduction:.0f}% reduction)")

        return compressed

    def _extract_signals(self, text: str) -> dict:
        """Extract key trading signals from text."""
        signals = {}

        # Direction
        for pattern, key in [
            (r"(BULLISH|BEARISH|NEUTRAL)", "direction"),
            (r"Confidence[:\s]*(\d+/\d+|[Ll]ow|[Mm]edium|[Hh]igh|\d+%?)", "confidence"),
            (r"FINAL TRANSACTION PROPOSAL:\s*\*{0,2}(BUY|SELL|HOLD)\*{0,2}", "signal"),
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                signals[key] = match.group(1).upper() if key != "confidence" else match.group(1)

        # Prices and levels
        prices = re.findall(r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", text)
        if prices:
            signals["prices_mentioned"] = list(set(prices))[:5]  # Max 5 unique prices

        # Percentages
        pcts = re.findall(r"([+-]?\d+\.?\d*)%", text)
        if pcts:
            signals["percentages"] = list(set(pcts))[:8]

        # RSI, MACD, etc.
        for indicator in ["RSI", "MACD", "ATR", "SMA", "EMA"]:
            match = re.search(rf"{indicator}[^:]*:\s*(\d+\.?\d*)", text)
            if match:
                signals[indicator.lower()] = match.group(1)

        # Support/Resistance
        support = re.findall(r"[Ss]upport.*?\$(\d[\d,]*(?:\.\d+)?)", text)
        resistance = re.findall(r"[Rr]esistance.*?\$(\d[\d,]*(?:\.\d+)?)", text)
        if support:
            signals["support"] = support[:3]
        if resistance:
            signals["resistance"] = resistance[:3]

        return signals

    def _remove_filler(self, text: str) -> str:
        """Remove common filler phrases that add no signal."""
        fillers = [
            r"(?i)in conclusion,?\s*",
            r"(?i)based on the (?:above |comprehensive )?(?:analysis|data),?\s*",
            r"(?i)it is (?:important to )?note that\s*",
            r"(?i)(?:overall|in summary|to summarize),?\s*",
            r"(?i)given the (?:current |present )?(?:market conditions|data),?\s*",
            r"(?i)as (?:mentioned |noted )?(?:above|earlier|previously),?\s*",
            r"(?i)it (?:should be |is )(?:noted|mentioned|observed) that\s*",
            r"(?i)the (?:key |main |primary )(?:takeaway|point|finding) is\s*",
            r"(?i)this (?:suggests|indicates|implies) that\s*",
            r"(?i)(?:furthermore|moreover|additionally|in addition),?\s*",
        ]
        result = text
        for filler in fillers:
            result = re.sub(filler, "", result)

        # Collapse multiple spaces/newlines
        result = re.sub(r"\n{3,}", "\n\n", result)
        result = re.sub(r"  +", " ", result)
        return result.strip()

    def _dedup_sections(self, text: str) -> str:
        """Remove sections that repeat data already shown."""
        lines = text.split("\n")
        seen_hashes = set()
        unique_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                unique_lines.append(line)
                continue

            # Hash normalized content (ignore case, whitespace)
            normalized = re.sub(r"\s+", " ", stripped.lower())
            h = hashlib.md5(normalized.encode()).hexdigest()[:8]

            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_lines.append(line)

        return "\n".join(unique_lines)

    def _build_compressed(self, cleaned: str, signals: dict, report_type: str) -> str:
        """Build final compressed report with structured header."""
        parts = []

        # Structured signal header
        signal = signals.get("signal", signals.get("direction", "?"))
        confidence = signals.get("confidence", "?")
        parts.append(f"## {report_type.upper()} | {signal} (conf: {confidence})")

        # Key numbers in compact format
        if "rsi" in signals:
            parts.append(f"RSI:{signals['rsi']}", )
        if "macd" in signals:
            parts.append(f"MACD:{signals['macd']}")

        # Support/Resistance
        levels = []
        if "support" in signals:
            levels.append(f"S:{','.join(signals['support'])}")
        if "resistance" in signals:
            levels.append(f"R:{','.join(signals['resistance'])}")
        if levels:
            parts.append(" ".join(levels))

        # Key percentages
        if "percentages" in signals and len(signals["percentages"]) <= 4:
            parts.append(f"Δ:{' '.join(signals['percentages'][:4])}%")

        parts.append("---")

        # Keep the cleaned body but truncate if too long
        body = cleaned
        if len(body) > 1500:
            # Keep first 1200 chars + last 300 chars (signal usually at end)
            body = body[:1200] + "\n[...]\n" + body[-300:]

        parts.append(body)

        return "\n".join(parts)

    # ─── Context Compression ─────────────────────────────────────────────

    def compress_messages(self, messages: list) -> list:
        """
        Compress a list of LangChain messages by:
        1. Removing tool call results that appear multiple times
        2. Summarizing long AI messages
        3. Deduplicating consecutive similar messages
        """
        if len(messages) <= 2:
            return messages

        compressed = []
        prev_hash = None

        for msg in messages:
            content = msg.content if hasattr(msg, "content") else str(msg)
            h = hashlib.md5(content.encode()).hexdigest()[:8]

            # Skip exact duplicates
            if h == prev_hash:
                continue
            prev_hash = h

            # Compress very long messages
            if len(content) > 3000:
                content = content[:1500] + f"\n[...{len(content)-1800} chars compressed...]\n" + content[-300:]

            compressed.append(msg)

        return compressed

    # ─── Debate History Compression ──────────────────────────────────────

    def compress_debate_history(self, history: str, max_chars: int = 2000) -> str:
        """
        Compress debate history by keeping only key arguments.
        
        Keeps:
        - First argument from each side (sets the thesis)
        - Last argument from each side (most refined position)
        - Any mention of specific numbers/signals
        """
        if len(history) <= max_chars:
            return history

        # Split by speaker turns
        turns = re.split(r"(?=### (?:Bull|Bear|Aggressive|Conservative|Neutral))", history)

        if len(turns) <= 3:
            # Just truncate
            return history[:max_chars] + "\n[...truncated...]"

        # Keep first turn, last 2 turns, and middle turns with numbers
        kept = [turns[0]]  # header/setup
        for turn in turns[1:-2]:
            if re.search(r"\$[\d,]+|\d+%|RSI|MACD|BUY|SELL|HOLD", turn):
                kept.append(turn[:300])  # Keep signal-bearing turns but truncate
        kept.extend(turns[-2:])  # Last 2 turns

        result = "\n".join(kept)
        if len(result) > max_chars:
            result = result[:max_chars] + "\n[...truncated...]"
        return result

    # ─── Token Tracking ──────────────────────────────────────────────────

    def track(self, agent: str, input_text: str, output_text: str):
        """Estimate and track token usage for an agent call."""
        # Rough estimate: 1 token ≈ 4 chars for English, ~3 chars mixed
        in_tokens = len(input_text) // 3
        out_tokens = len(output_text) // 3

        # Find or create stat
        stat = next((s for s in self.stats if s.agent == agent), None)
        if not stat:
            stat = TokenStats(agent=agent)
            self.stats.append(stat)

        stat.input_tokens += in_tokens
        stat.output_tokens += out_tokens
        stat.calls += 1

    def print_summary(self):
        """Print token usage summary."""
        if not self.stats:
            print("  No token usage tracked.")
            return

        print("\n  📊 TOKEN USAGE SUMMARY")
        print(f"  {'Agent':<25} {'Calls':>5} {'Input':>8} {'Output':>8} {'Total':>8}")
        print("  " + "─" * 58)

        total_in = total_out = 0
        for s in sorted(self.stats, key=lambda x: x.input_tokens + x.output_tokens, reverse=True):
            total = s.input_tokens + s.output_tokens
            total_in += s.input_tokens
            total_out += s.output_tokens
            print(f"  {s.agent:<25} {s.calls:>5} {s.input_tokens:>8,} {s.output_tokens:>8,} {total:>8,}")

        print("  " + "─" * 58)
        grand = total_in + total_out
        print(f"  {'TOTAL':<25} {sum(s.calls for s in self.stats):>5} {total_in:>8,} {total_out:>8,} {grand:>8,}")

        # Cost estimate (gpt-4o-mini pricing)
        cost_mini = grand / 1_000_000 * 0.30  # blended rate
        cost_4o = grand / 1_000_000 * 6.00
        print(f"\n  💰 Estimated cost (gpt-4o-mini): ${cost_mini:.4f}")
        print(f"  💰 Estimated cost (gpt-4o):      ${cost_4o:.4f}")

    def get_stats_dict(self) -> dict:
        """Return stats as dict for JSON output."""
        return {
            "agents": [
                {
                    "agent": s.agent,
                    "calls": s.calls,
                    "input_tokens": s.input_tokens,
                    "output_tokens": s.output_tokens,
                    "total": s.input_tokens + s.output_tokens,
                }
                for s in self.stats
            ],
            "total_input": sum(s.input_tokens for s in self.stats),
            "total_output": sum(s.output_tokens for s in self.stats),
            "total_tokens": sum(s.input_tokens + s.output_tokens for s in self.stats),
        }


# ─── Standalone Helpers ──────────────────────────────────────────────────────

def compress_market_data(price_data: dict, indicators: dict) -> str:
    """
    Format market data in ultra-compact notation.
    
    Instead of:
        "The current price is $67,112.00. The RSI (14) is 47.0, indicating
         neutral momentum. The MACD is -696.84 with a signal line of -812.96."
    
    Produces:
        "$67,112 | RSI:47 NEU | MACD:-697 sig:-813 | trend:BEAR"
    """
    parts = []

    if "price" in price_data:
        parts.append(f"${price_data['price']:,.0f}")

    if "rsi" in indicators:
        rsi = float(indicators["rsi"])
        label = "OB" if rsi > 70 else "OS" if rsi < 30 else "NEU"
        parts.append(f"RSI:{rsi:.0f} {label}")

    if "macd" in indicators:
        macd = float(indicators.get("macd", 0))
        sig = float(indicators.get("signal", 0))
        cross = "▲" if macd > sig else "▼"
        parts.append(f"MACD:{macd:.0f} {cross}")

    if "sma_50" in indicators:
        price = price_data.get("price", 0)
        sma = float(indicators["sma_50"])
        trend = "▲" if price > sma else "▼"
        parts.append(f"SMA50:{sma:.0f} {trend}")

    if "atr" in indicators:
        parts.append(f"ATR:{float(indicators['atr']):.0f}")

    return " | ".join(parts)
