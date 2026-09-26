# BiasClear

![CI](https://github.com/bws82/biasclear/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18676405.svg)](https://doi.org/10.5281/zenodo.18676405)

A rule-based persuasion linter built on [Persistent Influence Theory (PIT)](https://doi.org/10.5281/zenodo.18676405). BiasClear marks the structural moves a text makes to move its reader (manufactured consensus, authority substitution, false urgency, dissent dismissal) and names each one.

> **Status: v2 in progress (September 2026).** The v1 hosted service is offline. While rebuilding, we audited our own public claims, and several didn't hold up:
>
> - **Accuracy figures withdrawn.** The "100% F1" and "98.6% F1" figures came from sample sets the rules were tuned on. A held-out check we ran ourselves, on texts the rules had not seen, scored far lower. v2 will publish per-rule precision and recall on public, externally labeled benchmarks.
> - **Neutrality claim withdrawn.** v1 flags some institutions and credentials but not their mirror images (for example, "The CDC has concluded" is flagged while "The Heritage Foundation has concluded" is not). v2 replaces named-entity lists with structural rules and ships a swapped-pair symmetry suite as a release gate.
> - **Compliance and certificate claims withdrawn.** BiasClear is not a compliance product, and v1 "certificates" are not a verification mechanism.
>
> Everything v1 got wrong, and how v2 fixes it, will be published with the v2 release.

## What v2 will be

- **Runs in your browser.** The rule engine ships as a static page. Your text never leaves your device unless you turn on the optional second opinion, which sends it to your own AI provider with your own key.
- **Deterministic.** The same input always gets the same output, stamped with a versioned rule pack.
- **Measured, not claimed.** Published benchmark results, including what it misses.
- **Symmetric by test.** Every release has to pass swapped-pair tests across parties, institutions and ideologies.

## Quick start (v1 engine)

```bash
git clone https://github.com/bws82/biasclear.git
cd biasclear
python -m pip install -e ".[api,dev]"
python -m pytest tests/ -q
```

```python
import asyncio
from biasclear import scan_local

result = asyncio.run(scan_local("Experts agree there is no reasonable alternative."))
print(result["flags"])
```

`scan_local` is deterministic and needs no API key. The `deep` and `full` modes call an LLM provider and are being redesigned for v2.

## v1 architecture (archived)

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
# Reviewer / CI-equivalent path
python -m pip install -e ".[api,dev]"
python -m pytest tests/ -v

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
3. **Known asymmetries in v1 rules.** Some institution and credential rules are not symmetric (see the status notice above).
4. **LLM layer introduces variance.** Deep and full scans are not deterministic.
5. **Long documents untested.** Validated on passages and short documents, not 10K+ word texts.

## Security

Do not place live credentials in source code, examples, issue threads, or pull requests. Use environment variables and deployment-platform secret storage only.

## Support

BiasClear is an independent public-interest project. It has no server to fund; the best support right now is testing v2 and reporting misses or asymmetries as GitHub issues.

## License

AGPL-3.0 — see [LICENSE](LICENSE).

## Citation

```bibtex
@misc{slimp2026pit,
  title={Persistent Influence Theory: A Hierarchical Framework for Structural Persuasion and Information Fidelity},
  author={Slimp, Bradley},
  year={2026},
  publisher={Zenodo},
  doi={10.5281/zenodo.18676405}
}
```

A revised PIT v2 preprint is in preparation under the same Zenodo concept DOI.
