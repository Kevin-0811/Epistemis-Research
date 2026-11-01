"""Epistemis: a deterministic research prototype for scientific-text analysis."""

__version__ = "0.1.0"

from .classifier import analyze_input
from .metrics import compute_document_metrics, run_pipeline

__all__ = [
    "__version__",
    "analyze_input",
    "compute_document_metrics",
    "run_pipeline",
]
