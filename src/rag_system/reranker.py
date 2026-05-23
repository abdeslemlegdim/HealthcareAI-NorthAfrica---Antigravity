"""
Cross-Encoder Reranker for RAG Pipeline
Phase 2: Precision improvement through reranking
"""
from typing import List, Dict, Optional
import numpy as np

from src.models.model_loader import get_model_loader

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MedicalReranker:
    """
    Cross-encoder based reranker for medical Q&A
    Reranks retrieved candidates for better precision
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/biomed-roberta-base",
        enabled: bool = True
    ):
        """
        Initialize cross-encoder reranker
        
        Args:
            model_name: Cross-encoder model name
            enabled: Whether reranking is enabled
        """
        self.model_name = model_name
        self.enabled = enabled
        self.model = None
        self.loader = get_model_loader()
        
        if self.enabled:
            try:
                logger.info(f"Loading cross-encoder model via shared loader: {model_name}")
                self.model = self.loader.get_reranker()
                if self.model is None and not self.loader.use_rerank_api:
                    raise RuntimeError("Reranker model could not be loaded")
                logger.info("[OK] Reranker backend initialized (local_or_api)")
            except Exception as e:
                logger.error(f"Failed to load cross-encoder: {e}")
                self.enabled = False
    
    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Rerank candidates using cross-encoder
        
        Args:
            query: User query
            candidates: List of candidate results with 'document' and 'metadata'
            top_k: Number of top results to return (None = all)
            score_threshold: Optional minimum score threshold
            
        Returns:
            Reranked and filtered results
        """
        if not self.enabled or not candidates:
            logger.debug("Reranking disabled or no candidates, returning as-is")
            return candidates
        
        try:
            # Prepare query-document pairs
            pairs = []
            for candidate in candidates:
                doc_text = candidate.get('document', '')
                if isinstance(doc_text, str):
                    pairs.append([query, doc_text])
                else:
                    # Fallback if document is not a string
                    pairs.append([query, str(candidate.get('metadata', {}).get('content', ''))])
            
            # Score with cross-encoder
            scores = self.loader.rerank_pairs(pairs)
            if scores is None:
                logger.warning("Reranking backend unavailable; returning original order")
                return candidates
            
            # Add reranking scores to candidates
            reranked = []
            for candidate, score in zip(candidates, scores):
                result = candidate.copy()
                result['rerank_score'] = float(score)
                result['original_score'] = candidate.get('score', 0.0)
                reranked.append(result)
            
            # Sort by reranking score
            reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Apply threshold if specified
            if score_threshold is not None:
                reranked = [r for r in reranked if r['rerank_score'] >= score_threshold]
            
            # Apply top_k if specified
            if top_k is not None:
                reranked = reranked[:top_k]
            
            logger.info(f"Reranked {len(candidates)} candidates -> {len(reranked)} results")
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return candidates
    
    def rerank_with_scores(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Rerank documents directly (without metadata)
        
        Args:
            query: User query
            documents: List of document strings
            top_k: Number of top results
            
        Returns:
            List of dicts with document and rerank_score
        """
        if not self.enabled:
            logger.warning("Reranking disabled")
            return [{'document': doc, 'rerank_score': 0.0} for doc in documents]
        
        try:
            # Prepare query-document pairs
            pairs = [[query, doc] for doc in documents]
            
            # Score with cross-encoder
            scores = self.loader.rerank_pairs(pairs)
            if scores is None:
                return [{'document': doc, 'rerank_score': 0.0} for doc in documents]
            
            # Create results
            results = [
                {
                    'document': doc,
                    'rerank_score': float(score)
                }
                for doc, score in zip(documents, scores)
            ]
            
            # Sort by score
            results.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            # Apply top_k
            if top_k is not None:
                results = results[:top_k]
            
            return results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return [{'document': doc, 'rerank_score': 0.0} for doc in documents]
    
    def enable(self):
        """Enable reranking"""
        if self.model is None:
            try:
                self.model = self.loader.get_reranker()
                if self.model is None and not self.loader.use_rerank_api:
                    raise RuntimeError("Reranker model unavailable")
                self.enabled = True
                logger.info("Reranking enabled")
            except Exception as e:
                logger.error(f"Failed to enable reranking: {e}")
        else:
            self.enabled = True
            logger.info("Reranking enabled")
    
    def disable(self):
        """Disable reranking"""
        self.enabled = False
        logger.info("Reranking disabled")
    
    def is_enabled(self) -> bool:
        """Check if reranking is enabled"""
        return self.enabled and (self.model is not None or self.loader.use_rerank_api)
    
    def get_status(self) -> Dict:
        """Get reranker status"""
        return {
            'enabled': self.enabled,
            'model_loaded': self.model is not None,
            'model_name': self.model_name if self.enabled else None
        }


# Singleton instance
_reranker_instance = None

def get_reranker(
    model_name: str = "cross-encoder/biomed-roberta-base",
    enabled: bool = True
) -> MedicalReranker:
    """Get or create MedicalReranker singleton"""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = MedicalReranker(model_name=model_name, enabled=enabled)
    return _reranker_instance
