"""
Benchmark Runner — Precision/Recall/F1 per Pattern

Runs the calibration corpus through the frozen core and compares
engine output against human labels. Produces:

  1. Per-pattern precision, recall, F1
  2. Overall detection accuracy
  3. False positive analysis
  4. Truth Score correlation (engine score vs. human severity)
  5. Specific misses and false alarms for manual review

This is the tool that tells you if the engine is accurate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from biasclear.frozen_core import frozen_core, CoreEvaluation
from biasclear.scorer import calculate_truth_score
from calibration.corpus_parser import (
    CalibrationSample,
    TAG_TO_PATTERN_ID,
    PATTERN_ID_TO_TAG,
    parse_all_corpora,
)


@dataclass
class PatternMetrics:
    """Precision/recall metrics for a single pattern."""
    pattern_id: str
    human_tag: str
    true_positives: int = 0   # Engine flagged, human tagged
    false_positives: int = 0  # Engine flagged, human didn't tag
    false_negatives: int = 0  # Human tagged, engine missed
    true_negatives: int = 0   # Neither flagged

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def support(self) -> int:
        """Number of human-labeled positives for this pattern."""
        return self.true_positives + self.false_negatives


@dataclass
class BenchmarkResult:
    """Full benchmark output."""
    total_samples: int
    clean_samples: int
    biased_samples: int
    # Per-pattern metrics
    pattern_metrics: dict[str, PatternMetrics]
    # Overall detection
    overall_accuracy: float      # (TP + TN) / total across all patterns
    overall_precision: float     # Macro-averaged
    overall_recall: float        # Macro-averaged
    overall_f1: float            # Macro-averaged
    # Truth Score analysis
    avg_truth_score_clean: float     # Average score for clean samples
    avg_truth_score_biased: float    # Average score for biased samples
    truth_score_separation: float    # Gap between clean and biased averages
    # Detailed results for review
    false_positives: list[dict]      # Engine flagged clean text
    false_negatives: list[dict]      # Engine missed human-tagged bias
    # Scoring data
    truth_score_pairs: list[dict]    # (sample, engine_score, human_severity)


def run_benchmark(
    corpus_dir: str | Path = "calibration/corpus",
    domain: str = "legal",
) -> BenchmarkResult:
    """
    Run the full calibration benchmark.

    1. Parse all corpus files
    2. Run each sample through the frozen core
    3. Compare engine flags against human labels
    4. Compute metrics

    Args:
        corpus_dir: Path to directory containing corpus .txt files.
        domain: Domain to evaluate against.

    Returns:
        BenchmarkResult with full metrics.
    """
    samples = parse_all_corpora(corpus_dir)

    if not samples:
        raise ValueError(f"No samples found in {corpus_dir}")

    # Initialize per-pattern metrics for all known patterns
    all_pattern_ids = set(TAG_TO_PATTERN_ID.values())
    metrics: dict[str, PatternMetrics] = {}
    for tag, pid in TAG_TO_PATTERN_ID.items():
        if pid not in metrics:
            metrics[pid] = PatternMetrics(pattern_id=pid, human_tag=tag)

    false_positives_detail = []
    false_negatives_detail = []
    truth_score_pairs = []

    clean_scores = []
    biased_scores = []

    for sample in samples:
        # Run through engine
        core_eval = frozen_core.evaluate(sample.text, domain=sample.domain or domain)
        truth_score, _ = calculate_truth_score(core_eval)

        # Store result on sample
        sample.engine_result = {
            "truth_score": truth_score,
            "flags": [
                {"pattern_id": f.pattern_id, "category": f.category, "severity": f.severity}
                for f in core_eval.flags
            ],
            "aligned": core_eval.aligned,
            "knowledge_type": core_eval.knowledge_type,
        }

        # Engine's detected pattern IDs
        engine_pattern_ids = set()
        for flag in core_eval.flags:
            if flag.category == "structural":
                engine_pattern_ids.add(flag.pattern_id)

        # Human's expected pattern IDs
        human_pattern_ids = set()
        for tag in sample.tags:
            if tag in TAG_TO_PATTERN_ID:
                human_pattern_ids.add(TAG_TO_PATTERN_ID[tag])

        # Score tracking
        truth_score_pairs.append({
            "text": sample.text[:100],
            "source": sample.source,
            "truth_score": truth_score,
            "human_severity": sample.severity,
            "human_tags": sample.tags,
            "is_clean": sample.is_clean,
        })

        if sample.is_clean:
            clean_scores.append(truth_score)
        else:
            biased_scores.append(truth_score)

        # Per-pattern comparison
        for pid, pm in metrics.items():
            engine_has = pid in engine_pattern_ids
            human_has = pid in human_pattern_ids

            if engine_has and human_has:
                pm.true_positives += 1
            elif engine_has and not human_has:
                # Only count as FP if the sample is clean or this specific pattern wasn't tagged
                if sample.is_clean or pid not in human_pattern_ids:
                    pm.false_positives += 1
                    if sample.is_clean:
                        false_positives_detail.append({
                            "pattern_id": pid,
                            "text": sample.text[:200],
                            "source": sample.source,
                            "notes": sample.notes,
                            "human_tags": sample.tags,
                        })
            elif not engine_has and human_has:
                pm.false_negatives += 1
                false_negatives_detail.append({
                    "pattern_id": pid,
                    "human_tag": PATTERN_ID_TO_TAG.get(pid, pid),
                    "text": sample.text[:200],
                    "source": sample.source,
                    "notes": sample.notes,
                })
            else:
                pm.true_negatives += 1

    # Compute overall metrics (macro-averaged over patterns with support > 0)
    active_metrics = [m for m in metrics.values() if m.support > 0]
    if active_metrics:
        overall_precision = sum(m.precision for m in active_metrics) / len(active_metrics)
        overall_recall = sum(m.recall for m in active_metrics) / len(active_metrics)
        overall_f1 = sum(m.f1 for m in active_metrics) / len(active_metrics)
    else:
        overall_precision = overall_recall = overall_f1 = 0.0

    # Overall accuracy
    total_decisions = sum(
        m.true_positives + m.false_positives + m.false_negatives + m.true_negatives
        for m in metrics.values()
    )
    total_correct = sum(m.true_positives + m.true_negatives for m in metrics.values())
    overall_accuracy = total_correct / total_decisions if total_decisions > 0 else 0.0

    # Truth Score analysis
    avg_clean = sum(clean_scores) / len(clean_scores) if clean_scores else 0.0
    avg_biased = sum(biased_scores) / len(biased_scores) if biased_scores else 0.0

    clean_count = sum(1 for s in samples if s.is_clean)
    biased_count = len(samples) - clean_count

    return BenchmarkResult(
        total_samples=len(samples),
        clean_samples=clean_count,
        biased_samples=biased_count,
        pattern_metrics=metrics,
        overall_accuracy=round(overall_accuracy, 4),
        overall_precision=round(overall_precision, 4),
        overall_recall=round(overall_recall, 4),
        overall_f1=round(overall_f1, 4),
        avg_truth_score_clean=round(avg_clean, 1),
        avg_truth_score_biased=round(avg_biased, 1),
        truth_score_separation=round(avg_clean - avg_biased, 1),
        false_positives=false_positives_detail,
        false_negatives=false_negatives_detail,
        truth_score_pairs=truth_score_pairs,
    )


def format_report(result: BenchmarkResult) -> str:
    """Format benchmark results as a human-readable report."""
    lines = [
        "=" * 60,
        "BIASCLEAR CALIBRATION REPORT",
        "=" * 60,
        "",
        f"Samples: {result.total_samples} "
        f"({result.clean_samples} clean, {result.biased_samples} biased)",
        "",
        "--- OVERALL METRICS ---",
        f"Accuracy:  {result.overall_accuracy:.1%}",
        f"Precision: {result.overall_precision:.1%}",
        f"Recall:    {result.overall_recall:.1%}",
        f"F1 Score:  {result.overall_f1:.1%}",
        "",
        "--- TRUTH SCORE ANALYSIS ---",
        f"Avg score (clean samples):  {result.avg_truth_score_clean}",
        f"Avg score (biased samples): {result.avg_truth_score_biased}",
        f"Separation gap:             {result.truth_score_separation}",
        f"  {'✅ GOOD' if result.truth_score_separation >= 25 else '⚠️  NEEDS TUNING'}"
        f" (target: ≥25 point gap)",
        "",
        "--- PER-PATTERN BREAKDOWN ---",
        f"{'Pattern':<30} {'Prec':>6} {'Recall':>6} {'F1':>6} {'TP':>4} {'FP':>4} {'FN':>4} {'Support':>7}",
        "-" * 80,
    ]

    # Sort patterns: those with support first, then by F1
    sorted_patterns = sorted(
        result.pattern_metrics.values(),
        key=lambda m: (-m.support, -m.f1),
    )

    for m in sorted_patterns:
        if m.support > 0 or m.false_positives > 0:
            lines.append(
                f"{m.human_tag:<30} {m.precision:>5.0%} {m.recall:>6.0%} "
                f"{m.f1:>5.0%} {m.true_positives:>4} {m.false_positives:>4} "
                f"{m.false_negatives:>4} {m.support:>7}"
            )

    if result.false_negatives:
        lines.extend([
            "",
            "--- MISSES (Engine missed human-tagged bias) ---",
        ])
        for fn in result.false_negatives[:10]:
            lines.append(
                f"  [{fn['human_tag']}] {fn['text'][:80]}..."
            )
            if fn.get("notes"):
                lines.append(f"    Notes: {fn['notes']}")

    if result.false_positives:
        lines.extend([
            "",
            "--- FALSE ALARMS (Engine flagged clean text) ---",
        ])
        for fp in result.false_positives[:10]:
            lines.append(
                f"  [{fp['pattern_id']}] {fp['text'][:80]}..."
            )

    lines.extend(["", "=" * 60])
    return "\n".join(lines)


def save_report(result: BenchmarkResult, output_dir: str | Path = "calibration/reports"):
    """Save benchmark results as both human-readable report and JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Human-readable
    report_text = format_report(result)
    report_path = output_dir / "calibration_report.txt"
    report_path.write_text(report_text, encoding="utf-8")

    # Machine-readable JSON
    json_data = {
        "total_samples": result.total_samples,
        "clean_samples": result.clean_samples,
        "biased_samples": result.biased_samples,
        "overall": {
            "accuracy": result.overall_accuracy,
            "precision": result.overall_precision,
            "recall": result.overall_recall,
            "f1": result.overall_f1,
        },
        "truth_score": {
            "avg_clean": result.avg_truth_score_clean,
            "avg_biased": result.avg_truth_score_biased,
            "separation": result.truth_score_separation,
        },
        "per_pattern": {
            pid: {
                "precision": m.precision,
                "recall": m.recall,
                "f1": m.f1,
                "tp": m.true_positives,
                "fp": m.false_positives,
                "fn": m.false_negatives,
                "support": m.support,
            }
            for pid, m in result.pattern_metrics.items()
            if m.support > 0 or m.false_positives > 0
        },
        "false_positives": result.false_positives,
        "false_negatives": result.false_negatives,
        "truth_score_pairs": result.truth_score_pairs,
    }
    json_path = output_dir / "calibration_report.json"
    json_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")

    return report_path, json_path
