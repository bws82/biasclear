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

from app.config import settings
from app.frozen_core import CORE_VERSION
from app.audit import audit_chain
from app.detector import scan_local, scan_deep, scan_full
from app.corrector import correct_bias
from app.patterns.learned import learning_ring
from app.llm.factory import get_provider
from app.auth import require_api_key, AUTH_ENABLED
from app.rate_limit import check_rate_limit
from app.logging import setup_logging, get_logger
from app.schemas.scan import (
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

# CORS — tighten BIASCLEAR_CORS_ORIGINS in production
_cors_origins = os.getenv("BIASCLEAR_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static assets
_static_dir = Path(__file__).resolve().parent.parent / "static"
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
            "error_type": type(exc).__name__,
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
        raise HTTPException(502, f"LLM provider error: {result['error']}")

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
                "explanation": f"Scan failed: {type(r).__name__}",
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
    return {
        "status": "operational",
        "version": "1.0.0",
        "core_version": CORE_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "audit_entries": audit_chain.get_count(),
        "learned_patterns": len(learning_ring.get_active_patterns()),
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
    from app.frozen_core import frozen_core
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


# --- Version Headers Middleware ---
@app.middleware("http")
async def add_version_headers(request: Request, call_next):
    """Add BiasClear version headers to all responses."""
    response = await call_next(request)
    response.headers["X-BiasClear-Version"] = "1.0.0"
    response.headers["X-Core-Version"] = CORE_VERSION
    return response
