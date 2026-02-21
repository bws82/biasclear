"""
BiasClear API — Main Application

POST /scan         — Scan text for bias (local, deep, or full)
POST /scan/batch   — Batch scan multiple texts
POST /correct      — Correct detected bias in text
GET  /patterns     — List all detection patterns (by domain)
GET  /audit        — Recent audit chain entries
GET  /audit/verify — Verify chain integrity
GET  /health       — Health check
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from pathlib import Path

import os

from biasclear.config import settings
from biasclear.frozen_core import CORE_VERSION
from biasclear.audit import audit_chain
from biasclear.detector import scan_local, scan_deep, scan_full
from biasclear.corrector import correct_bias
from biasclear.patterns.learned import learning_ring
from biasclear.llm.factory import get_provider
from biasclear.auth import require_api_key, AUTH_ENABLED
from biasclear.rate_limit import check_rate_limit
from biasclear.cache import scan_cache
from biasclear.llm.gemini import CircuitOpenError
from biasclear.logging import setup_logging, get_logger
from biasclear.schemas.scan import (
    ScanRequest,
    ScanBatchRequest,
    ScanResponse,
    ScanBatchResponse,
    CorrectRequest,
    CorrectResponse,
    CertificateRequest,
    CertificateResponse,
    CertificateVerifyResponse,
    AuditResponse,
    ChainVerification,
    HealthResponse,
)

logger = get_logger("api")


# ============================================================
# STARTUP / SHUTDOWN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Wire up dependencies on startup."""
    setup_logging()

    # Production guard — warn loudly if auth is not configured on Render
    if os.getenv("RENDER", "").lower() == "true" and not AUTH_ENABLED:
        logger.warning(
            "⚠️  RUNNING ON RENDER WITHOUT AUTH — all endpoints are public. "
            "Set BIASCLEAR_API_KEYS in Render environment variables to enable auth."
        )

    # Warn if Gemini API key is missing — deep/full scans will degrade to local-only
    if not settings.GEMINI_API_KEY:
        logger.warning(
            "⚠️  GEMINI_API_KEY not set — deep and full scan modes will fall back to "
            "local-only analysis. Set GEMINI_API_KEY in environment variables for "
            "full detection capability. Get a key: https://aistudio.google.com/apikey"
        )

    learning_ring.set_audit_logger(audit_chain.log)
    logger.info("BiasClear API starting",
                extra={"core_version": CORE_VERSION, "auth_enabled": AUTH_ENABLED})
    yield
    logger.info("BiasClear API shutting down")


app = FastAPI(
    title="BiasClear API",
    description=(
        "Structural bias detection engine built on Persistent Influence Theory (PIT). "
        "Detects rhetorical manipulation patterns in text across legal, media, financial, "
        "and general domains. Features a frozen deterministic core (34 patterns), "
        "LLM-powered deep analysis, bias correction, and SHA-256 hash-chained audit trail.\n\n"
        "**Quick Start:** `POST /scan` with `{\"text\": \"your text\", \"mode\": \"local\"}` "
        "to scan for bias.\n\n"
        "**Peer-reviewed:** DOI 10.5281/zenodo.18676405\n\n"
        "**Compliance:** Designed for Colorado SB 205 and EU AI Act readiness."
    ),
    version=f"1.1.0 (core {CORE_VERSION})",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Scan", "description": "Scan text for structural bias and distortion patterns."},
        {"name": "Correct", "description": "Rewrite biased text while preserving factual content."},
        {"name": "Certificate", "description": "Generate and verify bias scan certificates."},
        {"name": "Audit", "description": "Tamper-evident SHA-256 hash-chained audit trail."},
        {"name": "Patterns", "description": "Browse frozen core and learned detection patterns."},
        {"name": "Health", "description": "Service health and version information."},
    ],
)

# CORS — set BIASCLEAR_CORS_ORIGINS in production (e.g. "https://biasclear.com")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
    allow_credentials=False,
)

