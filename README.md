# BiasClear API

![CI](https://github.com/bws82/biasclear/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18676405.svg)](https://doi.org/10.5281/zenodo.18676405)

Structural bias detection engine built on [Persistent Influence Theory (PIT)](https://doi.org/10.5281/zenodo.18676405).

BiasClear scans text for rhetorical manipulation patterns — manufactured consensus, authority substitution, false urgency, dissent dismissal — and explains exactly how the text is structured to influence the reader.

**Live:** [biasclear.com](https://biasclear.com) | **Paper:** [DOI 10.5281/zenodo.18676405](https://doi.org/10.5281/zenodo.18676405) | **EA Forum:** [I Built an Open-Source Tool That Audits AI Persuasion](https://forum.effectivealtruism.org/posts/zByjJ3cJZpHKjhxxY/i-built-an-open-source-tool-that-audits-ai-persuasion)

## Quick Start

```bash
# Clone and install
git clone https://github.com/bws82/biasclear.git
cd biasclear
pip install -e ".[dev,api]"

# Configure
cp .env.example .env
# Edit .env — set BIASCLEAR_LLM_PROVIDER and provider credentials
# Default: Bedrock (AWS). Alternative: Gemini (Google).

# Run
uvicorn api.main:app --reload
```

The API is live at `http://localhost:8000`. Interactive docs at `/docs`.

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
| `GET` | `/health` | Health check |

## Detection Domains

| Domain | Patterns | Example Targets |
|--------|----------|----------------|
| General | 14 | Consensus-as-evidence, false binary, fear urgency, shame lever |
| Legal | 6 | Settled-law dismissal, sanctions threats, straw man arguments |
| Media | 9 | Editorial-as-news, anonymous attribution, weasel quantifiers |
| Financial | 5 | Survivorship bias, anchoring, cherry-picked timeframes |

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BIASCLEAR_LLM_PROVIDER` | No | `gemini` | LLM provider: `bedrock` or `gemini` |
| `AWS_BEARER_TOKEN_BEDROCK` | If bedrock | — | Bedrock API key (long-term or short-term) |
| `AWS_REGION` | If bedrock | `us-east-1` | AWS region for Bedrock |
| `BEDROCK_MODEL_ID` | If bedrock | `us.anthropic.claude-sonnet-4-6` | Bedrock model ID |
| `GEMINI_API_KEY` | If gemini | — | Google Gemini API key |
| `BIASCLEAR_API_KEYS` | Production | — | Comma-separated API keys for auth |
| `BIASCLEAR_CORS_ORIGINS` | Production | `https://biasclear.com` | Allowed origins |

**Production default:** Bedrock with Anthropic Claude Sonnet 4.6. Gemini available as fallback — switch by changing `BIASCLEAR_LLM_PROVIDER`.

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
