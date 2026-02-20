"""
Corrector Tests — Full Coverage

Tests the corrector module:
  1. Threshold gate (_should_correct)
  2. Flag instruction builder (_build_flag_instructions)
  3. Post-correction verification (_verify_correction)
  4. Diff span computation (_compute_diff_spans)
  5. Full correct_bias flow (threshold path + mocked LLM path)
"""

from __future__ import annotations

import pytest

from biasclear.corrector import (
    _should_correct,
    _build_flag_instructions,
    _verify_correction,
    _compute_diff_spans,
    correct_bias,
    _PATTERN_LOOKUP,
)
from biasclear.llm import LLMProvider


# ============================================================
# MOCK LLM
# ============================================================

class MockLLM(LLMProvider):
    """Mock LLM that returns a pre-configured correction response."""

    def __init__(self, corrected_text: str = "Corrected text.", confidence: float = 0.9):
        self._corrected = corrected_text
        self._confidence = confidence
        self.calls = []

    async def generate(self, prompt, system_instruction=None, temperature=0.7, json_mode=False):
        self.calls.append(prompt)
        import json
        return json.dumps({
            "corrected": self._corrected,
            "changes_made": ["Removed bias framing"],
            "bias_removed": ["CONSENSUS_AS_EVIDENCE"],
            "confidence": self._confidence,
        })


# ============================================================
# THRESHOLD GATE
# ============================================================

class TestThresholdGate:
    """Verify _should_correct only triggers on real bias."""

    def test_clean_text_no_correction(self):
        """Score 100 + no flags = no correction."""
        assert _should_correct({
            "truth_score": 100,
            "flags": [],
        }) is False

    def test_high_score_no_structural_flags(self):
        """Score 90 + keyword-only flags = no correction."""
        assert _should_correct({
            "truth_score": 90,
            "flags": [
                {"category": "marker", "severity": "low"},
            ],
        }) is False

    def test_low_score_triggers(self):
        """Score <= 80 always triggers correction."""
        assert _should_correct({
            "truth_score": 80,
            "flags": [],
        }) is True

    def test_very_low_score_triggers(self):
        assert _should_correct({
            "truth_score": 41,
            "flags": [],
        }) is True

    def test_structural_moderate_triggers(self):
        """Structural flag with severity >= moderate triggers."""
        assert _should_correct({
            "truth_score": 95,
            "flags": [
                {"category": "structural", "severity": "moderate"},
            ],
        }) is True

    def test_structural_high_triggers(self):
        assert _should_correct({
            "truth_score": 95,
            "flags": [
                {"category": "structural", "severity": "high"},
            ],
        }) is True

    def test_structural_critical_triggers(self):
        assert _should_correct({
            "truth_score": 95,
            "flags": [
                {"category": "structural", "severity": "critical"},
            ],
        }) is True

    def test_structural_low_no_trigger(self):
        """Structural flag with severity 'low' alone doesn't trigger if score is high."""
        assert _should_correct({
            "truth_score": 95,
            "flags": [
                {"category": "structural", "severity": "low"},
            ],
        }) is False

    def test_boundary_score_81_no_trigger(self):
        """Score of 81 with no structural flags = no correction."""
        assert _should_correct({
            "truth_score": 81,
            "flags": [],
        }) is False


# ============================================================
# FLAG INSTRUCTIONS
# ============================================================

class TestFlagInstructions:
    """Verify _build_flag_instructions builds correct LLM guidance."""

    def test_no_structural_flags(self):
        result = _build_flag_instructions({
            "flags": [
                {"category": "marker", "pattern_id": "KW_TEST", "matched_text": "test"},
            ],
        })
        assert "No specific structural" in result

    def test_known_pattern_includes_description(self):
        result = _build_flag_instructions({
            "flags": [
                {
                    "category": "structural",
                    "pattern_id": "CONSENSUS_AS_EVIDENCE",
                    "matched_text": "All experts agree",
                    "severity": "high",
                },
            ],
        })
        assert "CONSENSUS_AS_EVIDENCE" in result
        assert "All experts agree" in result
        assert "high" in result

    def test_multiple_flags_numbered(self):
        result = _build_flag_instructions({
            "flags": [
                {
                    "category": "structural",
                    "pattern_id": "CONSENSUS_AS_EVIDENCE",
                    "matched_text": "experts agree",
                    "severity": "high",
                },
                {
                    "category": "structural",
                    "pattern_id": "DISSENT_DISMISSAL",
                    "matched_text": "debunked",
                    "severity": "high",
                },
            ],
        })
        assert "1." in result
        assert "2." in result

    def test_ai_flags_included(self):
        result = _build_flag_instructions({
            "flags": [
                {
                    "category": "structural",
                    "pattern_id": "CONSENSUS_AS_EVIDENCE",
                    "matched_text": "experts agree",
                    "severity": "high",
                },
                {
                    "source": "ai",
                    "pattern_id": "AI_DETECTED_PATTERN",
                    "matched_text": "some AI finding",
                    "severity": "moderate",
                    "description": "AI-detected bias pattern",
                },
            ],
        })
        assert "AI_DETECTED_PATTERN" in result
        assert "source: AI" in result

    def test_empty_flags(self):
        result = _build_flag_instructions({"flags": []})
        assert "No specific structural" in result


