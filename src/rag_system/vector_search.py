"""
FAISS Vector Search for Medical Knowledge
Semantic similarity search using sentence embeddings
"""
import numpy as np
from typing import List, Dict, Tuple
import pickle
import os
from pathlib import Path

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS not installed. Install with: pip install faiss-cpu")

from sentence_transformers import SentenceTransformer
from .knowledge_base import MEDICAL_KNOWLEDGE
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MedicalVectorSearch:
    """FAISS-based semantic search for medical knowledge"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialize vector search
        
        Args:
            model_name: Sentence transformer model name (default: all-mpnet-base-v2)
        """
        self.model_name = model_name
        
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.encoder = SentenceTransformer(model_name)
            self.dimension = self.encoder.get_sentence_embedding_dimension()
            logger.info(f"[OK] Model loaded successfully (dimension={self.dimension})")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
        
        self.index = None
        self.documents = []
        self.metadata = []
        
        logger.info(f"Initialized MedicalVectorSearch with {model_name} (dim={self.dimension})")
    
    def build_index(self, force_rebuild: bool = False):
        """
        Build FAISS index from medical knowledge base
        
        Args:
            force_rebuild: Force rebuild even if cache exists
        """
        if not FAISS_AVAILABLE:
            logger.error("FAISS not available. Cannot build index.")
            return False
        
        cache_dir = Path("data/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        index_path = cache_dir / "faiss_index.bin"
        docs_path = cache_dir / "documents.pkl"
        meta_path = cache_dir / "metadata.pkl"
        
        # Load from cache if exists
        if not force_rebuild and index_path.exists():
            logger.info("Loading FAISS index from cache...")
            self.index = faiss.read_index(str(index_path))
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            with open(meta_path, 'rb') as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded {len(self.documents)} documents from cache")
            return True
        
        logger.info("Building FAISS index from medical knowledge...")
        
        # Prepare documents
        documents = []
        metadata = []
        
        # MEDICAL_KNOWLEDGE is a dict, iterate over values
        for disease_key, disease in MEDICAL_KNOWLEDGE.items():
            disease_name = disease.get('name', disease_key)
            
            # Main description
            documents.append(f"{disease_name}: {disease.get('description', '')}")
            metadata.append({
                'disease': disease_name,
                'section': 'description',
                'content': disease.get('description', '')
            })
            
            # Symptoms
            for symptom in disease.get('symptoms', []):
                documents.append(f"{disease_name} symptom: {symptom}")
                metadata.append({
                    'disease': disease_name,
                    'section': 'symptoms',
                    'content': symptom
                })
            
            # Treatment
            for treatment in disease.get('treatment', []):
                documents.append(f"{disease_name} treatment: {treatment}")
                metadata.append({
                    'disease': disease_name,
                    'section': 'treatment',
                    'content': treatment
                })
            
            # Diagnosis
            for diagnosis in disease.get('diagnosis', []):
                documents.append(f"{disease_name} diagnosis: {diagnosis}")
                metadata.append({
                    'disease': disease_name,
                    'section': 'diagnosis',
                    'content': diagnosis
                })
            
            # Causes
            for cause in disease.get('causes', []):
                documents.append(f"{disease_name} cause: {cause}")
                metadata.append({
                    'disease': disease_name,
                    'section': 'causes',
                    'content': cause
                })
            
            # Prevention
            for prevention in disease.get('prevention', []):
                documents.append(f"{disease_name} prevention: {prevention}")
                metadata.append({
                    'disease': disease_name,
                    'section': 'prevention',
                    'content': prevention
                })
        
        self.documents = documents
        self.metadata = metadata
        
        logger.info(f"Encoding {len(documents)} documents...")
        embeddings = self.encoder.encode(documents, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        logger.info("Creating FAISS index...")
        self.index = faiss.IndexFlatL2(self.dimension)  # L2 distance
        self.index.add(embeddings)
        
        # Save to cache
        logger.info("Saving index to cache...")
        faiss.write_index(self.index, str(index_path))
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
        with open(meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        logger.info(f"[OK] Built FAISS index with {len(documents)} documents")
        return True
    
    def search(self, query: str, top_k: int = 5, threshold: float = None) -> List[Dict]:
        """
        Semantic search using FAISS
        
        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Optional distance threshold
        
        Returns:
            List of results with scores and metadata
        """
        if not FAISS_AVAILABLE or self.index is None:
            logger.warning("FAISS index not available")
            return []
        
        try:
            # Encode query
            query_embedding = self.encoder.encode([query])
            query_embedding = np.array(query_embedding).astype('float32')
            
            # Search
            distances, indices = self.index.search(query_embedding, top_k)
            
            # Format results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if threshold is not None and dist > threshold:
                    continue
                
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + dist)
                
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(similarity),
                    'distance': float(dist)
                })
            
            logger.debug(f"Search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def search_by_disease(self, query: str, disease: str, top_k: int = 3) -> List[Dict]:
        """
        Search within a specific disease
        
        Args:
            query: Search query
            disease: Disease name to filter by
            top_k: Number of results
        
        Returns:
            Filtered results for the disease
        """
        # Search broadly first
        all_results = self.search(query, top_k=top_k * 3)
        
        # Filter by disease
        filtered = [r for r in all_results if r['metadata']['disease'] == disease]
        
        return filtered[:top_k]
    
    def get_similar_diseases(self, query: str, top_k: int = 3) -> List[str]:
        """
        Get most relevant diseases for a query
        
        Args:
            query: Search query
            top_k: Number of diseases
        
        Returns:
            List of disease names
        """
        results = self.search(query, top_k=top_k * 2)
        
        # Extract unique diseases maintaining order
        seen = set()
        diseases = []
        for result in results:
            disease = result['metadata']['disease']
            if disease not in seen:
                seen.add(disease)
                diseases.append(disease)
                if len(diseases) >= top_k:
                    break
        
        return diseases


class HybridSearch:
    """Combines keyword and vector search"""
    
    def __init__(self, vector_search: MedicalVectorSearch):
        """
        Initialize hybrid search
        
        Args:
            vector_search: Vector search instance
        """
        self.vector_search = vector_search
        logger.info("Initialized HybridSearch")
    
    def search(self, query: str, top_k: int = 5, 
               vector_weight: float = 0.6, keyword_weight: float = 0.4) -> List[Dict]:
        """
        Hybrid search combining vector and keyword methods
        
        Args:
            query: Search query
            top_k: Number of results
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        
        Returns:
            Combined and ranked results
        """
        # Vector search
        vector_results = self.vector_search.search(query, top_k=top_k * 2)
        
        # Keyword search (simple matching)
        keyword_results = self._keyword_search(query, top_k=top_k * 2)
        
        # Combine scores
        combined_scores = {}
        
        for result in vector_results:
            doc_id = result['document']
            combined_scores[doc_id] = vector_weight * result['score']
        
        for result in keyword_results:
            doc_id = result['document']
            if doc_id in combined_scores:
                combined_scores[doc_id] += keyword_weight * result['score']
            else:
                combined_scores[doc_id] = keyword_weight * result['score']
        
        # Sort by combined score
        sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top results with metadata
        results = []
        for doc_id, score in sorted_docs[:top_k]:
            # Find metadata
            idx = self.vector_search.documents.index(doc_id)
            results.append({
                'document': doc_id,
                'metadata': self.vector_search.metadata[idx],
                'score': score
            })
        
        return results
    
    def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple keyword-based search"""
        query_lower = query.lower()
        query_terms = set(query_lower.split())
        
        scores = []
        for i, doc in enumerate(self.vector_search.documents):
            doc_lower = doc.lower()
            doc_terms = set(doc_lower.split())
            
            # Calculate overlap
            overlap = len(query_terms & doc_terms)
            score = overlap / max(len(query_terms), 1)
            
            if score > 0:
                scores.append((i, score))
        
        # Sort and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            results.append({
                'document': self.vector_search.documents[idx],
                'metadata': self.vector_search.metadata[idx],
                'score': score
            })
        
        return results


# Singleton instance
_vector_search_instance = None

def get_vector_search() -> MedicalVectorSearch:
    """Get or create vector search instance"""
    global _vector_search_instance
    if _vector_search_instance is None:
        _vector_search_instance = MedicalVectorSearch()
        _vector_search_instance.build_index()
    return _vector_search_instance
