"""
Build FAISS Index from Medical Knowledge
Phase 1: Embeddings + Vector Search
"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

from src.rag_system.vector_retriever import VectorRetriever
from src.rag_system.knowledge_base import MEDICAL_KNOWLEDGE
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def prepare_documents():
    """Extract documents and metadata from knowledge base"""
    documents = []
    metadata = []
    
    for disease_key, disease_info in MEDICAL_KNOWLEDGE.items():
        disease_name = disease_info.get('name', disease_key)
        
        # Description
        desc = disease_info.get('description', '')
        if desc:
            documents.append(f"{disease_name}: {desc}")
            metadata.append({
                'disease': disease_name,
                'section': 'description',
                'content': desc
            })
        
        # Symptoms
        for symptom in disease_info.get('symptoms', []):
            documents.append(f"{disease_name} symptom: {symptom}")
            metadata.append({
                'disease': disease_name,
                'section': 'symptoms',
                'content': symptom
            })
        
        # Treatment
        for treatment in disease_info.get('treatment', []):
            documents.append(f"{disease_name} treatment: {treatment}")
            metadata.append({
                'disease': disease_name,
                'section': 'treatment',
                'content': treatment
            })
        
        # Diagnosis
        for diagnosis in disease_info.get('diagnosis', []):
            documents.append(f"{disease_name} diagnosis: {diagnosis}")
            metadata.append({
                'disease': disease_name,
                'section': 'diagnosis',
                'content': diagnosis
            })
        
        # Causes
        for cause in disease_info.get('causes', []):
            documents.append(f"{disease_name} cause: {cause}")
            metadata.append({
                'disease': disease_name,
                'section': 'causes',
                'content': cause
            })
        
        # Prevention
        for prevention in disease_info.get('prevention', []):
            documents.append(f"{disease_name} prevention: {prevention}")
            metadata.append({
                'disease': disease_name,
                'section': 'prevention',
                'content': prevention
            })
    
    return documents, metadata


def main():
    """Build FAISS index with all-mpnet-base-v2"""
    print("\n" + "="*80)
    print("PHASE 1: Building FAISS Index")
    print("="*80)
    
    # Initialize retriever
    print("\n1. Initializing VectorRetriever...")
    retriever = VectorRetriever(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Prepare documents
    print("\n2. Preparing documents from medical knowledge base...")
    documents, metadata = prepare_documents()
    print(f"   ✅ Prepared {len(documents)} documents")
    
    # Build index
    print("\n3. Building FAISS index (this may take a minute)...")
    success = retriever.build_index(documents, metadata, force_rebuild=True)
    
    if success:
        stats = retriever.get_index_stats()
        print("\n" + "="*80)
        print("✅ PHASE 1 COMPLETE")
        print("="*80)
        print(f"\nIndex Statistics:")
        print(f"  Status: {stats['status']}")
        print(f"  Documents: {stats['num_documents']}")
        print(f"  Embedding Dimension: {stats['dimension']}")
        print(f"  Model: {stats['model']}")
        print(f"  Index Size: {stats['index_size_mb']:.2f} MB")
        print(f"\nIntegration: Vector search automatically enabled in RAG pipeline")
        print("="*80 + "\n")
        return 0
    else:
        print("\n❌ PHASE 1 FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
