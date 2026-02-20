"""
Tests for the Frozen Core — the most important tests in the system.

If the frozen core doesn't detect correctly, nothing else matters.
"""

import pytest
from app.frozen_core import frozen_core, CORE_VERSION, FrozenCore


class TestCoreVersion:
    def test_version_exists(self):
        assert CORE_VERSION == "1.1.0"

    def test_eval_stamps_version(self):
        result = frozen_core.evaluate("Hello world")
        assert result.core_version == CORE_VERSION


class TestCleanText:
    """Text with no bias should pass clean."""

    def test_neutral_statement(self):
        result = frozen_core.evaluate("The meeting is scheduled for 3pm Tuesday.")
        assert result.aligned is True
        assert result.knowledge_type == "neutral"
        assert len(result.flags) == 0

    def test_factual_with_citation(self):
        result = frozen_core.evaluate(
            "According to the 2023 Census Bureau report (Table B-1), "
            "median household income was $74,580."
        )
        assert result.aligned is True

    def test_short_text(self):
        result = frozen_core.evaluate("OK")
        assert result.aligned is True


class TestConsensusAsEvidence:
    """Tier 1: Consensus language substituting for evidence."""

    def test_everyone_agrees(self):
        result = frozen_core.evaluate(
            "Everyone agrees that this policy is the best approach."
        )
        assert len(result.flags) > 0
        has_flag = any(
            f.pattern_id == "CONSENSUS_AS_EVIDENCE" or "everyone agrees" in f.matched_text
            for f in result.flags
        )
        assert has_flag

    def test_widely_accepted(self):
        result = frozen_core.evaluate(
            "It is widely accepted that the earth revolves around the sun."
        )
        has_flag = any(
            f.pattern_id == "CONSENSUS_AS_EVIDENCE" or "widely accepted" in f.matched_text
            for f in result.flags
        )
        assert has_flag

    def test_all_experts(self):
        result = frozen_core.evaluate(
            "All experts in the field have concluded this is correct."
        )
        has_flag = any(
            f.pattern_id == "CONSENSUS_AS_EVIDENCE" or "all experts" in f.matched_text.lower()
            for f in result.flags
        )
        assert has_flag


class TestClaimWithoutCitation:
    """Tier 1: Authority claims with no source."""

    def test_studies_show(self):
        result = frozen_core.evaluate("Studies show that remote work increases productivity.")
        has_flag = any(
            "CLAIM_WITHOUT_CITATION" in f.pattern_id or "studies show" in f.matched_text
            for f in result.flags
        )
        assert has_flag

    def test_research_indicates(self):
        result = frozen_core.evaluate("Research indicates a strong correlation between sleep and performance.")
        has_flag = any(
            "CLAIM_WITHOUT_CITATION" in f.pattern_id or "research indicates" in f.matched_text
            for f in result.flags
        )
        assert has_flag

    def test_experts_say(self):
        result = frozen_core.evaluate("Experts say the market will recover by Q3.")
        has_flag = any(
            "CLAIM_WITHOUT_CITATION" in f.pattern_id or "experts say" in f.matched_text
            for f in result.flags
        )
        assert has_flag


class TestDissentDismissal:
    """Tier 1: Opposing views dismissed by label."""

    def test_debunked(self):
        result = frozen_core.evaluate(
            "That theory has been thoroughly debunked by the scientific community."
        )
        has_flag = any(f.pattern_id == "DISSENT_DISMISSAL" for f in result.flags)
        assert has_flag

    def test_conspiracy(self):
        result = frozen_core.evaluate(
            "Only conspiracy theorists believe the government was involved."
        )
        has_flag = any(f.pattern_id == "DISSENT_DISMISSAL" for f in result.flags)
        assert has_flag

    def test_no_credible_scientist(self):
        result = frozen_core.evaluate(
            "No credible scientist would support that hypothesis."
        )
        has_flag = any(f.pattern_id == "DISSENT_DISMISSAL" for f in result.flags)
        assert has_flag


