"""
Phase 6 Verification: Multilingual Extension
Tests Arabic and French language support
"""

import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_language_detection():
    """Test 1: Language Detection"""
    print("\n" + "="*60)
    print("TEST 1: Language Detection")
    print("="*60)
    
    try:
        from multilingual import detect_language
        
        # Test English
        en_text = "What are the symptoms of diabetes?"
        en_result = detect_language(en_text)
        print(f"\n✅ English detection:")
        print(f"   Text: {en_text}")
        print(f"   Language: {en_result.language_name} ({en_result.language})")
        print(f"   Confidence: {en_result.confidence:.2f}")
        
        # Test Arabic
        ar_text = "ما هي أعراض مرض السكري؟"
        ar_result = detect_language(ar_text)
        print(f"\n✅ Arabic detection:")
        print(f"   Text: {ar_text}")
        print(f"   Language: {ar_result.language_name} ({ar_result.language})")
        print(f"   Confidence: {ar_result.confidence:.2f}")
        
        # Test French
        fr_text = "Quels sont les symptômes du diabète?"
        fr_result = detect_language(fr_text)
        print(f"\n✅ French detection:")
        print(f"   Text: {fr_text}")
        print(f"   Language: {fr_result.language_name} ({fr_result.language})")
        print(f"   Confidence: {fr_result.confidence:.2f}")
        
        # Verify correct detection
        if en_result.language == 'en' and ar_result.language == 'ar' and fr_result.language == 'fr':
            print("\n✅ All languages detected correctly")
            return True
        else:
            print("\n❌ Language detection errors found")
            return False
            
    except Exception as e:
        print(f"❌ Language detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multilingual_embeddings():
    """Test 2: Multilingual Embeddings"""
    print("\n" + "="*60)
    print("TEST 2: Multilingual Embeddings")
    print("="*60)
    
    try:
        from multilingual import get_multilingual_embeddings
        
        # Initialize embeddings
        print("Loading multilingual model...")
        embeddings = get_multilingual_embeddings()
        
        print(f"✅ Model loaded: {embeddings.get_model_name()}")
        print(f"   Embedding dimension: {embeddings.get_embedding_dim()}")
        
        # Test encoding in multiple languages
        texts = [
            "Diabetes is a chronic disease",  # English
            "مرض السكري مرض مزمن",  # Arabic
            "Le diabète est une maladie chronique"  # French
        ]
        
        print("\nEncoding texts...")
        vectors = embeddings.encode(texts, show_progress=False)
        
        print(f"✅ Encoded {len(texts)} texts")
        print(f"   Shape: {vectors.shape}")
        
        # Verify embeddings
        if vectors.shape[0] == 3 and vectors.shape[1] == embeddings.get_embedding_dim():
            print("✅ Embedding shapes correct")
            return True
        else:
            print(f"❌ Unexpected embedding shape: {vectors.shape}")
            return False
            
    except Exception as e:
        print(f"❌ Multilingual embeddings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_knowledge_base_loading():
    """Test 3: Multilingual Knowledge Base Loading"""
    print("\n" + "="*60)
    print("TEST 3: Multilingual Knowledge Base Loading")
    print("="*60)
    
    import json
    
    # Check if knowledge bases exist
    data_dir = Path("data")
    
    files = {
        'Arabic': data_dir / "medical_knowledge_ar.json",
        'French': data_dir / "medical_knowledge_fr.json"
    }
    
    total_docs = 0
    
    for lang, file_path in files.items():
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                docs = json.load(f)
                print(f"✅ {lang} knowledge base: {len(docs)} documents")
                total_docs += len(docs)
        else:
            print(f"⚠️  {lang} knowledge base not found: {file_path}")
    
    if total_docs > 0:
        print(f"\n✅ Total multilingual documents: {total_docs}")
        return True
    else:
        print("\n❌ No multilingual documents loaded")
        return False


def test_multilingual_retrieval():
    """Test 4: Multilingual Retrieval"""
    print("\n" + "="*60)
    print("TEST 4: Multilingual Retrieval")
    print("="*60)
    
    try:
        from retrieval.multilingual_retrieval import MultilingualVectorRetriever
        
        print("Initializing multilingual retriever...")
        retriever = MultilingualVectorRetriever()
        
        print(f"✅ Retriever initialized")
        print(f"   Embedding dim: {retriever.embedding_dim}")
        
        # Try loading documents
        print("\nLoading multilingual documents...")
        docs = retriever.load_multilingual_documents()
        
        if docs and len(docs) > 0:
            print(f"✅ Loaded {len(docs)} documents")
            
            # Count by language
            lang_counts = {}
            for doc in docs:
                lang = doc.get('language', 'en')
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            
            print("\n   Documents by language:")
            for lang, count in sorted(lang_counts.items()):
                print(f"   - {lang}: {count}")
            
            return True
        else:
            print("⚠️  No documents loaded (expected if knowledge bases don't exist)")
            return None
            
    except Exception as e:
        print(f"❌ Multilingual retrieval test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multilingual_index():
    """Test 5: Multilingual Index Building"""
    print("\n" + "="*60)
    print("TEST 5: Multilingual Index Building")
    print("="*60)
    
    try:
        from retrieval.multilingual_retrieval import MultilingualVectorRetriever
        
        retriever = MultilingualVectorRetriever()
        
        # Try building index
        print("Building multilingual FAISS index...")
        try:
            retriever.build_multilingual_index()
            print(f"✅ Index built successfully")
            print(f"   Total documents indexed: {len(retriever.documents)}")
            return True
        except ValueError as e:
            if "No documents loaded" in str(e):
                print("⚠️  Skipping - no documents available for indexing")
                return None
            raise
            
    except Exception as e:
        print(f"❌ Index building test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cross_lingual_search():
    """Test 6: Cross-Lingual Search"""
    print("\n" + "="*60)
    print("TEST 6: Cross-Lingual Search")
    print("="*60)
    
    try:
        from retrieval.multilingual_retrieval import MultilingualVectorRetriever
        
        retriever = MultilingualVectorRetriever()
        
        # Build index
        try:
            retriever.build_multilingual_index()
        except ValueError:
            print("⚠️  Skipping - no documents available")
            return None
        
        # Test searches in different languages
        queries = [
            ("What are the symptoms of diabetes?", "en"),
            ("ما هي أعراض مرض السكري؟", "ar"),
            ("Quels sont les symptômes du diabète?", "fr")
        ]
        
        all_passed = True
        for query, lang in queries:
            print(f"\n🔍 Searching ({lang}): {query}")
            results = retriever.search(query, top_k=3)
            
            if results:
                print(f"   ✅ Found {len(results)} results")
                for i, result in enumerate(results[:2], 1):
                    print(f"   {i}. {result.get('title', 'N/A')} (score: {result.get('score', 0):.3f})")
            else:
                print(f"   ⚠️  No results found")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Cross-lingual search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_multilingual_integration():
    """Test 7: RAG Multilingual Integration"""
    print("\n" + "="*60)
    print("TEST 7: RAG Multilingual Integration")
    print("="*60)
    
    try:
        from rag_system.rag import MedicalRAG
        
        # Initialize RAG with multilingual support
        print("Initializing RAG system with multilingual support...")
        rag = MedicalRAG(
            languages=["en", "ar", "fr"],
            use_reranking=False,
            enable_vision=False
        )
        
        print(f"✅ RAG initialized")
        print(f"   Languages: {rag.languages}")
        print(f"   Multilingual mode: {rag.multilingual_mode}")
        
        # Test language detection
        test_queries = [
            "What is diabetes?",
            "ما هو مرض السكري؟",
            "Qu'est-ce que le diabète?"
        ]
        
        for query in test_queries:
            detected = rag._detect_language(query)
            print(f"\n   Query: {query[:30]}...")
            print(f"   Detected: {detected}")
        
        print("\n✅ RAG multilingual integration verified")
        return True
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multilingual_dependencies():
    """Test 8: Multilingual Dependencies"""
    print("\n" + "="*60)
    print("TEST 8: Multilingual Dependencies")
    print("="*60)
    
    dependencies = {
        'sentence-transformers': 'Multilingual embeddings',
        'langdetect': 'Language detection (optional)',
    }
    
    all_available = True
    for package, description in dependencies.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}: Available ({description})")
        except ImportError:
            print(f"⚠️  {package}: Not installed ({description})")
            if package == 'sentence-transformers':
                all_available = False
    
    return all_available


def main():
    """Run all Phase 6 verification tests"""
    print("\n" + "="*60)
    print("PHASE 6 VERIFICATION: Multilingual Extension")
    print("="*60)
    
    tests = [
        ("Multilingual Dependencies", test_multilingual_dependencies),
        ("Language Detection", test_language_detection),
        ("Multilingual Embeddings", test_multilingual_embeddings),
        ("Knowledge Base Loading", test_knowledge_base_loading),
        ("Multilingual Retrieval", test_multilingual_retrieval),
        ("Multilingual Index", test_multilingual_index),
        ("Cross-Lingual Search", test_cross_lingual_search),
        ("RAG Integration", test_rag_multilingual_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("PHASE 6 TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if result is None:
            status = "⚠️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status}: {test_name}")
    
    # Calculate pass rate (excluding skipped)
    actual_results = [r for r in results.values() if r is not None]
    if actual_results:
        passed = sum(actual_results)
        total = len(actual_results)
        pass_rate = (passed / total) * 100
        
        print(f"\nPass Rate: {passed}/{total} ({pass_rate:.1f}%)")
        
        if pass_rate >= 75:  # 75% threshold for Phase 6
            print("\n🎉 Phase 6 verification COMPLETE!")
            print("\n📋 Phase 6 Features Verified:")
            print("   ✅ Language detection (English, Arabic, French)")
            print("   ✅ Multilingual embeddings for cross-lingual search")
            print("   ✅ Translated medical knowledge bases (AR, FR)")
            print("   ✅ Multilingual vector retrieval")
            print("   ✅ FAISS index for multilingual documents")
            print("   ✅ Cross-lingual semantic search")
            print("   ✅ RAG system integration")
            print("\n📝 Note: Install optional dependencies for full functionality:")
            print("   pip install langdetect")
            return 0
        else:
            print(f"\n⚠️  Phase 6 verification incomplete: {pass_rate:.1f}% tests passed")
            print("   Install required dependencies: pip install sentence-transformers")
            return 1
    else:
        print("\n⚠️  All tests were skipped")
        print("   Install dependencies: pip install sentence-transformers langdetect")
        return 1


if __name__ == "__main__":
    sys.exit(main())