# Static assets
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the landing page."""
    index = _static_dir / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return JSONResponse({"message": "BiasClear API", "docs": "/docs"})


@app.get("/demo", include_in_schema=False)
async def demo_redirect():
    """Redirect /demo to the playground section of the landing page."""
    return RedirectResponse(url="/#playground")


@app.post("/beta-signup", include_in_schema=False)
async def beta_signup(request: Request):
    """Log beta signup interest. Emails are stored in the audit chain."""
    try:
        body = await request.json()
        email = body.get("email", "").strip()
        if not email or "@" not in email:
            return JSONResponse({"status": "error", "message": "Invalid email"}, status_code=400)
        audit_chain.log(
            event_type="beta_signup",
            data={"email": email, "source": "website"},
            core_version=CORE_VERSION,
        )
        logger.info("Beta signup recorded", extra={"email": email})
        return JSONResponse({"status": "ok", "message": "Signup recorded"})
    except Exception:
        logger.warning("Beta signup failed silently", exc_info=True)
        return JSONResponse({"status": "ok", "message": "Signup recorded"})


@app.get("/beta-signups", include_in_schema=False)
async def get_beta_signups(
    key_id: Optional[str] = Depends(require_api_key),
):
    """Retrieve all beta signup emails from the audit chain."""
    entries = audit_chain.get_recent(limit=500, event_type="beta_signup")
    emails = [
        {
            "email": e["data"].get("email", "unknown"),
            "timestamp": e["timestamp"],
            "source": e["data"].get("source", "unknown"),
        }
        for e in entries
    ]
    return {"total": len(emails), "signups": emails}


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions — return structured error, don't leak internals."""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={"error": str(exc), "path": request.url.path, "method": request.method},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. The scan could not be completed.",
        },
    )


# Lazy LLM provider
_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = get_provider(settings.LLM_PROVIDER)
    return _llm


# ============================================================
# ROUTES
# ============================================================

