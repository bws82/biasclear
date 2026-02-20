"""
Pattern Proposer — Closes the Self-Learning Loop

When a deep scan detects bias that the local frozen core MISSED,
this module extracts the novel pattern and proposes it to the
learning ring. This is how BiasClear gets smarter over time
without drifting from its mission.

The loop:
  1. Local scan runs → produces flags (or none)
  2. Deep scan runs → LLM finds additional bias
  3. Proposer compares: what did deep find that local missed?
  4. For each novel detection, ask the LLM to formalize it as a regex pattern
  5. Propose to learning ring → staging → confirmation → activation

The frozen core defines WHAT a distortion is.
The learning ring learns HOW to detect new instances of it.
The proposer is the bridge.
"""

from __future__ import annotations

import re
import hashlib
from typing import Optional

from biasclear.llm import LLMProvider
from biasclear.frozen_core import frozen_core, PIT_TIERS


PATTERN_EXTRACTION_PROMPT = """You are a pattern engineer for a bias detection system.

A deep analysis detected bias in text that the local rule-based detector missed.
Your job: formalize the detected distortion into a regex pattern that would catch
similar language in future text.

## What the deep analysis found
- Bias types: {bias_types}
- PIT Tier: {pit_tier}
- Explanation: {explanation}

## The text that triggered the detection
{text}

## Requirements for the regex pattern
1. Must be a valid Python regex (re module compatible)
2. Should use word boundaries (\\b) to prevent partial matches
3. Should be general enough to catch variations, specific enough to avoid false positives
4. Should use non-capturing groups (?:...) and alternation where appropriate
5. MUST be case-insensitive compatible (will be run with re.IGNORECASE)
6. Should target the LINGUISTIC STRUCTURE, not specific proper nouns or facts

## Return Format
Return JSON with:
- "pattern_id": short ALL_CAPS identifier (e.g., "HEDGED_AUTHORITY_CLAIM")
- "name": human-readable name (3-6 words)
- "description": one sentence explaining what this pattern detects
- "pit_tier": integer 1, 2, or 3
- "severity": "low" | "moderate" | "high" | "critical"
- "principle": which principle this violates — "Truth" | "Justice" | "Clarity" | "Agency" | "Identity"
- "regex": the Python regex pattern string

Return ONLY valid JSON. If you cannot formalize a useful pattern, return:
{{"pattern_id": null, "reason": "explanation of why"}}"""


