"""
Detector — Scan Orchestrator

Orchestrates the three scan modes:
  - local:  Frozen core only. Zero API cost. Instant.
  - deep:   LLM analysis only. Higher quality, costs money.
  - full:   Both layers merged. The real product.

This module coordinates between frozen_core, the LLM provider,
the scorer, and the learning ring.
"""

from __future__ import annotations

import logging

from typing import Optional

from biasclear.frozen_core import frozen_core, CoreEvaluation, CORE_VERSION
from biasclear.scorer import calculate_truth_score
from biasclear.llm import LLMProvider

logger = logging.getLogger(__name__)


# ============================================================
# DOMAIN-SPECIFIC PROMPT OVERLAYS
# ============================================================

DOMAIN_CONTEXT: dict[str, str] = {
    "legal": (
        "## Domain: Legal\n"
        "You are analyzing text from a legal context (filings, briefs, motions, opinions).\n"
        "Weight these manipulation patterns HIGHER:\n"
        "- Procedural manipulation disguised as legal standard\n"
        "- Weight-of-authority stacking without specific citations\n"
        "- Sanctions threats used as intimidation rather than legitimate remedy\n"
        "- \"Well-settled\" / \"plainly meritless\" dismissals that substitute rhetoric for argument\n"
        "- Characterization of opposing position as frivolous without engagement\n"
        "Flag any attempt to weaponize procedural language to avoid substantive argument."
    ),
    "media": (
        "## Domain: Media\n"
        "You are analyzing media content (news articles, editorials, reports).\n"
        "Weight these manipulation patterns HIGHER:\n"
        "- Narrative framing that pre-loads conclusions\n"
        "- Selective sourcing and manufactured consensus\n"
        "- Emotional anchoring through strategic word choice\n"
        "- False balance or false binary presentation\n"
        "- Headline-body disconnect (if detectable from text)\n"
        "- Institutional authority cited without specific evidence\n"
        "Flag language designed to manufacture consent rather than inform."
    ),
    "financial": (
        "## Domain: Financial\n"
        "You are analyzing financial content (reports, analyses, prospectuses).\n"
        "Weight these manipulation patterns HIGHER:\n"
        "- Survivorship bias in performance reporting\n"
        "- Cherry-picked timeframes for data presentation\n"
        "- Risk minimization through euphemism ('adjustment' for crash)\n"
        "- Authority bias via credential stacking\n"
        "- False precision creating illusion of certainty\n"
        "- FOMO/urgency language in investment context\n"
        "Flag language designed to manufacture confidence rather than convey risk."
    ),
    "political": (
        "## Domain: Political\n"
        "You are analyzing political content (speeches, policy, campaigns).\n"
        "Weight these manipulation patterns HIGHER:\n"
        "- In-group/out-group framing\n"
        "- Aspirational deflection (goals stated as achievements)\n"
        "- Scope intimidation (problem made too big to question)\n"
        "- Manufactured urgency and false deadlines\n"
        "- Moral framing used to prevent cost-benefit analysis\n"
        "- Consensus language substituting for evidence\n"
        "Flag rhetoric designed to mobilize rather than inform."
    ),
}


# ============================================================
# LLM PROMPTS
# ============================================================

