# BiasClear — Production Deployment Source of Truth

**Last updated:** 2026-03-15

## Production Service

| Field | Value |
|-------|-------|
| **Render service name** | `biasclear` |
| **Service ID** | `srv-d6b45vhr0fns73fe38a0` |
| **Public domain** | `biasclear.com` (custom domain attached) |
| **Render URL** | `biasclear.onrender.com` |
| **Runtime** | Docker (python:3.12-slim) |
| **Plan** | Starter ($7/mo) |
| **Region** | Oregon |
| **Repo** | `bws82/biasclear` branch `main` |
| **Auto-deploy** | Yes (on push to main) |

This is the **only** service that should serve public traffic.

## Required Environment Variables

All 12 must be set. Missing any AWS variable causes Bedrock failure and fallback to local-only scanning.

| Variable | Purpose | Sensitive |
|----------|---------|-----------|
| `AWS_ACCESS_KEY_ID` | Bedrock authentication | Yes |
| `AWS_SECRET_ACCESS_KEY` | Bedrock authentication | Yes |
| `AWS_REGION` | Bedrock region (`us-east-1`) | No |
| `BEDROCK_MODEL_ID` | LLM model (`us.anthropic.claude-sonnet-4-6`) | No |
| `BIASCLEAR_API_KEYS` | API key(s) for authenticated access | Yes |
| `BIASCLEAR_CORS_ORIGINS` | Allowed CORS origins (`https://biasclear.com`) | No |
| `BIASCLEAR_DOCS_ENABLED` | Enable `/docs` endpoint (`true`) | No |
| `BIASCLEAR_LLM_PROVIDER` | Primary provider (`bedrock`) | No |
| `BIASCLEAR_PLAYGROUND_SECRET` | Playground session token | Yes |
| `BIASCLEAR_REQUIRE_AUTH` | Enforce API key auth (`true`) | No |
| `GEMINI_API_KEY` | Fallback LLM provider key | Yes |
| `RENDER` | Render environment flag (`true`) | No |

## DNS Configuration

| Record | Value | Notes |
|--------|-------|-------|
| `biasclear.com` A | `216.24.57.1` | Render's IP |
| `www.biasclear.com` CNAME | `biasclear.onrender.com` | Points to production service |

## LLM Provider Chain

1. **Primary:** AWS Bedrock (Claude Sonnet 4.6) — 3x internal retry
2. **Fallback:** Google Gemini 2.5 Flash — auto-switches on credential/auth errors
3. **Circuit breaker:** 3 failures → open, 60s → half-open → retry
4. **Last resort:** Local-only scanning (frozen core only, `degraded: true`)

## Legacy Service (DO NOT USE FOR PRODUCTION)

| Field | Value |
|-------|-------|
| **Render service name** | `biasclear-api` |
| **Service ID** | `srv-d6ct5i7pm1nc739ehbag` |
| **Render URL** | `biasclear-api.onrender.com` |
| **Custom domain** | None |
| **Status** | Legacy — can be retired when confirmed unnecessary |

This service was created during initial Bedrock setup. It has a full env var set but **no custom domain**. It should not be used for production traffic. It can be deleted once we confirm no external references point to it.

**Incident (2026-03-15):** `biasclear.com` was serving from the old `biasclear` service which had only 2 env vars (missing all AWS credentials). All Bedrock calls failed silently and fell back to local-only. Fixed by copying all env vars to the correct service.

## Pre-Deploy Checklist

Before any deploy to production:

1. **Verify you are on the correct service** — `srv-d6b45vhr0fns73fe38a0` (the one with `biasclear.com` attached)
2. **Check env vars** — all 12 must be present (Environment tab in Render dashboard)
3. **Run smoke check** — `scripts/smoke_check.sh` after deploy completes
4. **Verify live** — `curl https://biasclear.com/health` should return `{"status": "ok"}`
5. **Test a scan** — confirm `source` is `llm+local` (not `local_fallback`) and `degraded` is `false`

## Health Monitoring

- **Health endpoint:** `GET /health` — returns `{"status": "ok"}` when running
- **Smoke script:** `scripts/smoke_check.sh` — validates full pipeline including LLM
- **Debug endpoint:** `GET /debug/llm-test` — temporary diagnostic (remove after stabilization)