class PatternProposer:
    """
    Compares local vs. deep scan results and proposes novel patterns
    to the learning ring.
    """

    def __init__(self, learning_ring):
        """
        Args:
            learning_ring: The LearningRing instance to propose patterns to.
        """
        self._ring = learning_ring

    async def extract_and_propose(
        self,
        text: str,
        local_flags: list[dict],
        deep_result: dict,
        llm: LLMProvider,
        scan_audit_hash: str,
    ) -> list[dict]:
        """
        Compare local vs. deep results. If deep found bias that local missed,
        extract the novel pattern and propose it to the learning ring.

        Args:
            text: The original scanned text.
            local_flags: Flags from the frozen core evaluation.
            deep_result: The full deep analysis result from the LLM.
            llm: The LLM provider for pattern formalization.
            scan_audit_hash: The audit hash of the scan that produced these results.

        Returns:
            List of proposal results from the learning ring.
        """
        # Skip if deep analysis didn't find bias
        if not deep_result.get("bias_detected", False):
            return []

        # Skip if deep severity is low — not worth learning from
        if deep_result.get("severity") in ("none", "low"):
            return []

        # Determine what deep found that local didn't
        local_pattern_ids = set(f.get("pattern_id", "") for f in local_flags)
        deep_bias_types = set(
            b for b in deep_result.get("bias_types", []) if b != "none"
        )

        # If local already caught substantial bias, the gap is smaller
        if len(local_flags) >= 3:
            return []

        # If local caught nothing but deep found significant bias — that's the gap
        novel_bias = deep_bias_types
        if not novel_bias:
            return []

        # Validate PIT tier is one we recognize
        pit_tier_raw = deep_result.get("pit_tier", "none")
        pit_tier_num = self._parse_tier(pit_tier_raw)
        if pit_tier_num is None:
            return []

        # Ask the LLM to formalize the pattern
        try:
            pattern_spec = await llm.generate_json(
                PATTERN_EXTRACTION_PROMPT.format(
                    bias_types=", ".join(novel_bias),
                    pit_tier=pit_tier_raw,
                    explanation=deep_result.get("explanation", ""),
                    text=text[:2000],  # Truncate for prompt size
                ),
                temperature=0.2,
            )
        except Exception:
            return []

        # Validate the LLM's response
        if not pattern_spec.get("pattern_id"):
            return []

        # Validate the regex compiles
        regex = pattern_spec.get("regex", "")
        if not self._validate_regex(regex):
            return []

        # Validate PIT tier from the LLM matches an existing tier
        proposed_tier = pattern_spec.get("pit_tier")
        if proposed_tier not in (1, 2, 3):
            return []

        # Validate severity
        proposed_severity = pattern_spec.get("severity", "moderate")
        if proposed_severity not in ("low", "moderate", "high", "critical"):
            proposed_severity = "moderate"

        # Validate principle
        valid_principles = {"Truth", "Justice", "Clarity", "Agency", "Identity"}
        proposed_principle = pattern_spec.get("principle", "Truth")
        if proposed_principle not in valid_principles:
            proposed_principle = "Truth"

        # Generate a deterministic pattern ID based on the regex
        # This ensures the same pattern discovered independently gets
        # the same ID — which is how confirmations accumulate
        pattern_id = self._generate_pattern_id(
            pattern_spec["pattern_id"], regex
        )

        # Propose to the learning ring
        result = self._ring.propose(
            pattern_id=pattern_id,
            name=pattern_spec.get("name", "Unnamed Pattern"),
            description=pattern_spec.get("description", ""),
            pit_tier=proposed_tier,
            severity=proposed_severity,
            principle=proposed_principle,
            regex=regex,
            source_scan_hash=scan_audit_hash,
        )

        return [result]

    def _parse_tier(self, tier_str: str) -> Optional[int]:
        """Parse a PIT tier string to an integer."""
        if tier_str == "none":
            return None
        # Handle "tier_1_ideological", "tier_2_psychological", etc.
        try:
            parts = tier_str.split("_")
            tier_num = int(parts[1])
            if tier_num in PIT_TIERS:
                return tier_num
        except (IndexError, ValueError):
            pass
        return None

    def _validate_regex(self, regex: str) -> bool:
        """Check if a regex string is valid and not degenerate."""
        if not regex or len(regex) < 5:
            return False
        if len(regex) > 1000:
            return False  # Too complex — likely garbage
        try:
            compiled = re.compile(regex, re.IGNORECASE)
            # Sanity check — it shouldn't match everything
            if compiled.match(""):
                return False
            # It shouldn't match simple common words
            common = ["the", "is", "a", "and", "to", "in"]
            matches_common = sum(1 for w in common if compiled.search(w))
            if matches_common >= 3:
                return False  # Too broad
            return True
        except re.error:
            return False

    def _generate_pattern_id(self, base_id: str, regex: str) -> str:
        """
        Generate a deterministic pattern ID.

        Uses the base ID from the LLM + a hash of the regex to ensure
        that independently discovered but identical patterns converge
        to the same ID for confirmation counting.
        """
        # Clean the base ID
        clean_id = re.sub(r"[^A-Z0-9_]", "", base_id.upper())
        if not clean_id:
            clean_id = "LEARNED"

        # Hash the regex for uniqueness
        regex_hash = hashlib.md5(regex.encode()).hexdigest()[:6]

        return f"L_{clean_id}_{regex_hash}"
