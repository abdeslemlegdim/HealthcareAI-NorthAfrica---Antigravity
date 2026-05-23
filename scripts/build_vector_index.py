"""
Build FAISS Index - Standalone script
Creates vector search index from medical knowledge
"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

from src.rag_system.vector_search import MedicalVectorSearch

def main():
    """Build the FAISS index"""
    print("\n🔧 Building FAISS Vector Index...")
    print("="*80)
    
    vs = MedicalVectorSearch()
    success = vs.build_index(force_rebuild=True)
    
    if success:
        print("\n✅ Index built successfully!")
        print(f"   📊 {len(vs.documents)} documents indexed")
        print(f"   💾 Saved to: data/cache/")
        print("\n   Ready to use with enhanced RAG system!")
    else:
        print("\n❌ Failed to build index")
        return 1
    
    print("="*80 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
