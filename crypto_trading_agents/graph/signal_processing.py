"""Signal processing — extract clean buy/sell/hold from agent output."""

import re


class SignalProcessor:
    """Extracts trading signals from agent text output."""

    def __init__(self, llm=None):
        self.llm = llm

    def process_signal(self, full_signal: str) -> str:
        """
        Extract the core trading decision from a full text signal.
        Looks for patterns like FINAL TRANSACTION PROPOSAL: **BUY** etc.
        """
        if not full_signal:
            return "HOLD"

        # Look for explicit final proposals
        patterns = [
            r"FINAL TRANSACTION PROPOSAL:\s*\*\*(BUY|SELL|HOLD)\*\*",
            r"FINAL TRANSACTION PROPOSAL:\s*(BUY|SELL|HOLD)",
            r"final (?:decision|proposal|recommendation).*?(BUY|SELL|HOLD)",
            r"\*\*(BUY|SELL|HOLD)\*\*",
        ]

        signal_upper = full_signal.upper()
        for pattern in patterns:
            match = re.search(pattern, signal_upper)
            if match:
                return match.group(1)

        # Fallback: look for keywords
        if "BUY" in signal_upper and "SELL" not in signal_upper:
            return "BUY"
        elif "SELL" in signal_upper and "BUY" not in signal_upper:
            return "SELL"

        return "HOLD"
