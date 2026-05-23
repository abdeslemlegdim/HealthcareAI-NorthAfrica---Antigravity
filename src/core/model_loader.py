"""Compatibility wrapper for centralized model loader.

This keeps a stable import path (`src.core.model_loader`) while the
implementation lives in `src.models.model_loader`.
"""

from src.models.model_loader import (  # noqa: F401
    ModelLoader,
    get_embedding_model,
    get_imaging_model,
    get_llm,
    get_model_loader,
    get_reranker,
)