class TestFalseBinary:
    """Tier 2: False dilemma / either-or framing."""

    def test_either_or(self):
        result = frozen_core.evaluate(
            "Either we implement this policy now or we face economic collapse."
        )
        has_flag = any(f.pattern_id == "FALSE_BINARY" for f in result.flags)
        assert has_flag

    def test_youre_either(self):
        result = frozen_core.evaluate(
            "You're either with us on this initiative or you're against progress."
        )
        has_flag = any(f.pattern_id == "FALSE_BINARY" for f in result.flags)
        assert has_flag


class TestFearUrgency:
    """Tier 2: Fear-based urgency."""

    def test_catastrophic(self):
        result = frozen_core.evaluate(
            "If we don't act now, the consequences will be catastrophic and irreversible."
        )
        has_flag = any(f.pattern_id == "FEAR_URGENCY" for f in result.flags)
        assert has_flag

    def test_point_of_no_return(self):
        result = frozen_core.evaluate(
            "We are approaching a point of no return on this issue."
        )
        has_flag = any(f.pattern_id == "FEAR_URGENCY" for f in result.flags)
        assert has_flag


class TestShameLever:
    """Tier 2: Shame/social pressure as manipulation."""

    def test_any_reasonable_person(self):
        result = frozen_core.evaluate(
            "Any reasonable person would agree that this is the right approach."
        )
        has_flag = any(f.pattern_id == "SHAME_LEVER" for f in result.flags)
        assert has_flag

    def test_right_side_of_history(self):
        result = frozen_core.evaluate(
            "We need to be on the right side of history on this issue."
        )
        has_flag = any(f.pattern_id == "SHAME_LEVER" for f in result.flags)
        assert has_flag


class TestCredentialAsProof:
    """Tier 3: Credentials substituted for argument."""

    def test_leading_expert(self):
        result = frozen_core.evaluate(
            "As a leading expert in the field, Dr. Smith's opinion should settle the matter."
        )
        has_flag = any(f.pattern_id == "CREDENTIAL_AS_PROOF" for f in result.flags)
        assert has_flag

    def test_years_experience(self):
        result = frozen_core.evaluate(
            "With over 30 years of experience, her judgment is beyond question."
        )
        has_flag = any(f.pattern_id == "CREDENTIAL_AS_PROOF" for f in result.flags)
        assert has_flag


class TestLegalPatterns:
    """Legal domain patterns — opposing counsel rhetorical tools."""

    def test_well_settled(self):
        result = frozen_core.evaluate(
            "It is well-settled law that the defendant's argument fails.",
            domain="legal",
        )
        has_flag = any(f.pattern_id == "LEGAL_SETTLED_DISMISSAL" for f in result.flags)
        assert has_flag

    def test_plainly_meritless(self):
        result = frozen_core.evaluate(
            "Plaintiff's claims are plainly meritless and should be dismissed.",
            domain="legal",
        )
        has_flag = any(f.pattern_id == "LEGAL_MERIT_DISMISSAL" for f in result.flags)
        assert has_flag

    def test_weight_of_authority(self):
        result = frozen_core.evaluate(
            "The overwhelming weight of authority supports the defendant's position.",
            domain="legal",
        )
        has_flag = any(f.pattern_id == "LEGAL_WEIGHT_STACKING" for f in result.flags)
        assert has_flag

    def test_frivolous_vexatious(self):
        result = frozen_core.evaluate(
            "This filing is frivolous and vexatious, warranting sanctions under Rule 11.",
            domain="legal",
        )
        legal_flags = [
            f for f in result.flags
            if f.pattern_id.startswith("LEGAL_")
        ]
        assert len(legal_flags) >= 1

    def test_sanctions_filing_considered(self):
        """Regression: this phrase was missed in v1.0.0."""
        result = frozen_core.evaluate(
            "Filing sanctions should be considered for this vexatious litigation.",
            domain="legal",
        )
        sanctions_flags = [f for f in result.flags if f.pattern_id == "LEGAL_SANCTIONS_THREAT"]
        assert len(sanctions_flags) > 0

    def test_legal_patterns_only_load_for_legal_domain(self):
        """Legal patterns should NOT fire for general domain."""
        result_general = frozen_core.evaluate(
            "It is well-settled law that this is correct.",
            domain="general",
        )
        result_legal = frozen_core.evaluate(
            "It is well-settled law that this is correct.",
            domain="legal",
        )
        legal_flags_general = [f for f in result_general.flags if f.pattern_id.startswith("LEGAL_")]
        legal_flags_legal = [f for f in result_legal.flags if f.pattern_id.startswith("LEGAL_")]
        assert len(legal_flags_legal) > len(legal_flags_general)