# ============================================================
# POST-CORRECTION VERIFICATION
# ============================================================

class TestVerification:
    """Verify _verify_correction re-scans through frozen core."""

    def test_clean_text_verifies(self):
        result = _verify_correction(
            "The court held in Smith v. Jones that the statute applies.",
            domain="legal",
        )
        assert result["truth_score_after"] >= 80
        assert result["aligned"] is True
        assert isinstance(result["flags_remaining"], int)

    def test_biased_text_fails_verification(self):
        result = _verify_correction(
            "All experts agree this is plainly frivolous and well-settled.",
            domain="legal",
        )
        assert result["truth_score_after"] < 80
        assert len(result["structural_remaining"]) > 0

    def test_general_domain(self):
        result = _verify_correction(
            "This is a neutral factual statement.",
            domain="general",
        )
        assert result["truth_score_after"] == 100
        assert result["flags_remaining"] == 0


# ============================================================
# DIFF SPANS
# ============================================================

class TestDiffSpans:
    """Verify _compute_diff_spans produces correct diffs."""

    def test_identical_text(self):
        spans = _compute_diff_spans("hello world", "hello world")
        assert len(spans) == 1
        assert spans[0]["type"] == "equal"

    def test_deletion(self):
        spans = _compute_diff_spans("hello cruel world", "hello world")
        types = [s["type"] for s in spans]
        assert "delete" in types
        assert "equal" in types

    def test_insertion(self):
        spans = _compute_diff_spans("hello world", "hello beautiful world")
        types = [s["type"] for s in spans]
        assert "insert" in types

    def test_replacement(self):
        spans = _compute_diff_spans(
            "All experts agree this is true.",
            "The evidence suggests this may be true.",
        )
        assert len(spans) > 1  # Not identical

    def test_positions_are_consistent(self):
        original = "The quick brown fox"
        corrected = "A quick red fox"
        spans = _compute_diff_spans(original, corrected)
        for span in spans:
            if span["type"] == "equal":
                assert span["orig_start"] < span["orig_end"]
                assert span["corr_start"] < span["corr_end"]
            elif span["type"] == "delete":
                assert span["orig_start"] < span["orig_end"]
                assert "corr_start" not in span
            elif span["type"] == "insert":
                assert span["corr_start"] < span["corr_end"]
                assert "orig_start" not in span

    def test_empty_strings(self):
        spans = _compute_diff_spans("", "")
        assert spans == []


# ============================================================
# PATTERN LOOKUP
# ============================================================

class TestPatternLookup:
    """Verify the pattern lookup table is populated correctly."""

    def test_lookup_has_core_patterns(self):
        assert "CONSENSUS_AS_EVIDENCE" in _PATTERN_LOOKUP
        assert "DISSENT_DISMISSAL" in _PATTERN_LOOKUP
        assert "FALSE_BINARY" in _PATTERN_LOOKUP

    def test_lookup_has_legal_patterns(self):
        assert "LEGAL_SETTLED_DISMISSAL" in _PATTERN_LOOKUP
        assert "LEGAL_MERIT_DISMISSAL" in _PATTERN_LOOKUP

    def test_lookup_has_media_patterns(self):
        assert "MEDIA_EDITORIAL_AS_NEWS" in _PATTERN_LOOKUP

    def test_lookup_has_financial_patterns(self):
        assert "FINANCIAL_SURVIVORSHIP" in _PATTERN_LOOKUP or len(_PATTERN_LOOKUP) > 20


# ============================================================
# FULL CORRECT_BIAS FLOW
# ============================================================

