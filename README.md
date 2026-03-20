# BiasClear

![CI](https://github.com/bws82/biasclear/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18676405.svg)](https://doi.org/10.5281/zenodo.18676405)

Structural bias detection engine built on [Persistent Influence Theory (PIT)](https://doi.org/10.5281/zenodo.18676405).

BiasClear scans text for rhetorical manipulation patterns — manufactured consensus, authority substitution, false urgency, dissent dismissal — and explains exactly how the text is structured to influence the reader.

**Live:** [biasclear.com](https://biasclear.com) | **Paper:** [DOI 10.5281/zenodo.18676405](https://doi.org/10.5281/zenodo.18676405) | **EA Forum:** [I Built an Open-Source Tool That Audits AI Persuasion](https://forum.effectivealtruism.org/posts/zByjJ3cJZpHKjhxxY/i-built-an-open-source-tool-that-audits-ai-persuasion)

## Reviewer Quick Links

| Resource | Link |
|----------|------|
| Reviewer Packet | [docs/REVIEWER_PACKET.md](docs/REVIEWER_PACKET.md) — architecture, validation, case studies, known limits |
| Live Health | [biasclear.com/health](https://biasclear.com/health) — real-time LLM status and canary results |
| API Documentation | [biasclear.com/docs](https://biasclear.com/docs) — full OpenAPI spec |
| Production Guide | [docs/PRODUCTION_DEPLOYMENT_SOURCE_OF_TRUTH.md](docs/PRODUCTION_DEPLOYMENT_SOURCE_OF_TRUTH.md) |
| Operations Checklist | [docs/OPERATIONS_CHECKLIST.md](docs/OPERATIONS_CHECKLIST.md) |
| PIT Preprint | [Zenodo](https://doi.org/10.5281/zenodo.18676405) · [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6270159) |

## Why This Is Different

1. **Structural, not statistical.** BiasClear detects the *mechanism* of persuasion — manufactured consensus, authority substitution, dissent dismissal — not surface sentiment or toxicity.
2. **Deterministic core.** 42 hand-authored patterns fire identically every time. No ML weights, no model drift, no training data.
3. **Identity-neutral.** "Trump is ruining everything" and "Biden is ruining everything" trigger the same patterns. Validated by 38 symmetry tests.
4. **Auditable.** Every scan produces a SHA-256 hash-chained audit entry with full score breakdown.
5. **Theoretically grounded.** Built on Persistent Influence Theory (PIT), published as a preprint on Zenodo and SSRN. PIT has not yet undergone formal peer review.

## Quick Start

### Install

```bash
git clone https://github.com/bws82/biasclear.git
cd biasclear
pip install ".[api]"
```

### Configure

BiasClear supports multiple LLM providers for contextual/deep analysis.

- **Production default:** Amazon Bedrock (Claude Sonnet)
- **Fallback:** Gemini

```bash
# Amazon Bedrock (recommended)
export BIASCLEAR_LLM_PROVIDER=bedrock
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key

# Or Gemini (fallback / optional)
export BIASCLEAR_LLM_PROVIDER=gemini
export GEMINI_API_KEY=your_gemini_api_key
```

### Run a scan

```python
from biasclear import scan_local

# Local scan — deterministic, zero API cost
result = scan_local("Experts agree there is no reasonable alternative.")
print(result["truth_score"], result["flags"])

# For deep/full scans, configure an LLM provider (see Configuration)
```

### Start the API server

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

## Architecture

```
┌─────────────────────────────────────────────┐
│                  API Layer                  │
│         FastAPI + Auth + Rate Limit         │
├──────────┬──────────────┬───────────────────┤
│  Local   │    Deep      │      Full         │
│  Scan    │    Scan      │      Scan         │
│  (free)  │  (1 LLM call)│  (1–2 LLM calls) │
├──────────┴──────────────┴───────────────────┤
│              Frozen Core (v1.2.0)           │
│     42 structural patterns · 4 domains      │
│        Deterministic · Immutable            │
├─────────────────────────────────────────────┤
│             Learning Ring                   │
│   LLM-proposed patterns · Governed lifecycle│
├─────────────────────────────────────────────┤
│             Audit Chain                     │
│        SHA-256 hash-chained · SQLite        │
└─────────────────────────────────────────────┘
```

## Scan Modes

| Mode | Cost | What it does |
|------|------|-------------|
| **local** | Free | Frozen core patterns only. Fully deterministic. |
| **deep** | 1 API call | LLM analysis guided by PIT principles. |
| **full** | 1–2 API calls | Local + deep combined. Adds impact projection if truth score < 80. |

## Detection Domains

| Domain | Patterns | Example Targets |
|--------|----------|----------------|
| General | 22 | Consensus-as-evidence, false binary, fear urgency, shame lever |
| Legal | 6 | Settled-law dismissal, sanctions threats, straw man arguments |
| Media | 9 | Editorial-as-news, anonymous attribution, weasel quantifiers |
| Financial | 5 | Survivorship bias, anchoring, cherry-picked timeframes |

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/scan` | Scan text for bias | API key required |
| `POST` | `/scan/batch` | Batch scan multiple texts | API key required |
| `POST` | `/correct` | Rewrite text to remove detected bias | API key required |
| `GET` | `/patterns` | List active detection patterns | No |
| `GET` | `/audit` | Recent audit chain entries | No |
| `GET` | `/audit/verify` | Verify audit chain integrity | No |
| `POST` | `/certificate` | Generate a bias scan certificate | API key required |
| `GET` | `/certificate/verify/{hash}` | Verify a certificate by audit hash | No |
| `GET` | `/patterns/learned` | List learned (non-frozen) patterns | No |
| `GET` | `/health` | Health check | No |

## Configuration

### Core settings

| Variable | Required | Description |
|----------|----------|-------------|
| `BIASCLEAR_API_KEYS` | Yes (for hosted API use) | API keys authorized to access protected endpoints |
| `BIASCLEAR_LLM_PROVIDER` | No | LLM provider: `bedrock` (default) or `gemini` |
| `AWS_REGION` | Required for Bedrock | AWS region (recommended: `us-east-1`) |
| `BEDROCK_MODEL_ID` | Required for Bedrock | Bedrock model ID for deep analysis |
| `AWS_ACCESS_KEY_ID` | Required for Bedrock | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Required for Bedrock | AWS secret key |
| `GEMINI_API_KEY` | Required only for Gemini | Gemini API key if using Gemini |

See `.env.example` for the full list.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run calibration benchmark
python run_calibration.py

# Run calibration with optimization recommendations
python run_calibration.py --optimize
```

## Docker

```bash
docker build -t biasclear .
docker run -p 8000:8000 --env-file .env biasclear
```

## Known Limits

These are stated honestly:

1. **PIT is a preprint.** Not yet formally peer-reviewed.
2. **Calibration corpus is small.** 118 samples. Systematic precision/recall on large corpora has not been completed.
3. **LLM layer introduces variance.** The deterministic core is fully symmetric; the LLM layer is not.
4. **Solo developer.** Built and maintained by one person.
5. **Long documents untested.** Validated on passages and short documents, not 10K+ word texts.

## Security

Do not place live credentials in source code, examples, issue threads, or pull requests. Use environment variables and deployment-platform secret storage only.

## License

AGPL-3.0 — see [LICENSE](LICENSE).

## Citation

```bibtex
@misc{slimp2025pit,
  title={Persistent Influence Theory: A Framework for Detecting Structural Bias in Text},
  author={Slimp, Bradley},
  year={2025},
  doi={10.5281/zenodo.18676405}
}
```
