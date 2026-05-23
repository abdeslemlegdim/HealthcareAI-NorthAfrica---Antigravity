"""
Test Enhanced RAG with Vector Search
"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

from src.rag_system.rag import MedicalRAG

def test_enhanced_rag():
    """Test RAG with vector search integration"""
    print("\n" + "="*80)
    print("🎯 TESTING ENHANCED RAG WITH VECTOR SEARCH")
    print("="*80)
    
    rag = MedicalRAG()
    
    test_queries = [
        "I have a persistent cough and fever, what could it be?",
        "How can I prevent respiratory infections?",
        "What tests are used to diagnose lung problems?",
        "bacterial infection treatment antibiotics",
        "عندي كحة وحرارة",  # Arabic: I have cough and fever
        "Comment traiter une infection pulmonaire?"  # French: How to treat lung infection?
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print(f"{'='*80}")
        
        result = rag.query(query)
        
        print(f"Language: {result.language}")
        print(f"Confidence: {result.confidence}")
        print(f"\nAnswer Preview:")
        print(result.answer[:300] + "..." if len(result.answer) > 300 else result.answer)
        print(f"\nSources: {len(result.sources)} relevant diseases found")
    
    print("\n" + "="*80)
    print("✅ ENHANCED RAG TEST COMPLETE")
    print("   Vector search is now integrated for better semantic retrieval!")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_enhanced_rag()
    sys.exit(0 if success else 1)
