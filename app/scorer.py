"""
Truth Score Calculator

Computes a 0-100 Truth Score from combined local + deep analysis.
Separated from detector.py for single-responsibility.

Score = 100 minus weighted penalties from:
  - Flag severity (structural > keyword)
  - PIT tier depth
  - Number and type of distortions
  - Deep analysis severity (when available)
"""

from __future__ import annotations

from app.frozen_core import CoreEvaluation, Flag


def calculate_truth_score(
    core_eval: CoreEvaluation,
    deep_result: dict | None = None,
) -> int:
    """
    Calculate Truth Score from local evaluation + optional deep analysis.

    Scoring:
      Start at 100.
      Structural flags:  critical=-25, high=-20, moderate=-14, low=-8
      Keyword markers:   -4 each
      PIT tier penalty:  tier_1=-10, tier_2=-7, tier_3=-4
      Multi-tier span:   -5 per additional unique tier (if flags span 2+)
      Deep severity:     critical=-20, high=-15, moderate=-8, low=-4
      Deep bias types:   -4 each (unique)
      Floor at 0, cap at 100.
    """
    score = 100

    # --- Local penalties ---
    tier_set: set[int] = set()

    for flag in core_eval.flags:
        if flag.category == "structural":
            penalty = {"critical": 25, "high": 20, "moderate": 14, "low": 8}
            score -= penalty.get(flag.severity, 8)
            tier_set.add(flag.pit_tier)
        elif flag.category == "marker":
            score -= 4

    # PIT tier penalty (from dominant tier)
    if core_eval.pit_tier_active:
        try:
            tier_num = int(core_eval.pit_tier_active.split("_")[1])
            tier_penalty = {1: 10, 2: 7, 3: 4}
            score -= tier_penalty.get(tier_num, 0)
        except (IndexError, ValueError):
            pass

    # Multi-tier diversity penalty: distortions spanning multiple PIT tiers
    # indicates a more sophisticated or embedded bias pattern
    if len(tier_set) > 1:
        score -= (len(tier_set) - 1) * 5

    # --- Deep analysis penalties (when available) ---
    if deep_result:
        severity = deep_result.get("severity", "none")
        deep_sev_penalty = {
            "critical": 20, "high": 15, "moderate": 8, "low": 4, "none": 0,
        }
        score -= deep_sev_penalty.get(severity, 0)

        bias_types = deep_result.get("bias_types", [])
        unique_types = [b for b in bias_types if b != "none"]
        score -= len(set(unique_types)) * 4

    return max(0, min(100, score))
