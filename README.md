# BiasClear API

![CI](https://github.com/bws82/biasclear/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18676405.svg)](https://doi.org/10.5281/zenodo.18676405)

Structural bias detection engine built on [Persistent Influence Theory (PIT)](https://doi.org/10.5281/zenodo.18676405).

BiasClear scans text for rhetorical manipulation patterns — manufactured consensus, authority substitution, false urgency, dissent dismissal — and explains exactly how the text is structured to influence the reader.

**Live:** [biasclear.com](https://biasclear.com) | **Paper:** [DOI 10.5281/zenodo.18676405](https://doi.org/10.5281/zenodo.18676405) | **EA Forum:** [I Built an Open-Source Tool That Audits AI Persuasion](https://forum.effectivealtruism.org/posts/zByjJ3cJZpHKjhxxY/i-built-an-open-source-tool-that-audits-ai-persuasion)

## Quick Start

### Install

```bash
git clone https://github.com/bws82/biasclear.git
cd biasclear
pip install ".[api]"
```

### Configure

BiasClear supports multiple LLM providers for contextual/deep analysis.

- **Production default:** Amazon Bedrock
- **Fallback / optional:** Gemini

Set the provider and credentials you want to use:

```bash
# Option A — Amazon Bedrock (recommended)
export BIASCLEAR_LLM_PROVIDER=bedrock
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
# For authentication, use one of the following:
# Render / bearer token path
export AWS_BEARER_TOKEN_BEDROCK=your_bedrock_bearer_token
# Standard AWS credentials
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key

# Option B — Gemini (fallback / optional)
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

## Architecture

```
┌─────────────────────────────────────────────┐
│                  API Layer                  │
│         FastAPI + Auth + Rate Limit         │
├──────────┬──────────────┬───────────────────┤
│  Local   │    Deep      │      Full         │
│  Scan    │    Scan      │      Scan         │
│  (free)  │  (LLM call)  │  (local + deep)   │
├──────────┴──────────────┴───────────────────┤
│              Frozen Core (v1.2.0)           │
│     39 structural patterns · 4 domains      │
│        Deterministic · Immutable            │
├─────────────────────────────────────────────┤
│             Learning Ring                   │
│   LLM-proposed patterns · Governed lifecycle│
├─────────────────────────────────────────────┤
│             Audit Chain                     │
│        SHA-256 hash-chained · SQLite        │
└─────────────────────────────────────────────┘
```

## Runtime

BiasClear uses a provider-flexible architecture for contextual and deep analysis.

- **Current production default:** Amazon Bedrock
- **Current model path:** Anthropic Claude via Bedrock
- **Fallback option:** Gemini

The deterministic core scan remains rule-based and reproducible regardless of provider choice. Provider-backed analysis is used to extend contextual interpretation, not to replace the core structural audit layer.

## Scan Modes

| Mode | Cost | What it does |
|------|------|-------------|
| **local** | Free | Frozen core patterns + keyword markers. Deterministic. |
| **deep** | 1 API call | LLM analysis guided by PIT principles. |
| **full** | 1 API call | Local + deep combined. Triggers learning ring. |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scan` | Scan text for bias |
| `POST` | `/scan/batch` | Batch scan multiple texts |
| `POST` | `/correct` | Rewrite text to remove detected bias |
| `GET` | `/patterns` | List active detection patterns |
| `GET` | `/audit` | Recent audit chain entries |
| `GET` | `/audit/verify` | Verify audit chain integrity |
| `POST` | `/certificate` | Generate a bias scan certificate |
| `GET` | `/certificate/verify/{hash}` | Verify a certificate by audit hash |
| `GET` | `/patterns/learned` | List learned (non-frozen) patterns |
| `GET` | `/health` | Health check |

## Detection Domains

| Domain | Patterns | Example Targets |
|--------|----------|----------------|
| General | 19 | Consensus-as-evidence, false binary, fear urgency, shame lever |
| Legal | 6 | Settled-law dismissal, sanctions threats, straw man arguments |
| Media | 9 | Editorial-as-news, anonymous attribution, weasel quantifiers |
| Financial | 5 | Survivorship bias, anchoring, cherry-picked timeframes |

## Configuration

### Core settings

| Variable | Required | Description |
|----------|----------|-------------|
| `BIASCLEAR_API_KEYS` | Yes (for hosted API use) | API keys authorized to access protected endpoints |
| `BIASCLEAR_LLM_PROVIDER` | No | LLM provider for contextual/deep analysis. Supported values: `bedrock`, `gemini` |
| `AWS_REGION` | Required for Bedrock | AWS region for Bedrock runtime (default recommended: `us-east-1`) |
| `BEDROCK_MODEL_ID` | Required for Bedrock | Bedrock model ID used for deep analysis |
| `AWS_BEARER_TOKEN_BEDROCK` | Optional for Bedrock | Bedrock bearer-token auth path, commonly used in hosted environments like Render |
| `AWS_ACCESS_KEY_ID` | Optional for Bedrock | Standard AWS access key for local/dev environments |
| `AWS_SECRET_ACCESS_KEY` | Optional for Bedrock | Standard AWS secret key for local/dev environments |
| `GEMINI_API_KEY` | Required only for Gemini | Gemini API key if using Gemini as provider |

### Notes

- **Production default:** Bedrock
- **Current recommended provider:** Amazon Bedrock
- **Gemini remains supported as a fallback**
- If `BIASCLEAR_LLM_PROVIDER` is not set, it defaults to `bedrock`
- Do not commit secrets to source control; use environment variables or your deployment platform's secret manager

### Example environment configuration

#### Bedrock (recommended)

```bash
BIASCLEAR_LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
AWS_BEARER_TOKEN_BEDROCK=your_bedrock_bearer_token
```

#### Bedrock (standard AWS credentials)

```bash
BIASCLEAR_LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

#### Gemini (fallback)

```bash
BIASCLEAR_LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
```

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
