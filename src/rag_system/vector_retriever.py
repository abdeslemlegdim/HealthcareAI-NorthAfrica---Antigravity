"""
Vector Retriever - FAISS-based semantic search
Phase 1 implementation with hybrid scoring
"""
import json
from datetime import datetime, timezone
import numpy as np
from typing import List, Dict, Optional
import pickle
from pathlib import Path
import time

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from src.models.model_loader import get_model_loader
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorRetriever:
    """
    FAISS-based vector retriever for semantic search
    Implements document embedding pipeline and index persistence
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/biomed_roberta_base",
        index_path: str = "data/cache/faiss_index.bin",
        docs_path: str = "data/cache/documents.pkl",
        metadata_path: str = "data/cache/metadata.pkl",
        batch_size: int = 32,
    ):
        """
        Initialize vector retriever
        
        Args:
            model_name: Sentence transformer model
            index_path: Path to FAISS index file
            docs_path: Path to documents pickle
            metadata_path: Path to metadata pickle
        """
        if not FAISS_AVAILABLE:
            logger.error("FAISS not installed. Install with: pip install faiss-cpu")
            raise ImportError("FAISS required for vector retrieval")
        
        self.model_name = model_name
        self.index_path = Path(index_path)
        self.docs_path = Path(docs_path)
        self.metadata_path = Path(metadata_path)
        self.manifest_path = self.index_path.with_suffix(".manifest.json")
        self.batch_size = batch_size
        self.loader = get_model_loader()
        self.last_embedding_ms = 0.0
        self.last_search_ms = 0.0
        self.cache_manifest: Dict[str, object] = {}
        
        # Load embedding model
        try:
            logger.info(f"Initializing embedding backend via shared loader: {model_name}")
            self.encoder = self.loader.get_embedding_model()
            self.dimension = 0
            if self.encoder is not None:
                self.dimension = int(self.encoder.get_sentence_embedding_dimension())
                logger.info(f"[OK] Local embedding model loaded (dim={self.dimension})")
            else:
                logger.info("Embedding local model unavailable; API mode will be used if configured")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

        self.cache_manifest = self._read_manifest()
        if self.dimension <= 0:
            self.dimension = int(self.cache_manifest.get("embedding_dimension", 0) or 0)
        
        # Initialize index
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Auto-load from cache if exists
        if self.index_path.exists():
            self._load_from_cache()
        
        logger.info("VectorRetriever initialized successfully")

    def _current_embedding_name(self) -> str:
        """Return the best available name for the active embedding backend."""
        encoder_name = getattr(self.encoder, "name_or_path", None)
        if isinstance(encoder_name, str) and encoder_name.strip():
            return encoder_name.strip()
        shared_name = getattr(self.loader, "embedding_model_name", None)
        if isinstance(shared_name, str) and shared_name.strip():
            return shared_name.strip()
        return self.model_name

    def _current_embedding_dimension(self) -> int:
        """Resolve the current embedding dimension from the model or cache."""
        if self.encoder is not None:
            try:
                return int(self.encoder.get_sentence_embedding_dimension())
            except Exception:
                pass

        if self.dimension > 0:
            return int(self.dimension)

        manifest_dim = self.cache_manifest.get("embedding_dimension")
        try:
            return int(manifest_dim)
        except Exception:
            return 0

    def _read_manifest(self) -> Dict[str, object]:
        """Load the cache manifest if it exists."""
        if not self.manifest_path.exists():
            return {}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            return manifest if isinstance(manifest, dict) else {}
        except Exception as exc:
            logger.warning("Failed to read FAISS manifest %s: %s", self.manifest_path, exc)
            return {}

    def _write_manifest(self) -> None:
        """Persist cache metadata for compatibility checks."""
        try:
            manifest = {
                "embedding_model_name": self._current_embedding_name(),
                "embedding_dimension": int(self.dimension),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "document_count": len(self.documents),
                "metadata_count": len(self.metadata),
                "index_file": str(self.index_path),
            }
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            self.cache_manifest = manifest
        except Exception as exc:
            logger.warning("Failed to write FAISS manifest: %s", exc)

    def _cache_matches_current_embedding(self) -> bool:
        """Check whether the on-disk cache matches the active embedding setup."""
        if not self.index:
            return False

        cached_model = str(self.cache_manifest.get("embedding_model_name", "") or "").strip()
        current_model = str(self._current_embedding_name()).strip()
        cached_dim = int(self.cache_manifest.get("embedding_dimension", getattr(self.index, "d", 0)) or getattr(self.index, "d", 0) or 0)
        current_dim = self._current_embedding_dimension()

        if current_dim and int(getattr(self.index, "d", current_dim)) != current_dim:
            return False

        if cached_dim and current_dim and cached_dim != current_dim:
            return False

        if cached_model and current_model and cached_model != current_model:
            return False

        return True

    def _build_index_from_documents(self, documents: List[str], metadata: List[Dict]) -> bool:
        """Encode documents and build a fresh FAISS index."""
        if len(documents) != len(metadata):
            raise ValueError("documents and metadata must have same length")

        embeddings = self.loader.embed_texts(documents, normalize=True, language="en")
        if embeddings is None:
            raise RuntimeError("Embedding generation failed for index build")

        embeddings = embeddings.astype("float32")
        self.dimension = int(embeddings.shape[1])

        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)

        self.documents = documents
        self.metadata = metadata
        self._save_to_cache()
        return True

    def _rebuild_from_cache_documents(self) -> bool:
        """Rebuild the index from cached documents when embedding metadata changed."""
        if not self.documents or not self.metadata:
            return False
        if self.encoder is None and not self.loader.use_embedding_api:
            logger.warning("Cannot rebuild FAISS cache without an embedding backend")
            return False

        try:
            logger.info("Rebuilding FAISS index from cached documents using %s", self._current_embedding_name())
            return self._build_index_from_documents(self.documents, self.metadata)
        except Exception as exc:
            logger.error("Failed to rebuild FAISS index from cache: %s", exc)
            return False
    
    def build_index(
        self,
        documents: List[str],
        metadata: List[Dict],
        force_rebuild: bool = False
    ) -> bool:
        """
        Build FAISS index from documents
        
        Args:
            documents: List of document texts
            metadata: List of metadata dicts (same length as documents)
            force_rebuild: Force rebuild even if cache exists
            
        Returns:
            True if successful
        """
        # Check cache
        if not force_rebuild:
            if self._load_from_cache():
                logger.info("Loaded index from cache")
                return True
        
        try:
            logger.info(f"Building FAISS index from {len(documents)} documents...")
            self._build_index_from_documents(documents, metadata)
            
            logger.info(f"[OK] FAISS index built successfully ({len(documents)} documents)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            return False
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: Optional[float] = None,
        language: Optional[str] = None,
    ) -> List[Dict]:
        """
        Perform semantic search using FAISS
        
        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Optional similarity threshold (0-1)
            
        Returns:
            List of results with scores and metadata
        """
        if self.index is None:
            logger.warning("Index not built. Call build_index() first.")
            return []

        if self.dimension <= 0 and hasattr(self.index, "d"):
            self.dimension = int(self.index.d)

        if hasattr(self.index, "d") and int(self.index.d) != int(self.dimension):
            logger.error(
                "Index dimension mismatch (index=%s, encoder=%s). Skipping vector search.",
                getattr(self.index, "d", "unknown"),
                self.dimension,
            )
            return []
        
        try:
            # Encode query
            emb_start = time.perf_counter()
            query_embedding = self.loader.embed_texts([query], normalize=True, language=language)
            if query_embedding is None:
                raise RuntimeError("Query embedding failed")
            query_embedding = query_embedding.astype('float32')
            faiss.normalize_L2(query_embedding)
            self.last_embedding_ms = (time.perf_counter() - emb_start) * 1000.0
            
            # Search FAISS index
            search_start = time.perf_counter()
            distances, indices = self.index.search(query_embedding, top_k)
            self.last_search_ms = (time.perf_counter() - search_start) * 1000.0
            
            # Format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                # IndexFlatIP over L2-normalized vectors yields cosine similarity.
                similarity = max(0.0, min(1.0, float(dist)))
                
                # Apply threshold if specified
                if threshold is not None and similarity < threshold:
                    continue
                
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': similarity,
                    'distance': float(1.0 - similarity),
                    'index': int(idx)
                })
            
            logger.debug(f"Semantic search returned {len(results)} results")
            return results
            
        except Exception as e:
            self.last_embedding_ms = 0.0
            self.last_search_ms = 0.0
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def hybrid_score(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict]:
        """
        Combine vector and keyword search results
        
        Args:
            vector_results: Results from semantic search
            keyword_results: Results from keyword search
            vector_weight: Weight for vector scores (0-1)
            keyword_weight: Weight for keyword scores (0-1)
            
        Returns:
            Combined and re-ranked results
        """
        try:
            # Normalize weights
            total_weight = vector_weight + keyword_weight
            vector_weight /= total_weight
            keyword_weight /= total_weight
            
            # Create score map by document ID
            scores = {}
            
            # Add vector scores
            for result in vector_results:
                doc_id = result.get('index', id(result['document']))
                scores[doc_id] = {
                    'combined_score': vector_weight * result['score'],
                    'vector_score': result['score'],
                    'keyword_score': 0.0,
                    'metadata': result['metadata'],
                    'document': result['document']
                }
            
            # Add keyword scores
            for result in keyword_results:
                doc_id = result.get('index', id(result['document']))
                if doc_id in scores:
                    scores[doc_id]['combined_score'] += keyword_weight * result['score']
                    scores[doc_id]['keyword_score'] = result['score']
                else:
                    scores[doc_id] = {
                        'combined_score': keyword_weight * result['score'],
                        'vector_score': 0.0,
                        'keyword_score': result['score'],
                        'metadata': result['metadata'],
                        'document': result['document']
                    }
            
            # Sort by combined score
            ranked = sorted(
                scores.values(),
                key=lambda x: x['combined_score'],
                reverse=True
            )
            
            logger.debug(f"Hybrid scoring combined {len(ranked)} results")
            return ranked
            
        except Exception as e:
            logger.error(f"Hybrid scoring failed: {e}")
            return vector_results if vector_results else keyword_results
    
    def _save_to_cache(self):
        """Persist index and data to disk"""
        try:
            # Create cache directory
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save documents and metadata
            with open(self.docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            self._write_manifest()
            
            logger.info(f"Index persisted to {self.index_path}")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_from_cache(self) -> bool:
        """Load index and data from disk"""
        try:
            if not (self.index_path.exists() and 
                    self.docs_path.exists() and 
                    self.metadata_path.exists()):
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))

            # Load documents and metadata
            with open(self.docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)

            self.cache_manifest = self._read_manifest()
            if self.dimension <= 0:
                self.dimension = int(self.cache_manifest.get("embedding_dimension", getattr(self.index, "d", 0)) or getattr(self.index, "d", 0) or 0)

            if not self._cache_matches_current_embedding():
                logger.warning(
                    "Cached FAISS index is stale for model=%s dim=%s; rebuilding from cached documents.",
                    self.cache_manifest.get("embedding_model_name", self._current_embedding_name()),
                    self.cache_manifest.get("embedding_dimension", getattr(self.index, "d", "unknown")),
                )
                self.index = None
                return self._rebuild_from_cache_documents()
            
            logger.info(f"Loaded {len(self.documents)} documents from cache")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load from cache: {e}")
            return False
    
    def get_index_stats(self) -> Dict:
        """Get index statistics"""
        if self.index is None:
            return {'status': 'not_built'}
        
        return {
            'status': 'ready',
            'num_documents': len(self.documents),
            'dimension': self.dimension,
            'model': self.model_name,
            'embedding_model_name': self._current_embedding_name(),
            'cache_manifest': self.cache_manifest,
            'index_size_mb': self.index_path.stat().st_size / (1024 * 1024) if self.index_path.exists() else 0
        }


# Singleton instance for convenience
_retriever_instance = None

def get_retriever(model_name: str = "sentence-transformers/biomed_roberta_base") -> VectorRetriever:
    """Get or create VectorRetriever singleton"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = VectorRetriever(model_name=model_name)
    return _retriever_instance