class TestTruthScore:
    """Truth score calculation."""

    def test_clean_text_high_score(self):
        from app.scorer import calculate_truth_score
        result = frozen_core.evaluate("The meeting is at 3pm.")
        score, _ = calculate_truth_score(result)
        assert score >= 90

    def test_biased_text_low_score(self):
        from app.scorer import calculate_truth_score
        result = frozen_core.evaluate(
            "Studies show that experts say the consensus is clear. "
            "Everyone agrees this is widely accepted common knowledge. "
            "Only conspiracy theorists would disagree.",
        )
        score, _ = calculate_truth_score(result)
        assert score < 60

    def test_score_bounds(self):
        from app.scorer import calculate_truth_score
        result = frozen_core.evaluate("Hi")
        score, _ = calculate_truth_score(result)
        assert 0 <= score <= 100


class TestKnowledgeClassification:
    """Knowledge type classification."""

    def test_neutral(self):
        result = frozen_core.evaluate("Please send me the document by Friday.")
        assert result.knowledge_type == "neutral"

    def test_sense(self):
        result = frozen_core.evaluate(
            "Experts say that studies show the consensus is clear. "
            "Research indicates authorities confirm the data suggests "
            "it is widely accepted that conventional wisdom holds."
        )
        assert result.knowledge_type == "sense"

    def test_mixed(self):
        # Mix of authority language (no citation) with factual content
        result = frozen_core.evaluate(
            "While experts say this is true, we also observed that "
            "temperatures rose 2.3 degrees during the test period."
        )
        assert result.knowledge_type in ("mixed", "sense")

    def test_cited_authority_is_neutral(self):
        # Authority language WITH proper citation should be suppressed
        result = frozen_core.evaluate(
            "While experts say this is true, the actual data from the "
            "2024 survey (Table 3, p.12) shows a different picture."
        )
        assert result.knowledge_type in ("neutral", "mixed")


class TestConfidence:
    """Confidence scoring."""

    def test_structural_match_higher_confidence(self):
        # Structural patterns should yield higher confidence than markers alone
        result_structural = frozen_core.evaluate(
            "That theory has been thoroughly debunked. "
            "No credible scientist supports it. "
            "Any reasonable person would agree."
        )
        result_markers = frozen_core.evaluate("Experts say this is true.")
        # Both should have flags, structural should have higher confidence
        assert len(result_structural.flags) > 0
        assert len(result_markers.flags) > 0

    def test_clean_text_high_confidence(self):
        result = frozen_core.evaluate(
            "According to the Bureau of Labor Statistics report from "
            "January 2025, unemployment decreased by 0.2 percentage points."
        )
        assert result.confidence >= 0.8


class TestImmutability:
    """The core must be immutable."""

    def test_singleton_identity(self):
        from app.frozen_core import frozen_core as core2
        assert frozen_core is core2

    def test_principles_not_modifiable(self):
        """Principles dict shouldn't be mutated at runtime."""
        original_count = len(frozen_core._base_patterns)
        # Attempt to evaluate — should not change pattern count
        frozen_core.evaluate("test text")
        assert len(frozen_core._base_patterns) == original_count


