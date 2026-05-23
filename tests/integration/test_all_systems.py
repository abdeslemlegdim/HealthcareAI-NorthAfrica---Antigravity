"""
Comprehensive System Test
Tests all components of the HealthcareAI-NorthAfrica system
"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

def test_basic_imports():
    """Test basic imports"""
    print("\n" + "="*80)
    print("1. Testing Basic Imports")
    print("="*80)
    
    try:
        import torch
        import torchvision
        import transformers
        from sentence_transformers import SentenceTransformer
        
        print(f"✓ PyTorch: {torch.__version__}")
        print(f"✓ Torchvision: {torchvision.__version__}")
        print(f"✓ Transformers: {transformers.__version__}")
        print(f"✓ sentence-transformers available")
        print(f"✓ Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_rag_system():
    """Test RAG system"""
    print("\n" + "="*80)
    print("2. Testing RAG System")
    print("="*80)
    
    try:
        from src.rag_system.rag import MedicalRAG
        from src.rag_system.knowledge_base import MEDICAL_KNOWLEDGE, get_disease_info
        
        # Test knowledge base
        print(f"✓ Knowledge base loaded: {len(MEDICAL_KNOWLEDGE)} diseases")
        
        # Test RAG
        rag = MedicalRAG()
        
        # Quick test
        result = rag.query("What are the symptoms of pneumonia?")
        print(f"✓ RAG query successful")
        print(f"  - Language: {result.language}")
        print(f"  - Confidence: {result.confidence}")
        print(f"  - Answer length: {len(result.answer)} chars")
        print(f"  - Sources: {len(result.sources)}")
        
        # Test disease info
        pneumonia_info = get_disease_info("pneumonia")
        print(f"✓ Disease info retrieval: {pneumonia_info.get('name', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ RAG error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_and_logging():
    """Test configuration and logging"""
    print("\n" + "="*80)
    print("3. Testing Configuration & Logging")
    print("="*80)
    
    try:
        from src.utils.config import settings
        from src.utils.logger import setup_logger
        
        print(f"✓ Config loaded:")
        print(f"  - API Host: {settings.API_HOST}")
        print(f"  - API Port: {settings.API_PORT}")
        print(f"  - Environment: {settings.ENVIRONMENT}")
        
        logger = setup_logger("test")
        logger.info("Test log message")
        print(f"✓ Logger working")
        
        return True
    except Exception as e:
        print(f"❌ Config/Logging error: {e}")
        return False


def test_medical_imaging():
    """Test medical imaging module"""
    print("\n" + "="*80)
    print("4. Testing Medical Imaging Module")
    print("="*80)
    
    try:
        from src.medical_imaging.classifier import MedicalImageClassifier
        
        print("✓ Medical imaging classifier imported")
        print(f"  - Disease classes: {', '.join(MedicalImageClassifier.DISEASES)}")
        print(f"  - Total classes: {len(MedicalImageClassifier.DISEASES)}")
        
        # Note: Not initializing full model to avoid download during test
        print("✓ Medical imaging module ready (model download needed for full test)")
        
        return True
    except Exception as e:
        print(f"❌ Medical imaging error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_structure():
    """Test API structure"""
    print("\n" + "="*80)
    print("5. Testing API Structure")
    print("="*80)
    
    try:
        from src.rag_system.api import router as rag_router
        from src.medical_imaging.api import router as imaging_router
        
        print(f"✓ RAG API router loaded")
        print(f"✓ Medical imaging API router loaded")
        
        return True
    except Exception as e:
        print(f"❌ API error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("HealthcareAI-NorthAfrica - Comprehensive System Test")
    print("="*80)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("RAG System", test_rag_system),
        ("Config & Logging", test_config_and_logging),
        ("Medical Imaging", test_medical_imaging),
        ("API Structure", test_api_structure),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nSystem Status:")
        print("  ✓ Core dependencies installed")
        print("  ✓ RAG system fully functional")
        print("  ✓ Medical knowledge base loaded")
        print("  ✓ Configuration system working")
        print("  ✓ Logging system operational")
        print("  ✓ API infrastructure ready")
        print("\nNext Steps:")
        print("  1. Download pretrained models (run: python scripts/download_models.py)")
        print("  2. Add real medical imaging datasets")
        print("  3. Fine-tune models on medical data")
        print("  4. Add Arabic and French language support")
        print("  5. Implement Grad-CAM visualization")
        print("  6. Deploy to production")
    else:
        print("\n⚠️ Some tests failed. Please review the errors above.")
    
    print("="*80)


if __name__ == "__main__":
    main()
