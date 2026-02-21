"""
Frozen Core — Immutable Inner Ring

This module IS the product. Everything else is enhancement.

The frozen core defines:
  1. What constitutes a distortion (immutable definitions)
  2. The PIT tier taxonomy (immutable structure)
  3. Structural detection patterns (deterministic, no LLM)
  4. The evaluation engine (rule-based, zero API cost)

This module is FROZEN. It does not learn, adapt, or drift.
Its principles are code, not weights. They cannot be:
  - Prompt-injected
  - Modified at runtime
  - Overridden by model output
  - Updated without a new versioned release

The outer learning ring (patterns/learned.py) can expand
DETECTION capability. It cannot redefine what a distortion IS.
That definition lives here and only here.

Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# --- Core Version (stamped on every scan result) ---
CORE_VERSION = "1.2.0"


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Flag:
    """A single detection flag raised during evaluation."""
    category: str          # e.g., "structural", "marker", "legal"
    pattern_id: str        # e.g., "CLAIM_WITHOUT_CITATION"
    matched_text: str      # The text fragment that triggered the flag
    pit_tier: int          # 1, 2, or 3
    severity: str          # "low", "moderate", "high", "critical"
    description: str       # Human-readable explanation


@dataclass
class CoreEvaluation:
    """Result of a frozen core evaluation."""
    aligned: bool
    knowledge_type: str         # "sense", "revelation", "mixed", "neutral"
    confidence: float           # 0.0 to 1.0
    flags: list[Flag]
    primary_principle: str      # Which principle is most at stake
    pit_tier_active: Optional[str]  # Most active PIT tier, or None
    summary: str                # Human-readable summary
    core_version: str = CORE_VERSION


# ============================================================
# IMMUTABLE PRINCIPLES
# ============================================================

PRINCIPLES = {
    "Truth": {
        "definition": "Do not distort reality or mislead",
        "test": "Is this grounded in verifiable evidence or speculative consensus?",
    },
    "Justice": {
        "definition": "Treat sources, people, and statements fairly",
        "test": "Does this treat all parties fairly, or dismiss without engagement?",
    },
    "Clarity": {
        "definition": "Seek genuine understanding for the reader",
        "test": "Does this clarify or does it obscure?",
    },
    "Agency": {
        "definition": "The reader should be empowered to decide, not manipulated into compliance",
        "test": "Does this empower or does it create dependency?",
    },
    "Identity": {
        "definition": "Evaluate claims on their merit, not their origin",
        "test": "Is this judged by substance or by who said it?",
    },
}

# ============================================================
# PIT TIER DEFINITIONS (Immutable)
# ============================================================

PIT_TIERS = {
    1: {
        "name": "Ideological",
        "alias": "The Source Code",
        "description": (
            "Foundational meta-narratives that define epistemic boundaries. "
            "Renders incompatible information illegitimate before it is even evaluated."
        ),
        "distortion_patterns": [
            "Presupposes a worldview without evidence",
            "Frames dissent as ignorance or bad faith",
            "Conflates correlation with causation",
            "Uses loaded language to predetermine conclusions",
            "Appeals to consensus as a substitute for evidence",
        ],
    },
    2: {
        "name": "Psychological",
        "alias": "The Compiler",
        "description": (
            "Cognitive and social processes that compile ideological boundaries "
            "into personal filters. Manages dissonance by favoring confirming data."
        ),
        "distortion_patterns": [
            "Uses fear or urgency to motivate compliance",
            "Appeals to authority without substantive argument",
            "Creates false urgency to bypass critical thinking",
            "Frames options as binary when they are not",
            "Uses shame, guilt, or social pressure as a lever",
        ],
    },
    3: {
        "name": "Institutional",
        "alias": "The Execution",
        "description": (
            "Institutional structures that amplify compliant narratives "
            "and suppress dissent. Embeds persistence in societal machinery."
        ),
        "distortion_patterns": [
            "Cites institutional authority as proof",
            "Appeals to credentials over substance",
            "Dismisses non-institutional sources without engagement",
            "Uses bureaucratic language to obscure meaning",
            "Frames institutional position as inherently neutral",
        ],
    },
}


# ============================================================
# STRUCTURAL DETECTION PATTERNS (The real detection engine)
# ============================================================

@dataclass
class StructuralPattern:
    """
    A structural detection pattern. Unlike keyword markers, these
    encode RELATIONSHIPS between linguistic elements — assertion +
    authority + no evidence, for example.

    Each pattern is:
    - Deterministic (regex-based, no LLM)
    - Mapped to a PIT tier
    - Scored for severity
    - Immutable (part of the frozen core)
    """
    id: str
    name: str
    description: str
    pit_tier: int
    severity: str
    principle: str  # Which principle this violates
    # Regex patterns — ALL must match for the pattern to trigger
    # Uses named groups for matched_text extraction
    indicators: list[str]
    # Minimum number of indicators that must match
    min_matches: int
    # If True, suppress this pattern when matched text appears near a citation
    suppress_if_cited: bool = False


# --- Tier 1: Ideological Structural Patterns ---

STRUCTURAL_PATTERNS: list[StructuralPattern] = [
    StructuralPattern(
        id="CONSENSUS_AS_EVIDENCE",
        name="Consensus Substituted for Evidence",
        description=(
            "Uses agreement among people or institutions as proof of truth, "
            "rather than presenting the underlying evidence."
        ),
        pit_tier=1,
        severity="high",
        principle="Truth",
        indicators=[
            r"\b(?:(?:everyone|everybody)\s+(?:knows?|agrees?|understands?|recognizes?|accepts?|sees?|can\s+see)|"
            r"all\s+(?:\w+\s+)?(?:experts?|scientists?|researchers?)|"
            r"most\s+(?:people|experts?|scholars?)|"
            r"the\s+(?:\w+\s+)?consensus(?!\s+(?:forecast|estimate|projection|expectation|view|number|figure|range))|"
            r"(?:experts?|scientists?|researchers?|scholars?)\s+(?:unanimously|overwhelmingly)\s+"
            r"(?:agree|concur|confirm)|"
            r"unanimously\s+(?:agree|agreed|concur|accept|endorse)|"
            r"widely\s+accepted|universally\s+recognized|"
            r"broadly\s+agreed|generally\s+accepted|"
            r"it\s+is\s+(?:widely|broadly|universally)\s+(?:known|accepted|recognized))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="CLAIM_WITHOUT_CITATION",
        name="Authoritative Claim Without Citation",
        description=(
            "Asserts something as established fact using authority language "
            "but provides no source, citation, or verifiable reference."
        ),
        pit_tier=1,
        severity="moderate",
        principle="Truth",
        indicators=[
            r"\b(?:studies?\s+(?:show|prove|demonstrate|confirm|indicate|suggest|find|reveal)|"
            r"research\s+(?:shows?|proves?|demonstrates?|confirms?|indicates?|suggests?|has\s+shown)|"
            r"experts?\s+(?:say|agree|confirm|believe|have\s+(?:found|shown|concluded))|"
            r"science\s+(?:shows?|proves?|has\s+(?:shown|proven|established))|"
            r"data\s+(?:shows?|proves?|suggests?|confirms?|indicates?)|"
            r"evidence\s+(?:shows?|suggests?|indicates?|confirms?|demonstrates?))\b",
        ],
        min_matches=1,
        suppress_if_cited=True,
    ),
    StructuralPattern(
        id="DISSENT_DISMISSAL",
        name="Dissent Dismissed by Label",
        description=(
            "Opposing viewpoints are dismissed through labeling rather than "
            "substantive rebuttal. The label substitutes for argument."
        ),
        pit_tier=1,
        severity="high",
        principle="Justice",
        indicators=[
            r"\b(?:fringe|debunked|conspiracy|discredited|pseudoscience|"
            r"junk\s+science|misinformation|disinformation|"
            r"deniers?|denialists?|cranks?|quacks?|"
            r"has\s+been\s+(?:thoroughly\s+)?(?:debunked|disproven|discredited|refuted)|"
            r"no\s+(?:serious|credible|reputable)\s+(?:scientist|researcher|expert|scholar))\b",
        ],
        min_matches=1,
    ),

    # --- Tier 2: Psychological Structural Patterns ---

    StructuralPattern(
        id="FALSE_BINARY",
        name="False Binary / False Dilemma",
        description=(
            "Frames a situation as having only two options when additional "
            "alternatives exist. Forces a choice between extremes."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Clarity",
        indicators=[
            r"\b(?:either\s+.{3,60}\s+or\b|"
            r"you(?:'re|\s+are)\s+either\s+.{3,40}\s+or\b|"
            r"(?:only|just)\s+two\s+(?:options?|choices?|alternatives?|paths?)|"
            r"there(?:'s|\s+is)\s+(?:only|just)\s+(?:one\s+(?:way|option|choice))|"
            r"(?:no|without\s+(?:any)?)\s+(?:middle\s+ground|third\s+(?:option|way|alternative|choice)|other\s+(?:option|choice|alternative)s?)|"
            r"(?:a\s+)?(?:clear|stark|simple|binary)\s+choice\s*:.{3,60}\s+or\s+|"
            r"if\s+(?:you(?:'re|\s+are))\s+not\s+.{3,40}(?:then|,)\s+you(?:'re|\s+are))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="FEAR_URGENCY",
        name="Fear-Based Urgency",
        description=(
            "Uses fear, catastrophic language, or artificial time pressure "
            "to bypass critical evaluation and force compliance."
        ),
        pit_tier=2,
        severity="high",
        principle="Agency",
        indicators=[
            r"\b(?:catastroph(?:e|ic)|devastating|irreversibl[ey]|"
            r"point\s+of\s+no\s+return|too\s+late|"
            r"(?:act|decide|move)\s+(?:now|immediately|before\s+it(?:'s|\s+is)\s+too\s+late)|"
            r"(?:running\s+out\s+of|no)\s+time|"
            r"(?:dire|grave|existential)\s+(?:threat|risk|consequences?|danger)|"
            r"(?:complete|total|utter|imminent)\s+(?:collapse|destruction|failure|ruin|disaster)|"
            r"(?:window|opportunity)\s+(?:is\s+)?(?:closing|narrowing|disappearing|running\s+out)|"
            r"(?:crisis|emergency)\s+(?:demands?|requires?|necessitates?)|"
            r"(?:severe|permanent)\s+(?:and\s+)?(?:permanent|severe|irreversibl[ey]|lasting)|"
            r"consequences\s+will\s+be\s+(?:severe|dire|catastrophic|devastating|permanent)|"
            r"if\s+(?:we|you)\s+(?:don(?:'t|ot)|fail\s+to)\s+act)\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="SHAME_LEVER",
        name="Shame or Social Pressure as Lever",
        description=(
            "Uses social shame, guilt, or peer pressure to coerce agreement "
            "rather than persuading through evidence or argument."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Agency",
        indicators=[
            r"\b(?:any\s+(?:reasonable|rational|intelligent|educated|decent)\s+person|"
            r"only\s+(?:a\s+fool|an?\s+idiot|ignorant\s+people?)|"
            r"(?:right|wrong)\s+side\s+of\s+history|"
            r"history\s+will\s+(?:judge|remember|not\s+(?:forget|forgive))|"
            r"how\s+(?:can|could)\s+(?:you|anyone)\s+(?:possibly|seriously)|"
            r"(?:everyone|all)\s+(?:reasonable|intelligent|educated)\s+people?\s+"
            r"(?:know|agree|understand|accept))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="EMOTIONAL_SUBSTITUTION",
        name="Emotional Appeal Substituted for Argument",
        description=(
            "Replaces logical argument or evidence with emotional language "
            "designed to produce a feeling rather than an understanding."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Clarity",
        indicators=[
            r"\b(?:(?:heartbreaking|shocking|outrageous|disgusting|appalling|"
            r"horrifying|terrifying|sickening|unconscionable)\s+(?:that|how|when)|"
            r"(?:simply|truly|absolutely|utterly)\s+(?:heartbreaking|devastating|"
            r"unconscionable|horrifying|appalling|outrageous)|"
            r"(?:the\s+)?(?:suffering|pain|devastation|tragedy|anguish)\s+"
            r"speaks?\s+for\s+(?:itself|themselves)|"
            r"no\s+(?:decent|reasonable|compassionate|caring|moral)\s+"
            r"(?:person|human|individual)\s+(?:could|would|can|should)|"
            r"(?:think\s+(?:of|about)\s+the\s+children|won(?:'t|\s+not)\s+"
            r"(?:someone|somebody)\s+think\s+of)|"
            r"(?:blood\s+on\s+(?:your|their)\s+hands|"
            r"how\s+(?:do\s+you|can\s+you)\s+(?:sleep|live\s+with)))\b",
        ],
        min_matches=1,
    ),

    # --- Tier 3: Institutional Structural Patterns ---

    StructuralPattern(
        id="CREDENTIAL_AS_PROOF",
        name="Credential Cited as Proof",
        description=(
            "Uses a person's or institution's credentials, title, or status "
            "as the primary evidence for a claim, rather than the underlying argument."
        ),
        pit_tier=3,
        severity="moderate",
        principle="Identity",
        indicators=[
            r"\b(?:(?:as\s+)?(?:a|the)\s+(?:leading|top|renowned|respected|"
            r"prominent|distinguished|eminent|preeminent)\s+"
            r"(?:expert|authority|scientist|researcher|professor|doctor|scholar)|"
            r"with\s+(?:over\s+|combined\s+)?(?:\d+|twenty|thirty|forty|fifty|sixty)\s+years?\s+(?:of\s+)?experience|"
            r"holders?\s+of\s+(?:advanced|doctoral|graduate|terminal|multiple)\s+degrees?|"
            r"(?:nobel|pulitzer|award)[- ]winning|"
            r"(?:harvard|stanford|mit|oxford|cambridge)[- ](?:trained|educated|based)|"
            r"(?:my|his|her|their|our|its)\s+(?:extensive|impressive|unparalleled|"
            r"unmatched|superior)\s+(?:credentials?|qualifications?|expertise|experience)|"
            r"(?:our\s+)?qualifications?\s+(?:speak|stand)\s+for\s+(?:them|it)sel(?:f|ves)|"
            r"credentials?\s+(?:speak|stand)\s+for\s+(?:them|it)sel(?:f|ves)|"
            r"(?:should\s+)?settle\s+this\s+debate|"
            r"less\s+qualified\s+(?:analysts?|experts?|researchers?|commentators?|"
            r"critics?|opponents?|voices?))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="INSTITUTIONAL_NEUTRALITY",
        name="Institutional Position Framed as Neutral",
        description=(
            "Presents an institution's stance as objective or neutral fact "
            "rather than as one position among possible positions."
        ),
        pit_tier=3,
        severity="moderate",
        principle="Justice",
        indicators=[
            r"\b(?:(?:the\s+)?(?:official|established|accepted|recognized|authoritative|"
            r"institutional)\s+(?:position|view|stance|guidance|recommendation|consensus)|"
            r"according\s+to\s+(?:the\s+)?(?:official|established)\s+(?:position|guidance)|"
            r"(?:every|all)\s+(?:major|leading|reputable)\s+(?:regulatory|governing|"
            r"oversight|scientific|medical|professional)\s+(?:body|bodies|agency|agencies|"
            r"organization|institution)|"
            r"speaks?\s+with\s+(?:one|a\s+single|a\s+unified)\s+"
            r"(?:authoritative|unified|clear)\s+voice|"
            r"(?:as\s+)?(?:a|an)\s+(?:neutral|independent|impartial|objective|unbiased)\s+"
            r"(?:third\s+party|observer|arbiter|assessor|evaluator|authority|organization|body)|"
            r"(?:objectively|independently|impartially)\s+(?:and\s+)?(?:without|free\s+(?:from|of))\s+"
            r"(?:preference|bias|prejudice|partiality|favor)|"
            r"(?:reflects?|represents?)\s+the\s+evidence\s+(?:objectively|independently|impartially|neutrally)|"
            r"the\s+(?:CDC|WHO|FDA|NIH|AMA|ABA|SEC|EPA|DOJ|FBI)\s+"
            r"(?:has\s+)?(?:stated?|confirmed?|determined?|concluded?|established?))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="BUREAUCRATIC_OBSCURITY",
        name="Bureaucratic Language Obscuring Meaning",
        description=(
            "Uses dense institutional or bureaucratic jargon to make a simple "
            "claim appear more authoritative or to obscure its actual meaning."
        ),
        pit_tier=3,
        severity="low",
        principle="Clarity",
        indicators=[
            r"\b(?:pursuant\s+to\s+(?:the\s+)?(?:aforementioned|foregoing|"
            r"operationalization|implementation|effectuation)|"
            r"(?:hereinafter|heretofore|hereinabove|notwithstanding\s+the\s+foregoing)|"
            r"it\s+(?:is|should\s+be)\s+(?:noted|observed|recognized)\s+that|"
            r"(?:the\s+)?(?:above-?referenced|above-?mentioned|above-?described|"
            r"aforementioned)\s+(?:matter|issue|subject|concern)|"
            r"(?:operationalization|effectuate|incentivize|synergize|"
            r"paradigm(?:atic)?|cross-?functional)\s+\w+\s+"
            r"(?:framework|paradigm|metrics?|protocol|methodology|mechanism))\b",
        ],
        min_matches=1,
    ),

    # --- Tier 1: Additional Ideological Patterns ---

    StructuralPattern(
        id="INEVITABILITY_FRAME",
        name="Inevitability Framing",
        description=(
            "Presents an outcome, trend, or position as historically inevitable "
            "to discourage resistance or critical evaluation. Substitutes momentum "
            "narrative for evidence."
        ),
        pit_tier=1,
        severity="moderate",
        principle="Agency",
        indicators=[
            r"\b(?:(?:the\s+)?(?:inevitable|inexorable|inescapable|unstoppable)\s+"
            r"(?:march|trend|shift|move(?:ment)?|direction|trajectory|conclusion|outcome)|"
            r"(?:history|the\s+future|progress|time)\s+"
            r"(?:will\s+(?:show|prove|judge|vindicate|remember)|has\s+shown|is\s+(?:on\s+)?(?:our|the)\s+side)|"
            r"on\s+the\s+(?:right|wrong)\s+side\s+of\s+history|"
            r"(?:this\s+is\s+)?(?:the\s+(?:way|direction)\s+(?:the\s+)?(?:world|field|industry|market|profession)\s+"
            r"is\s+(?:heading|moving|going|trending))|"
            r"(?:there\s+is\s+no|(?:you|we)\s+can(?:no|')?t)\s+"
            r"(?:stopping|resisting|fighting|holding\s+back)\s+(?:this|the\s+(?:tide|trend|future|change)))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="APPEAL_TO_TRADITION",
        name="Appeal to Tradition / Precedent Inertia",
        description=(
            "Cites historical practice, tradition, or 'the way things have always been' "
            "as justification for a position, without evaluating whether the tradition "
            "is actually sound."
        ),
        pit_tier=1,
        severity="moderate",
        principle="Truth",
        indicators=[
            r"\b(?:(?:we(?:'ve|\s+have)?|they(?:'ve|\s+have)?|(?:it\s+)?has)\s+"
            r"always\s+(?:been\s+)?(?:done|worked|operated|functioned|practiced)"
            r"(?:\s+it)?\s+(?:this|that)\s+way|"
            r"(?:time[- ](?:tested|honored|proven)|long[- ]standing|age[- ]old)\s+"
            r"(?:practice|tradition|principle|approach|method|wisdom|custom)\s+"
            r"(?:dictates?|requires?|demands?|shows?|proves?|tells?\s+us)|"
            r"(?:depart(?:ing|ure)?|deviat(?:ing|ion)?|break(?:ing)?)\s+from\s+"
            r"(?:(?:established|accepted|longstanding|traditional|settled)\s+)?"
            r"(?:practice|tradition|norms?|customs?|precedent)\s+"
            r"(?:would\s+be|is)\s+(?:unwise|dangerous|reckless|ill[- ]advised|inadvisable))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="FALSE_EQUIVALENCE",
        name="False Equivalence",
        description=(
            "Presents two unequal positions, arguments, or evidence sets as roughly "
            "equivalent to minimize a stronger position or elevate a weaker one. "
            "Often disguised as 'balanced' analysis."
        ),
        pit_tier=1,
        severity="moderate",
        principle="Justice",
        indicators=[
            r"\b(?:(?:both|each|either)\s+side(?:s)?\s+(?:has|have|makes?|presents?)\s+"
            r"(?:valid|good|legitimate|strong|compelling|reasonable|fair)\s+"
            r"(?:points?|arguments?|claims?|cases?)|"
            r"(?:the\s+truth|reality|the\s+answer)\s+(?:is\s+|lies?\s+)?(?:somewhere\s+)?in\s+the\s+middle|"
            r"(?:there\s+are|we\s+(?:can\s+)?(?:see|find))\s+(?:valid\s+)?(?:arguments?|points?)\s+"
            r"on\s+(?:both|all|either)\s+sides?|"
            r"(?:it(?:'s|\s+is)|this\s+is)\s+(?:not\s+(?:as\s+)?(?:simple|clear[- ]cut|straightforward|"
            r"black\s+and\s+white)\s+as)\s+(?:(?:some|many|most)\s+(?:people|critics?|observers?)\s+)?(?:suggest|claim|argue|think|believe))\b",
        ],
        min_matches=1,
    ),

    # --- Tier 2: Additional Psychological Patterns ---

    StructuralPattern(
        id="MORAL_HIGH_GROUND",
        name="Moral Authority Claim",
        description=(
            "Claims moral superiority to shut down debate. Uses moral framing "
            "to make disagreement appear not just wrong but morally deficient."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Justice",
        indicators=[
            r"\b(?:(?:any|every|no)\s+(?:decent|moral|ethical|responsible|"
            r"right[- ]thinking|reasonable|thoughtful|caring)\s+"
            r"(?:person|human|individual|citizen|professional|leader|organization)\s+"
            r"(?:would|should|must|could|can)\s+(?:see|recognize|understand|agree|acknowledge|know)|"
            r"(?:it(?:'s|\s+is)|this\s+is)\s+(?:simply|just|purely|fundamentally)\s+"
            r"(?:a\s+matter\s+of|about|an?\s+(?:issue|question)\s+of)\s+"
            r"(?:basic\s+)?(?:human\s+)?(?:decency|morality|ethics|dignity|conscience)|"
            r"(?:moral(?:ly)?|ethic(?:al(?:ly)?)?)\s+(?:bankrupt|reprehensible|indefensible|"
            r"unconscionable|abhorrent|repugnant)\s+(?:to|for|that)|"
            r"(?:on\s+the\s+)?(?:right|wrong)\s+side\s+of\s+(?:morality|ethics|decency|justice|history))\b",
        ],
        min_matches=1,
    ),

    # --- Subtle Manipulation Patterns (v1.2.0 — closes detection gaps) ---

    StructuralPattern(
        id="SOFT_CONSENSUS",
        name="Soft Consensus Manufacturing",
        description=(
            "Uses softer consensus language — 'the overwhelming majority', "
            "'growing body of evidence', 'increasingly recognized' — to manufacture "
            "the appearance of agreement without citing specific evidence or sources. "
            "More subtle than explicit 'everyone agrees' but equally manipulative."
        ),
        pit_tier=1,
        severity="moderate",
        principle="Truth",
        indicators=[
            # "the overwhelming/vast/great majority of [group] agree/support"
            r"\b(?:the\s+)?(?:overwhelming|vast|great|clear|strong)\s+"
            r"(?:majority|bulk|preponderance)\s+of\s+"
            r"(?:\w+\s+){0,5}?"
            r"(?:agree|support|believe|recognize|acknowledge|accept|endorse|"
            r"favor|advocate|concur|confirm)\b",
            # "growing body of evidence/research/consensus suggests/shows"
            r"\b(?:growing|mounting|increasing|expanding|emerging)\s+"
            r"(?:body\s+of\s+)?(?:evidence|research|consensus|agreement|"
            r"recognition|support|literature)\s+"
            r"(?:suggests?|shows?|indicates?|supports?|points?\s+to|"
            r"confirms?|demonstrates?)\b",
            # "increasingly/widely recognized/accepted that"
            r"\b(?:increasingly|now\s+widely|now\s+broadly)\s+"
            r"(?:recognized|accepted|understood|acknowledged|adopted|embraced)\s+"
            r"(?:that|as|by|among|across|in)\b",
        ],
        min_matches=1,
        suppress_if_cited=True,
    ),
    StructuralPattern(
        id="COMPETENCE_DISMISSAL",
        name="Competence-Based Dismissal",
        description=(
            "Dismisses opposing views by questioning the competence, understanding, "
            "or expertise of those who disagree, rather than addressing their arguments. "
            "Substitutes an attack on the critic's qualifications for engagement "
            "with their position."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Justice",
        indicators=[
            # "those who oppose/disagree ... appear to misunderstand/fail to grasp"
            r"\b(?:those\s+who\s+|(?:people|anyone|critics?|opponents?)\s+(?:who\s+)?)"
            r"(?:oppose|disagree|object|resist|question|challenge|doubt|reject)"
            r"(?:\s+\w+){0,5}\s+"
            r"(?:(?:appear|seem)\s+to\s+)?"
            r"(?:misunderstand|fail\s+to\s+(?:grasp|understand|appreciate|comprehend))\b",
            # "simply don't understand the complexity/nuance"
            r"\b(?:(?:simply|clearly|obviously|apparently)\s+)?"
            r"(?:don(?:'t|ot)|do\s+not|fail(?:s)?\s+to)\s+"
            r"(?:fully\s+)?(?:understand|grasp|appreciate|comprehend)\s+"
            r"(?:the\s+)?(?:\w+\s+)?(?:complexity|nuance|subtlet(?:y|ies)|intricac(?:y|ies)|"
            r"reality|scope|implications?|challenges?|requirements?)\b",
            # "lack the expertise/understanding to"
            r"\b(?:lack(?:s|ing)?|without)\s+(?:the\s+)?"
            r"(?:sufficient|adequate|necessary|proper|requisite|required|relevant)?\s*"
            r"(?:expertise|understanding|knowledge|background|training|"
            r"experience|qualifications?|competenc[ey])\s+"
            r"(?:to|in|of|for|about|regarding)\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="VAGUE_INSTITUTIONAL_APPEAL",
        name="Vague Institutional Appeal",
        description=(
            "References unnamed 'leading organizations', 'top institutions', or "
            "'responsible bodies' to create an impression of institutional backing "
            "without identifying specific institutions that can be verified."
        ),
        pit_tier=3,
        severity="moderate",
        principle="Truth",
        indicators=[
            # "leading/major/prominent organizations agree/support/recommend"
            # Allow up to 5 words between org noun and verb (e.g., "across the financial services sector")
            r"\b(?:leading|top|major|prominent|respected|responsible|"
            r"relevant|key|important|significant)\s+"
            r"(?:organizations?|institutions?|bodies|agencies|authorities|"
            r"groups?|stakeholders?|voices?|figures?)\s+"
            r"(?:(?:\w+\s+){0,5}?)?"
            r"(?:have\s+)?(?:agree|support|recognize|endorse|confirm|recommend|"
            r"advocate|call\s+for|emphasize|stress|urge|warn|advise|suggest)\b",
            # "industry/professional leaders have long recognized"
            r"\b(?:industry|sector|professional|regulatory|governing|oversight|"
            r"scientific|academic|medical|expert)\s+"
            r"(?:leaders?|bodies|authorities|groups?|organizations?|voices?|consensus)\s+"
            r"(?:have\s+)?(?:long\s+)?(?:recognized|accepted|emphasized|stressed|"
            r"warned|advocated|recommended|confirmed|supported|endorsed)\b",
        ],
        min_matches=1,
        suppress_if_cited=True,
    ),
    StructuralPattern(
        id="ASPIRATIONAL_DEFLECTION",
        name="Aspirational Deflection",
        description=(
            "Uses aspirational language — 'we are committed to', 'our goal is to', "
            "'we strive to' — as a substitute for evidence of actual achievement. "
            "States intentions as if they were accomplishments, deflecting scrutiny "
            "of actual outcomes."
        ),
        pit_tier=1,
        severity="low",
        principle="Truth",
        indicators=[
            # "our goal/mission/commitment is to"
            r"\b(?:our|the)\s+"
            r"(?:goal|mission|vision|commitment|pledge|promise|"
            r"priority|objective|aspiration)\s+"
            r"(?:is|remains|has\s+(?:always\s+)?been)\s+to\b",
            # "we strive/aim/aspire/endeavor to ensure/build/create"
            r"\bwe\s+(?:strive|aim|aspire|endeavor|seek|work)\s+to\s+"
            r"(?:ensure|build|create|foster|promote|advance|achieve|deliver|"
            r"provide|maintain|improve|uphold|protect|support)\b",
            # "we are deeply/firmly committed to"
            r"\b(?:we|our\s+(?:team|organization|company|institution))\s+"
            r"(?:are\s+)?(?:deeply|fully|firmly|strongly|wholly)?\s*"
            r"(?:committed|dedicated|devoted)\s+to\b",
        ],
        min_matches=2,  # Single aspirational statement is normal; pattern is accumulation
    ),
    StructuralPattern(
        id="DISMISSAL_BY_REFRAMING",
        name="Dismissal by Reframing",
        description=(
            "Reframes or recharacterizes an opposing argument into something different "
            "than what was actually argued, then addresses the reframed version. "
            "More subtle than a straw man — presents the reframing as clarification "
            "or 'what they really mean.'"
        ),
        pit_tier=2,
        severity="moderate",
        principle="Justice",
        indicators=[
            # "what they're really saying/arguing/asking"
            r"\bwhat\s+(?:they(?:'re|\s+are)|he(?:'s|\s+is)|she(?:'s|\s+is))\s+"
            r"(?:really|actually|essentially|fundamentally|truly)\s+"
            r"(?:saying|arguing|asking|suggesting|proposing|demanding|"
            r"claiming|getting\s+at)\b",
            # "this is really/actually/essentially about/just/merely"
            r"\b(?:this|that|the\s+argument|their\s+(?:position|argument|claim))\s+"
            r"(?:is\s+)?(?:really|actually|essentially|fundamentally)\s+"
            r"(?:about|just|merely|nothing\s+more\s+than|"
            r"an?\s+(?:attempt|effort)\s+to)\b",
            # "boiled/stripped down to its core/essence"
            r"\b(?:(?:stripped|boiled|reduced)|when\s+you\s+(?:strip|boil|reduce))\s+"
            r"(?:it\s+)?(?:down\s+)?(?:to\s+)?(?:its?\s+)?"
            r"(?:core|essence|basics?|fundamentals?)\b",
        ],
        min_matches=1,
    ),
]
# These are loaded when domain="legal" is specified

LEGAL_STRUCTURAL_PATTERNS: list[StructuralPattern] = [
    StructuralPattern(
        id="LEGAL_SETTLED_DISMISSAL",
        name="Settled Law Dismissal",
        description=(
            "Uses 'well-settled law' or equivalent to dismiss a legal argument "
            "without engaging its substance. Often used by opposing counsel to "
            "avoid actually arguing the merits."
        ),
        pit_tier=3,
        severity="high",
        principle="Justice",
        indicators=[
            r"\b(?:well[- ]settled(?:\s+law|\s+that|\s+principle)?|"
            r"(?:clearly|plainly)\s+(?:established|settled|erroneous)|"
            r"black[- ]letter\s+law|hornbook\s+law|"
            r"settled\s+(?:law|principle|precedent|authority)|"
            r"controlling\s+authority\s+(?:is\s+)?clear)\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="LEGAL_MERIT_DISMISSAL",
        name="Merit Dismissed Without Engagement",
        description=(
            "Dismisses a legal argument as frivolous, meritless, or vexatious "
            "without substantively addressing the argument itself."
        ),
        pit_tier=3,
        severity="critical",
        principle="Justice",
        indicators=[
            r"\b(?:plainly\s+meritless|wholly\s+(?:without\s+merit|frivolous)|"
            r"patently\s+frivolous|(?:clearly|obviously)\s+frivolous|"
            r"vexatious\s+(?:litigant|litigation|filing)|"
            r"(?:no|lacks?\s+any)\s+(?:legal\s+)?merit|"
            r"fails?\s+as\s+a\s+matter\s+of\s+law|"
            r"no\s+reasonable\s+(?:jury|judge|court|person)\s+"
            r"(?:could|would)\s+(?:find|conclude|agree))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="LEGAL_WEIGHT_STACKING",
        name="Authority Weight Stacking",
        description=(
            "Piles on institutional citations or authority references to create "
            "an impression of overwhelming consensus, substituting volume of "
            "authority for strength of reasoning."
        ),
        pit_tier=3,
        severity="moderate",
        principle="Truth",
        indicators=[
            r"\b(?:(?:the\s+)?(?:weight|overwhelming\s+weight|vast\s+majority|"
            r"great\s+weight)\s+of\s+(?:authority|case\s+law|precedent|the\s+law)|"
            r"(?:every|all|virtually\s+(?:every|all))\s+(?:court|jurisdiction|circuit)\s+"
            r"(?:to\s+(?:have\s+)?(?:address|consider)|that\s+has\s+(?:addressed|considered))|"
            r"(?:no\s+(?:court|jurisdiction|circuit)\s+has\s+(?:ever\s+)?(?:held|found|ruled)))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="LEGAL_SANCTIONS_THREAT",
        name="Sanctions Threat as Silencing Tool",
        description=(
            "Threatens Rule 11 sanctions or similar penalties not to enforce "
            "legitimate standards but to intimidate a party into abandoning "
            "a non-frivolous argument."
        ),
        pit_tier=2,
        severity="high",
        principle="Agency",
        indicators=[
            # Group 1: Explicit sanctions rule references
            r"\b(?:rule\s+11|28\s+U\.?S\.?C\.?\s+§?\s*1927|"
            r"(?:inherent|statutory)\s+(?:authority|power)\s+to\s+sanction)\b",
            # Group 2: Sanctions action language
            r"\b(?:sanctions?\s+(?:are|may\s+be|should\s+be|will\s+be|must\s+be)\s+"
            r"(?:warranted|appropriate|imposed|sought|considered|pursued|explored)|"
            r"(?:filing|seeking|imposing|requesting)\s+sanctions?\s+"
            r"(?:against|for|should|is|are|may|will)|"
            r"(?:subject\s+to|warrants?|merit(?:s|ing)?|justify|justifies)\s+"
            r"sanctions?)\b",
            # Group 3: Frivolous/vexatious ONLY when directly paired with sanctions
            r"\b(?:(?:frivolous|vexatious)\s+(?:(?:and|or)\s+(?:sanctions?-?able|"
            r"warrant(?:s|ing)\s+sanctions?))|"
            r"vexatious\s+(?:litigation|filing|action|claim|motion)\s+"
            r"(?:warrant(?:s|ing)|merit(?:s|ing)?|justif(?:y|ies|ying))\s+sanctions?)\b",
            # Group 4: Sanctions + referral to disciplinary bodies
            r"\b(?:(?:refer(?:ring|ral)?|report(?:ing)?)\s+(?:to\s+)?(?:the\s+)?"
            r"(?:disciplinary|bar|ethics)\s+(?:committee|board|authority|counsel)|"
            r"sanctions?\s+should\s+be\s+(?:considered|imposed|explored))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="LEGAL_PROCEDURAL_GATEKEEPING",
        name="Procedural Gatekeeping to Avoid Substance",
        description=(
            "Uses procedural arguments (waiver, preservation, standing, timeliness) "
            "to avoid addressing the substantive merits of an argument. Distinct from "
            "legitimate procedural objections because the procedural claim is used as "
            "the SOLE basis for dismissal without any engagement with the underlying issue."
        ),
        pit_tier=3,
        severity="moderate",
        principle="Justice",
        indicators=[
            r"\b(?:(?:failed|failure)\s+to\s+(?:properly\s+)?(?:preserve|raise|exhaust|"
            r"assert|present|brief|argue|plead)|"
            r"(?:not\s+(?:properly|timely)\s+)?(?:before\s+(?:this|the)\s+(?:court|tribunal)|"
            r"preserved\s+(?:for|on)\s+(?:appeal|review))|"
            r"(?:waived|forfeited|abandoned|conceded)\s+(?:this|that|the|any)\s+"
            r"(?:argument|claim|issue|objection|right|contention|point)|"
            r"(?:procedurally?\s+(?:barred?|default(?:ed)?|foreclosed?|precluded?))|"
            r"(?:lacks?\s+(?:standing|capacity|authority|jurisdiction)\s+to\s+"
            r"(?:raise|assert|bring|maintain|pursue)))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="LEGAL_STRAW_MAN",
        name="Straw Man Mischaracterization",
        description=(
            "Mischaracterizes the opposing party's argument — typically by overstating, "
            "oversimplifying, or fabricating a position — then attacks the distorted "
            "version rather than the actual argument."
        ),
        pit_tier=2,
        severity="high",
        principle="Truth",
        indicators=[
            # "Plaintiff argues/claims/contends/suggests that [ALL/EVERY/ANY/NEVER/ALWAYS]"
            # — absolutist mischaracterization framing
            r"\b(?:(?:plaintiff|defendant|petitioner|respondent|appellant|appellee|"
            r"(?:opposing|other)\s+(?:party|side|counsel))\s+"
            r"(?:argues?|claims?|contends?|suggests?|asserts?|maintains?|would\s+have\s+"
            r"(?:this|the)\s+(?:court|jury)\s+believe)\s+(?:that\s+)?"
            r"(?:all|every|any|no|never|always|each\s+and\s+every|absolutely|"
            r"the\s+entirety\s+of|(?:without\s+)?any\s+exception))\b",
            # "essentially arguing/asking" — reductive mischaracterization
            r"\b(?:(?:is\s+)?(?:essentially|effectively|really|actually|in\s+(?:effect|essence))\s+"
            r"(?:arguing|asking|claiming|demanding|suggesting|requesting|contending)\s+(?:that\s+)?"
            r"(?:this\s+(?:court|jury)|(?:we|the\s+(?:defendant|plaintiff)))\s+"
            r"(?:should|must|(?:would\s+)?have\s+to))\b",
        ],
        min_matches=1,
    ),
]


# --- Media Domain: Structural Patterns ---
# These are loaded when domain="media" is specified

MEDIA_STRUCTURAL_PATTERNS: list[StructuralPattern] = [
    StructuralPattern(
        id="MEDIA_EDITORIAL_AS_NEWS",
        name="Editorializing Disguised as Reporting",
        description=(
            "Uses loaded adjectives, value judgments, or editorial framing in what "
            "is presented as straight news reporting. The judgment is embedded in "
            "the description rather than attributed to a source."
        ),
        pit_tier=1,
        severity="moderate",
        principle="Truth",
        indicators=[
            # "The controversial/failed/embattled/beleaguered/troubled [noun]"
            r"\b(?:the|a|an)\s+(?:controversial|embattled|beleaguered|troubled|"
            r"divisive|polarizing|contentious|ill[- ]fated|misguided|reckless|"
            r"ill[- ]conceived|widely[- ]criticized|much[- ]maligned|"
            r"disgraced|scandal[- ]plagued|under[- ]fire|"
            r"so[- ]called|self[- ]styled|self[- ]proclaimed)\s+"
            r"(?:\w+\s+)?"  # Allow one optional modifier (e.g., "controversial tax policy")
            r"(?:policy|proposal|plan|initiative|program|measure|decision|move|"
            r"leader|official|executive|figure|group|organization|company|bill|law)\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="MEDIA_ANONYMOUS_ATTRIBUTION",
        name="Anonymous or Unverifiable Source Attribution",
        description=(
            "Attributes claims to unnamed, vague, or unverifiable sources. "
            "While legitimate anonymous sourcing exists, this pattern detects "
            "cases where the vagueness itself substitutes for evidence."
        ),
        pit_tier=3,
        severity="moderate",
        principle="Truth",
        indicators=[
            r"\b(?:(?:unnamed|anonymous|unidentified)\s+"
            r"(?:sources?|officials?|insiders?|aides?|staffers?|people|persons?)|"
            r"(?:sources?\s+(?:close\s+to|familiar\s+with|with\s+(?:knowledge|insight)))|"
            r"(?:(?:people|those|individuals)\s+(?:familiar\s+with|briefed\s+on|"
            r"close\s+to)\s+(?:the\s+)?(?:matter|situation|discussions?|negotiations?|deliberations?))|"
            r"(?:critics?\s+(?:say|argue|claim|contend|charge|allege|maintain)\b)|"
            r"(?:insiders?\s+(?:say|reveal|claim|warn|suggest|report)))\b",
        ],
        min_matches=1,
        suppress_if_cited=True,  # Suppress if specific names/orgs appear nearby
    ),
    StructuralPattern(
        id="MEDIA_WEASEL_QUANTIFIERS",
        name="Weasel Words / Vague Quantifiers",
        description=(
            "Uses vague quantifiers to imply broader agreement or evidence "
            "than actually exists. 'Many believe,' 'some experts,' 'it is widely "
            "thought' — these create an impression of consensus without committing "
            "to a verifiable claim."
        ),
        pit_tier=2,
        severity="low",
        principle="Clarity",
        indicators=[
            r"\b(?:(?:many|some|numerous|several|various|countless|growing\s+number\s+of)\s+"
            r"(?:experts?|analysts?|observers?|critics?|commentators?|researchers?|"
            r"officials?|insiders?|people|believe|say|argue|think|feel|suggest|contend|claim)|"
            r"it\s+(?:is|has\s+been)\s+(?:widely|broadly|generally|commonly|frequently|often)\s+"
            r"(?:believed|thought|assumed|accepted|reported|noted|observed|suggested|argued|felt)|"
            r"(?:there\s+(?:is|are)\s+(?:growing|mounting|increasing|widespread|"
            r"broad|considerable))\s+"
            r"(?:concern|evidence|support|sentiment|consensus|agreement|belief|feeling|sense))\b",
        ],
        min_matches=2,  # Require 2 instances — single weasel word is common in legitimate writing
    ),
    StructuralPattern(
        id="MEDIA_FALSE_BALANCE",
        name="False Balance / Both-Sidesism",
        description=(
            "Gives equal presentation weight to a fringe or discredited position "
            "alongside a well-established position, creating a false impression "
            "of legitimate debate. Distinct from genuine balanced reporting."
        ),
        pit_tier=1,
        severity="high",
        principle="Justice",
        indicators=[
            # "Some/others say [fringe claim], while/but [mainstream scientists/experts] disagree"
            r"\b(?:(?:some|others?|a\s+(?:few|handful|minority))\s+"
            r"(?:say|believe|argue|claim|contend|insist|maintain)\s+"
            r"(?:that\s+)?.{10,80}?"
            r"(?:while|but|however|although|yet)\s+"
            r"(?:(?:most|mainstream|the\s+majority\s+of|established|leading)\s+)?"
            r"(?:scientists?|experts?|researchers?|doctors?|economists?|scholars?|"
            r"the\s+scientific\s+community)"
            r".{0,60}?"  # Allow qualifier phrase (e.g., "at major institutions")
            r"(?:say|disagree|reject|dispute|counter|point\s+out|emphasize|note|maintain))\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="MEDIA_EMOTIONAL_LEAD",
        name="Emotional Lead / Hook",
        description=(
            "Opens a news piece with emotionally charged framing designed to "
            "create a visceral reaction before facts are presented. The emotional "
            "frame then colors interpretation of subsequent information."
        ),
        pit_tier=2,
        severity="low",
        principle="Clarity",
        indicators=[
            # Emotional adjectives at or near the start of text (first 100 chars)
            # This is a special case — we check position, not just presence
            r"^.{0,50}(?:shocking|heartbreaking|devastating|horrifying|terrifying|"
            r"outrageous|stunning|alarming|disturbing|chilling|sickening|"
            r"gut[- ]wrenching|jaw[- ]dropping|eye[- ]opening|mind[- ]boggling|"
            r"bombshell|explosive|damning|damaging|scathing|searing|blistering|"
            r"firestorm|backlash|uproar|outcry|fury)\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="MEDIA_BURIED_QUALIFIER",
        name="Buried Qualifier / Buried Denial",
        description=(
            "Places critical qualifying information — corrections, denials, "
            "caveats, or exculpatory context — deep in the text after the "
            "dominant framing has been established. The reader absorbs the "
            "frame before encountering the complication."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Justice",
        indicators=[
            # Qualifier word + negation/denial language appearing deep in text (200+ chars in).
            # The key signal is: transition word followed by qualifying content
            # that contradicts or undermines the preceding narrative.
            r"(?<=.{200})\b(?:"
            r"(?:however|but|although|though|nevertheless|nonetheless|that\s+said)"
            r",?\s+.{5,150}?"
            r"(?:no\s+(?:evidence|proof|indication|link|connection|basis)|"
            r"not\s+(?:confirmed?|verified|established|proven|supported|substantiated)|"
            r"denied|disputed|rejected|retracted|corrected|clarified|"
            r"could\s+not\s+(?:be\s+)?(?:confirmed?|verified|corroborated)|"
            r"remains?\s+(?:unclear|unproven|unverified|disputed|contested))"
            r")\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="MEDIA_SELECTIVE_QUOTATION",
        name="Scare Quotes / Selective Quotation",
        description=(
            "Uses single words or very short fragments in quotation marks to "
            "editorialize — implying doubt, irony, or dismissal without making "
            "an explicit argument. Distinct from legitimate quotation of sources."
        ),
        pit_tier=1,
        severity="low",
        principle="Truth",
        indicators=[
            # Scare quotes: single word or 2-word fragment in quotes used
            # to cast doubt, often preceded by so-called or their
            # Matches straight quotes, curly quotes, and so-called
            '(?:'
            '(?:so[- ]called\\s+)?["\u201c][a-z]{3,15}["\u201d]'  # "reform", "expert"
            '|'
            '(?:their|the|its|his|her)\\s+["\u201c][a-z]{3,20}["\u201d]'  # their "research"
            '|'
            '["\u201c][a-z]+["\u201d]\\s+(?:policy|plan|reform|solution|approach|strategy|theory|claim)'
            # "smart" policy, "balanced" approach
            ')',
        ],
        min_matches=2,  # Single scare quote can be legitimate; pattern is repeated use
    ),
    StructuralPattern(
        id="MEDIA_ASYMMETRIC_ATTRIBUTION",
        name="Asymmetric Source Attribution",
        description=(
            "Uses neutral verbs ('said', 'stated', 'explained') for one side "
            "and loaded verbs ('claimed', 'alleged', 'insisted', 'admitted') for "
            "the other. The verb choice signals credibility to the reader before "
            "the substance is evaluated."
        ),
        pit_tier=1,
        severity="moderate",
        principle="Justice",
        indicators=[
            # Loaded attribution verbs that signal doubt or guilt — distinct
            # from neutral verbs like said/stated/explained/noted
            r"\b(?:claimed|alleged|insisted|admitted|conceded|boasted|"
            r"ranted|lashed\s+out|snapped|fired\s+back|hit\s+back|"
            r"doubled\s+down|refused\s+to\s+(?:say|comment|acknowledge)|"
            r"grudgingly\s+(?:acknowledged|accepted|admitted)|"
            r"tried\s+to\s+(?:claim|argue|justify|explain\s+away))\b",
        ],
        min_matches=2,  # Single loaded verb is normal; pattern requires repeated use
    ),
    StructuralPattern(
        id="MEDIA_SPECULATIVE_FRAMING",
        name="Speculation Presented as Likely",
        description=(
            "Presents speculative outcomes, predictions, or possibilities as "
            "near-certainties using hedged but directional language. 'Could face', "
            "'is expected to', 'is likely to', 'may soon' — these create an "
            "expectation without committing to a verifiable claim."
        ),
        pit_tier=2,
        severity="low",
        principle="Clarity",
        indicators=[
            r"\b(?:"
            r"(?:is|are|was|were)\s+(?:expected|likely|poised|set|slated|"
            r"widely\s+expected|all\s+but\s+certain|virtually\s+certain)\s+to\b|"
            r"(?:could|may|might)\s+(?:soon|eventually|ultimately|well)\s+"
            r"(?:face|lead\s+to|result\s+in|mean|signal|spell|trigger|cause|bring)|"
            r"(?:raises?\s+(?:the\s+)?(?:specter|prospect|possibility|threat|fear|question)\s+(?:of|that))|"
            r"(?:fueling\s+(?:speculation|concerns?|fears?|worries|expectations?)\s+(?:that|about|of))|"
            r"(?:(?:signs?|indications?|signals?)\s+(?:point(?:ing)?|suggest(?:ing)?)\s+(?:to|toward|that))"
            r")\b",
        ],
        min_matches=2,  # Single speculative phrase is normal journalism; pattern is accumulation
    ),
]


# ============================================================
# FINANCIAL STRUCTURAL PATTERNS (domain="financial")
# ============================================================
# These detect distortion patterns specific to financial analysis,
# investment recommendations, and economic commentary.
# Loaded when domain="financial" is specified.

FINANCIAL_STRUCTURAL_PATTERNS: list[StructuralPattern] = [
    StructuralPattern(
        id="FIN_SURVIVORSHIP_BIAS",
        name="Survivorship Bias",
        description=(
            "Draws conclusions from winners/successes while ignoring failures, "
            "dropouts, or non-survivors. Creates a distorted picture of probability "
            "by only examining the surviving sample."
        ),
        pit_tier=1,
        severity="high",
        principle="Truth",
        indicators=[
            r"\b(?:"
            r"(?:(?:top|best|most\s+successful|leading|outperforming|winning)\s+"
            r"(?:funds?|stocks?|companies|firms?|portfolios?|managers?|investors?|traders?)"
            r".{0,30}?"
            r"(?:all|each|consistently|always|invariably|without\s+exception|every\s+one)\s+"
            r"(?:show|demonstrate|prove|have|share|follow|use|employ))|"
            r"(?:(?:every|all)\s+(?:successful|top|great|legendary|billionaire)\s+"
            r"(?:\w+\s+)?"  # Optional modifier: "tech", "retail", etc.
            r"(?:investors?|traders?|fund\s+managers?|CEOs?|entrepreneurs?)"
            r".{0,30}?"
            r"(?:has|have|did|does|follows?|uses?|swears?\s+by|recommends?|bought|held|"
            r"studied|followed|shared|adopted|employed|practiced))|"
            r"(?:(?:if\s+you\s+had\s+invested|a\s+\$?\d[\d,]*\s+investment)\s+(?:in|into)\s+"
            r".{5,60}?(?:would\s+(?:now\s+)?be\s+worth|would\s+have\s+(?:grown|returned|become)))"
            r")\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="FIN_ANCHORING",
        name="Arbitrary Anchoring",
        description=(
            "Sets an arbitrary reference point that biases evaluation of subsequent "
            "numbers. A stock 'down 50% from highs' or 'up 200% from lows' conveys "
            "different impressions of the same price depending on the anchor chosen."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Clarity",
        indicators=[
            r"\b(?:"
            r"(?:(?:down|off|fallen|declined|dropped|lost|crashed)\s+"
            r"(?:\d+%|[\d.]+\s*percent)\s+(?:from|since|off)\s+"
            r"(?:(?:its?|the)\s+)?(?:all[- ]time|52[- ]week|record|recent|pandemic|peak)\s+"
            r"(?:high|peak|top|record|maximum))|"
            r"(?:(?:up|gained|risen|surged|soared|rallied|jumped)\s+"
            r"(?:\d+%|[\d.]+\s*percent)\s+(?:from|since|off)\s+"
            r"(?:(?:its?|the)\s+)?(?:all[- ]time|52[- ]week|record|recent|pandemic|march\s+2020)\s+"
            r"(?:low|bottom|trough|minimum|lows?))|"
            r"(?:(?:trading|priced|valued|selling)\s+at\s+(?:just|only|merely|a\s+fraction\s+of)\s+"
            r"(?:\d+%|[\d.]+\s*percent|a\s+\w+)\s+of\s+"
            r"(?:(?:its?|the)\s+)?(?:book|intrinsic|fair|replacement|peak)\s+(?:value|worth|price))"
            r")\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="FIN_CHERRY_PICKED_TIMEFRAME",
        name="Cherry-Picked Timeframe",
        description=(
            "Selects a specific date range that supports the desired conclusion "
            "while obscuring what happens with different start/end dates. The choice "
            "of timeframe IS the argument rather than supporting it."
        ),
        pit_tier=1,
        severity="high",
        principle="Truth",
        indicators=[
            r"\b(?:"
            r"(?:(?:since|starting\s+(?:from|in)|over\s+the\s+(?:past|last))\s+"
            r"(?:january|february|march|april|may|june|july|august|september|october|"
            r"november|december|\d{4}|the\s+(?:crash|correction|bottom|peak|pandemic|crisis|dip))"
            r".{0,40}?"
            r"(?:(?:returned?|gained?|lost|delivered|produced|generated|averaged)\s+"
            r"(?:an?\s+)?(?:annualized\s+)?(?:\d+%|[\d.]+\s*percent)))|"
            r"(?:(?:in\s+the\s+(?:last|past)\s+(?:\d+|one|two|three|five|ten|twenty)\s+"
            r"(?:years?|months?|quarters?|decades?|trading\s+days?))"
            r".{0,30}?"
            r"(?:outperform|beat|trounce|crush|lag|trail|underperform))"
            r")",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="FIN_PROJECTION_AS_FACT",
        name="Projection Presented as Fact",
        description=(
            "Presents forecasts, estimates, or models as established facts rather "
            "than probabilistic estimates. 'Revenue will reach' vs 'Revenue is "
            "projected to reach' — the missing qualifier hides uncertainty."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Clarity",
        indicators=[
            r"\b(?:"
            r"(?:(?:the\s+(?:stock|market|economy|sector|industry|company|price|index))\s+"
            r"(?:will|is\s+going\s+to|is\s+set\s+to|is\s+destined\s+to)\s+"
            r"(?:reach|hit|surge|soar|crash|plunge|double|triple|decline|grow|rise|fall)\b)|"
            r"(?:(?:revenue|earnings|profits?|sales|growth|GDP|returns?|prices?)\s+"
            r"(?:will|is\s+going\s+to)\s+"
            r"(?:reach|hit|exceed|surpass|top|double|decline|fall|drop|grow)\s+"
            r"(?:\$?[\d,.]+\s*(?:billion|million|trillion|percent|%|bps)?))|"
            r"(?:(?:guaranteed|certain|assured|inevitable|can(?:no|')?t\s+(?:fail|lose|miss))\s+"
            r"(?:returns?|gains?|profits?|growth|income|appreciation|yield))"
            r")\b",
        ],
        min_matches=1,
    ),
    StructuralPattern(
        id="FIN_RECENCY_EXTRAPOLATION",
        name="Recency Bias / Trend Extrapolation",
        description=(
            "Extrapolates recent short-term performance into indefinite future "
            "expectations. 'The fund returned 40% last year' implies it will "
            "continue, but the conclusion is unstated rather than argued."
        ),
        pit_tier=2,
        severity="moderate",
        principle="Truth",
        indicators=[
            r"\b(?:"
            r"(?:(?:has|have)\s+(?:consistently|always|never\s+failed\s+to|"
            r"(?:year\s+after\s+year|quarter\s+after\s+quarter))\s+"
            r"(?:outperformed?|beaten?|delivered|generated|produced|returned))|"
            r"(?:(?:continues?\s+(?:to|its)\s+(?:streak|run|track\s+record|"
            r"winning\s+ways|momentum|trajectory|trend))\b)|"
            r"(?:(?:there(?:'s|\s+is)\s+no\s+(?:reason|sign|indication)\s+"
            r"(?:to\s+(?:think|believe|expect|assume)\s+)?"
            r"(?:this|the|it)\s+(?:will|would|could|should)\s+"
            r"(?:stop|end|slow|change|reverse)))"
            r")\b",
        ],
        min_matches=1,
    ),
]


# ============================================================
# KEYWORD MARKERS (Legacy — still useful for quick flagging)
# ============================================================

SENSE_KNOWLEDGE_MARKERS: list[str] = [
    "experts say",
    "studies show",
    "everyone agrees",
    "it's obvious that",
    "science has proven",
    "the consensus is",
    "most people think",
    "research indicates",
    "authorities confirm",
    "the data suggests",
    "conventional wisdom",
    "mainstream view",
    "widely accepted",
    "common knowledge",
    "it goes without saying",
    "undeniably",
    "unquestionably",
]


# ============================================================
# THE EVALUATION ENGINE
# ============================================================

class FrozenCore:
    """
    Immutable evaluation engine. Deterministic. Zero API cost.

    Runs structural pattern detection + keyword marker scanning.
    Returns a CoreEvaluation with flags, scores, and classification.

    This class is instantiated once as a singleton. It holds no
    mutable state. The patterns it evaluates against are defined
    above as module-level constants and cannot be changed at runtime.
    """

    def __init__(self):
        self._base_patterns = STRUCTURAL_PATTERNS
        self._legal_patterns = LEGAL_STRUCTURAL_PATTERNS
        self._media_patterns = MEDIA_STRUCTURAL_PATTERNS
        self._financial_patterns = FINANCIAL_STRUCTURAL_PATTERNS
        self._keyword_markers = SENSE_KNOWLEDGE_MARKERS

    def evaluate(
        self,
        text: str,
        domain: str = "general",
        external_patterns: Optional[list[StructuralPattern]] = None,
    ) -> CoreEvaluation:
        """
        Evaluate text against the frozen core.

        Args:
            text: The text to evaluate.
            domain: "general" | "legal" | "media" | "financial"
            external_patterns: Additional patterns from the learning ring.
                These EXTEND detection but cannot override frozen definitions.

        Returns:
            CoreEvaluation with full detection results.
        """
        flags: list[Flag] = []

        # --- Phase 1: Structural pattern detection ---
        active_patterns = list(self._base_patterns)
        if domain == "legal":
            active_patterns.extend(self._legal_patterns)
        elif domain == "media":
            active_patterns.extend(self._media_patterns)
        elif domain == "financial":
            active_patterns.extend(self._financial_patterns)
        elif domain == "auto":
            # Run all domain patterns — report which domains flagged
            active_patterns.extend(self._legal_patterns)
            active_patterns.extend(self._media_patterns)
            active_patterns.extend(self._financial_patterns)
        if external_patterns:
            active_patterns.extend(external_patterns)

        for pattern in active_patterns:
            matches = self._match_structural(text, pattern)
            if matches:
                # Citation suppression: if the pattern is designed to detect
                # claims WITHOUT citation, suppress when a citation IS present
                if pattern.suppress_if_cited:
                    if all(self._has_nearby_citation(text, m) for m in matches):
                        continue  # All matches have nearby citations — suppress
                flags.append(Flag(
                    category="structural",
                    pattern_id=pattern.id,
                    matched_text=matches[0][:120],  # Truncate for storage
                    pit_tier=pattern.pit_tier,
                    severity=pattern.severity,
                    description=pattern.description,
                ))

        # --- Phase 2: Keyword marker scan ---
        text_lower = text.lower()
        for marker in self._keyword_markers:
            if marker in text_lower:
                # Context-aware suppression: if the marker appears near
                # a citation pattern, it's likely legitimate — downweight
                # rather than flag. This prevents "Studies show (Smith et al., 2024)"
                # from triggering a false positive.
                if self._has_nearby_citation(text, marker):
                    continue  # Suppress — legitimate citation context
                flags.append(Flag(
                    category="marker",
                    pattern_id=f"SK_{marker.upper().replace(' ', '_')}",
                    matched_text=marker,
                    pit_tier=1,  # Keyword markers default to Tier 1
                    severity="low",
                    description=f"Sense Knowledge marker detected: '{marker}'",
                ))

        # --- Phase 3: Classification ---
        knowledge_type = self._classify_knowledge(flags)
        pit_tier_active = self._dominant_tier(flags)
        primary_principle = self._primary_principle(flags)
        confidence = self._calculate_confidence(flags, text)
        aligned = knowledge_type in ("neutral", "mixed") or len(flags) == 0

        summary = self._build_summary(flags, knowledge_type, pit_tier_active)

        return CoreEvaluation(
            aligned=aligned,
            knowledge_type=knowledge_type,
            confidence=confidence,
            flags=flags,
            primary_principle=primary_principle,
            pit_tier_active=pit_tier_active,
            summary=summary,
        )

    def _match_structural(
        self, text: str, pattern: StructuralPattern
    ) -> list[str]:
        """Match a structural pattern against text. Returns matched fragments."""
        matches = []
        for indicator_regex in pattern.indicators:
            found = re.findall(indicator_regex, text, re.IGNORECASE | re.DOTALL)
            matches.extend(found)
        return matches if len(matches) >= pattern.min_matches else []

    # Citation patterns for context-aware suppression
    _CITATION_PATTERNS = re.compile(
        r"(?:"
        r"\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-z]+))?,?\s*\d{4}\)"  # (Smith et al., 2024)
        r"|"
        r"\[\d+\]"  # [1], [23]
        r"|"
        r"\b\d+\s+[A-Z][a-z]+\.?\s+(?:\d+[a-z]?\s+)?(?:at\s+)?\d+"  # 42 U.S.C. § 1983
        r"|"
        r"(?:Id\.|Ibid\.|Supra|Infra)\s"  # Legal citations
        r"|"
        r"\b[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+"  # Case names: Smith v. Jones
        r"|"
        r"(?:Table|Fig(?:ure)?|Appendix|Exhibit)\s+[A-Z0-9]"  # Table 1, Fig. 3
        r"|"
        r"\bp(?:p)?\.?\s*\d+"  # p. 12, pp. 34-56
        r"|"
        r"(?:Report|Bulletin|Publication|Circular)\s+(?:No\.?|Number)\s+[\d-]+"  # Report No. 2023-47
        r"|"
        r"(?:Nat'l|Fed\.|Dep't|Comm'n|Inst\.|Ass'n|Gov't)\s"  # Institutional abbreviations
        r"|"
        r"\([\w\s.']+,\s*(?:at\s+)?\d{1,4}(?:\s*-\s*\d{1,4})?\)"  # (Source, at 15-23)
        r")",
        re.IGNORECASE,
    )

    def _has_nearby_citation(self, text: str, marker: str, window: int = 120) -> bool:
        """
        Check if a marker appears near a citation pattern.

        Looks within a character window around the marker for evidence
        of a proper citation (parenthetical reference, legal citation,
        figure reference, etc.). If found, the marker is likely being
        used legitimately.

        Args:
            text: The full text.
            marker: The marker string that was found.
            window: Character window to search around the marker.

        Returns:
            True if a citation was found nearby, False otherwise.
        """
        text_lower = text.lower()
        marker_lower = marker.lower()
        idx = text_lower.find(marker_lower)
        if idx == -1:
            return False

        # Extract the window around the marker (from original case text)
        start = max(0, idx - window)
        end = min(len(text), idx + len(marker) + window)
        context = text[start:end]

        return bool(self._CITATION_PATTERNS.search(context))

    def _classify_knowledge(self, flags: list[Flag]) -> str:
        """Classify the knowledge type based on detected flags."""
        if not flags:
            return "neutral"

        structural_count = sum(1 for f in flags if f.category == "structural")
        marker_count = sum(1 for f in flags if f.category == "marker")
        total = structural_count + marker_count

        if structural_count >= 2 or total >= 4:
            return "sense"
        elif total >= 1:
            return "mixed"
        return "neutral"

    def _dominant_tier(self, flags: list[Flag]) -> Optional[str]:
        """Determine which PIT tier is most active."""
        if not flags:
            return None
        tier_counts = {1: 0, 2: 0, 3: 0}
        # Weight structural flags higher than keyword markers
        for f in flags:
            weight = 3 if f.category == "structural" else 1
            tier_counts[f.pit_tier] = tier_counts.get(f.pit_tier, 0) + weight
        dominant = max(tier_counts, key=tier_counts.get)
        if tier_counts[dominant] == 0:
            return None
        tier_info = PIT_TIERS.get(dominant, {})
        return f"tier_{dominant}_{tier_info.get('name', 'unknown').lower()}"

    def _primary_principle(self, flags: list[Flag]) -> str:
        """Determine which principle is most at stake."""
        if not flags:
            return "Truth"
        # Count principle violations from structural patterns
        principle_counts: dict[str, int] = {}
        for f in flags:
            if f.category == "structural":
                # Look up the pattern to get its principle
                for p in self._base_patterns + self._legal_patterns + self._media_patterns + self._financial_patterns:
                    if p.id == f.pattern_id:
                        principle_counts[p.principle] = (
                            principle_counts.get(p.principle, 0) + 1
                        )
                        break
        if principle_counts:
            return max(principle_counts, key=principle_counts.get)
        return "Truth"  # Default

    def _calculate_confidence(self, flags: list[Flag], text: str) -> float:
        """
        Calculate confidence in the evaluation.

        Higher confidence when:
        - More structural patterns match (not just keywords)
        - Text is long enough for meaningful analysis
        - Multiple tiers are involved (cross-validation)
        """
        if not flags:
            # No flags = confident it's clean, but less so for very short text
            return 0.9 if len(text) > 100 else 0.6

        structural = sum(1 for f in flags if f.category == "structural")
        markers = sum(1 for f in flags if f.category == "marker")
        unique_tiers = len(set(f.pit_tier for f in flags))

        base = 0.5
        base += min(structural * 0.12, 0.36)  # Up to +0.36 for structural
        base += min(markers * 0.03, 0.09)      # Up to +0.09 for markers
        base += min(unique_tiers * 0.05, 0.10) # Up to +0.10 for tier diversity

        return min(base, 0.95)

    def _build_summary(
        self,
        flags: list[Flag],
        knowledge_type: str,
        pit_tier_active: Optional[str],
    ) -> str:
        """Build a human-readable summary of the evaluation."""
        if not flags:
            return "No distortion patterns detected. Text appears neutral."

        structural = [f for f in flags if f.category == "structural"]
        markers = [f for f in flags if f.category == "marker"]

        parts = []
        if structural:
            names = list(set(f.pattern_id for f in structural))
            parts.append(
                f"Detected {len(structural)} structural distortion(s): "
                f"{', '.join(names)}."
            )
        if markers:
            parts.append(
                f"Found {len(markers)} Sense Knowledge marker(s)."
            )
        if pit_tier_active:
            tier_num = int(pit_tier_active.split("_")[1])
            tier_info = PIT_TIERS.get(tier_num, {})
            parts.append(
                f"Primary distortion tier: {tier_info.get('name', 'Unknown')} "
                f"({tier_info.get('alias', '')})."
            )
        return " ".join(parts)

    def get_patterns(self, domain: str = "general") -> list[dict]:
        """
        Return all active patterns for a given domain.

        Used by the GET /patterns endpoint to expose the detection surface.
        """
        patterns = list(self._base_patterns)
        if domain in ("legal", "auto"):
            patterns.extend(self._legal_patterns)
        if domain in ("media", "auto"):
            patterns.extend(self._media_patterns)
        if domain in ("financial", "auto"):
            patterns.extend(self._financial_patterns)

        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "pit_tier": p.pit_tier,
                "severity": p.severity,
                "principle": p.principle,
                "domain": (
                    "legal" if p.id.startswith("LEGAL_") else
                    "media" if p.id.startswith("MEDIA_") else
                    "financial" if p.id.startswith("FIN_") else
                    "general"
                ),
            }
            for p in patterns
        ]

    def get_principles_prompt(self) -> str:
        """
        Return the frozen principles formatted for LLM system prompt injection.
        Used by the deep analysis layer (detector.py) when calling the LLM.
        """
        lines = ["## BiasClear Frozen Core Principles (Immutable)\n"]
        for name, p in PRINCIPLES.items():
            lines.append(f"### {name}")
            lines.append(f"- **Definition:** {p['definition']}")
            lines.append(f"- **Test:** {p['test']}")
            lines.append("")

        lines.append("## PIT Distortion Tiers\n")
        for tier_num, tier in PIT_TIERS.items():
            lines.append(f"### Tier {tier_num}: {tier['name']} ({tier['alias']})")
            lines.append(f"_{tier['description']}_")
            for pattern in tier["distortion_patterns"]:
                lines.append(f"- {pattern}")
            lines.append("")

        return "\n".join(lines)


# ============================================================
# SINGLETON — instantiated once, never mutated
# ============================================================

frozen_core = FrozenCore()
