"""
Corrector — Flag-Aware Bias Remediation

Takes biased text + scan results, uses the LLM to rewrite
with distortions removed while preserving factual content.

Key design principles:
  1. Correction = subtraction (remove bias framing, don't rewrite)
  2. Flag-aware: each structural flag carries its pattern description
  3. Threshold gate: keyword markers alone never trigger correction
  4. Post-correction verification: re-scan to confirm improvement
  5. Iterative: up to 3 correction passes with re-verification
"""

from __future__ import annotations

import logging
from typing import Optional

import diff_match_patch as dmp_module

from biasclear.frozen_core import (
    LEGAL_STRUCTURAL_PATTERNS,
    STRUCTURAL_PATTERNS,
    MEDIA_STRUCTURAL_PATTERNS,
    FINANCIAL_STRUCTURAL_PATTERNS,
    StructuralPattern,
    frozen_core,
)
from biasclear.llm import LLMProvider
from biasclear.scorer import calculate_truth_score

logger = logging.getLogger(__name__)

# Singleton diff engine
_dmp = dmp_module.diff_match_patch()

# Build a lookup table: pattern_id -> StructuralPattern
_PATTERN_LOOKUP: dict[str, StructuralPattern] = {
    p.id: p
    for p in (
        STRUCTURAL_PATTERNS
        + LEGAL_STRUCTURAL_PATTERNS
        + MEDIA_STRUCTURAL_PATTERNS
        + FINANCIAL_STRUCTURAL_PATTERNS
    )
}

# Severity ordering for threshold gate
_SEVERITY_RANK = {"critical": 4, "high": 3, "moderate": 2, "low": 1}


CORRECTION_PROMPT = """You are BiasClear's Correction Engine.

{principles}

## Your Task
Rewrite the following text to remove detected distortions while
preserving all factual content and original meaning.

## Rules
1. Correction = SUBTRACTION. Remove the bias framing, do not rewrite content.
2. Follow each flag's specific correction instruction exactly.
3. Preserve ALL factual claims — only remove the bias packaging.
4. Do not add information the original didn't contain.
5. Do not add hedging, qualifiers, or "on the other hand" language.
6. Corrected text should be shorter or equal length — never longer.

## Detected Distortions (correct each one)
{flag_instructions}

## Original Text
{text}

Return JSON with:
- "corrected": the rewritten text
- "changes_made": array of strings describing each specific change
- "bias_removed": array of pattern IDs that were corrected
- "confidence": float 0.0 to 1.0 (your confidence in the correction quality)"""


REFINEMENT_PROMPT = """You are BiasClear's Correction Engine (Iteration {iteration}).

Your PREVIOUS correction attempt still contains these distortions:

{surviving_flags}

## Rules
1. You MUST address every surviving distortion listed above.
2. Correction = SUBTRACTION. Remove framing, do not add content.
3. The text below is your OWN previous output — refine it further.
4. Do not add hedging, qualifiers, or "on the other hand" language.
5. The result should be shorter or equal length — never longer.

## Text to Refine
{text}

Return JSON with:
- "corrected": the refined text
- "changes_made": array of strings describing each change in THIS iteration
- "bias_removed": array of pattern IDs corrected in THIS iteration
- "confidence": float 0.0 to 1.0"""


MAX_ITERATIONS = 3


def _should_correct(scan_result: dict) -> bool:
    """
    Correction threshold gate.

    Correction activates ONLY when:
      (a) truth_score <= 80, OR
      (b) at least one structural flag with severity >= "moderate"

    Keyword markers alone NEVER trigger correction.
    """
    truth_score = scan_result.get("truth_score", 100)
    if truth_score <= 80:
        return True

    flags = scan_result.get("flags", [])
    for flag in flags:
        if flag.get("category") == "structural":
            severity = flag.get("severity", "low")
            if _SEVERITY_RANK.get(severity, 0) >= _SEVERITY_RANK["moderate"]:
                return True

    return False