DEEP_ANALYSIS_PROMPT = """You are BiasClear, a bias detection engine operating under the Persistent Influence Theory (PIT) framework.

{principles}

{domain_context}

## Your Task
Analyze the following text for bias, distortion, and rhetorical manipulation. Be thorough — detect ALL distortions, not just obvious ones. Institutional rhetoric, moral framing, aspirational language used to prevent scrutiny, and consensus manufacturing all count.

## Already Detected (by the deterministic engine)
These patterns were already found — do NOT duplicate them:
{local_flags}

## Analysis Requirements
Return a JSON object with:
1. "knowledge_type" — "sense" | "revelation" | "mixed" | "neutral"
2. "bias_detected" — boolean
3. "bias_types" — array from: ["authority_bias", "groupthink", "confirmation_bias", "framing_bias", "appeal_to_consensus", "false_urgency", "institutional_bias", "false_binary", "emotional_manipulation", "credential_appeal", "moral_framing", "aspirational_deflection", "manufactured_consensus", "scope_intimidation", "none"]
4. "pit_tier" — "tier_1_ideological" | "tier_2_psychological" | "tier_3_institutional" | "none"
5. "pit_tier_detail" — specific distortion pattern identified
6. "confidence" — float 0.0 to 1.0
7. "explanation" — 2-3 sentences on what was detected and why it matters
8. "severity" — "none" | "low" | "moderate" | "high" | "critical"
9. "flags" — array of NEW distortions not already detected. Each object:
   - "pattern_id": short_snake_case name (e.g. "moral_authority_framing", "manufactured_urgency")
   - "matched_text": the EXACT substring from the input text
   - "severity": "low" | "moderate" | "high" | "critical"
   - "pit_tier": 1 | 2 | 3
   - "category": "structural"
   Only include patterns NOT in the already-detected list above.

## Text to Analyze
{text}

Return ONLY valid JSON."""


IMPACT_PROJECTION_PROMPT = """Based on the text and bias audit below, predict two divergent futures:

1. PATH A — "The Trap": What happens if the reader accepts this biased framing?
   Focus on: missed opportunities, false security, strategic paralysis, cascading errors.

2. PATH B — "The Leverage": What happens if the reader sees through the bias?
   Focus on: competitive advantage, clarity, decisiveness, strategic positioning.

## Original Text
{text}

## Detected Bias
{audit_summary}

Return ONLY valid JSON with:
- "path_a_title": 3-6 word title for the trap
- "path_a_desc": 2-3 sentence description
- "path_b_title": 3-6 word title for the leverage
- "path_b_desc": 2-3 sentence description"""


# ============================================================
# SCAN FUNCTIONS
# ============================================================

async def scan_local(
    text: str,
    domain: str = "general",
    external_patterns: Optional[list] = None,
) -> dict:
    """
    Local-only scan. Frozen core + learning ring patterns.
    Zero API cost. Deterministic.
    """
    core_eval = frozen_core.evaluate(
        text, domain=domain, external_patterns=external_patterns,
    )
    truth_score, score_breakdown = calculate_truth_score(core_eval)

    return _build_result(
        text=text,
        core_eval=core_eval,
        truth_score=truth_score,
        scan_mode="local",
        score_breakdown=score_breakdown,
    )


async def scan_deep(
    text: str,
    llm: LLMProvider,
    domain: str = "general",
    learning_ring=None,
    audit_chain=None,
) -> dict:
    """
    Deep scan. LLM-powered analysis with frozen principles as context.
    When learning_ring is provided, novel patterns are proposed for learning.
    """
    prompt = DEEP_ANALYSIS_PROMPT.format(
        principles=frozen_core.get_principles_prompt(),
        domain_context=DOMAIN_CONTEXT.get(domain, ""),
        text=text,
        local_flags="(none)",
    )

    try:
        deep_result = await llm.generate_json(prompt, temperature=0.2)
    except Exception as e:
        return {
            "text": text,
            "error": str(e),
            "scan_mode": "deep",
            "source": "error",
        }

    # Calculate truth score from deep result only
    core_eval = frozen_core.evaluate(text, domain=domain)
    ai_flags = _extract_ai_flags(deep_result, [])
    truth_score, score_breakdown = calculate_truth_score(core_eval, deep_result, ai_flags)

    result = _build_result(
        text=text,
        core_eval=core_eval,
        truth_score=truth_score,
        scan_mode="deep",
        deep_result=deep_result,
        ai_flags=ai_flags,
        score_breakdown=score_breakdown,
    )

    # Self-learning loop — propose novel patterns
    if learning_ring and deep_result and audit_chain:
        try:
            from biasclear.patterns.proposer import PatternProposer
            proposer = PatternProposer(learning_ring)
            proposals = await proposer.extract_and_propose(
                text=text,
                local_flags=result["flags"],
                deep_result=deep_result,
                llm=llm,
                scan_audit_hash=result.get("audit_hash", "unknown"),
            )
            result["learning_proposals"] = proposals
        except Exception:
            result["learning_proposals"] = []
    else:
        result["learning_proposals"] = []

    return result


