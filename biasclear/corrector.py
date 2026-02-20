"""
Corrector — Bias Remediation

Takes biased text + scan results, uses the LLM to rewrite
with distortions removed while preserving factual content.
"""

from __future__ import annotations

from biasclear.frozen_core import frozen_core
from biasclear.llm import LLMProvider


CORRECTION_PROMPT = """You are BiasClear's Correction Engine.

{principles}

## Your Task
Rewrite the following text to remove detected distortions while
preserving all factual content and original meaning.

## Detected Bias
- Knowledge Type: {knowledge_type}
- Bias Types: {bias_types}
- PIT Tier: {pit_tier}
- Explanation: {explanation}

## Rules
1. Remove appeals to authority/consensus that substitute for evidence
2. Replace distortion packaging with grounded, direct statements
3. Preserve ALL factual claims — only remove the bias framing
4. Do not add information the original didn't contain
5. Produce neutral, clear prose
6. Corrected text should be shorter or equal length

## Original Text
{text}

Return JSON with:
- "corrected": the rewritten text
- "changes_made": array of strings describing each change
- "bias_removed": array of bias types addressed
- "confidence": float 0.0 to 1.0"""


async def correct_bias(
    text: str,
    scan_result: dict,
    llm: LLMProvider,
) -> dict:
    """Correct detected bias in text using LLM remediation."""
    if not scan_result.get("bias_detected", False):
        return {
            "original": text,
            "corrected": text,
            "changes_made": [],
            "bias_removed": [],
            "confidence": 1.0,
            "note": "No bias detected — no correction needed.",
        }

    prompt = CORRECTION_PROMPT.format(
        principles=frozen_core.get_principles_prompt(),
        text=text,
        knowledge_type=scan_result.get("knowledge_type", "unknown"),
        bias_types=", ".join(scan_result.get("bias_types", [])),
        pit_tier=scan_result.get("pit_tier", "none"),
        explanation=scan_result.get("explanation", ""),
    )

    try:
        result = await llm.generate_json(prompt, temperature=0.3)
        result["original"] = text
        return result
    except Exception as e:
        return {
            "original": text,
            "corrected": text,
            "changes_made": [],
            "bias_removed": [],
            "confidence": 0.0,
            "error": str(e),
        }
