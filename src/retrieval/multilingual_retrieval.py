"""
Multilingual Vector Retrieval
Phase 6: Cross-lingual medical document retrieval
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
import json
import numpy as np

from src.rag_system.vector_retriever import VectorRetriever
from multilingual import get_multilingual_embeddings, MultilingualEmbeddings

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultilingualVectorRetriever(VectorRetriever):
    """
    Multilingual Vector Retrieval System
    
    Features:
    - Cross-lingual semantic search (query in any language, retrieve from all)
    - Support for English, Arabic, French medical documents
    - Compatible with Phase 1 infrastructure
    - Parallel indexing of multilingual knowledge bases
    """
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        model_name: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Initialize multilingual vector retriever
        
        Args:
            index_path: Path to FAISS index directory
            model_name: Multilingual model name
            device: Device for computation
        """
        # Set default index path for multilingual retriever
        if index_path is None:
            index_path = "data/cache/multilingual_faiss_index.bin"
        
        # Set up multilingual embeddings
        self.multilingual_embeddings = get_multilingual_embeddings(
            model_name=model_name,
            device=device
        )
        
        # Initialize with parent class (will override embedding model)
        super().__init__(index_path=index_path)
        
        # Replace monolingual embeddings with multilingual
        self.embeddings = self.multilingual_embeddings
        self.embedding_dim = self.multilingual_embeddings.get_embedding_dim()
        
        logger.info(f"✅ Multilingual retriever initialized ({self.embedding_dim}-dim)")
    
    def load_multilingual_documents(
        self,
        knowledge_paths: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Load documents from multiple language knowledge bases
        
        Args:
            knowledge_paths: List of paths to knowledge JSON files
                            If None, loads default en/ar/fr files
        
        Returns:
            List of all documents from all languages
        """
        if knowledge_paths is None:
            # Default knowledge base paths
            data_dir = Path("data")
            knowledge_paths = [
                str(data_dir / "processed" / "medical_documents.json"),  # English
                str(data_dir / "medical_knowledge_ar.json"),  # Arabic
                str(data_dir / "medical_knowledge_fr.json"),  # French
            ]
        
        all_documents = []
        
        for kb_path in knowledge_paths:
            if not Path(kb_path).exists():
                logger.warning(f"Knowledge base not found: {kb_path}")
                continue
            
            try:
                with open(kb_path, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                    all_documents.extend(docs)
                    logger.info(f"Loaded {len(docs)} documents from {Path(kb_path).name}")
            except Exception as e:
                logger.error(f"Failed to load {kb_path}: {e}")
        
        logger.info(f"Total multilingual documents loaded: {len(all_documents)}")
        return all_documents
    
    def build_multilingual_index(
        self,
        knowledge_paths: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ):
        """
        Build FAISS index from multilingual documents
        
        Args:
            knowledge_paths: Paths to knowledge base files
            save_path: Directory to save index
        """
        # Load multilingual documents
        documents = self.load_multilingual_documents(knowledge_paths)
        
        if not documents:
            raise ValueError("No documents loaded for indexing")
        
        # Extract content for embedding
        doc_contents = []
        for doc in documents:
            # Combine title and content for better retrieval
            content = f"{doc.get('title', '')} {doc.get('content', '')}"
            doc_contents.append(content.strip())
        
        logger.info(f"Encoding {len(doc_contents)} multilingual documents...")
        
        # Encode with multilingual model
        embeddings = self.multilingual_embeddings.encode_documents(
            doc_contents,
            batch_size=32,
            show_progress=True
        )
        
        # Build FAISS index
        import faiss
        
        # Use L2 normalized vectors for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create index
        self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product (cosine)
        self.index.add(embeddings.astype('float32'))
        
        # Store documents
        self.documents = documents
        
        logger.info(f"✅ Multilingual index built with {len(documents)} documents")
        
        # Save index
        if save_path:
            self.save_index(save_path)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None
    ) -> List[dict]:
        """
        Search multilingual index
        
        Args:
            query: Search query (any supported language)
            top_k: Number of results to return
            language: Optional language filter (en, ar, fr)
        
        Returns:
            List of retrieved documents with scores
        """
        if self.index is None:
            raise ValueError("Index not loaded. Call build_multilingual_index() or load_index() first.")
        
        # Encode query with multilingual model
        query_embedding = self.multilingual_embeddings.encode_query(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Normalize for cosine similarity
        import faiss
        faiss.normalize_L2(query_embedding)
        
        # Search
        # Retrieve more than needed if language filtering
        search_k = top_k * 3 if language else top_k
        scores, indices = self.index.search(query_embedding, search_k)
        
        # Prepare results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= len(self.documents):
                continue
            
            doc = self.documents[idx]
            
            # Language filtering
            if language and doc.get('language', 'en') != language:
                continue
            
            result = {
                **doc,
                'score': float(score),
                'rank': len(results) + 1
            }
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results


# Singleton instance
_multilingual_retriever = None

def get_multilingual_retriever(
    index_path: Optional[str] = None,
    model_name: Optional[str] = None
) -> MultilingualVectorRetriever:
    """
    Get or create multilingual retriever instance (singleton)
    
    Args:
        index_path: Path to index directory
        model_name: Multilingual model name
        
    Returns:
        MultilingualVectorRetriever instance
    """
    global _multilingual_retriever
    
    if _multilingual_retriever is None:
        _multilingual_retriever = MultilingualVectorRetriever(
            index_path=index_path,
            model_name=model_name
        )
    
    return _multilingual_retriever