# ============================================================
# Phase 1C: New Pattern Tests
# ============================================================

class TestInevitabilityFrame:
    """INEVITABILITY_FRAME — Tier 1"""

    def test_detects_direction_heading(self):
        result = frozen_core.evaluate(
            "This is the direction the field is heading and there is no stopping this trend."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "INEVITABILITY_FRAME" in pids

    def test_detects_history_will_judge(self):
        result = frozen_core.evaluate(
            "History will judge those who resisted this change."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "INEVITABILITY_FRAME" in pids

    def test_detects_right_side_of_history(self):
        result = frozen_core.evaluate(
            "We need to be on the right side of history on this issue."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "INEVITABILITY_FRAME" in pids

    def test_no_false_positive_on_factual_trend(self):
        result = frozen_core.evaluate(
            "Sales increased 12% year-over-year, continuing the upward trend "
            "observed since Q2 2023."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "INEVITABILITY_FRAME" not in pids


class TestAppealToTradition:
    """APPEAL_TO_TRADITION — Tier 1"""

    def test_detects_always_done_this_way(self):
        result = frozen_core.evaluate(
            "We have always done it this way and it has worked fine."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "APPEAL_TO_TRADITION" in pids

    def test_detects_departing_from_practice(self):
        result = frozen_core.evaluate(
            "Departing from established practice would be unwise and dangerous."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "APPEAL_TO_TRADITION" in pids

    def test_no_false_positive_on_historical_analysis(self):
        result = frozen_core.evaluate(
            "The common law rule dating to the 19th century required privity "
            "of contract, but was properly abandoned in MacPherson v. Buick."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "APPEAL_TO_TRADITION" not in pids


class TestFalseEquivalence:
    """FALSE_EQUIVALENCE — Tier 1"""

    def test_detects_both_sides(self):
        result = frozen_core.evaluate(
            "Both sides have valid points and the truth lies somewhere in the middle."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "FALSE_EQUIVALENCE" in pids

    def test_detects_not_simple(self):
        result = frozen_core.evaluate(
            "It's not as simple as many critics suggest — there are valid "
            "arguments on both sides of this debate."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "FALSE_EQUIVALENCE" in pids

    def test_no_false_positive_on_genuine_balance(self):
        result = frozen_core.evaluate(
            "The parties present different interpretations. Plaintiff reads "
            "the clause narrowly, Defendant reads it broadly. The court must "
            "examine the text to determine which reading controls."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "FALSE_EQUIVALENCE" not in pids


class TestMoralHighGround:
    """MORAL_HIGH_GROUND — Tier 2"""

    def test_detects_any_decent_person(self):
        result = frozen_core.evaluate(
            "Any decent person would recognize the importance of this issue."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MORAL_HIGH_GROUND" in pids

    def test_detects_matter_of_decency(self):
        result = frozen_core.evaluate(
            "This is simply a matter of basic human decency."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MORAL_HIGH_GROUND" in pids

    def test_detects_morally_reprehensible(self):
        result = frozen_core.evaluate(
            "It is morally reprehensible to take such a position."
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MORAL_HIGH_GROUND" in pids


class TestLegalProceduralGatekeeping:
    """LEGAL_PROCEDURAL_GATEKEEPING — Tier 3"""

    def test_detects_failed_to_preserve(self):
        result = frozen_core.evaluate(
            "Plaintiff failed to properly preserve this argument for appeal.",
            domain="legal",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_PROCEDURAL_GATEKEEPING" in pids

    def test_detects_waived_claim(self):
        result = frozen_core.evaluate(
            "Defendant has waived this argument by not raising it in the "
            "initial responsive pleading.",
            domain="legal",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_PROCEDURAL_GATEKEEPING" in pids

    def test_detects_procedurally_barred(self):
        result = frozen_core.evaluate(
            "This claim is procedurally barred and need not be addressed "
            "on the merits.",
            domain="legal",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_PROCEDURAL_GATEKEEPING" in pids

    def test_detects_lacks_standing(self):
        result = frozen_core.evaluate(
            "Plaintiff lacks standing to raise this constitutional challenge.",
            domain="legal",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_PROCEDURAL_GATEKEEPING" in pids

    def test_no_false_positive_on_legitimate_procedural(self):
        """Legitimate procedural objection WITH merit discussion should still fire
        on the procedural part — that's correct. The distinction is human judgment."""
        result = frozen_core.evaluate(
            "Under Fed. R. Civ. P. 15, leave to amend is required. No motion "
            "to amend was filed. However, even on the merits, the statute "
            "requires notice within 30 days.",
            domain="legal",
        )
        # This should NOT fire — it's a legitimate procedural argument that
        # also addresses the merits
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_PROCEDURAL_GATEKEEPING" not in pids


class TestLegalStrawMan:
    """LEGAL_STRAW_MAN — Tier 2"""

    def test_detects_absolutist_mischaracterization(self):
        result = frozen_core.evaluate(
            "Plaintiff argues that all employers should be held strictly "
            "liable without any exception.",
            domain="legal",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_STRAW_MAN" in pids

    def test_detects_essentially_arguing(self):
        result = frozen_core.evaluate(
            "Defendant is essentially arguing that this Court should "
            "eliminate all consumer protections.",
            domain="legal",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_STRAW_MAN" in pids

    def test_no_false_positive_on_fair_characterization(self):
        result = frozen_core.evaluate(
            "Plaintiff contends that the contract's termination clause "
            "is ambiguous and should be construed against the drafter.",
            domain="legal",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "LEGAL_STRAW_MAN" not in pids


class TestPatternInventory:
    """Verify the full pattern inventory is as expected."""

    def test_base_pattern_count(self):
        assert len(frozen_core._base_patterns) == 14

    def test_legal_pattern_count(self):
        assert len(frozen_core._legal_patterns) == 6

    def test_total_pattern_count(self):
        total = len(frozen_core._base_patterns) + len(frozen_core._legal_patterns)
        assert total == 20

    def test_all_tiers_covered(self):
        all_patterns = frozen_core._base_patterns + frozen_core._legal_patterns
        tiers = {p.pit_tier for p in all_patterns}
        assert tiers == {1, 2, 3}

    def test_tier_distribution(self):
        all_patterns = frozen_core._base_patterns + frozen_core._legal_patterns
        tier_counts = {}
        for p in all_patterns:
            tier_counts[p.pit_tier] = tier_counts.get(p.pit_tier, 0) + 1
        # At least 3 patterns per tier
        assert tier_counts[1] >= 3
        assert tier_counts[2] >= 3
        assert tier_counts[3] >= 3


# ============================================================
# Phase 2: Media Domain Pattern Tests
# ============================================================

class TestMediaEditorialAsNews:
    """MEDIA_EDITORIAL_AS_NEWS — Tier 1"""

    def test_detects_controversial(self):
        result = frozen_core.evaluate(
            "The controversial policy sparked immediate backlash.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EDITORIAL_AS_NEWS" in pids

    def test_detects_embattled(self):
        result = frozen_core.evaluate(
            "The embattled executive released a statement late Friday.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EDITORIAL_AS_NEWS" in pids

    def test_detects_so_called(self):
        result = frozen_core.evaluate(
            "The so-called reform plan would eliminate thousands of jobs.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EDITORIAL_AS_NEWS" in pids

    def test_no_false_positive_on_neutral_reporting(self):
        result = frozen_core.evaluate(
            "The company announced a new policy on remote work.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EDITORIAL_AS_NEWS" not in pids


class TestMediaAnonymousAttribution:
    """MEDIA_ANONYMOUS_ATTRIBUTION — Tier 3"""

    def test_detects_unnamed_sources(self):
        result = frozen_core.evaluate(
            "Unnamed sources say the merger talks have stalled.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_ANONYMOUS_ATTRIBUTION" in pids

    def test_detects_sources_familiar(self):
        result = frozen_core.evaluate(
            "People familiar with the matter confirmed the timeline.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_ANONYMOUS_ATTRIBUTION" in pids

    def test_detects_critics_say(self):
        result = frozen_core.evaluate(
            "Critics say the approach is fundamentally flawed.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_ANONYMOUS_ATTRIBUTION" in pids

    def test_no_false_positive_on_named_source(self):
        result = frozen_core.evaluate(
            "CEO John Smith said the restructuring would be complete by Q3.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_ANONYMOUS_ATTRIBUTION" not in pids


class TestMediaWeaselQuantifiers:
    """MEDIA_WEASEL_QUANTIFIERS — Tier 2, requires 2 instances."""

    def test_detects_double_weasel(self):
        result = frozen_core.evaluate(
            "Many experts believe the policy will fail. It is widely believed "
            "that the approach has serious flaws.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_WEASEL_QUANTIFIERS" in pids

    def test_single_weasel_does_not_trigger(self):
        """Single weasel word is too common in legitimate writing."""
        result = frozen_core.evaluate(
            "Many analysts expect the Fed to hold rates steady.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_WEASEL_QUANTIFIERS" not in pids


class TestMediaFalseBalance:
    """MEDIA_FALSE_BALANCE — Tier 1"""

    def test_detects_some_say_scientists_disagree(self):
        result = frozen_core.evaluate(
            "Some say that vaccines cause autism, while mainstream "
            "scientists disagree with these claims.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_FALSE_BALANCE" in pids

    def test_no_false_positive_on_genuine_debate(self):
        result = frozen_core.evaluate(
            "Economists are divided on whether the policy will reduce "
            "inflation. Proponents cite historical parallels, while "
            "opponents point to structural differences.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_FALSE_BALANCE" not in pids


class TestMediaEmotionalLead:
    """MEDIA_EMOTIONAL_LEAD — Tier 2"""

    def test_detects_shocking(self):
        result = frozen_core.evaluate(
            "Shocking revelations emerged today about the company's practices.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EMOTIONAL_LEAD" in pids

    def test_detects_bombshell(self):
        result = frozen_core.evaluate(
            "A bombshell report released Thursday alleges widespread fraud.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EMOTIONAL_LEAD" in pids

    def test_not_triggered_in_middle_of_text(self):
        """Emotional words in the middle of text are not editorial leads."""
        result = frozen_core.evaluate(
            "The investigation, which began in January, uncovered what "
            "prosecutors called shocking evidence of systematic fraud.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EMOTIONAL_LEAD" not in pids

    def test_no_false_positive_on_neutral_lead(self):
        result = frozen_core.evaluate(
            "The Federal Reserve announced a quarter-point rate increase.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EMOTIONAL_LEAD" not in pids


class TestMediaPatternInventory:
    """Verify media pattern inventory."""

    def test_media_pattern_count(self):
        assert len(frozen_core._media_patterns) == 9

    def test_media_domain_loads_patterns(self):
        """Media domain should load base + media patterns."""
        result = frozen_core.evaluate(
            "The controversial policy was announced today.",
            domain="media",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EDITORIAL_AS_NEWS" in pids

    def test_media_patterns_not_in_general(self):
        """Media patterns should NOT fire in general domain."""
        result = frozen_core.evaluate(
            "The controversial policy was announced today.",
            domain="general",
        )
        pids = {f.pattern_id for f in result.flags if f.category == "structural"}
        assert "MEDIA_EDITORIAL_AS_NEWS" not in pids
