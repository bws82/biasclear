# BiasClear — Production Deployment Guide

**Last updated:** 2026-03-15

## Production Service

| Field | Value |
|-------|-------|
| **Public domain** | `biasclear.com` |
| **Runtime** | Docker (python:3.12-slim) |
| **Hosting** | Render (Starter plan) |
| **Region** | Oregon |
| **Repo** | `bws82/biasclear` branch `main` |
| **Auto-deploy** | Yes (on push to main) |

## Required Environment Variables

All 12 must be set. Missing any AWS variable causes Bedrock failure and fallback to local-only scanning.

| Variable | Purpose | Sensitive |
|----------|---------|-----------|
| `AWS_ACCESS_KEY_ID` | Bedrock authentication | Yes |
| `AWS_SECRET_ACCESS_KEY` | Bedrock authentication | Yes |
| `AWS_REGION` | Bedrock region | No |
| `BEDROCK_MODEL_ID` | LLM model identifier | No |
| `BIASCLEAR_API_KEYS` | API key(s) for authenticated access | Yes |
| `BIASCLEAR_CORS_ORIGINS` | Allowed CORS origins | No |
| `BIASCLEAR_DOCS_ENABLED` | Enable `/docs` endpoint | No |
| `BIASCLEAR_LLM_PROVIDER` | Primary provider (`bedrock`) | No |
| `BIASCLEAR_PLAYGROUND_SECRET` | Playground session token | Yes |
| `BIASCLEAR_REQUIRE_AUTH` | Enforce API key auth (`true`) | No |
| `GEMINI_API_KEY` | Fallback LLM provider key | Yes |
| `RENDER` | Render environment flag (`true`) | No |

## LLM Provider Chain

1. **Primary:** AWS Bedrock (Claude Sonnet) — 3x internal retry
2. **Fallback:** Google Gemini 2.5 Flash — auto-switches on credential/auth errors
3. **Circuit breaker:** 3 failures → open, 60s → half-open → retry
4. **Last resort:** Local-only scanning (frozen core only, `degraded: true`)

## Pre-Deploy Checklist

Before any deploy to production:

1. **Check env vars** — all 12 must be present in the hosting dashboard
2. **Run smoke check** — `scripts/smoke_check.sh` after deploy completes
3. **Verify live** — `curl https://biasclear.com/health` should return `{"status": "ok"}`
4. **Test a scan** — confirm `source` is `llm+local` (not `local_fallback`) and `degraded` is `false`

## Health Monitoring

- **Health endpoint:** `GET /health` — returns service status, LLM availability, uptime
- **Smoke script:** `scripts/smoke_check.sh` — validates full pipeline including LLM
