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
from biasclear.logging import setup_logging, get_logger
from biasclear.schemas.scan import (
    ScanRequest,
    ScanBatchRequest,
    ScanResponse,
    ScanBatchResponse,
    CorrectRequest,
    CorrectResponse,
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

    learning_ring.set_audit_logger(audit_chain.log)
    logger.info("BiasClear API starting",
                extra={"core_version": CORE_VERSION, "auth_enabled": AUTH_ENABLED})
    yield
    logger.info("BiasClear API shutting down")


app = FastAPI(
    title="BiasClear API",
    description="Bias detection engine built on Persistent Influence Theory (PIT)",
    version=f"1.1.0 (core {CORE_VERSION})",
    lifespan=lifespan,
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

@app.post("/scan", response_model=ScanResponse)
async def scan_text(
    request: ScanRequest,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Scan text for bias and distortion."""
    check_rate_limit(key_id)
    start = time.time()

    learned = learning_ring.get_active_patterns()

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


@app.post("/scan/batch", response_model=ScanBatchResponse)
async def scan_batch(
    request: ScanBatchRequest,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Batch scan multiple texts concurrently."""
    check_rate_limit(key_id)

    learned = learning_ring.get_active_patterns()

    async def _scan_one(item: ScanRequest) -> dict:
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


@app.post("/correct", response_model=CorrectResponse)
async def correct_text(
    request: CorrectRequest,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Correct bias in text using LLM remediation."""
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


@app.get("/audit", response_model=AuditResponse)
async def get_audit(
    limit: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    key_id: Optional[str] = Depends(require_api_key),
):
    """Get recent audit chain entries."""
    entries = audit_chain.get_recent(limit=limit, event_type=event_type)
    return {
        "entries": entries,
        "total_count": audit_chain.get_count(),
    }


@app.get("/audit/verify", response_model=ChainVerification)
async def verify_audit(
    limit: int = Query(100, ge=1, le=1000),
    key_id: Optional[str] = Depends(require_api_key),
):
    """Verify integrity of the audit chain."""
    result = audit_chain.verify_chain(limit=limit)

    audit_chain.log(
        event_type="chain_verified",
        data=result,
        core_version=CORE_VERSION,
    )

    return result


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — no auth required."""
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


@app.get("/patterns")
async def get_patterns(
    domain: str = Query("general", pattern="^(general|legal|media|financial|auto)$"),
    key_id: Optional[str] = Depends(require_api_key),
):
    """
    Return all active detection patterns for a given domain.

    Use domain="auto" to see ALL patterns across all domains.
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


@app.get("/patterns/learned")
async def get_learned_patterns(
    key_id: Optional[str] = Depends(require_api_key),
):
    """Return all learned patterns with full governance metadata."""
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
