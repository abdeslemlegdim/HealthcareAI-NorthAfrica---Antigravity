"""Test the enhanced RAG system with comprehensive knowledge base"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

from src.rag_system.rag import MedicalRAG

def test_rag():
    print("="*80)
    print("Testing Enhanced RAG System with Comprehensive Knowledge Base")
    print("="*80)
    
    # Initialize RAG
    rag = MedicalRAG()
    
    # Test questions
    questions = [
        "What are the symptoms of pneumonia?",
        "How is COVID-19 treated?",
        "What causes tuberculosis?",
        "What tests diagnose cardiomegaly?",
        "How to prevent pleural effusion?",
        "What are risk factors for atelectasis?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print('-'*80)
        
        result = rag.query(question)
        print(f"Language: {result.language}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"\nAnswer:")
        print(result.answer)
        
        if result.sources:
            print(f"\nSources ({len(result.sources)}):")
            for j, source in enumerate(result.sources[:3], 1):
                print(f"  {j}. {source.get('title')} (Relevance: {source.get('relevance_score', 0):.2f})")
    
    print("\n" + "="*80)
    print("✅ RAG System Test Complete!")
    print("="*80)

if __name__ == "__main__":
    test_rag()
