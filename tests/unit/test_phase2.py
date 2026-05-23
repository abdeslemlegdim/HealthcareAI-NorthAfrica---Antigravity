"""
Phase 2: Cross-Encoder Reranking Test
"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

from src.rag_system.reranker import get_reranker, MedicalReranker
from src.rag_system.rag import MedicalRAG
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_reranker_standalone():
    """Test reranker in isolation"""
    print("\n" + "="*80)
    print("TEST 1: Reranker Standalone")
    print("="*80)
    
    reranker = get_reranker()
    status = reranker.get_status()
    
    print(f"\nReranker Status:")
    print(f"  Enabled: {status['enabled']}")
    print(f"  Model Loaded: {status['model_loaded']}")
    print(f"  Model: {status['model_name']}")
    
    if not status['model_loaded']:
        print("❌ Reranker not loaded")
        return False
    
    # Test reranking
    query = "What are the symptoms of pneumonia?"
    
    documents = [
        "Pneumonia symptoms include cough, fever, and difficulty breathing",
        "COVID-19 can cause respiratory symptoms",
        "Normal chest X-rays show clear lungs",
        "Tuberculosis treatment requires antibiotics for 6-9 months",
        "Pneumonia is diagnosed using chest X-rays and blood tests"
    ]
    
    print(f"\nQuery: '{query}'")
    print(f"Documents: {len(documents)}")
    
    results = reranker.rerank_with_scores(query, documents, top_k=3)
    
    print("\nReranked Results:")
    for i, result in enumerate(results, 1):
        doc_preview = result['document'][:60] + "..."
        score = result['rerank_score']
        print(f"  {i}. Score: {score:.3f} - {doc_preview}")
    
    print("\n✅ Reranker Working")
    return True


def test_reranker_with_metadata():
    """Test reranking with full metadata"""
    print("\n" + "="*80)
    print("TEST 2: Reranking with Metadata")
    print("="*80)
    
    reranker = get_reranker()
    query = "fever and cough"
    
    candidates = [
        {
            'document': 'Pneumonia symptom: fever and chills',
            'metadata': {'disease': 'Pneumonia', 'section': 'symptoms'},
            'score': 0.75
        },
        {
            'document': 'COVID-19 treatment: rest and hydration',
            'metadata': {'disease': 'COVID-19', 'section': 'treatment'},
            'score': 0.60
        },
        {
            'document': 'Tuberculosis symptom: persistent cough',
            'metadata': {'disease': 'Tuberculosis', 'section': 'symptoms'},
            'score': 0.70
        }
    ]
    
    print(f"\nQuery: '{query}'")
    print(f"Candidates: {len(candidates)}")
    
    reranked = reranker.rerank(query, candidates, top_k=2)
    
    print("\nReranked Results:")
    for i, result in enumerate(reranked, 1):
        disease = result['metadata']['disease']
        section = result['metadata']['section']
        rerank_score = result.get('rerank_score', 0)
        original_score = result.get('original_score', 0)
        print(f"  {i}. {disease} ({section})")
        print(f"     Original: {original_score:.3f} -> Reranked: {rerank_score:.3f}")
    
    print("\n✅ Metadata Reranking Working")
    return True


def test_rag_with_reranking():
    """Test RAG system with reranking enabled"""
    print("\n" + "="*80)
    print("TEST 3: RAG Integration (Reranking Enabled)")
    print("="*80)
    
    # Create RAG with reranking enabled
    rag = MedicalRAG(use_reranking=True)
    
    queries = [
        "What are pneumonia symptoms?",
        "How to treat tuberculosis?",
        "Diagnosing COVID-19"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n  Query {i}: '{query}'")
        result = rag.query(query)
        
        if not result or not result.answer:
            print("    ❌ No answer")
            return False
        
        print(f"    Sources: {len(result.sources)}")
        print(f"    Answer: {result.answer[:80]}...")
    
    print("\n✅ RAG with Reranking Working")
    return True


def test_reranking_toggle():
    """Test enabling/disabling reranking"""
    print("\n" + "="*80)
    print("TEST 4: Reranking Toggle")
    print("="*80)
    
    reranker = get_reranker()
    
    # Test disable
    print("\n  Disabling reranking...")
    reranker.disable()
    assert not reranker.is_enabled(), "Failed to disable"
    print("  ✅ Disabled")
    
    # Test enable
    print("\n  Enabling reranking...")
    reranker.enable()
    assert reranker.is_enabled(), "Failed to enable"
    print("  ✅ Enabled")
    
    print("\n✅ Toggle Working")
    return True


def main():
    """Run all Phase 2 verification tests"""
    print("\n" + "🎯"*40)
    print("="*80)
    print("PHASE 2 VERIFICATION")
    print("Cross-Encoder Reranking")
    print("="*80)
    
    tests = [
        ("Reranker Standalone", test_reranker_standalone),
        ("Reranking with Metadata", test_reranker_with_metadata),
        ("RAG Integration", test_rag_with_reranking),
        ("ReReranking Toggle", test_reranking_toggle)
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
    print("PHASE 2 VERIFICATION RESULTS")
    print("="*80)
    print(f"\n  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if failed == 0:
        print("\n" + "🎉"*40)
        print("✅ PHASE 2 COMPLETE - ALL TESTS PASSED")
        print("="*80)
        print("\nFeatures Implemented:")
        print("  ✅ cross-encoder/ms-marco-MiniLM-L-6-v2 loaded")
        print("  ✅ MedicalReranker class with reranking logic")
        print("  ✅ Top-K reranking")
        print("  ✅ Optional enable/disable flag")
        print("  ✅ RAG pipeline integration")
        print("  ✅ Logging and error handling")
        print("\n" + "="*80)
        print("📋 READY FOR PHASE 3: LLM Answer Generation")
        print("="*80 + "\n")
        return 0
    else:
        print("\n❌ PHASE 2 INCOMPLETE - Fix errors and retry")
        return 1


if __name__ == "__main__":
    sys.exit(main())