def _build_flag_instructions(scan_result: dict) -> str:
    """
    Build per-flag correction instructions from scan results.

    Each structural flag is looked up in the pattern registry.
    Uses the pattern's description as correction guidance.
    """
    lines = []
    idx = 1
    flags = scan_result.get("flags", [])

    for flag in flags:
        if flag.get("category") != "structural":
            continue

        pattern_id = flag.get("pattern_id", "")
        matched_text = flag.get("matched_text", "")
        severity = flag.get("severity", "moderate")
        pattern = _PATTERN_LOOKUP.get(pattern_id)

        description = ""
        if pattern:
            description = pattern.description
        elif flag.get("description"):
            description = flag["description"]

        lines.append(
            f'{idx}. [{pattern_id}] (severity: {severity})\n'
            f'   Matched: "{matched_text}"\n'
            f'   What to fix: {description}\n'
            f'   Action: Remove or rephrase the distortion framing. Keep factual content.'
        )
        idx += 1

    # Include AI-sourced flags too
    for flag in flags:
        if flag.get("source") == "ai":
            pattern_id = flag.get("pattern_id", "")
            matched_text = flag.get("matched_text", "")
            severity = flag.get("severity", "moderate")
            description = flag.get("description", "AI-detected distortion pattern")

            lines.append(
                f'{idx}. [{pattern_id}] (severity: {severity}, source: AI)\n'
                f'   Matched: "{matched_text}"\n'
                f'   What to fix: {description}\n'
                f'   Action: Remove or rephrase the distortion framing. Keep factual content.'
            )
            idx += 1

    if not lines:
        return "No specific structural distortions flagged for correction."

    return "\n".join(lines)


def _verify_correction(corrected_text: str, domain: str = "general") -> dict:
    """
    Post-correction verification: re-scan corrected text through frozen core.

    Returns verification dict with before/after comparison.
    """
    verification_eval = frozen_core.evaluate(corrected_text, domain=domain)
    verification_score, _ = calculate_truth_score(verification_eval)

    structural_remaining = [
        {
            "pattern_id": f.pattern_id,
            "severity": f.severity,
            "matched_text": f.matched_text[:80],
        }
        for f in verification_eval.flags
        if f.category == "structural"
    ]

    return {
        "truth_score_after": verification_score,
        "flags_remaining": len(verification_eval.flags),
        "structural_remaining": structural_remaining,
        "aligned": verification_eval.aligned,
    }


def _build_surviving_instructions(verification: dict) -> str:
    """
    Build correction instructions from surviving structural flags
    found during post-correction verification.
    """
    remaining = verification.get("structural_remaining", [])
    if not remaining:
        return "No specific distortions remaining."

    lines = []
    for idx, flag in enumerate(remaining, 1):
        pattern = _PATTERN_LOOKUP.get(flag["pattern_id"])
        description = pattern.description if pattern else "Structural distortion"
        lines.append(
            f'{idx}. [{flag["pattern_id"]}] '
            f'Still matched: "{flag["matched_text"]}"\n'
            f'   What to fix: {description}'
        )
    return "\n".join(lines) or "Unresolved structural patterns detected."


def _compute_diff_spans(original: str, corrected: str) -> list[dict]:
    """
    Compute deterministic text diffs between original and corrected.

    Uses diff-match-patch (Google's text diff library) — no LLM involved.
    Returns spans with type (equal/delete/insert), text, and positions.
    """
    diffs = _dmp.diff_main(original, corrected)
    _dmp.diff_cleanupSemantic(diffs)

    spans = []
    orig_pos = 0
    corr_pos = 0

    for op, text in diffs:
        if op == 0:  # EQUAL
            spans.append({
                "type": "equal",
                "text": text,
                "orig_start": orig_pos,
                "orig_end": orig_pos + len(text),
                "corr_start": corr_pos,
                "corr_end": corr_pos + len(text),
            })
            orig_pos += len(text)
            corr_pos += len(text)
        elif op == -1:  # DELETE
            spans.append({
                "type": "delete",
                "text": text,
                "orig_start": orig_pos,
                "orig_end": orig_pos + len(text),
            })
            orig_pos += len(text)
        elif op == 1:  # INSERT
            spans.append({
                "type": "insert",
                "text": text,
                "corr_start": corr_pos,
                "corr_end": corr_pos + len(text),
            })
            corr_pos += len(text)

    return spans