async def scan_full(
    text: str,
    llm: LLMProvider,
    domain: str = "general",
    external_patterns: Optional[list] = None,
    learning_ring=None,
    audit_chain=None,
) -> dict:
    """
    Full scan. Local frozen core + deep LLM analysis merged.
    This is the real product.

    When learning_ring and audit_chain are provided, the self-learning
    loop is active: novel patterns discovered by deep analysis are
    proposed to the learning ring for governed activation.
    """
    # Phase 1: Local
    core_eval = frozen_core.evaluate(
        text, domain=domain, external_patterns=external_patterns,
    )

    # Build local flag summary for Gemini deduplication
    local_flag_ids = [f.pattern_id for f in core_eval.flags]
    local_flags_str = ", ".join(local_flag_ids) if local_flag_ids else "(none)"

    # Phase 2: Deep — Gemini as co-detector
    prompt = DEEP_ANALYSIS_PROMPT.format(
        principles=frozen_core.get_principles_prompt(),
        domain_context=DOMAIN_CONTEXT.get(domain, ""),
        text=text,
        local_flags=local_flags_str,
    )

    deep_result = None
    try:
        deep_result = await llm.generate_json(prompt, temperature=0.2)
    except Exception as e:
        logger.warning("Gemini co-detection failed: %s", e)

    # Phase 3: Score (includes AI flag penalties)
    ai_flags = _extract_ai_flags(deep_result, local_flag_ids)
    truth_score, score_breakdown = calculate_truth_score(core_eval, deep_result, ai_flags)

    # Phase 4: Impact projection (only if truth_score < 80)
    impact = None
    if truth_score < 80 and deep_result:
        audit_summary = (
            f"Severity: {deep_result.get('severity', 'unknown')}, "
            f"Bias types: {', '.join(deep_result.get('bias_types', []))}, "
            f"PIT Tier: {deep_result.get('pit_tier', 'none')}, "
            f"Explanation: {deep_result.get('explanation', '')}"
        )
        try:
            impact = await llm.generate_json(
                IMPACT_PROJECTION_PROMPT.format(
                    text=text, audit_summary=audit_summary,
                ),
                temperature=0.7,
            )
        except Exception:
            impact = None

    result = _build_result(
        text=text,
        core_eval=core_eval,
        truth_score=truth_score,
        scan_mode="full",
        deep_result=deep_result,
        impact_projection=impact,
        ai_flags=ai_flags,
        score_breakdown=score_breakdown,
    )

    # Phase 5: Self-learning loop — propose novel patterns
    if learning_ring and deep_result and audit_chain:
        try:
            from biasclear.patterns.proposer import PatternProposer
            proposer = PatternProposer(learning_ring)
            proposals = await proposer.extract_and_propose(
                text=text,
                local_flags=result["flags"],
                deep_result=deep_result,
                llm=llm,
                scan_audit_hash=result.get("audit_hash", "unknown"),
            )
            result["learning_proposals"] = proposals
        except Exception:
            result["learning_proposals"] = []
    else:
        result["learning_proposals"] = []

    return result


def _extract_ai_flags(
    deep_result: Optional[dict],
    local_flag_ids: list[str],
) -> list[dict]:
    """Extract and validate AI-detected flags from Gemini response."""
    if not deep_result:
        return []

    raw_flags = deep_result.get("flags", [])
    if not isinstance(raw_flags, list):
        return []

    ai_flags = []
    seen_ids = set(f.lower() for f in local_flag_ids)

    for f in raw_flags:
        if not isinstance(f, dict):
            continue

        pattern_id = f.get("pattern_id", "").strip()
        matched_text = f.get("matched_text", "").strip()
        severity = f.get("severity", "moderate").lower()
        pit_tier = f.get("pit_tier", 2)

        # Skip if missing required fields
        if not pattern_id or not matched_text:
            continue

        # Skip duplicates of local flags
        if pattern_id.lower() in seen_ids:
            continue

        # Normalize severity
        if severity not in ("low", "moderate", "high", "critical"):
            severity = "moderate"

        # Normalize pit_tier
        try:
            pit_tier = int(pit_tier)
        except (TypeError, ValueError):
            pit_tier = 2
        pit_tier = max(1, min(3, pit_tier))

        ai_flags.append({
            "category": f.get("category", "structural"),
            "pattern_id": pattern_id,
            "matched_text": matched_text,
            "pit_tier": pit_tier,
            "severity": severity,
            "description": f.get("description", ""),
            "source": "ai",
        })
        seen_ids.add(pattern_id.lower())

    return ai_flags


