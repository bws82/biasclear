"""
Tests for the calibration framework.

Tests cover:
  - Corpus parser (format parsing, edge cases)
  - Benchmark runner (metric calculation, report generation)
  - Weight optimizer (recommendation logic)
"""

import json
import textwrap
from pathlib import Path

import pytest

from calibration.corpus_parser import (
    CalibrationSample,
    parse_corpus,
    parse_all_corpora,
    _parse_block,
    TAG_TO_PATTERN_ID,
)
from calibration.benchmark import (
    run_benchmark,
    format_report,
    save_report,
    PatternMetrics,
    BenchmarkResult,
)
from calibration.optimizer import optimize_weights, format_optimization_report
from biasclear.frozen_core import frozen_core
from biasclear.scorer import calculate_truth_score

# Absolute path to the seed corpus (works regardless of CWD)
REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_CORPUS = REPO_ROOT / "calibration" / "corpus"


# ============================================================
# Corpus Parser Tests
# ============================================================

class TestCorpusParser:

    def test_parse_single_sample(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text(textwrap.dedent("""\
            ---
            tags: settled_law_dismissal
            severity: high
            source: test filing
            notes: test note

            It is well-settled law that this claim is meritless.

            ---
        """))
        samples = parse_corpus(corpus)
        assert len(samples) == 1
        s = samples[0]
        assert s.tags == ["settled_law_dismissal"]
        assert s.severity == "high"
        assert s.source == "test filing"
        assert s.notes == "test note"
        assert "well-settled" in s.text
        assert not s.is_clean

    def test_parse_clean_sample(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text(textwrap.dedent("""\
            ---
            tags: clean
            severity: none
            source: test

            This is a factual statement with no bias.

            ---
        """))
        samples = parse_corpus(corpus)
        assert len(samples) == 1
        assert samples[0].is_clean
        assert samples[0].tags == ["clean"]

    def test_parse_multiple_tags(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text(textwrap.dedent("""\
            ---
            tags: settled_law_dismissal, merit_dismissal, sanctions_threat
            severity: critical
            source: aggressive filing

            Combined attack text.

            ---
        """))
        samples = parse_corpus(corpus)
        assert len(samples) == 1
        s = samples[0]
        assert len(s.tags) == 3
        assert "settled_law_dismissal" in s.tags
        assert "merit_dismissal" in s.tags
        assert "sanctions_threat" in s.tags
        assert s.severity == "critical"

    def test_parse_multiple_samples(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text(textwrap.dedent("""\
            ---
            tags: clean
            severity: none
            source: test

            Clean text here.

            ---
            tags: fear_urgency
            severity: moderate
            source: test

            Act now or face disaster!

            ---
        """))
        samples = parse_corpus(corpus)
        assert len(samples) == 2
        assert samples[0].is_clean
        assert not samples[1].is_clean

    def test_skip_comments(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text(textwrap.dedent("""\
            # This is a comment
            # Another comment

            ---
            tags: clean
            severity: none
            source: test

            Actual sample text.

            ---
        """))
        samples = parse_corpus(corpus)
        assert len(samples) == 1

    def test_default_values(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text(textwrap.dedent("""\
            ---

            Just text with no metadata.

            ---
        """))
        samples = parse_corpus(corpus)
        assert len(samples) == 1
        s = samples[0]
        assert s.tags == ["clean"]
        assert s.severity == "none"
        assert s.source == "unknown"
        assert s.domain == "legal"

    def test_empty_file(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text("# Only comments\n# Nothing here\n")
        samples = parse_corpus(corpus)
        assert len(samples) == 0

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_corpus("/nonexistent/path.txt")

    def test_multiline_text(self, tmp_path):
        corpus = tmp_path / "test.txt"
        corpus.write_text(textwrap.dedent("""\
            ---
            tags: clean
            severity: none
            source: test

            First line of the passage.
            Second line continues the thought.
            Third line wraps up.

            ---
        """))
        samples = parse_corpus(corpus)
        assert len(samples) == 1
        assert "First line" in samples[0].text
        assert "Third line" in samples[0].text

    def test_tag_to_pattern_mapping(self):
        """All human tags should map to valid pattern IDs."""
        expected_tags = [
            "settled_law_dismissal", "merit_dismissal", "weight_stacking",
            "sanctions_threat", "procedural_gatekeeping", "straw_man",
            "consensus_as_evidence", "claim_without_citation",
            "dissent_dismissal", "false_binary", "fear_urgency", "shame_lever",
            "credential_as_proof", "institutional_neutrality",
            "inevitability_frame", "appeal_to_tradition",
            "false_equivalence", "moral_high_ground",
        ]
        for tag in expected_tags:
            assert tag in TAG_TO_PATTERN_ID, f"Missing mapping for tag: {tag}"

    def test_parse_all_corpora(self, tmp_path):
        """parse_all_corpora reads from all .txt files."""
        (tmp_path / "a.txt").write_text(textwrap.dedent("""\
            ---
            tags: clean
            severity: none
            source: file_a

            Sample A.

            ---
        """))
        (tmp_path / "b.txt").write_text(textwrap.dedent("""\
            ---
            tags: fear_urgency
            severity: moderate
            source: file_b

            Sample B.

            ---
        """))
        samples = parse_all_corpora(tmp_path)
        assert len(samples) == 2


# ============================================================
# Benchmark Runner Tests
# ============================================================

class TestBenchmark:

    def test_benchmark_runs_on_seed_corpus(self):
        """Full benchmark should run on the seed corpus."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        assert result.total_samples >= 30  # Grows as we add samples
        assert result.clean_samples >= 8
        assert result.biased_samples >= 15

    def test_benchmark_metrics_ranges(self):
        """All metrics should be in valid ranges."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        assert 0 <= result.overall_accuracy <= 1
        assert 0 <= result.overall_precision <= 1
        assert 0 <= result.overall_recall <= 1
        assert 0 <= result.overall_f1 <= 1
        assert 0 <= result.avg_truth_score_clean <= 100
        assert 0 <= result.avg_truth_score_biased <= 100

    def test_clean_scores_higher_than_biased(self):
        """Clean samples should score higher than biased samples."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        assert result.avg_truth_score_clean > result.avg_truth_score_biased
        assert result.truth_score_separation > 0

    def test_report_format(self):
        """format_report should return a non-empty string."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        report = format_report(result)
        assert "BIASCLEAR CALIBRATION REPORT" in report
        assert "OVERALL METRICS" in report
        assert "TRUTH SCORE ANALYSIS" in report

    def test_save_report(self, tmp_path):
        """save_report should create both txt and json files."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        txt_path, json_path = save_report(result, tmp_path)
        assert txt_path.exists()
        assert json_path.exists()
        # JSON should be valid
        data = json.loads(json_path.read_text())
        assert "overall" in data
        assert "per_pattern" in data
        assert "truth_score" in data

    def test_pattern_metrics_math(self):
        """Verify precision/recall/F1 calculations."""
        m = PatternMetrics(
            pattern_id="TEST",
            human_tag="test",
            true_positives=8,
            false_positives=2,
            false_negatives=2,
            true_negatives=88,
        )
        assert m.precision == pytest.approx(0.8, abs=0.01)
        assert m.recall == pytest.approx(0.8, abs=0.01)
        assert m.f1 == pytest.approx(0.8, abs=0.01)
        assert m.support == 10

    def test_pattern_metrics_edge_case_zero(self):
        """Zero values should return 0, not division error."""
        m = PatternMetrics(pattern_id="TEST", human_tag="test")
        assert m.precision == 0.0
        assert m.recall == 0.0
        assert m.f1 == 0.0
        assert m.support == 0

    def test_empty_corpus_raises(self, tmp_path):
        """Should raise on empty corpus."""
        (tmp_path / "empty.txt").write_text("# empty\n")
        with pytest.raises(ValueError, match="No samples found"):
            run_benchmark(corpus_dir=tmp_path)


# ============================================================
# Weight Optimizer Tests
# ============================================================

class TestOptimizer:

    def test_optimizer_runs(self):
        """Optimizer should produce a report on seed data."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        opt = optimize_weights(result)
        assert opt.current_separation > 0
        assert isinstance(opt.recommendations, list)
        assert len(opt.summary) > 0

    def test_optimizer_report_format(self):
        """format_optimization_report should return non-empty string."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        opt = optimize_weights(result)
        text = format_optimization_report(opt)
        assert "WEIGHT OPTIMIZATION REPORT" in text

    def test_optimizer_detects_biased_avg_too_high(self):
        """When biased avg > 60, optimizer should recommend penalties."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        # Seed data biased avg is ~75 (above 60 target)
        if result.avg_truth_score_biased > 60:
            opt = optimize_weights(result)
            penalty_recs = [
                r for r in opt.recommendations
                if "penalty" in r.parameter or "sensitivity" in r.parameter
            ]
            assert len(penalty_recs) > 0, "Should recommend penalty increases"

    def test_optimizer_no_recs_when_perfect(self):
        """If metrics are perfect, no recommendations."""
        # Create a fake perfect result
        perfect = BenchmarkResult(
            total_samples=10,
            clean_samples=5,
            biased_samples=5,
            pattern_metrics={},
            overall_accuracy=1.0,
            overall_precision=1.0,
            overall_recall=1.0,
            overall_f1=1.0,
            avg_truth_score_clean=95.0,
            avg_truth_score_biased=40.0,
            truth_score_separation=55.0,
            false_positives=[],
            false_negatives=[],
            truth_score_pairs=[],
        )
        opt = optimize_weights(perfect)
        assert len(opt.recommendations) == 0


# ============================================================
# Integration Tests
# ============================================================

class TestCalibrationIntegration:

    def test_full_pipeline(self, tmp_path):
        """Full pipeline: parse → benchmark → optimize → report."""
        # Create a mini corpus
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "test.txt").write_text(textwrap.dedent("""\
            ---
            tags: clean
            severity: none
            source: integration test

            The court held in Smith v. Jones, 123 F.3d 456 (2020)
            that the statute applies to these facts.

            ---
            tags: settled_law_dismissal
            severity: high
            source: integration test

            It is well-settled law that these claims are without merit
            and should be summarily rejected.

            ---
        """))

        # Run full pipeline
        result = run_benchmark(corpus_dir=corpus_dir, domain="legal")
        assert result.total_samples == 2
        assert result.clean_samples == 1
        assert result.biased_samples == 1

        # Save report
        report_dir = tmp_path / "reports"
        txt_path, json_path = save_report(result, report_dir)
        assert txt_path.exists()

        # Run optimizer
        opt = optimize_weights(result)
        assert isinstance(opt.summary, str)

    def test_seed_corpus_f1_baseline(self):
        """Seed corpus should achieve F1 > 0.90 as a regression guard."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        assert result.overall_f1 > 0.90, (
            f"F1 regression: {result.overall_f1:.2%} (expected > 90%)"
        )

    def test_seed_corpus_clean_separation(self):
        """Clean samples should score meaningfully higher than biased."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        assert result.truth_score_separation > 25, (
            f"Separation regression: {result.truth_score_separation:.0f} "
            f"(expected > 25 points)"
        )

    def test_seed_corpus_no_clean_false_positives(self):
        """Clean samples should have zero structural false positives."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        clean_fps = [fp for fp in result.false_positives if fp.get("source", "").startswith("synthetic")]
        assert result.avg_truth_score_clean >= 95, (
            f"Clean avg {result.avg_truth_score_clean:.0f} suggests FP problem "
            f"(expected >= 95)"
        )

    def test_seed_corpus_biased_avg_below_threshold(self):
        """Biased samples should average below 70 Truth Score."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        assert result.avg_truth_score_biased <= 70, (
            f"Biased avg {result.avg_truth_score_biased:.0f} too high "
            f"(expected <= 70)"
        )

    def test_seed_corpus_100_percent_recall(self):
        """All 14 patterns with labeled samples should achieve 100% recall."""
        result = run_benchmark(corpus_dir=SEED_CORPUS, domain="legal")
        for pid, m in result.pattern_metrics.items():
            if m.support > 0:
                assert m.recall == 1.0, (
                    f"Pattern {m.human_tag} has {m.recall:.0%} recall "
                    f"({m.false_negatives} misses). Expected 100%."
                )


class TestScorerCalibration:
    """Tests for the Truth Score calculator."""

    def test_clean_text_scores_100(self):
        """Text with no flags should score 100."""
        eval_result = frozen_core.evaluate(
            "The court entered judgment on March 15, 2024. See Dkt. 45.",
            domain="legal",
        )
        score, _ = calculate_truth_score(eval_result)
        assert score == 100

    def test_single_moderate_flag_scores_below_80(self):
        """A single moderate structural flag should push score below 80."""
        eval_result = frozen_core.evaluate(
            "We face a simple choice: either accept or face ruin. "
            "There is no middle ground.",
            domain="legal",
        )
        score, _ = calculate_truth_score(eval_result)
        assert score < 80, f"Single moderate flag scored {score} (expected < 80)"

    def test_multi_flag_scores_below_50(self):
        """Multi-flag stacked samples should score well below 50."""
        eval_result = frozen_core.evaluate(
            "It is well-settled law that this claim is frivolous. "
            "Filing sanctions should be considered for this vexatious "
            "litigation. The weight of authority is overwhelming.",
            domain="legal",
        )
        score, _ = calculate_truth_score(eval_result)
        assert score < 50, f"Multi-flag stacked scored {score} (expected < 50)"

    def test_multi_tier_penalty_applies(self):
        """Flags spanning multiple PIT tiers should get extra penalty."""
        # Tier 1 only (consensus)
        eval_t1 = frozen_core.evaluate(
            "Everyone agrees this is correct. The consensus is clear.",
            domain="general",
        )
        score_t1, _ = calculate_truth_score(eval_t1)

        # Tier 1 + Tier 2 (consensus + fear)
        eval_multi = frozen_core.evaluate(
            "Everyone agrees this is correct. If we do not act "
            "immediately, the consequences will be catastrophic.",
            domain="general",
        )
        score_multi, _ = calculate_truth_score(eval_multi)

        # Multi-tier should score lower than single-tier (beyond just the extra flag penalty)
        assert score_multi < score_t1, (
            f"Multi-tier {score_multi} should be < single-tier {score_t1}"
        )


class TestCitationSuppression:
    """Tests for the citation suppression bug fix (case sensitivity)."""

    def test_structural_pattern_suppressed_with_report_citation(self):
        """CLAIM_WITHOUT_CITATION should be suppressed near Report No. citations."""
        eval_result = frozen_core.evaluate(
            "Research indicates that recidivism drops 18-24% "
            "(Nat'l Inst. of Justice, Report No. 2023-47, at 15).",
            domain="legal",
        )
        structural_flags = [f for f in eval_result.flags if f.category == "structural"]
        assert len(structural_flags) == 0, (
            f"Structural flags should be suppressed near citation: "
            f"{[f.pattern_id for f in structural_flags]}"
        )

    def test_structural_pattern_fires_without_citation(self):
        """CLAIM_WITHOUT_CITATION should fire when no citation is present."""
        eval_result = frozen_core.evaluate(
            "Research indicates that the approach is fundamentally flawed. "
            "Experts say we need a paradigm shift.",
            domain="legal",
        )
        structural_ids = [f.pattern_id for f in eval_result.flags if f.category == "structural"]
        assert "CLAIM_WITHOUT_CITATION" in structural_ids

    def test_id_citation_suppresses_nearby_markers(self):
        """Id. legal citation should suppress nearby keyword markers."""
        eval_result = frozen_core.evaluate(
            "The data suggests compliance rates peak within 90 days "
            "(Id. at 22-23).",
            domain="legal",
        )
        marker_flags = [f for f in eval_result.flags if f.category == "marker"]
        assert len(marker_flags) == 0, (
            f"Markers should be suppressed near Id. citation: "
            f"{[f.pattern_id for f in marker_flags]}"
        )
