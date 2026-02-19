"""
Weight Optimizer — Scoring Calibration

Takes benchmark results and recommends scoring weight adjustments
to maximize the separation between clean and biased Truth Scores.

The optimizer does NOT auto-apply changes. It produces recommendations
that a human reviews before updating scorer.py. This is consistent
with the frozen core philosophy — even the learning that happens
is governed and auditable.

Optimization targets:
  1. Maximize Truth Score separation (clean avg - biased avg)
  2. Minimize false positive rate (clean samples scored low)
  3. Minimize false negative rate (biased samples scored high)
  4. Clean samples should score ≥ 85
  5. Biased samples should score ≤ 60
"""

from __future__ import annotations

from dataclasses import dataclass
from calibration.benchmark import BenchmarkResult


@dataclass
class WeightRecommendation:
    """A single recommended weight adjustment."""
    parameter: str       # e.g., "structural_high_penalty"
    current_value: float
    recommended_value: float
    reason: str
    impact: str          # Expected impact description


@dataclass
class OptimizationReport:
    """Full optimization output."""
    current_separation: float
    target_separation: float
    recommendations: list[WeightRecommendation]
    summary: str


# Current scoring weights from scorer.py
CURRENT_WEIGHTS = {
    "structural_critical": 25,
    "structural_high": 20,
    "structural_moderate": 14,
    "structural_low": 8,
    "marker_penalty": 4,
    "tier_1_penalty": 10,
    "tier_2_penalty": 7,
    "tier_3_penalty": 4,
    "multi_tier_span": 5,
    "deep_critical": 20,
    "deep_high": 15,
    "deep_moderate": 8,
    "deep_low": 4,
    "deep_bias_type_penalty": 4,
}