class TestCorrectBias:
    """Integration tests for correct_bias — the full pipeline."""

    @pytest.mark.asyncio
    async def test_no_bias_returns_passthrough(self):
        """No bias detected = no correction, passthrough."""
        llm = MockLLM()
        result = await correct_bias(
            text="The court ruled on the merits.",
            scan_result={"truth_score": 100, "bias_detected": False, "flags": []},
            llm=llm,
        )
        assert result["correction_triggered"] is False
        assert result["original"] == result["corrected"]
        assert result["confidence"] == 1.0
        assert len(llm.calls) == 0  # No LLM call made

    @pytest.mark.asyncio
    async def test_below_threshold_no_correction(self):
        """High score + only keyword markers = no correction."""
        llm = MockLLM()
        result = await correct_bias(
            text="Some text with minor issues.",
            scan_result={
                "truth_score": 95,
                "bias_detected": True,
                "flags": [
                    {"category": "marker", "severity": "low", "pattern_id": "KW_TEST"},
                ],
            },
            llm=llm,
        )
        assert result["correction_triggered"] is False
        assert len(llm.calls) == 0

    @pytest.mark.asyncio
    async def test_above_threshold_calls_llm(self):
        """Low score triggers LLM correction."""
        corrected = "The evidence suggests this conclusion."
        llm = MockLLM(corrected_text=corrected)
        result = await correct_bias(
            text="All experts agree this is true.",
            scan_result={
                "truth_score": 41,
                "bias_detected": True,
                "flags": [
                    {
                        "category": "structural",
                        "pattern_id": "CONSENSUS_AS_EVIDENCE",
                        "matched_text": "All experts agree",
                        "severity": "high",
                    },
                ],
            },
            llm=llm,
        )
        assert result["correction_triggered"] is True
        assert result["original"] == "All experts agree this is true."
        assert result["corrected"] == corrected
        assert len(llm.calls) >= 1
        assert "diff_spans" in result
        assert "verification" in result

    @pytest.mark.asyncio
    async def test_structural_flag_triggers_even_with_high_score(self):
        """Structural moderate flag at high score still triggers."""
        llm = MockLLM(corrected_text="Corrected.")
        result = await correct_bias(
            text="All experts agree.",
            scan_result={
                "truth_score": 95,
                "bias_detected": True,
                "flags": [
                    {
                        "category": "structural",
                        "pattern_id": "CONSENSUS_AS_EVIDENCE",
                        "matched_text": "All experts agree",
                        "severity": "moderate",
                    },
                ],
            },
            llm=llm,
        )
        assert result["correction_triggered"] is True
        assert len(llm.calls) >= 1

    @pytest.mark.asyncio
    async def test_domain_passed_to_verification(self):
        """Domain is forwarded to post-correction verification."""
        llm = MockLLM(corrected_text="The statute applies.")
        result = await correct_bias(
            text="Well-settled law proves this.",
            scan_result={
                "truth_score": 50,
                "bias_detected": True,
                "flags": [
                    {
                        "category": "structural",
                        "pattern_id": "LEGAL_SETTLED_DISMISSAL",
                        "matched_text": "Well-settled law",
                        "severity": "high",
                    },
                ],
            },
            llm=llm,
            domain="legal",
        )
        assert result["correction_triggered"] is True
        assert "verification" in result

    @pytest.mark.asyncio
    async def test_llm_error_returns_graceful_fallback(self):
        """LLM failure returns original text with error field."""

        class FailingLLM(LLMProvider):
            async def generate(self, prompt, **kwargs):
                raise RuntimeError("LLM is down")

        result = await correct_bias(
            text="All experts agree.",
            scan_result={
                "truth_score": 30,
                "bias_detected": True,
                "flags": [
                    {
                        "category": "structural",
                        "pattern_id": "CONSENSUS_AS_EVIDENCE",
                        "matched_text": "All experts agree",
                        "severity": "high",
                    },
                ],
            },
            llm=FailingLLM(),
        )
        assert result["corrected"] == "All experts agree."
        assert result["error"] is not None
        assert result["confidence"] == 0.0
        assert result["correction_triggered"] is True

    @pytest.mark.asyncio
    async def test_result_has_iteration_metadata(self):
        """Successful correction includes iteration tracking."""
        llm = MockLLM(corrected_text="Clean text.")
        result = await correct_bias(
            text="All experts agree this is settled.",
            scan_result={
                "truth_score": 41,
                "bias_detected": True,
                "flags": [
                    {
                        "category": "structural",
                        "pattern_id": "CONSENSUS_AS_EVIDENCE",
                        "matched_text": "All experts agree",
                        "severity": "high",
                    },
                ],
            },
            llm=llm,
        )
        assert "iteration_count" in result
        assert "iterations" in result
        assert "converged" in result
        assert result["iteration_count"] >= 1
