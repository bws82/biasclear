# BiasClear — Technical Brief for Funders and Collaborators

**March 2026**

## What BiasClear Is

BiasClear is a structural bias detection engine that scans text for rhetorical manipulation patterns — framing, manufactured consensus, causal totalization, authority substitution, false urgency — and explains exactly how the text is engineered to influence the reader.

It is not a sentiment classifier. It does not flag opinions for being unpopular. It identifies the *structural techniques* that make text persuasive in ways the reader may not notice.

## What Makes It Novel

**1. Deterministic + LLM hybrid architecture.** BiasClear runs a frozen core of 42 hand-authored detection patterns across 4 domains as deterministic code (no ML weights). These patterns fire identically every time, on every run. An LLM layer (currently Claude Sonnet via AWS Bedrock) then analyzes what the rules cannot see — novel manipulation, contextual framing, implicit bias. The deterministic core governs the LLM layer, not the other way around.

**2. Persistent Influence Theory (PIT).** The detection patterns are organized under a published theoretical framework — PIT — which models structural persuasion across three tiers: ideological, psychological, and institutional. PIT is a preprint published on [Zenodo](https://doi.org/10.5281/zenodo.18676405) and [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6270159). It has not yet undergone formal peer review.

**3. Auditability.** Every scan produces a SHA-256 hash-chained audit entry. The chain is tamper-evident and append-only. Each result includes a full score breakdown showing exactly which patterns fired, what penalties were applied, and why. This is designed for environments where explainability is not optional — legal, regulatory, compliance.

**4. Identity-neutral detection.** The system detects structural distortion regardless of who is being discussed. "Trump is ruining everything" and "Biden is ruining everything" trigger the same causal totalization patterns. Bounded factual claims ("The policy caused me to lose my health insurance") stay clean. This is validated by 38 symmetry and boundary tests.

**5. Domain-specific coverage.** Four detection domains — Legal, Media, Financial, General — with patterns built from real-world examples (opposing counsel briefs, news articles, financial reports). Legal patterns detect settled-law dismissals, merit attacks, sanctions threats. Media patterns detect weasel quantifiers, buried qualifiers, editorial-as-news framing.

## What Is Deterministic vs. LLM-Assisted

| Layer | What It Does | Deterministic? |
|-------|-------------|----------------|
| Frozen Core (42 patterns) | Structural pattern matching via compiled regex + logic | Yes — same input always produces same output |
| PIT Tier Classification | Maps flags to influence tier (ideological, psychological, institutional) | Yes — rule-based mapping |
| Score Calculation | Weighted penalty aggregation from all flags | Yes — algorithmic, no ML |
| SHA-256 Audit Chain | Hash-chained provenance for every scan | Yes — cryptographic |
| Deep Analysis | Contextual framing, novel patterns, nuance detection | No — LLM-assisted (Bedrock/Gemini) |
| Explanation Generation | Natural language explanation of findings | No — LLM-generated |
| Bias Correction | Suggests debiased rewrites | No — LLM-generated |

In `local` mode, BiasClear runs without any LLM — fully deterministic, zero external dependencies. In `full` mode, both layers work together.

## What Is Already Validated

- **318 passing tests** across the full test suite
- **38 causal-blame symmetry and boundary tests** — political figures, authority figures, institutions treated identically
- **Boundary control tests** — bounded factual claims verified clean of false positives
- **3 domain calibration sets** — legal, media, financial examples with expected outcomes
- **Live production verification** — `mode=full`, `source: llm+local`, `degraded: false` confirmed on public domain

## What Already Works Well

- Deterministic core catches structural manipulation that LLMs alone miss or normalize
- Legal domain detects real opposing-counsel rhetoric patterns from actual litigation
- Causal blame detection (new, March 2026) catches totalizing attribution without flagging bounded factual claims
- Audit chain provides cryptographic provenance that no comparable tool offers
- Graceful degradation — if the LLM is unavailable, the system falls back to local-only scanning with transparent degradation signals
- Open source (AGPL-3.0) with published preprint and public API

## What Still Needs Support

**Calibration depth.** The frozen core has 42 patterns with test coverage, but systematic precision/recall measurement across large corpora has not been completed. A calibration corpus of 500-1000 labeled examples per domain would significantly strengthen confidence claims.

**LLM consistency.** The AI layer introduces scoring variance across entity swaps — the same sentence structure about different subjects can produce different AI-layer penalties. The deterministic core is fully symmetric, but the LLM is not. Prompt engineering and structured output constraints can reduce this but not eliminate it entirely.

**Peer review.** PIT is a preprint. Formal peer review would strengthen the theoretical foundation. Collaborators with expertise in rhetoric, persuasion psychology, or computational linguistics would be valuable.

**Scale testing.** BiasClear has been tested on individual documents and short passages. Performance on long documents (10K+ words), batch processing, and high-throughput API usage has not been stress-tested.

**Additional domains.** Healthcare, education, and government communications are natural extensions but require domain-expert pattern authoring.

## Why Funding Helps Now

BiasClear is past prototype. It has a working public API, a published theoretical framework, a deterministic detection engine, an LLM-assisted analysis layer, cryptographic auditability, and 318 passing tests. It is deployed on AWS infrastructure and serving real scans.

What it needs to become a credible tool for regulated industries:

1. **Calibration corpus development** — labeled datasets for precision/recall validation ($5-15K for domain expert annotation)
2. **Compute for LLM consistency research** — structured output experiments to reduce AI-layer variance (AWS/Anthropic credits)
3. **Academic collaboration** — co-authorship on peer-reviewed publication of PIT framework
4. **Security audit** — third-party review of the audit chain and API security model
5. **Domain expansion** — expert-authored patterns for healthcare and government communications

## Technical Stack

- **Language:** Python 3.12
- **Framework:** FastAPI + uvicorn
- **LLM Primary:** AWS Bedrock (Claude Sonnet 4.6)
- **LLM Fallback:** Google Gemini 2.5 Flash
- **Hosting:** Render (Docker)
- **Database:** SQLite (audit chain, learned patterns)
- **License:** AGPL-3.0
- **Package:** [PyPI](https://pypi.org/project/biasclear)
- **Source:** [GitHub](https://github.com/bws82/biasclear)
- **Preprint:** [Zenodo DOI](https://doi.org/10.5281/zenodo.18676405) | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6270159)

## Contact

Bradley Slimp — [brad@biasclear.com](mailto:brad@biasclear.com) — [LinkedIn](https://www.linkedin.com/in/brad-s-82694021/)
