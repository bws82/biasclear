"""
Tests for Phase 1B features:
- Context-aware citation suppression
- Learning ring governance lifecycle
- Pattern proposer validation logic
"""

import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock

from biasclear.frozen_core import frozen_core


# ============================================================
# CITATION SUPPRESSION
# ============================================================

class TestCitationSuppression:
    """Markers near legitimate citations should be suppressed."""

    def test_parenthetical_citation_suppresses(self):
        """'Studies show (Smith et al., 2024)...' should NOT flag."""
        result = frozen_core.evaluate(
            "Studies show (Smith et al., 2024) that sleep improves cognitive performance."
        )
        markers = [f for f in result.flags if f.category == "marker"]
        assert len(markers) == 0

    def test_no_citation_still_flags(self):
        """'Studies show that...' with no citation SHOULD flag."""
        result = frozen_core.evaluate(
            "Studies show that sleep improves cognitive performance."
        )
        markers = [f for f in result.flags if f.category == "marker"]
        assert len(markers) > 0

    def test_legal_citation_suppresses(self):
        """Markers near case law citations should be suppressed."""
        result = frozen_core.evaluate(
            "Research indicates, per Johnson v. Smith, that the standard applies."
        )
        markers = [f for f in result.flags if f.category == "marker"]
        assert len(markers) == 0

    def test_bracket_citation_suppresses(self):
        """Markers near [1] style citations should be suppressed."""
        result = frozen_core.evaluate(
            "The data suggests [14] a strong correlation between variables."
        )
        markers = [f for f in result.flags if f.category == "marker"]
        assert len(markers) == 0

    def test_table_reference_suppresses(self):
        """Markers near 'Table 3, p. 47' should be suppressed."""
        result = frozen_core.evaluate(
            "The data suggests a correlation (see Table 3, p. 47) between the two variables."
        )
        markers = [f for f in result.flags if f.category == "marker"]
        assert len(markers) == 0

    def test_multiple_markers_partial_suppression(self):
        """Only markers with nearby citations are suppressed; others still flag."""
        # The two sections are separated by enough text to exceed the 120-char window
        result = frozen_core.evaluate(
            "Studies show (Smith, 2024) that cognitive load increases error rates "
            "in standardized testing environments across multiple demographics and "
            "age groups in longitudinal research designs. "
            "In a completely unrelated matter, experts say the consensus is that "
            "everyone agrees this policy is undeniably correct."
        )
        markers = [f for f in result.flags if f.category == "marker"]
        # "studies show" suppressed (has citation within window)
        suppressed = [m for m in markers if "studies show" in m.matched_text]
        assert len(suppressed) == 0
        # "experts say", "the consensus is", "everyone agrees", "undeniably"
        # should still flag (far from any citation)
        assert len(markers) >= 2

    def test_structural_patterns_unaffected(self):
        """Citation suppression only applies to keyword markers, not structural patterns."""
        result = frozen_core.evaluate(
            "That theory has been thoroughly debunked (see Jones, 2023)."
        )
        structural = [f for f in result.flags if f.category == "structural"]
        # DISSENT_DISMISSAL should still fire even with a citation nearby
        # because "debunked" is a structural pattern, not a keyword marker
        assert any(f.pattern_id == "DISSENT_DISMISSAL" for f in structural)


# ============================================================
# LEARNING RING
# ============================================================

