"""Memory system for tracking past decisions and outcomes."""

import os
import json
from pathlib import Path
from typing import Optional


class CryptoSituationMemory:
    """
    Memory that stores past analysis situations and their outcomes.
    Agents reflect on past decisions to improve future ones.
    """

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.memory_dir = Path(config.get("results_dir", "./results")) / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / f"{name}.json"
        self.memories = self._load()

    def _load(self) -> list:
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text())
            except Exception:
                return []
        return []

    def _save(self):
        self.memory_file.write_text(json.dumps(self.memories, indent=2))

    def add_memory(self, situation: str, decision: str, returns: float):
        """Add a new memory entry."""
        self.memories.append({
            "situation": situation,
            "decision": decision,
            "returns": returns,
        })
        self._save()

    def get_memories(self, current_situation: str, limit: int = 5) -> str:
        """
        Retrieve relevant past memories based on the current situation.
        Returns the most recent memories as a formatted string.
        """
        if not self.memories:
            return "No past memories available."

        recent = self.memories[-limit:]
        lines = [f"**Past {self.name} memories:**"]
        for m in recent:
            result = "profit ✅" if m["returns"] > 0 else "loss ❌" if m["returns"] < 0 else "flat ➡️"
            lines.append(
                f"- Situation: {m['situation'][:100]}... "
                f"| Decision: {m['decision']} | Result: {result} ({m['returns']:+.1f}%)"
            )
        return "\n".join(lines)
