#!/usr/bin/env python3
"""
Sync crypto-trading-agents analysis results to signalhub public folder.

Why: SignalHub frontend needs access to TA analysis JSON to display per-coin deep dive.
      This script copies the latest analysis file for each coin into signalhub/public/results/
      so that the frontend can fetch them via HTTP.

Usage:
    python3 scripts/sync_ta_results.py

Requires:
    - Both projects in adjacent folders (or adjust paths below)
    - Trading agents must have been run at least once to generate results
"""

import json
import shutil
from pathlib import Path

# Paths — adjust if your folder structure differs
WORKSPACE = Path(__file__).resolve().parents[2]  # assume script lives in crypto-trading-agents/scripts/
TA_RESULTS = WORKSPACE / "crypto-trading-agents" / "results"
SIGNALHUB_PUBLIC = WORKSPACE / "projects" / "signalhub" / "public" / "results"

def sync():
    if not TA_RESULTS.exists():
        print(f"❌ Trading agents results folder not found: {TA_RESULTS}")
        return

    # Ensure target exists
    SIGNALHUB_PUBLIC.mkdir(parents=True, exist_ok=True)

    copied = 0
    for coin_dir in TA_RESULTS.iterdir():
        if not coin_dir.is_dir():
            continue
        coin_id = coin_dir.name
        # Find the latest analysis JSON (sorted by filename)
        analyses = sorted(coin_dir.glob("analysis_*.json"))
        if not analyses:
            print(f"⚠️  No analysis found for {coin_id}")
            continue
        latest = analyses[-1]  # last by alphabetical (date-based filename)
        target_dir = SIGNALHUB_PUBLIC / coin_id
        target_dir.mkdir(exist_ok=True)
        target_file = target_dir / "analysis_latest.json"
        shutil.copy2(latest, target_file)
        print(f"✅ {coin_id}: {latest.name} → {target_file.relative_to(WORKSPACE)}")
        copied += 1

    print(f"\n✨ Synced {copied} coin analyses to signalhub public folder.")
    print(f"   SignalHub will now show Trading Agents data when you click a coin row.")

if __name__ == "__main__":
    sync()