class TestLearningRing:
    """Test the governed pattern lifecycle."""

    @pytest.fixture
    def ring(self):
        """Create a fresh learning ring with temp database."""
        from biasclear.patterns.learned import LearningRing
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        ring = LearningRing(
            db_path=path,
            activation_threshold=3,  # Lower threshold for testing
            fp_limit=0.20,
        )
        yield ring
        os.unlink(path)

    def test_propose_new_pattern(self, ring):
        """Proposing a new pattern should stage it with 1 confirmation."""
        result = ring.propose(
            pattern_id="TEST_PATTERN",
            name="Test Pattern",
            description="A test pattern for unit testing.",
            pit_tier=1,
            severity="moderate",
            principle="Truth",
            regex=r"\btest\s+distortion\b",
            source_scan_hash="abc123",
        )
        assert result["accepted"] is True
        assert result["action"] == "proposed"
        assert result["confirmations"] == 1

    def test_confirm_increments(self, ring):
        """Proposing the same pattern again increments confirmations."""
        ring.propose(
            pattern_id="TEST_PATTERN", name="Test", description="Test",
            pit_tier=1, severity="moderate", principle="Truth",
            regex=r"\btest\b", source_scan_hash="scan1",
        )
        result = ring.propose(
            pattern_id="TEST_PATTERN", name="Test", description="Test",
            pit_tier=1, severity="moderate", principle="Truth",
            regex=r"\btest\b", source_scan_hash="scan2",
        )
        assert result["action"] == "confirmed"
        assert result["confirmations"] == 2

    def test_auto_activate_at_threshold(self, ring):
        """Pattern should auto-activate at the confirmation threshold."""
        for i in range(3):  # threshold is 3 in this fixture
            result = ring.propose(
                pattern_id="TEST_ACTIVATE", name="Test", description="Test",
                pit_tier=2, severity="high", principle="Agency",
                regex=r"\bactivation\s+test\b", source_scan_hash=f"scan{i}",
            )
        assert result["action"] == "activated"
        assert result["pattern_id"] == "TEST_ACTIVATE"

    def test_active_patterns_returned_as_structural(self, ring):
        """Active patterns should be compatible with frozen core evaluation."""
        # Activate a pattern
        for i in range(3):
            ring.propose(
                pattern_id="TEST_STRUCTURAL", name="Test Structural",
                description="Detects 'absolutely certain without doubt'",
                pit_tier=1, severity="moderate", principle="Truth",
                regex=r"\babsolutely\s+certain\s+without\s+doubt\b",
                source_scan_hash=f"scan{i}",
            )
        active = ring.get_active_patterns()
        assert len(active) == 1
        assert active[0].id == "TEST_STRUCTURAL"
        assert active[0].pit_tier == 1

        # Use with frozen core
        result = frozen_core.evaluate(
            "It is absolutely certain without doubt that this is correct.",
            external_patterns=active,
        )
        learned_flags = [f for f in result.flags if f.pattern_id == "TEST_STRUCTURAL"]
        assert len(learned_flags) == 1

    def test_reject_invalid_pit_tier(self, ring):
        """Patterns with invalid PIT tiers should be rejected."""
        result = ring.propose(
            pattern_id="BAD_TIER", name="Bad", description="Bad",
            pit_tier=99, severity="low", principle="Truth",
            regex=r"\bbad\b", source_scan_hash="scan1",
        )
        assert result["accepted"] is False
        assert "does not exist" in result["reason"]

    def test_false_positive_deactivation(self, ring):
        """Pattern should auto-deactivate if FP rate exceeds limit."""
        # Activate a pattern
        for i in range(3):
            ring.propose(
                pattern_id="FP_TEST", name="FP Test", description="Test",
                pit_tier=1, severity="low", principle="Truth",
                regex=r"\bfp\s+test\b", source_scan_hash=f"scan{i}",
            )

        # Record evaluations and false positives
        for _ in range(10):
            ring.record_evaluation("FP_TEST")
        # 3 FPs out of 10 = 30%, exceeds 20% limit
        ring.report_false_positive("FP_TEST")
        ring.report_false_positive("FP_TEST")
        result = ring.report_false_positive("FP_TEST")

        assert result["action"] == "deactivated"

        # Should no longer appear in active patterns
        active = ring.get_active_patterns()
        assert not any(p.id == "FP_TEST" for p in active)

    def test_audit_logger_called(self, ring):
        """Audit logger should be called on state transitions."""
        logged = []
        ring.set_audit_logger(lambda etype, data: logged.append(etype))

        ring.propose(
            pattern_id="AUDIT_TEST", name="Audit", description="Test",
            pit_tier=1, severity="low", principle="Truth",
            regex=r"\baudit\b", source_scan_hash="scan1",
        )
        assert "pattern_proposed" in logged

    def test_get_all_patterns(self, ring):
        """get_all_patterns should return metadata for all patterns."""
        ring.propose(
            pattern_id="META_TEST", name="Meta", description="Test metadata",
            pit_tier=2, severity="high", principle="Clarity",
            regex=r"\bmeta\b", source_scan_hash="scan1",
        )
        patterns = ring.get_all_patterns()
        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] == "META_TEST"
        assert patterns[0]["status"] == "staging"
        assert patterns[0]["pit_tier"] == 2


