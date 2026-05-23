"""
Multilingual Embeddings Module
Phase 6: Cross-lingual semantic embeddings
"""

import logging
import os
from typing import List, Optional
import numpy as np

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available")


class MultilingualEmbeddings:
    """
    Multilingual Embeddings for Cross-lingual Medical QA
    
    Features:
    - Supports English, Arabic, French
    - Cross-lingual retrieval (query in any language, retrieve from all)
    - Medical domain adaptation
    - Compatible with Phase 1 vector retrieval
    
    Models:
    - intfloat/multilingual-e5-base (768-dim, best quality)
    - paraphrase-multilingual-MiniLM-L12-v2 (384-dim, faster)
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize multilingual embeddings
        
        Args:
            model_name: Model identifier (default: paraphrase-multilingual-MiniLM-L12-v2)
            device: Device for computation ('cuda' or 'cpu')
            cache_dir: Directory to cache models
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers required. Install: pip install sentence-transformers")
        
        # Default to lightweight multilingual model
        self.model_name = model_name or os.getenv(
            "MULTILINGUAL_MODEL",
            "paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        self.device = device or os.getenv("DEVICE", "cpu")
        self.cache_dir = cache_dir
        
        # Load model
        logger.info(f"Loading multilingual model: {self.model_name}")
        self.model = SentenceTransformer(
            self.model_name,
            device=self.device,
            cache_folder=self.cache_dir
        )
        
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"✅ Multilingual embeddings loaded ({self.embedding_dim}-dim)")
    
    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Encode texts to embeddings
        
        Args:
            texts: List of texts to encode (any supported language)
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length
            
        Returns:
            Numpy array of embeddings [N, D]
        """
        if not texts:
            return np.array([])
        
        # Encode with sentence-transformers
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def encode_query(self, query: str, normalize: bool = True) -> np.ndarray:
        """
        Encode single query (convenience method)
        
        Args:
            query: Query text (any supported language)
            normalize: Normalize embedding
            
        Returns:
            1D embedding vector
        """
        # For E5 models, add instruction prefix for better retrieval
        if 'e5' in self.model_name.lower():
            query = f"query: {query}"
        
        embedding = self.model.encode(
            [query],
            normalize_embeddings=normalize,
            convert_to_numpy=True
        )
        
        return embedding[0]
    
    def encode_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Encode documents for indexing
        
        Args:
            documents: List of documents (any supported language)
            batch_size: Batch size
            show_progress: Show progress
            
        Returns:
            Embeddings array [N, D]
        """
        # For E5 models, add passage prefix
        if 'e5' in self.model_name.lower():
            documents = [f"passage: {doc}" for doc in documents]
        
        return self.encode(
            documents,
            batch_size=batch_size,
            show_progress=show_progress,
            normalize=True
        )
    
    def get_embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.embedding_dim
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name


# Singleton instance
_multilingual_embeddings = None

def get_multilingual_embeddings(
    model_name: Optional[str] = None,
    device: Optional[str] = None
) -> MultilingualEmbeddings:
    """
    Get or create multilingual embeddings instance (singleton)
    
    Args:
        model_name: Model identifier
        device: Device ('cuda' or 'cpu')
        
    Returns:
        MultilingualEmbeddings instance
    """
    global _multilingual_embeddings
    
    if _multilingual_embeddings is None:
        _multilingual_embeddings = MultilingualEmbeddings(
            model_name=model_name,
            device=device
        )
    
    return _multilingual_embeddings