# ============================================================
# RESULT BUILDER
# ============================================================

def _build_result(
    text: str,
    core_eval: CoreEvaluation,
    truth_score: int,
    scan_mode: str,
    deep_result: Optional[dict] = None,
    impact_projection: Optional[dict] = None,
    ai_flags: Optional[list[dict]] = None,
    score_breakdown: Optional[dict] = None,
) -> dict:
    """Build a unified scan result from local + deep + AI flags."""
    ai_flags = ai_flags or []

    # Merge bias types from both sources
    local_bias_types = list(set(f.pattern_id for f in core_eval.flags))
    deep_bias_types = []
    if deep_result:
        deep_bias_types = [
            b for b in deep_result.get("bias_types", []) if b != "none"
        ]

    # Determine overall severity — worst of core, AI, and deep
    all_severities = [f.severity for f in core_eval.flags]
    all_severities.extend(f["severity"] for f in ai_flags)
    if deep_result and deep_result.get("severity"):
        all_severities.append(deep_result["severity"])

    severity_order = ["critical", "high", "moderate", "low", "none"]
    severity = "none"
    for s in severity_order:
        if s in all_severities:
            severity = s
            break

    # Merge explanation
    explanation = core_eval.summary
    if deep_result and deep_result.get("explanation"):
        explanation = deep_result["explanation"]

    # Merge confidence — take the higher of the two
    confidence = core_eval.confidence
    if deep_result and deep_result.get("confidence"):
        confidence = max(confidence, deep_result["confidence"])

    # Determine pit tier — prefer deep analysis
    pit_tier = core_eval.pit_tier_active or "none"
    if deep_result and deep_result.get("pit_tier"):
        pit_tier = deep_result["pit_tier"]

    pit_detail = ""
    if deep_result and deep_result.get("pit_tier_detail"):
        pit_detail = deep_result["pit_tier_detail"]

    # Knowledge type — prefer deep
    knowledge_type = core_eval.knowledge_type
    if deep_result and deep_result.get("knowledge_type"):
        knowledge_type = deep_result["knowledge_type"]

    # Build merged flags: core flags (source: core) + AI flags (source: ai)
    core_flags = [
        {
            "category": f.category,
            "pattern_id": f.pattern_id,
            "matched_text": f.matched_text,
            "pit_tier": f.pit_tier,
            "severity": f.severity,
            "description": f.description,
            "source": "core",
        }
        for f in core_eval.flags
    ]
    merged_flags = core_flags + ai_flags

    return {
        "text": text,
        "truth_score": truth_score,
        "knowledge_type": knowledge_type,
        "bias_detected": len(merged_flags) > 0 or (
            deep_result.get("bias_detected", False) if deep_result else False
        ),
        "bias_types": list(set(local_bias_types + deep_bias_types)),
        "pit_tier": pit_tier,
        "pit_detail": pit_detail,
        "severity": severity,
        "confidence": round(confidence, 3),
        "explanation": explanation,
        "flags": merged_flags,
        "impact_projection": (
            {
                "path_a": {
                    "title": impact_projection.get("path_a_title", ""),
                    "description": impact_projection.get("path_a_desc", ""),
                },
                "path_b": {
                    "title": impact_projection.get("path_b_title", ""),
                    "description": impact_projection.get("path_b_desc", ""),
                },
            }
            if impact_projection
            else None
        ),
        "scan_mode": scan_mode,
        "source": "local" if scan_mode == "local" else (
            "gemini+local" if deep_result else "local_fallback"
        ),
        "core_version": CORE_VERSION,
        "score_breakdown": score_breakdown,
    }