# ============================================================
# PATTERN PROPOSER — VALIDATION LOGIC
# ============================================================

class TestPatternProposer:
    """Test the proposer's validation and filtering logic."""

    @pytest.fixture
    def proposer(self):
        from biasclear.patterns.proposer import PatternProposer
        mock_ring = MagicMock()
        mock_ring.propose.return_value = {"accepted": True, "action": "proposed"}
        return PatternProposer(mock_ring), mock_ring

    def test_validate_regex_valid(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        assert p._validate_regex(r"\btest\s+pattern\b") is True

    def test_validate_regex_invalid(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        assert p._validate_regex(r"[invalid") is False

    def test_validate_regex_too_broad(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        # Matches everything — should be rejected
        assert p._validate_regex(r".*") is False

    def test_validate_regex_too_short(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        assert p._validate_regex(r"\b") is False

    def test_validate_regex_too_long(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        assert p._validate_regex("a" * 1001) is False

    def test_parse_tier_valid(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        assert p._parse_tier("tier_1_ideological") == 1
        assert p._parse_tier("tier_2_psychological") == 2
        assert p._parse_tier("tier_3_institutional") == 3

    def test_parse_tier_invalid(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        assert p._parse_tier("none") is None
        assert p._parse_tier("tier_99_fake") is None
        assert p._parse_tier("garbage") is None

    def test_generate_pattern_id_deterministic(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        id1 = p._generate_pattern_id("TEST_ID", r"\btest\b")
        id2 = p._generate_pattern_id("TEST_ID", r"\btest\b")
        assert id1 == id2  # Same inputs → same ID

    def test_generate_pattern_id_different_regex(self):
        from biasclear.patterns.proposer import PatternProposer
        p = PatternProposer(MagicMock())
        id1 = p._generate_pattern_id("TEST_ID", r"\btest\b")
        id2 = p._generate_pattern_id("TEST_ID", r"\bother\b")
        assert id1 != id2  # Different regex → different ID

    @pytest.mark.asyncio
    async def test_skip_no_bias(self, proposer):
        """Should skip if deep analysis found no bias."""
        p, ring = proposer
        results = await p.extract_and_propose(
            text="clean text",
            local_flags=[],
            deep_result={"bias_detected": False},
            llm=AsyncMock(),
            scan_audit_hash="hash1",
        )
        assert results == []
        ring.propose.assert_not_called()

    @pytest.mark.asyncio
    async def test_skip_low_severity(self, proposer):
        """Should skip if deep severity is low."""
        p, ring = proposer
        results = await p.extract_and_propose(
            text="mild text",
            local_flags=[],
            deep_result={"bias_detected": True, "severity": "low", "bias_types": ["framing_bias"]},
            llm=AsyncMock(),
            scan_audit_hash="hash1",
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_skip_local_already_caught(self, proposer):
        """Should skip if local already caught 3+ flags."""
        p, ring = proposer
        results = await p.extract_and_propose(
            text="flagged text",
            local_flags=[
                {"pattern_id": "A"}, {"pattern_id": "B"}, {"pattern_id": "C"}
            ],
            deep_result={
                "bias_detected": True, "severity": "high",
                "bias_types": ["authority_bias"], "pit_tier": "tier_1_ideological",
            },
            llm=AsyncMock(),
            scan_audit_hash="hash1",
        )
        assert results == []