@app.post("/scan", response_model=ScanResponse, tags=["Scan"])
async def scan_text(
    request: ScanRequest,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Scan text for structural bias and distortion patterns.

    Supports three modes:
    - **local**: Frozen core only (free, instant, deterministic)
    - **deep**: LLM-powered analysis (higher quality, 1 API call)
    - **full**: Both layers combined (recommended, enables learning ring)

    Results are cached for 1 hour — identical scans return instantly.
    If the LLM is unavailable, deep/full modes gracefully degrade to local.
    """
    check_rate_limit(key_id)
    start = time.time()

    learned = learning_ring.get_active_patterns()
    lr_version = str(len(learned))  # Cache key includes learning ring state

    # Check cache first — identical scans return instantly
    cached = await scan_cache.get(request.text, request.domain, request.mode, extra=lr_version)
    if cached is not None:
        duration = int((time.time() - start) * 1000)
        logger.info(
            f"Scan cache hit: score={cached.get('truth_score', '?')} mode={request.mode}",
            extra={
                "truth_score": cached.get("truth_score"),
                "scan_mode": request.mode,
                "domain": request.domain,
                "duration_ms": duration,
                "key_id": key_id,
            },
        )
        return cached

    # Circuit breaker: if LLM is down and mode requires it, fall back to local
    try:
        if request.mode == "local":
            result = await scan_local(
                request.text, domain=request.domain, external_patterns=learned,
            )
        elif request.mode == "deep":
            result = await scan_deep(
                request.text, llm=_get_llm(), domain=request.domain,
                learning_ring=learning_ring, audit_chain=audit_chain,
            )
        elif request.mode == "full":
            result = await scan_full(
                request.text,
                llm=_get_llm(),
                domain=request.domain,
                external_patterns=learned,
                learning_ring=learning_ring,
                audit_chain=audit_chain,
            )
        else:
            raise HTTPException(400, f"Invalid mode: {request.mode}")
    except CircuitOpenError:
        # LLM circuit breaker is open — gracefully degrade to local-only
        logger.warning(
            "Circuit breaker open — falling back to local scan",
            extra={"requested_mode": request.mode, "domain": request.domain},
        )
        result = await scan_local(
            request.text, domain=request.domain, external_patterns=learned,
        )
        result["scan_mode"] = f"local (fallback from {request.mode})"
        result["_degraded"] = True
        result["_degradation_warning"] = (
            "LLM circuit breaker is open due to repeated failures. Results are from "
            "the local deterministic engine only. Some subtle bias patterns may not "
            "be detected. Truth score has been capped at 85."
        )
        # Cap truth_score — local-only can't detect subtle patterns
        if result["truth_score"] > 85:
            result["truth_score"] = 85

    if "error" in result and not result.get("bias_detected"):
        logger.error(
            "LLM provider error during scan",
            extra={"error": result["error"], "scan_mode": request.mode, "domain": request.domain},
        )
        raise HTTPException(502, "LLM provider temporarily unavailable. Please try again.")

    audit_hash = audit_chain.log(
        event_type=f"scan_{request.mode}",
        data={
            "truth_score": result["truth_score"],
            "bias_detected": result["bias_detected"],
            "severity": result["severity"],
            "pit_tier": result["pit_tier"],
            "domain": request.domain,
            "flags_count": len(result["flags"]),
            "key_id": key_id,
        },
        core_version=CORE_VERSION,
    )
    result["audit_hash"] = audit_hash

    # Store in cache for future identical scans
    await scan_cache.put(request.text, request.domain, request.mode, result, extra=lr_version)

    duration = int((time.time() - start) * 1000)
    logger.info(
        f"Scan complete: score={result['truth_score']} mode={request.mode}",
        extra={
            "truth_score": result["truth_score"],
            "scan_mode": request.mode,
            "domain": request.domain,
            "flags_count": len(result["flags"]),
            "duration_ms": duration,
            "key_id": key_id,
        },
    )

    return result


@app.post("/scan/batch", response_model=ScanBatchResponse, tags=["Scan"])
async def scan_batch(
    request: ScanBatchRequest,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Batch scan up to 100 texts concurrently.

    Each item is scanned independently. Failed items return a placeholder
    result with `scan_mode: "error"` rather than failing the entire batch.
    """
    check_rate_limit(key_id)

    learned = learning_ring.get_active_patterns()

    async def _scan_one(item: ScanRequest) -> dict:
        try:
            if item.mode == "local":
                return await scan_local(
                    item.text, domain=item.domain, external_patterns=learned,
                )
            elif item.mode == "deep":
                return await scan_deep(
                    item.text, llm=_get_llm(), domain=item.domain,
                    learning_ring=learning_ring, audit_chain=audit_chain,
                )
            else:
                return await scan_full(
                    item.text,
                    llm=_get_llm(),
                    domain=item.domain,
                    external_patterns=learned,
                    learning_ring=learning_ring,
                    audit_chain=audit_chain,
                )
        except CircuitOpenError:
            # Degrade to local-only if LLM is down
            result = await scan_local(
                item.text, domain=item.domain, external_patterns=learned,
            )
            result["scan_mode"] = f"local (fallback from {item.mode})"
            return result

    results = await asyncio.gather(
        *[_scan_one(item) for item in request.items],
        return_exceptions=True,
    )

    successful = [r for r in results if isinstance(r, dict)]
    audit_chain.log(
        event_type="scan_batch",
        data={
            "total": len(request.items),
            "scanned": len(successful),
            "errors": len(results) - len(successful),
            "key_id": key_id,
        },
        core_version=CORE_VERSION,
    )

    clean_results = []
    for r in results:
        if isinstance(r, dict):
            clean_results.append(r)
        else:
            logger.warning(
                "Batch scan item failed",
                extra={"error": str(r), "error_type": type(r).__name__},
            )
            clean_results.append({
                "text": "",
                "truth_score": 0,
                "knowledge_type": "unknown",
                "bias_detected": False,
                "bias_types": [],
                "pit_tier": "none",
                "pit_detail": "",
                "severity": "none",
                "confidence": 0.0,
                "explanation": "Scan failed for this item.",
                "flags": [],
                "impact_projection": None,
                "scan_mode": "error",
                "source": "error",
                "core_version": CORE_VERSION,
            })

    logger.info(
        f"Batch complete: {len(successful)}/{len(request.items)} scanned",
        extra={"key_id": key_id},
    )

    return {
        "results": clean_results,
        "total": len(request.items),
        "scanned": len(successful),
    }


@app.post("/correct", response_model=CorrectResponse, tags=["Correct"])
async def correct_text(
    request: CorrectRequest,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Rewrite biased text to remove structural distortion while preserving facts.

    Requires a previous scan result as input. Uses iterative LLM correction
    with post-correction verification (up to 3 passes). Returns the corrected
    text, a list of changes made, and visual diff spans.
    """
    check_rate_limit(key_id)

    result = await correct_bias(
        text=request.text,
        scan_result=request.scan_result,
        llm=_get_llm(),
        domain=request.domain,
    )

    audit_chain.log(
        event_type="correction",
        data={
            "changes_count": len(result.get("changes_made", [])),
            "bias_removed": result.get("bias_removed", []),
            "confidence": result.get("confidence", 0.0),
            "key_id": key_id,
        },
        core_version=CORE_VERSION,
    )

    return result


@app.post("/certificate", response_model=CertificateResponse, tags=["Certificate"])
async def generate_certificate(
    request: CertificateRequest,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Generate a verifiable HTML certificate for a completed bias scan.

    The certificate is a self-contained HTML document with truth score,
    detected flags, PIT tier analysis, and a verification link tied to
    the audit chain. Suitable for attaching to legal filings, editorial
    reviews, or compliance documentation.
    """
    from datetime import datetime, timezone
    from biasclear.certificate import generate_certificate_html, compute_certificate_id

    check_rate_limit(key_id)

    issued_at = datetime.now(timezone.utc).isoformat()
    certificate_id = compute_certificate_id(request.text, issued_at)

    # Build verify URL from request context
    verify_url = f"https://biasclear.com/certificate/verify/{request.audit_hash}"

    html = generate_certificate_html(
        text=request.text,
        scan_result=request.scan_result,
        audit_hash=request.audit_hash,
        certificate_id=certificate_id,
        issued_at=issued_at,
        verify_url=verify_url,
    )

    audit_chain.log(
        event_type="certificate_generated",
        data={
            "certificate_id": certificate_id,
            "audit_hash": request.audit_hash,
            "truth_score": request.scan_result.get("truth_score"),
            "key_id": key_id,
        },
        core_version=CORE_VERSION,
    )

    logger.info(
        "Certificate generated",
        extra={"audit_hash": request.audit_hash, "key_id": key_id},
    )

    return {
        "certificate_id": certificate_id,
        "audit_hash": request.audit_hash,
        "html": html,
        "issued_at": issued_at,
        "verify_url": verify_url,
    }


@app.get("/certificate/verify/{audit_hash}", response_model=CertificateVerifyResponse, tags=["Certificate"])
async def verify_certificate(audit_hash: str):
    """Verify a certificate by its audit chain hash. No authentication required.

    Returns whether the hash exists in the audit chain, along with the
    original event type, timestamp, and truth score.
    """
    entries = audit_chain.get_recent(limit=500)
    for entry in entries:
        if entry["hash"] == audit_hash:
            return {
                "verified": True,
                "audit_hash": audit_hash,
                "event_type": entry["event_type"],
                "timestamp": entry["timestamp"],
                "truth_score": entry["data"].get("truth_score"),
            }

    return {
        "verified": False,
        "audit_hash": audit_hash,
    }


@app.get("/audit", response_model=AuditResponse, tags=["Audit"])
async def get_audit(
    limit: int = Query(20, ge=1, le=100, description="Number of entries to return (1-100)."),
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. scan_local, correction)."),
    key_id: Optional[str] = Depends(require_api_key),
):
    """Retrieve recent audit chain entries.

    The audit chain is a SHA-256 hash-linked append-only log of all system events.
    Each entry references the previous entry's hash, creating a tamper-evident chain.
    """
    entries = audit_chain.get_recent(limit=limit, event_type=event_type)
    return {
        "entries": entries,
        "total_count": audit_chain.get_count(),
    }


@app.get("/audit/verify", response_model=ChainVerification, tags=["Audit"])
async def verify_audit(
    limit: int = Query(100, ge=1, le=1000, description="Number of entries to verify (1-1000)."),
    key_id: Optional[str] = Depends(require_api_key),
):
    """Verify integrity of the audit chain by checking hash links.

    Walks the chain and confirms each entry's hash matches its content
    and links correctly to the previous entry. Returns any broken links found.
    """
    result = audit_chain.verify_chain(limit=limit)

    audit_chain.log(
        event_type="chain_verified",
        data=result,
        core_version=CORE_VERSION,
    )

    return result


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Service health check. No authentication required.

    Returns current version, LLM provider status, audit chain size,
    and learning ring statistics.
    """
    all_learned = learning_ring.get_all_patterns()
    return {
        "status": "operational",
        "version": "1.1.0",
        "core_version": CORE_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "audit_entries": audit_chain.get_count(),
        "learned_patterns_active": len([p for p in all_learned if p["status"] == "active"]),
        "learned_patterns_staging": len([p for p in all_learned if p["status"] == "staging"]),
        "learning_enabled": True,
    }


@app.get("/patterns", tags=["Patterns"])
async def get_patterns(
    domain: str = Query("general", pattern="^(general|legal|media|financial|auto)$",
                        description="Domain filter: general, legal, media, financial, or auto (all)."),
    key_id: Optional[str] = Depends(require_api_key),
):
    """List all active detection patterns for a domain.

    Returns both frozen core patterns (immutable, deterministic) and
    learned patterns (governance-approved expansions). Use `domain=auto`
    to see all patterns across all domains.
    """
    from biasclear.frozen_core import frozen_core
    check_rate_limit(key_id)

    patterns = frozen_core.get_patterns(domain=domain)
    learned = learning_ring.get_active_patterns()

    # Add learned patterns
    learned_dicts = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "pit_tier": p.pit_tier,
            "severity": p.severity,
            "principle": p.principle,
            "domain": "learned",
        }
        for p in learned
    ]

    return {
        "domain": domain,
        "core_version": CORE_VERSION,
        "frozen_patterns": len(patterns),
        "learned_patterns": len(learned_dicts),
        "total_patterns": len(patterns) + len(learned_dicts),
        "patterns": patterns + learned_dicts,
    }


@app.get("/patterns/learned", tags=["Patterns"])
async def get_learned_patterns(
    key_id: Optional[str] = Depends(require_api_key),
):
    """List all learned patterns with full governance metadata.

    Includes staging, active, and deactivated patterns with their
    confirmation counts, false positive rates, and activation thresholds.
    """
    all_patterns = learning_ring.get_all_patterns()
    active = [p for p in all_patterns if p["status"] == "active"]
    staging = [p for p in all_patterns if p["status"] == "staging"]
    deactivated = [p for p in all_patterns if p["status"] == "deactivated"]

    return {
        "core_version": CORE_VERSION,
        "total": len(all_patterns),
        "active": len(active),
        "staging": len(staging),
        "deactivated": len(deactivated),
        "activation_threshold": learning_ring.activation_threshold,
        "fp_limit": learning_ring.fp_limit,
        "patterns": all_patterns,
    }


# --- Security + Version Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security and version headers to all responses."""
    response = await call_next(request)
    # Version headers
    response.headers["X-BiasClear-Version"] = "1.1.0"
    response.headers["X-Core-Version"] = CORE_VERSION
    # Security headers
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# --- Body Size Limit Middleware ---
_MAX_BODY_BYTES = 1_048_576  # 1 MB


@app.middleware("http")
async def enforce_body_size_limit(request: Request, call_next):
    """Reject requests exceeding 1MB — guards both Content-Length and chunked bodies."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > _MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large."},
                )
        except ValueError:
            pass  # Malformed content-length; let the framework handle it

    # For methods that carry a body, also check actual size
    # (catches chunked transfer encoding with no Content-Length header)
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        if len(body) > _MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large."},
            )

    return await call_next(request)


# --- Request Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every API request with method, path, status, duration."""
    path = request.url.path
    # Skip noise: static assets and health checks
    if path.startswith("/static") or path == "/health":
        return await call_next(request)

    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)

    logger.info(
        f"{request.method} {path} → {response.status_code} ({duration_ms}ms)",
        extra={
            "method": request.method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response
