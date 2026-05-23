"""
Quick demo script to test the Healthcare AI Assistant
Works with minimal dependencies - no heavy ML packages required
"""
import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("🏥 Healthcare AI Assistant - Quick Demo")
print("=" * 60)

# Test 1: Basic imports
print("\n1️⃣ Testing basic imports...")
try:
    from src.utils.config import settings
    from src.utils.logger import logger
    print("   ✅ Configuration and logging imported")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: RAG System (lightweight)
print("\n2️⃣ Testing RAG System...")
try:
    from src.rag_system.rag import MedicalRAG
    
    rag = MedicalRAG(languages=["ar", "fr", "en"])
    
    # Test queries
    queries = [
        ("What are pneumonia symptoms?", "en"),
        ("ما هي أعراض الالتهاب الرئوي؟", "ar"),
        ("Comment traiter le COVID-19?", "fr"),
    ]
    
    for question, expected_lang in queries:
        result = rag.query(question)
        print(f"\n   Question ({expected_lang}): {question}")
        print(f"   Answer: {result.answer[:100]}...")
        print(f"   Language: {result.language}")
        print(f"   Confidence: {result.confidence:.2%}")
    
    print("\n   ✅ RAG System working!")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check if PyTorch is available
print("\n3️⃣ Checking ML dependencies...")
try:
    import torch
    print(f"   ✅ PyTorch {torch.__version__} installed")
    print(f"   Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    
    # Try to load classifier
    try:
        from src.medical_imaging.classifier import MedicalImageClassifier
        classifier = MedicalImageClassifier(backbone="efficientnet_b0", device="cpu")
        print(f"   ✅ Medical Imaging classifier loaded")
        print(f"   Supported diseases: {len(classifier.DISEASES)}")
    except Exception as e:
        print(f"   ⚠️ Classifier error: {e}")
        
except ImportError:
    print("   ⚠️ PyTorch not installed yet - medical imaging will be limited")

# Test 4: API availability
print("\n4️⃣ Testing API endpoints...")
print("   Start the server with: python main.py")
print("   Then visit: http://localhost:8000/docs")
print("\n   Available endpoints:")
print("   - POST /api/v1/imaging/classify - Classify X-ray images")
print("   - POST /api/v1/rag/query - Query medical knowledge")
print("   - GET /api/v1/rag/examples - Get example queries")

# Summary
print("\n" + "=" * 60)
print("✅ Demo complete!")
print("=" * 60)
print("\n📝 Next steps:")
print("   1. Run: python main.py")
print("   2. Open: http://localhost:8000/docs")
print("   3. Try the /api/v1/rag/query endpoint")
print("   4. Upload an X-ray to /api/v1/imaging/classify")
print("\n")
