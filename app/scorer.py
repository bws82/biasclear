"""
Truth Score Calculator

Computes a 0-100 Truth Score from combined local + deep analysis.
Separated from detector.py for single-responsibility.

Score = 100 minus weighted penalties from:
  - Flag severity (structural > keyword)
  - PIT tier depth
  - Number and type of distortions
  - AI-discovered flags (lighter weight — non-deterministic)
  - Deep analysis severity (when available)
"""

from __future__ import annotations

from app.frozen_core import CoreEvaluation, Flag


def calculate_truth_score(
    core_eval: CoreEvaluation,
    deep_result: dict | None = None,
    ai_flags: list[dict] | None = None,
) -> tuple[int, dict]:
    """
    Calculate Truth Score from local evaluation + optional deep analysis + AI flags.

    Returns:
        (score, breakdown) where breakdown is a dict showing every penalty applied.

    Scoring:
      Start at 100.
      Structural flags:  critical=-25, high=-20, moderate=-14, low=-8
      Keyword markers:   -4 each
      PIT tier penalty:  tier_1=-10, tier_2=-7, tier_3=-4
      Multi-tier span:   -5 per additional unique tier (if flags span 2+)
      AI flags:          critical=-14, high=-10, moderate=-6, low=-3 (lighter weight)
      Deep severity:     critical=-20, high=-15, moderate=-8, low=-4
      Deep bias types:   -4 each (unique)
      Floor at 0, cap at 100.
    """
    ai_flags = ai_flags or []
    score = 100
    breakdown: dict = {
        "starting_score": 100,
        "core_structural_penalties": [],
        "core_marker_penalty": 0,
        "pit_tier_penalty": 0,
        "multi_tier_penalty": 0,
        "ai_flag_penalties": [],
        "deep_severity_penalty": 0,
        "deep_bias_type_penalty": 0,
    }

    # --- Local penalties ---
    tier_set: set[int] = set()
    structural_penalty = {"critical": 25, "high": 20, "moderate": 14, "low": 8}
    marker_count = 0

    for flag in core_eval.flags:
        if flag.category == "structural":
            pen = structural_penalty.get(flag.severity, 8)
            score -= pen
            tier_set.add(flag.pit_tier)
            breakdown["core_structural_penalties"].append({
                "pattern": flag.pattern_id,
                "severity": flag.severity,
                "penalty": -pen,
            })
        elif flag.category == "marker":
            score -= 4
            marker_count += 1

    breakdown["core_marker_penalty"] = -(marker_count * 4)

    # PIT tier penalty (from dominant tier)
    if core_eval.pit_tier_active:
        try:
            tier_num = int(core_eval.pit_tier_active.split("_")[1])
            tier_penalty = {1: 10, 2: 7, 3: 4}
            pen = tier_penalty.get(tier_num, 0)
            score -= pen
            breakdown["pit_tier_penalty"] = -pen
        except (IndexError, ValueError):
            pass

    # Multi-tier diversity penalty: distortions spanning multiple PIT tiers
    # indicates a more sophisticated or embedded bias pattern
    if len(tier_set) > 1:
        pen = (len(tier_set) - 1) * 5
        score -= pen
        breakdown["multi_tier_penalty"] = -pen

    # --- AI flag penalties (lighter than core — non-deterministic) ---
    ai_penalty_map = {"critical": 14, "high": 10, "moderate": 6, "low": 3}
    for af in ai_flags:
        sev = af.get("severity", "moderate")
        pen = ai_penalty_map.get(sev, 6)
        score -= pen
        breakdown["ai_flag_penalties"].append({
            "pattern": af.get("pattern_id", "unknown"),
            "severity": sev,
            "penalty": -pen,
        })

    # --- Deep analysis penalties (when available) ---
    if deep_result:
        severity = deep_result.get("severity", "none")
        deep_sev_penalty = {
            "critical": 20, "high": 15, "moderate": 8, "low": 4, "none": 0,
        }
        pen = deep_sev_penalty.get(severity, 0)
        score -= pen
        breakdown["deep_severity_penalty"] = -pen

        bias_types = deep_result.get("bias_types", [])
        unique_types = [b for b in bias_types if b != "none"]
        type_pen = len(set(unique_types)) * 4
        score -= type_pen
        breakdown["deep_bias_type_penalty"] = -type_pen

    final = max(0, min(100, score))
    breakdown["final_score"] = final
    return final, breakdown