def optimize_weights(result: BenchmarkResult) -> OptimizationReport:
    """
    Analyze benchmark results and produce weight recommendations.

    Strategy:
    - If clean samples score too low → reduce penalties (FP problem)
    - If biased samples score too high → increase penalties (FN problem)
    - If separation is < 25 → adjust both sides toward targets
    - If specific patterns have high FP → reduce their severity weight
    - If specific patterns have high FN → increase their severity weight
    """
    recommendations = []

    avg_clean = result.avg_truth_score_clean
    avg_biased = result.avg_truth_score_biased
    separation = result.truth_score_separation

    # Target: clean ≥ 85, biased ≤ 60, separation ≥ 25
    TARGET_CLEAN = 85.0
    TARGET_BIASED = 60.0
    TARGET_SEPARATION = 25.0

    # --- Check clean samples ---
    if avg_clean < TARGET_CLEAN and result.clean_samples > 0:
        # Clean text scoring too low → false positives dragging scores down
        gap = TARGET_CLEAN - avg_clean

        # Check if markers are the problem (most common FP source)
        fp_from_markers = sum(
            1 for fp in result.false_positives
            if fp["pattern_id"].startswith("SK_")
        )
        fp_from_structural = len(result.false_positives) - fp_from_markers

        if fp_from_markers > fp_from_structural:
            new_marker = max(1, CURRENT_WEIGHTS["marker_penalty"] - 1)
            recommendations.append(WeightRecommendation(
                parameter="marker_penalty",
                current_value=CURRENT_WEIGHTS["marker_penalty"],
                recommended_value=new_marker,
                reason=f"Clean samples avg {avg_clean:.0f} (target ≥{TARGET_CLEAN:.0f}). "
                       f"{fp_from_markers} false positives from keyword markers.",
                impact=f"Reduces marker penalty from {CURRENT_WEIGHTS['marker_penalty']} to {new_marker}. "
                       f"Expected to raise clean avg by ~{gap * 0.3:.0f} points.",
            ))
        else:
            recommendations.append(WeightRecommendation(
                parameter="structural_low_penalty",
                current_value=CURRENT_WEIGHTS["structural_low"],
                recommended_value=max(3, CURRENT_WEIGHTS["structural_low"] - 2),
                reason=f"Clean samples avg {avg_clean:.0f} (target ≥{TARGET_CLEAN:.0f}). "
                       f"Low-severity structural patterns may be over-penalizing.",
                impact="Reduces low-severity structural penalty. "
                       "May slightly increase biased sample scores too.",
            ))

    # --- Check biased samples ---
    if avg_biased > TARGET_BIASED and result.biased_samples > 0:
        # Biased text scoring too high → engine not penalizing enough
        gap = avg_biased - TARGET_BIASED

        # Check which patterns have high false negative rates
        weak_patterns = [
            (pid, m) for pid, m in result.pattern_metrics.items()
            if m.support > 0 and m.recall < 0.5
        ]

        if weak_patterns:
            for pid, m in weak_patterns:
                recommendations.append(WeightRecommendation(
                    parameter=f"pattern_sensitivity:{pid}",
                    current_value=m.recall,
                    recommended_value=0.0,
                    reason=f"Pattern {m.human_tag} has {m.recall:.0%} recall "
                           f"({m.false_negatives} misses out of {m.support} labeled instances). "
                           f"The regex may need expansion.",
                    impact="Requires regex tuning in frozen_core.py, not weight adjustment.",
                ))
        else:
            # Patterns are detecting but penalties aren't strong enough
            recommendations.append(WeightRecommendation(
                parameter="structural_high_penalty",
                current_value=CURRENT_WEIGHTS["structural_high"],
                recommended_value=CURRENT_WEIGHTS["structural_high"] + 3,
                reason=f"Biased samples avg {avg_biased:.0f} (target ≤{TARGET_BIASED:.0f}). "
                       f"Patterns are detecting but penalties are too light.",
                impact=f"Increases high-severity penalty from "
                       f"{CURRENT_WEIGHTS['structural_high']} to "
                       f"{CURRENT_WEIGHTS['structural_high'] + 3}.",
            ))

    # --- Check separation ---
    if separation < TARGET_SEPARATION:
        recommendations.append(WeightRecommendation(
            parameter="truth_score_separation",
            current_value=separation,
            recommended_value=TARGET_SEPARATION,
            reason=f"Truth Score separation is {separation:.0f} points "
                   f"(target ≥{TARGET_SEPARATION:.0f}). Clean and biased samples "
                   f"aren't sufficiently distinguished.",
            impact="Apply the above recommendations to widen the gap. "
                   "If insufficient, consider adding penalty for multiple "
                   "flags from different PIT tiers.",
        ))

    # --- Per-pattern FP analysis ---
    for pid, m in result.pattern_metrics.items():
        if m.false_positives >= 3 and m.support == 0:
            recommendations.append(WeightRecommendation(
                parameter=f"pattern_false_positive:{pid}",
                current_value=m.false_positives,
                recommended_value=0,
                reason=f"Pattern {pid} has {m.false_positives} false positives "
                       f"and 0 true positives. It may be triggering on "
                       f"legitimate text.",
                impact="Consider tightening the regex or adding context-aware "
                       "suppression for this pattern.",
            ))

    # --- Summary ---
    if not recommendations:
        summary = (
            f"Calibration looks good. Separation: {separation:.0f} points. "
            f"Clean avg: {avg_clean:.0f}. Biased avg: {avg_biased:.0f}. "
            f"No weight adjustments recommended."
        )
    else:
        summary = (
            f"Found {len(recommendations)} adjustment(s). "
            f"Current separation: {separation:.0f} points "
            f"(target ≥{TARGET_SEPARATION:.0f}). "
            f"Clean avg: {avg_clean:.0f} (target ≥{TARGET_CLEAN:.0f}). "
            f"Biased avg: {avg_biased:.0f} (target ≤{TARGET_BIASED:.0f})."
        )

    return OptimizationReport(
        current_separation=separation,
        target_separation=TARGET_SEPARATION,
        recommendations=recommendations,
        summary=summary,
    )


def format_optimization_report(report: OptimizationReport) -> str:
    """Format optimization report for human review."""
    lines = [
        "=" * 60,
        "BIASCLEAR WEIGHT OPTIMIZATION REPORT",
        "=" * 60,
        "",
        report.summary,
        "",
    ]

    if report.recommendations:
        lines.append("--- RECOMMENDATIONS ---")
        lines.append("")
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec.parameter}")
            lines.append(f"   Current: {rec.current_value}")
            lines.append(f"   Recommended: {rec.recommended_value}")
            lines.append(f"   Reason: {rec.reason}")
            lines.append(f"   Impact: {rec.impact}")
            lines.append("")
    else:
        lines.append("No adjustments needed.")

    lines.extend(["", "=" * 60])
    return "\n".join(lines)
