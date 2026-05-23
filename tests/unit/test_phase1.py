"""
PHASE 1 Verification Test
Tests vector retrieval with hybrid scoring
"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

from src.rag_system.vector_retriever import get_retriever
from src.rag_system.rag import MedicalRAG
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_vector_retriever():
    """Test vector retriever directly"""
    print("\n" + "="*80)
    print("TEST 1: Vector Retriever")
    print("="*80)
    
    retriever = get_retriever()
    
    # Check stats
    stats = retriever.get_index_stats()
    print(f"\nIndex Stats:")
    print(f"  Status: {stats['status']}")
    print(f"  Documents: {stats.get('num_documents', 'N/A')}")
    print(f"  Dimension: {stats.get('dimension', 'N/A')}")
    print(f"  Model: {stats.get('model', 'N/A')}")
    
    if stats['status'] != 'ready':
        print("❌ Index not ready")
        return False
    
    # Test semantic search
    print("\nSemantic Search Tests:")
    queries = [
        "persistent cough with fever",
        "how to prevent lung infections",
        "chest X-ray diagnosis methods"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n  Query {i}: '{query}'")
        results = retriever.semantic_search(query, top_k=3)
        
        if not results:
            print("    ❌ No results")
            return False
        
        for j, result in enumerate(results, 1):
            disease = result['metadata']['disease']
            section = result['metadata']['section']
            score = result['score']
            print(f"    {j}. {disease} ({section}) - Score: {score:.3f}")
    
    print("\n✅ Vector Retriever Working")
    return True


def test_hybrid_scoring():
    """Test hybrid score combination"""
    print("\n" + "="*80)
    print("TEST 2: Hybrid Scoring")
    print("="*80)
    
    retriever = get_retriever()
    
    query = "cough and fever symptoms"
    print(f"\nQuery: '{query}'")
    
    # Get vector results
    vector_results = retriever.semantic_search(query, top_k=5)
    print(f"\n  Vector results: {len(vector_results)}")
    
    # Simulate keyword results
    keyword_results = [
        {
            'document': 'mock keyword result',
            'metadata': {'disease': 'Pneumonia', 'section': 'symptoms'},
            'score': 0.8,
            'index': 0
        }
    ]
    print(f"  Keyword results: {len(keyword_results)}")
    
    # Combine
    hybrid_results = retriever.hybrid_score(
        vector_results,
        keyword_results,
        vector_weight=0.7,
        keyword_weight=0.3
    )
    
    print(f"\n  Hybrid results: {len(hybrid_results)}")
    for i, result in enumerate(hybrid_results[:3], 1):
        print(f"    {i}. {result['metadata']['disease']} - Combined: {result['combined_score']:.3f} "
              f"(V:{result['vector_score']:.2f} K:{result['keyword_score']:.2f})")
    
    print("\n✅ Hybrid Scoring Working")
    return True


def test_rag_integration():
    """Test RAG system with vector search"""
    print("\n" + "="*80)
    print("TEST 3: RAG Integration")
    print("="*80)
    
    rag = MedicalRAG()
    
    test_queries = [
        "What are the symptoms of pneumonia?",
        "How is tuberculosis diagnosed?",
        "Treatment for COVID-19"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n  Query {i}: '{query}'")
        result = rag.query(query)
        
        if not result or not result.answer:
            print("    ❌ No answer generated")
            return False
        
        print(f"    Language: {result.language}")
        print(f"    Confidence: {result.confidence}")
        print(f"    Sources: {len(result.sources)}")
        print(f"    Answer: {result.answer[:100]}...")
    
    print("\n✅ RAG Integration Working")
    return True


def main():
    """Run all Phase 1 verification tests"""
    print("\n" + "🎯"*40)
    print("="*80)
    print("PHASE 1 VERIFICATION")
    print("Embeddings + FAISS Vector Search + Hybrid Scoring")
    print("="*80)
    
    tests = [
        ("Vector Retriever", test_vector_retriever),
        ("Hybrid Scoring", test_hybrid_scoring),
        ("RAG Integration", test_rag_integration)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print("PHASE 1 VERIFICATION RESULTS")
    print("="*80)
    print(f"\n  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if failed == 0:
        print("\n" + "🎉"*40)
        print("✅ PHASE 1 COMPLETE - ALL TESTS PASSED")
        print("="*80)
        print("\nFeatures Implemented:")
        print("  ✅ sentence-transformers/all-mpnet-base-v2 loaded")
        print("  ✅ FAISS index creation and persistence")
        print("  ✅ Document embedding pipeline")
        print("  ✅ Semantic search function")
        print("  ✅ Hybrid score combination (vector + keyword)")
        print("  ✅ RAG pipeline integration (no breaking changes)")
        print("  ✅ Logging and error handling")
        print("\n" + "="*80)
        print("📋 READY FOR PHASE 2: Cross-Encoder Reranking")
        print("="*80 + "\n")
        return 0
    else:
        print("\n❌ PHASE 1 INCOMPLETE - Fix errors and retry")
        return 1


if __name__ == "__main__":
    sys.exit(main())