async def _correction_loop(
    text: str,
    scan_result: dict,
    llm: LLMProvider,
    domain: str = "general",
) -> tuple[dict, dict, list[dict]]:
    """
    Run correction → verify → retry cycle (max MAX_ITERATIONS).

    Returns:
      (result, final_verification, iterations_history)
    """
    iterations: list[dict] = []
    current_text = text
    truth_score_before = scan_result.get("truth_score", 100)
    original_structural_count = len([
        f for f in scan_result.get("flags", [])
        if f.get("category") == "structural"
    ])

    result = {}
    verification = {}

    for i in range(MAX_ITERATIONS):
        if i == 0:
            flag_instructions = _build_flag_instructions(scan_result)
            prompt = CORRECTION_PROMPT.format(
                principles=frozen_core.get_principles_prompt(),
                text=text,
                flag_instructions=flag_instructions,
            )
        else:
            surviving = _build_surviving_instructions(verification)
            prompt = REFINEMENT_PROMPT.format(
                iteration=i + 1,
                surviving_flags=surviving,
                text=current_text,
            )

        result = await llm.generate_json(prompt, temperature=0.3)
        corrected_text = result.get("corrected", current_text)

        verification = _verify_correction(corrected_text, domain=domain)
        verification["truth_score_before"] = truth_score_before
        verification["passed"] = (
            verification["truth_score_after"] >= truth_score_before
            and verification["flags_remaining"] <= original_structural_count
        )

        iterations.append({
            "iteration": i + 1,
            "truth_score": verification["truth_score_after"],
            "flags_remaining": verification["flags_remaining"],
            "passed": verification["passed"],
        })

        if verification["passed"]:
            break

        current_text = corrected_text

    return result, verification, iterations


async def correct_bias(
    text: str,
    scan_result: dict,
    llm: LLMProvider,
    domain: str = "general",
) -> dict:
    """
    Correct detected bias in text using flag-aware LLM remediation.

    Flow:
      1. Threshold gate check
      2. Iterative correction loop (up to MAX_ITERATIONS):
         a. Build per-flag instructions
         b. LLM correction
         c. Post-correction verification
         d. If verification fails, retry with surviving flags
      3. Compute deterministic diff spans
    """
    # --- Threshold gate ---
    if not _should_correct(scan_result):
        return {
            "original": text,
            "corrected": text,
            "changes_made": [],
            "bias_removed": [],
            "confidence": 1.0,
            "correction_triggered": False,
            "note": "Below correction threshold — no structural distortions requiring correction.",
        }

    # --- Iterative correction ---
    try:
        result, verification, iterations = await _correction_loop(
            text, scan_result, llm, domain,
        )

        result["original"] = text
        result["correction_triggered"] = True
        result["verification"] = verification

        result["iteration_count"] = len(iterations)
        result["iterations"] = iterations
        result["converged"] = iterations[-1]["passed"] if iterations else False

        # --- Inline diff spans (deterministic, no LLM) ---
        corrected_text = result.get("corrected", text)
        result["diff_spans"] = _compute_diff_spans(text, corrected_text)

        return result

    except Exception as e:
        logger.error("Correction failed: %s", e, exc_info=True)
        return {
            "original": text,
            "corrected": text,
            "changes_made": [],
            "bias_removed": [],
            "confidence": 0.0,
            "correction_triggered": True,
            "error": str(e),
        }
