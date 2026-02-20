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

from typing import Optional

from app.frozen_core import frozen_core, CoreEvaluation, CORE_VERSION
from app.scorer import calculate_truth_score
from app.llm import LLMProvider


# ============================================================
# LLM PROMPTS
# ============================================================

DEEP_ANALYSIS_PROMPT = """You are BiasClear, a bias detection engine operating under the Persistent Influence Theory (PIT) framework.

{principles}

## Your Task
Analyze the following text for bias and distortion. Classify it according to the PIT framework.

## Analysis Requirements
Return a JSON object with:
1. "knowledge_type" — "sense" | "revelation" | "mixed" | "neutral"
2. "bias_detected" — boolean
3. "bias_types" — array from: ["authority_bias", "groupthink", "confirmation_bias", "framing_bias", "appeal_to_consensus", "false_urgency", "institutional_bias", "false_binary", "emotional_manipulation", "credential_appeal", "none"]
4. "pit_tier" — "tier_1_ideological" | "tier_2_psychological" | "tier_3_institutional" | "none"
5. "pit_tier_detail" — specific distortion pattern identified
6. "confidence" — float 0.0 to 1.0
7. "explanation" — 2-3 sentences on what was detected and why it matters
8. "severity" — "none" | "low" | "moderate" | "high" | "critical"

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
    truth_score = calculate_truth_score(core_eval)

    return _build_result(
        text=text,
        core_eval=core_eval,
        truth_score=truth_score,
        scan_mode="local",
    )


async def scan_deep(
    text: str,
    llm: LLMProvider,
    domain: str = "general",
) -> dict:
    """
    Deep scan. LLM-powered analysis with frozen principles as context.
    """
    prompt = DEEP_ANALYSIS_PROMPT.format(
        principles=frozen_core.get_principles_prompt(),
        text=text,
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
    # Create a minimal core eval for the scorer
    core_eval = frozen_core.evaluate(text, domain=domain)
    truth_score = calculate_truth_score(core_eval, deep_result)

    result = _build_result(
        text=text,
        core_eval=core_eval,
        truth_score=truth_score,
        scan_mode="deep",
        deep_result=deep_result,
    )
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

    # Phase 2: Deep
    prompt = DEEP_ANALYSIS_PROMPT.format(
        principles=frozen_core.get_principles_prompt(),
        text=text,
    )

    deep_result = None
    try:
        deep_result = await llm.generate_json(prompt, temperature=0.2)
    except Exception:
        pass  # Fall back to local-only if LLM fails

    # Phase 3: Score
    truth_score = calculate_truth_score(core_eval, deep_result)

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
    )

    # Phase 5: Self-learning loop — propose novel patterns
    if learning_ring and deep_result and audit_chain:
        try:
            from app.patterns.proposer import PatternProposer
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
) -> dict:
    """Build a unified scan result from local + deep components."""
    # Merge bias types from both sources
    local_bias_types = list(set(f.pattern_id for f in core_eval.flags))
    deep_bias_types = []
    if deep_result:
        deep_bias_types = [
            b for b in deep_result.get("bias_types", []) if b != "none"
        ]

    # Determine overall severity
    if deep_result and deep_result.get("severity"):
        severity = deep_result["severity"]
    else:
        severities = [f.severity for f in core_eval.flags]
        severity_order = ["critical", "high", "moderate", "low", "none"]
        severity = "none"
        for s in severity_order:
            if s in severities:
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

    return {
        "text": text,
        "truth_score": truth_score,
        "knowledge_type": knowledge_type,
        "bias_detected": len(core_eval.flags) > 0 or (
            deep_result.get("bias_detected", False) if deep_result else False
        ),
        "bias_types": list(set(local_bias_types + deep_bias_types)),
        "pit_tier": pit_tier,
        "pit_detail": pit_detail,
        "severity": severity,
        "confidence": round(confidence, 3),
        "explanation": explanation,
        "flags": [
            {
                "category": f.category,
                "pattern_id": f.pattern_id,
                "matched_text": f.matched_text,
                "pit_tier": f.pit_tier,
                "severity": f.severity,
                "description": f.description,
            }
            for f in core_eval.flags
        ],
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
    }
