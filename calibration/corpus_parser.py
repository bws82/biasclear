"""
Corpus Parser — Reads Tagged Calibration Samples

Parses the simple text format used for calibration corpus files.
Each sample is a block of text preceded by metadata tags,
separated by '---' delimiters.

Format:
    ---
    tags: settled_law_dismissal, merit_dismissal
    severity: high
    source: Jones Day MTD, Dkt. 45, p.12
    notes: Classic dismissal combo
    domain: legal

    The actual passage text goes here. It can span
    multiple lines.

    ---
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CalibrationSample:
    """A single labeled sample from the calibration corpus."""
    text: str
    tags: list[str]               # Human-labeled bias tags (or ["clean"])
    severity: str                 # Human-labeled severity
    source: str                   # Where the passage came from
    notes: str                    # Annotator notes
    domain: str                   # legal, general, media, financial
    is_clean: bool                # True if tagged as "clean" (no bias)

    # Populated after engine evaluation
    engine_result: Optional[dict] = None


# Map human tags to expected pattern IDs in the frozen core
TAG_TO_PATTERN_ID = {
    "settled_law_dismissal": "LEGAL_SETTLED_DISMISSAL",
    "merit_dismissal": "LEGAL_MERIT_DISMISSAL",
    "weight_stacking": "LEGAL_WEIGHT_STACKING",
    "sanctions_threat": "LEGAL_SANCTIONS_THREAT",
    "procedural_gatekeeping": "LEGAL_PROCEDURAL_GATEKEEPING",
    "straw_man": "LEGAL_STRAW_MAN",
    "consensus_as_evidence": "CONSENSUS_AS_EVIDENCE",
    "claim_without_citation": "CLAIM_WITHOUT_CITATION",
    "dissent_dismissal": "DISSENT_DISMISSAL",
    "false_binary": "FALSE_BINARY",
    "fear_urgency": "FEAR_URGENCY",
    "shame_lever": "SHAME_LEVER",
    "credential_as_proof": "CREDENTIAL_AS_PROOF",
    "institutional_neutrality": "INSTITUTIONAL_NEUTRALITY",
    "emotional_substitution": "EMOTIONAL_SUBSTITUTION",
    "bureaucratic_obscurity": "BUREAUCRATIC_OBSCURITY",
    "inevitability_frame": "INEVITABILITY_FRAME",
    "appeal_to_tradition": "APPEAL_TO_TRADITION",
    "false_equivalence": "FALSE_EQUIVALENCE",
    "moral_high_ground": "MORAL_HIGH_GROUND",
    # Media domain
    "editorial_as_news": "MEDIA_EDITORIAL_AS_NEWS",
    "anonymous_attribution": "MEDIA_ANONYMOUS_ATTRIBUTION",
    "weasel_quantifiers": "MEDIA_WEASEL_QUANTIFIERS",
    "false_balance": "MEDIA_FALSE_BALANCE",
    "emotional_lead": "MEDIA_EMOTIONAL_LEAD",
    "buried_qualifier": "MEDIA_BURIED_QUALIFIER",
    "selective_quotation": "MEDIA_SELECTIVE_QUOTATION",
    "asymmetric_attribution": "MEDIA_ASYMMETRIC_ATTRIBUTION",
    "speculative_framing": "MEDIA_SPECULATIVE_FRAMING",
    # Financial domain
    "survivorship_bias": "FIN_SURVIVORSHIP_BIAS",
    "anchoring": "FIN_ANCHORING",
    "cherry_picked_timeframe": "FIN_CHERRY_PICKED_TIMEFRAME",
    "projection_as_fact": "FIN_PROJECTION_AS_FACT",
    "recency_extrapolation": "FIN_RECENCY_EXTRAPOLATION",
    # v1.2.0 subtle manipulation patterns
    "soft_consensus": "SOFT_CONSENSUS",
    "competence_dismissal": "COMPETENCE_DISMISSAL",
    "vague_institutional_appeal": "VAGUE_INSTITUTIONAL_APPEAL",
    "aspirational_deflection": "ASPIRATIONAL_DEFLECTION",
    "dismissal_by_reframing": "DISMISSAL_BY_REFRAMING",
}

# Reverse map for reporting
PATTERN_ID_TO_TAG = {v: k for k, v in TAG_TO_PATTERN_ID.items()}


def parse_corpus(filepath: str | Path) -> list[CalibrationSample]:
    """
    Parse a calibration corpus file into a list of samples.

    Args:
        filepath: Path to the corpus text file.

    Returns:
        List of CalibrationSample objects.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Corpus file not found: {filepath}")

    content = filepath.read_text(encoding="utf-8")

    # Normalize: split on lines that are just --- (with optional whitespace)
    # This handles --- at start of file, between blocks, and at end
    blocks = re.split(r"(?:^|\n)\s*---\s*(?:\n|$)", content)

    samples = []
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("#"):
            continue

        sample = _parse_block(block)
        if sample:
            samples.append(sample)

    return samples


def _parse_block(block: str) -> Optional[CalibrationSample]:
    """Parse a single sample block."""
    lines = block.split("\n")

    # Extract metadata lines (key: value) from the top
    metadata = {}
    text_lines = []
    in_text = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue  # Skip comments

        if not in_text:
            match = re.match(r"^(tags|severity|source|notes|domain)\s*:\s*(.+)$", stripped, re.IGNORECASE)
            if match:
                key = match.group(1).lower()
                value = match.group(2).strip()
                metadata[key] = value
            elif stripped:
                # First non-metadata, non-empty line starts the text
                in_text = True
                text_lines.append(line)
        else:
            text_lines.append(line)

    text = "\n".join(text_lines).strip()
    if not text:
        return None

    # Parse tags
    raw_tags = metadata.get("tags", "clean")
    tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
    if not tags:
        tags = ["clean"]

    severity = metadata.get("severity", "none").lower()
    source = metadata.get("source", "unknown")
    notes = metadata.get("notes", "")
    domain = metadata.get("domain", "legal")
    is_clean = "clean" in tags

    return CalibrationSample(
        text=text,
        tags=tags,
        severity=severity,
        source=source,
        notes=notes,
        domain=domain,
        is_clean=is_clean,
    )


def parse_all_corpora(corpus_dir: str | Path) -> list[CalibrationSample]:
    """Parse all .txt corpus files in a directory."""
    corpus_dir = Path(corpus_dir)
    samples = []
    for filepath in sorted(corpus_dir.glob("*.txt")):
        samples.extend(parse_corpus(filepath))
    return samples
