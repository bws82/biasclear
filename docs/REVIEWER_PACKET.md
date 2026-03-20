# BiasClear — Reviewer Packet

**Version:** 1.2.0 | **Date:** March 2026 | **Status:** Live at [biasclear.com](https://biasclear.com)

## What BiasClear Is

BiasClear is a structural bias detection engine. It scans text for rhetorical manipulation patterns — manufactured consensus, authority substitution, false urgency, dissent dismissal, causal totalization — and explains exactly how the text is structured to influence the reader.

It is not a sentiment classifier, toxicity filter, or political bias detector. It identifies structural persuasion techniques that operate below conscious awareness.

## How It Works

BiasClear uses a hybrid architecture with two distinct layers:

**1. Frozen Core (deterministic)**
- 42 hand-authored detection patterns organized under Persistent Influence Theory (PIT)
- 4 detection domains: General (22 patterns), Legal (6), Media (9), Financial (5)
- 3 PIT tiers: Ideological, Psychological, Institutional
- Compiled regex + logic rules — same input always produces same output
- No ML weights, no training data, no model drift

**2. Deep Analysis Layer (LLM-assisted)**
- Contextual analysis via AWS Bedrock (Claude Sonnet 4.6)
- Detects novel manipulation the frozen core cannot see
- Generates natural language explanations
- The deterministic core governs the LLM layer, not the other way around

### Scan Modes

| Mode | Cost | LLM Calls | What It Does |
|------|------|-----------|-------------|
| `local` | Free | 0 | Frozen core only. Fully deterministic. |
| `deep` | Paid | 1 | LLM analysis guided by PIT principles. |
| `full` | Paid | 1–2 | Local + deep combined. Second call for impact projection when truth score < 80. |

### What Is Deterministic vs. LLM-Assisted

| Component | Deterministic? |
|-----------|---------------|
| 42 frozen core patterns | Yes |
| PIT tier classification | Yes |
| Score calculation (weighted penalties) | Yes |
| SHA-256 audit chain | Yes |
| Deep contextual analysis | No — LLM |
| Explanation generation | No — LLM |
| Impact projection | No — LLM |

## Why It Is Differentiated

1. **Structural, not statistical.** Detects the *mechanism* of persuasion, not just surface sentiment.
2. **Deterministic core.** 42 patterns fire identically every time. No model variance on the core layer.
3. **Identity-neutral.** "Trump is ruining everything" and "Biden is ruining everything" trigger the same patterns. Validated by 38 symmetry tests.
4. **Auditable.** Every scan produces a SHA-256 hash-chained audit entry with full score breakdown.
5. **Theoretically grounded.** Built on Persistent Influence Theory, published on [Zenodo](https://doi.org/10.5281/zenodo.18676405) and [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6270159).

## Production Architecture

| Component | Detail |
|-----------|--------|
| Runtime | Docker (python:3.12-slim) |
| Hosting | Render (Oregon) |
| LLM Primary | AWS Bedrock — Claude Sonnet 4.6 |
| LLM Fallback | Google Gemini 2.5 Flash |
| Circuit Breaker | 3 failures → open 60s → half-open → retry |
| Degradation | Falls back to local-only with explicit `degraded: true` flag |
| Health Canary | Background LLM probe every 4 minutes |
| Auth | API key required for all scan endpoints |
| License | AGPL-3.0 |

## Validation and Testing

- **318 passing tests** across the full test suite
- **38 causal-blame symmetry and boundary tests** — political figures, authority figures, institutions treated identically
- **118-sample calibration corpus** with 100% accuracy, precision, recall, F1 on the deterministic core
- **31.7-point truth score separation** between clean and biased samples in calibration
- **Boundary control tests** — bounded factual claims verified clean of false positives
- **Live production verification** — `source: llm+local`, `degraded: false` confirmed March 20, 2026

## Known Limits

These are stated honestly:

1. **LLM layer introduces variance.** The same sentence about different subjects can produce different AI-layer penalties. The deterministic core is fully symmetric; the LLM is not.
2. **Calibration corpus is small.** 118 samples. Systematic precision/recall on large corpora (500-1000+ per domain) has not been completed.
3. **PIT is a preprint.** Not yet formally peer-reviewed.
4. **Long document performance untested.** Validated on passages and short documents, not 10K+ word texts.
5. **5 domains only.** Healthcare, education, government communications not yet covered.
6. **Audit chain is local.** Tamper-evident via SHA-256 hash chain, but not distributed — it is a local integrity mechanism, not a public blockchain.

## Recent Incident (March 20, 2026) — Resolved

**What happened:** Invisible character corruption in the AWS secret key stored in Render's environment variables caused all Bedrock API calls to fail with `InvalidSignatureException`. The Gemini fallback was also rate-limited, causing the service to degrade to local-only mode.

**What we fixed:**
1. Re-entered the correct AWS credentials (verified via SHA-256 hash comparison)
2. Added startup LLM smoke check — logs ERROR immediately on credential failure
3. Added periodic LLM canary — keeps health status accurate during idle periods
4. Health endpoint now reports truthful LLM state with explicit status semantics
5. Degraded scan results are no longer cached

**Why this builds confidence:** The system correctly detected its own degradation, reported it truthfully in the health endpoint, and recovered cleanly when credentials were fixed. The new canary ensures idle periods are never confused with failures.

## Quick Verification (5 minutes)

**1. Check health:**
```bash
curl https://biasclear.com/health
# Expect: "llm_available": true, "llm_status": "ready"
```

**2. Run a scan:**
```bash
curl -X POST https://biasclear.com/scan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"text":"Experts agree there is no reasonable alternative.","mode":"full","domain":"general"}'
# Expect: "source": "llm+local", "degraded": false, bias flags detected
```

**3. Try the playground:** Visit [biasclear.com](https://biasclear.com) and use the interactive scanner — no API key needed.

**4. Read the preprint:** [DOI 10.5281/zenodo.18676405](https://doi.org/10.5281/zenodo.18676405)

**5. Review the code:** [github.com/bws82/biasclear](https://github.com/bws82/biasclear)

## Case Studies

### Case Study 1: Legal — Opposing Counsel Rhetoric

**Input:** "The plaintiff's claims have no basis in established law and any competent attorney would recognize this as a frivolous filing that warrants sanctions."

**What BiasClear detects:**
- `LEGAL_MERIT_DISMISSAL` — dismisses claims without engaging with the legal substance
- `LEGAL_SANCTIONS_THREAT` — uses sanctions as a rhetorical weapon rather than a procedural remedy
- `COMPETENCE_DISMISSAL` — implies incompetence of opposing counsel to delegitimize the position

**Why it matters:** In litigation, these patterns suppress legitimate legal arguments by attacking the attorney rather than the law. BiasClear identifies the structural technique so the reader can evaluate the actual legal merits separately from the rhetorical packaging.

### Case Study 2: Media — Manufactured Consensus in Reporting

**Input:** "Scientists overwhelmingly agree that this policy is the only viable path forward, and critics have been largely discredited by recent studies."

**What BiasClear detects:**
- `CONSENSUS_AS_EVIDENCE` — uses agreement as proof rather than presenting underlying evidence
- `DISSENT_DISMISSAL` — frames critics as "discredited" without specifying which studies or how
- `CLAIM_WITHOUT_CITATION` — "recent studies" provides no verifiable reference
- `INEVITABILITY_FRAME` — "only viable path" forecloses alternatives

**Why it matters:** News articles using these patterns create the impression of settled science or policy consensus while omitting the actual evidence chain. BiasClear makes the rhetorical structure visible so readers can demand the underlying data.

### Case Study 3: Financial — Projection Framing in Investment Materials

**Input:** "Based on current trends, this fund is projected to deliver 15% annual returns, significantly outperforming the market as it has consistently done over the past three years."

**What BiasClear detects:**
- `FIN_PROJECTION_AS_FACT` — presents a forward-looking estimate as if it were a reliable prediction
- `FIN_CHERRY_PICKED_TIMEFRAME` — selects a favorable 3-year window without longer context
- `FIN_SURVIVORSHIP_BIAS` — implied comparison to "the market" without acknowledging failed funds

**Why it matters:** Investment materials frequently use these patterns to create confidence that is not supported by the underlying data. Regulatory frameworks (SEC, FCA) require that projections be clearly labeled; BiasClear detects when the structural framing undermines that distinction.

## What Support Enables

BiasClear is past prototype — it has a working public API, a published theoretical framework, a deterministic detection engine, an LLM-assisted analysis layer, cryptographic auditability, and 318 passing tests. It is deployed on AWS infrastructure and serving real scans.

What it needs to reach the next level of credibility:

1. **Calibration corpus development.** Labeled datasets for systematic precision/recall validation across all 4 domains. The current corpus (118 samples) demonstrates the approach works; a 500-1000 sample corpus per domain would provide statistically meaningful confidence numbers.
2. **LLM consistency research.** Structured output experiments to reduce AI-layer variance across entity swaps. The deterministic core is fully symmetric; the LLM layer is not. Prompt engineering and structured constraints can reduce this, which requires compute credits for systematic testing.
3. **Academic collaboration.** Co-authorship on a peer-reviewed publication of the PIT framework would strengthen the theoretical foundation.
4. **Security audit.** Third-party review of the audit chain and API security model.
5. **Domain expansion.** Expert-authored patterns for healthcare and government communications — natural next domains that require domain-specific knowledge to author responsibly.

## Technical Stack

| Component | Detail |
|-----------|--------|
| Language | Python 3.12 |
| Framework | FastAPI + uvicorn |
| LLM Primary | AWS Bedrock (Claude Sonnet 4.6) |
| LLM Fallback | Google Gemini 2.5 Flash |
| Hosting | Render (Docker) |
| Database | SQLite (audit chain, learned patterns) |
| License | AGPL-3.0 |
| Package | [PyPI](https://pypi.org/project/biasclear) |
| Source | [GitHub](https://github.com/bws82/biasclear) |
| Preprint | [Zenodo](https://doi.org/10.5281/zenodo.18676405) · [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6270159) |

## Contact

Bradley Slimp — [brad@biasclear.com](mailto:brad@biasclear.com) — [LinkedIn](https://www.linkedin.com/in/brad-s-82694021/)
