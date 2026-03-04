# Changelog

All notable changes to BiasClear are documented here.

## [1.2.0] — 2026-02-21 (Current)

### Security
- **AAA hardening**: Playground session tokens (HMAC-SHA256, IP-bound, 1hr TTL, 50-use cap), per-IP rate limiting (sliding window), CSP headers, OpenAPI docs lockdown in production, UUID request tracing
- **17 hardening fixes**: CORS lockdown, auth wiring, security headers (HSTS, X-Frame, nosniff, referrer, permissions-policy, COOP, CORP), error message sanitization, audit chain integrity

### Added
- **Revenue-ready features**: Scan result caching (1hr TTL), LLM circuit breaker with graceful degradation, scan certificates (verifiable HTML), pricing tiers on landing page, CI security pipeline (pip-audit, TruffleHog, Semgrep SAST)
- **Calibration corpus**: 4 domain-specific test corpora (general, legal, media, financial) with benchmarking and optimization tools
- 9 new detection patterns — regex fixes for 100% recall against calibration corpus
- Self-scan button — BiasClear scans its own AI output for bias
- Pre-loaded domain examples in playground

### Fixed
- FastAPI 0.116.1 upgraded to 0.128.8 to resolve Starlette CVE
- 7 reliability fixes: subtle bias detection improvements, LLM fallback warnings, score capping
- Audit DB path fallback when persistent disk not mounted

## [1.1.0] — 2026-02-14

### Added
- **Correction engine**: Iterative flag-aware bias correction with verification pipeline
- **CI pipeline**: 4-job GitHub Actions (tests, pip-audit, TruffleHog secret scan, Semgrep SAST)
- **Test suite expansion**: 240 tests total (84 frozen core, 34 corrector, 36 calibration, 25 security, 22 API, 27 phase1b, 12 infra)
- Correction UI in playground — detect then fix in one flow
- Live audit chain feed on landing page
- Self-scan capability — analyze BiasClear's own outputs
- `/beta-signups` endpoint with API key auth

### Changed
- Monorepo merge: `app/` refactored to `biasclear/` package + `api/main.py` thin server
- CORS lockdown, structured request logging, persistent audit DB path on Render

## [1.0.0] — 2026-02-08

### Added
- **Frozen Core** (v1.0.0): 34 deterministic structural detection patterns across 4 domains
  - General (14 patterns): consensus-as-evidence, false binary, fear urgency, shame lever, etc.
  - Legal (6 patterns): settled-law dismissal, sanctions threats, straw man arguments
  - Media (9 patterns): editorial-as-news, anonymous attribution, weasel quantifiers
  - Financial (5 patterns): survivorship bias, anchoring, cherry-picked timeframes
- **5 immutable principles**: Truth, Justice, Clarity, Agency, Identity
- **3 PIT tiers**: Ideological, Psychological, Institutional
- **Learning Ring**: LLM-proposed pattern discovery with governed lifecycle (5 confirmations to activate, auto-deactivate above 15% FP rate)
- **Audit Chain**: SHA-256 hash-chained tamper-evident logging in SQLite
- **3 scan modes**: local (free/deterministic), deep (LLM-powered), full (combined)
- **Truth Score**: 0-100 composite scoring with detailed penalty breakdown
- FastAPI REST API with auth, rate limiting, input validation
- Interactive landing page with playground demo
- Docker deployment with health checks
- Render.com deployment blueprint with persistent disk
- AGPL-3.0 license
