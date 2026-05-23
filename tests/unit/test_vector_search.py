"""
Test FAISS Vector Search
"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

from src.rag_system.vector_search import MedicalVectorSearch, HybridSearch

def test_vector_search():
    """Test vector search functionality"""
    print("\n" + "="*80)
    print("🔍 TESTING FAISS VECTOR SEARCH")
    print("="*80)
    
    # Initialize
    print("\n1️⃣  Initializing vector search...")
    vs = MedicalVectorSearch()
    
    # Build index
    print("\n2️⃣  Building FAISS index from medical knowledge...")
    success = vs.build_index(force_rebuild=True)
    
    if not success:
        print("❌ Failed to build index")
        return False
    
    print(f"   ✅ Index built with {len(vs.documents)} documents")
    print(f"   📊 Embedding dimension: {vs.dimension}")
    
    # Test queries
    print("\n3️⃣  Testing semantic search...")
    
    test_queries = [
        "I have a persistent cough and fever",
        "trouble breathing shortness of breath",
        "how to prevent lung infections",
        "what tests diagnose pneumonia",
        "bacterial lung disease treatment"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{query}'")
        results = vs.search(query, top_k=3)
        
        for j, result in enumerate(results, 1):
            disease = result['metadata']['disease']
            section = result['metadata']['section']
            score = result['score']
            content = result['metadata']['content'][:60] + "..."
            
            print(f"      {j}. {disease} ({section}) - Score: {score:.3f}")
            print(f"         {content}")
    
    # Test disease similarity
    print("\n4️⃣  Testing disease similarity...")
    query = "respiratory infection with cough"
    similar_diseases = vs.get_similar_diseases(query, top_k=3)
    print(f"   Query: '{query}'")
    print(f"   Most relevant diseases: {', '.join(similar_diseases)}")
    
    # Test hybrid search
    print("\n5️⃣  Testing hybrid search...")
    hybrid = HybridSearch(vs)
    
    query = "fever and cough symptoms"
    print(f"   Query: '{query}'")
    results = hybrid.search(query, top_k=5)
    
    for i, result in enumerate(results, 1):
        disease = result['metadata']['disease']
        section = result['metadata']['section']
        score = result['score']
        print(f"      {i}. {disease} ({section}) - Combined Score: {score:.3f}")
    
    print("\n" + "="*80)
    print("✅ VECTOR SEARCH TEST PASSED!")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_vector_search()
    sys.exit(0 if success else 1)
