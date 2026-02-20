"""
BiasClear — Bias Detection and Correction Engine

Built on Persistent Influence Theory (PIT) and the Frozen Core architecture.

Public API:
  - frozen_core:  Immutable evaluation engine (deterministic, zero API cost)
  - scan_local:   Local-only scan via frozen core
  - scan_deep:    LLM-powered deep analysis
  - scan_full:    Combined local + deep (the real product)
  - correct_bias: Flag-aware iterative correction with verification
  - calculate_truth_score: Composite truth score from evaluation flags
  - AuditChain:   SHA-256 hash-chained tamper-evident logging
  - LearningRing: Governed pattern expansion with auto-activation/deactivation
  - LLMProvider:  Abstract LLM interface for provider swapping

Usage:
    from biasclear import frozen_core, scan_local, scan_full
    from biasclear import AuditChain, LearningRing
    from biasclear import LLMProvider
"""

__version__ = "1.1.0"

from biasclear.frozen_core import (
    frozen_core,
    CoreEvaluation,
    Flag,
    StructuralPattern,
    CORE_VERSION,
    PRINCIPLES,
    PIT_TIERS,
)
from biasclear.detector import scan_local, scan_deep, scan_full
from biasclear.corrector import correct_bias
from biasclear.scorer import calculate_truth_score
from biasclear.audit import AuditChain, audit_chain
from biasclear.patterns.learned import LearningRing, learning_ring
from biasclear.llm import LLMProvider
from biasclear.llm.factory import get_provider

__all__ = [
    "frozen_core",
    "CoreEvaluation",
    "Flag",
    "StructuralPattern",
    "CORE_VERSION",
    "PRINCIPLES",
    "PIT_TIERS",
    "scan_local",
    "scan_deep",
    "scan_full",
    "correct_bias",
    "calculate_truth_score",
    "AuditChain",
    "audit_chain",
    "LearningRing",
    "learning_ring",
    "LLMProvider",
    "get_provider",
]
