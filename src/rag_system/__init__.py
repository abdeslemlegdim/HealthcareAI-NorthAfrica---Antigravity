"""
RAG (Retrieval-Augmented Generation) System Module

This module implements:
- Hybrid retrieval (FAISS vector search + BM25 keyword search)
- Multi-lingual medical knowledge retrieval (Arabic, French, English)
- Cross-encoder reranking
- LLM-powered answer generation
- Medical knowledge graph integration
"""

__all__ = ["MedicalRAG", "HybridRetriever", "MedicalKnowledgeGraph"]
