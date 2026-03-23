# BiasClear — Funder Brief

## What It Is

BiasClear is an open-source structural bias detection engine. It scans text for rhetorical manipulation patterns — manufactured consensus, authority substitution, false urgency, dissent dismissal — and explains exactly how the text is structured to influence the reader.

It is not a sentiment classifier. It identifies the *structural techniques* that make text persuasive in ways the reader may not notice.

## What Makes It Unique

1. **Deterministic core.** 42 hand-authored detection patterns across 4 domains (Legal, Media, Financial, General) fire identically every time. No ML weights, no model drift.

2. **Hybrid architecture.** The deterministic core governs an LLM layer (currently Claude Sonnet via AWS Bedrock) that detects what rules cannot — novel manipulation, contextual framing, implicit bias. The rules constrain the model, not the other way around.

3. **Identity-neutral detection.** "Trump is ruining everything" and "Biden is ruining everything" trigger the same patterns. Bounded factual claims stay clean. Verified by 32 symmetry and boundary tests.

4. **Cryptographic auditability.** Every scan produces a SHA-256 hash-chained audit entry. Tamper-evident, append-only. Designed for legal, regulatory, and compliance contexts.

5. **Published theoretical framework.** Built on Persistent Influence Theory (PIT), published on Zenodo (DOI: 10.5281/zenodo.18676405) and SSRN. PIT has not yet undergone formal peer review.

## What Exists Today

- Live public API at [biasclear.com](https://biasclear.com) with interactive playground
- 326 passing tests including 32 symmetry/boundary tests
- 118-sample calibration corpus across 4 domains
- Full CI pipeline: test, security audit, secret scanning, static analysis
- AWS Bedrock production infrastructure with Gemini fallback and circuit breaker
- Background health canary verifying LLM availability every 4 minutes
- Open source under AGPL-3.0 with public GitHub repository

## What Is Still Early

These are stated honestly:

- **PIT is a preprint.** Formal peer review has not occurred.
- **Calibration corpus is small.** 118 samples demonstrate the approach; statistically meaningful per-domain validation requires 500-1000 samples.
- **LLM layer introduces variance.** The deterministic core is fully symmetric; the LLM layer can produce different results across entity swaps.
- **Solo developer.** Built and maintained by one person (Bradley Slimp).
- **Limited production traffic history.** The system is live but does not yet have substantial usage data.
- **Long documents untested.** Validated on passages and short documents, not 10K+ word texts.

## Why Fund It Now

BiasClear is past prototype but needs targeted support to become credible for regulated industries. The engine works. The theoretical framework exists. The infrastructure is healthy. What is missing is the validation depth and expert review that turns a working tool into a trusted one.

Funding at this stage has high leverage because the core product exists — investment goes directly to validation, calibration, and credibility, not to building something from scratch.

## What Funding Unlocks

### $10K — Validation Foundation
- Professional calibration corpus development: 500+ labeled samples across 2 priority domains
- Systematic precision/recall measurement with published results
- Updated preprint with empirical validation data

### $25K — Credibility Threshold
- Everything in $10K, plus:
- Full 4-domain calibration corpus (500+ samples each)
- LLM consistency research: structured output experiments to reduce AI-layer variance
- Security audit of the API and audit chain by an independent reviewer
- Compute credits for systematic testing across model versions

### $50K — Research and Domain Expansion
- Everything in $25K, plus:
- Academic collaboration toward peer-reviewed publication of PIT framework
- Expert-authored detection patterns for 1-2 new domains (healthcare, government communications)
- Long-document and batch processing stress testing
- Community contributor onboarding and documentation

## Technical Summary

| Component | Detail |
|-----------|--------|
| Engine | Python 3.12, FastAPI |
| Frozen Core | 42 deterministic patterns, 4 domains |
| LLM | AWS Bedrock (Claude Sonnet), Gemini fallback |
| Auditability | SHA-256 hash-chained, tamper-evident |
| License | AGPL-3.0 |
| Live | [biasclear.com](https://biasclear.com) |
| Source | [github.com/bws82/biasclear](https://github.com/bws82/biasclear) |
| Preprint | [DOI 10.5281/zenodo.18676405](https://doi.org/10.5281/zenodo.18676405) |

## Contact

Bradley Slimp — [brad@biasclear.com](mailto:brad@biasclear.com) — [LinkedIn](https://www.linkedin.com/in/brad-s-82694021/)
