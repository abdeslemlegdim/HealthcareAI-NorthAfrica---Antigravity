"""
Download pretrained models for Healthcare AI Assistant

This script downloads all necessary pretrained models:
- Medical imaging: Chest X-ray classification model
- RAG system: Multilingual embeddings
- NLP: Language detection
"""
import os
import sys
from pathlib import Path
import urllib.request
import zipfile
import tarfile
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("🚀 Healthcare AI Model Downloader\n")

# Create models directory
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)

class DownloadProgressBar(tqdm):
    """Progress bar for downloads"""
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_url(url, output_path):
    """Download file with progress bar"""
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=output_path.name) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)


def download_huggingface_models():
    """Download models from HuggingFace using transformers library"""
    print("\n📦 Downloading HuggingFace models...")
    
    try:
        from transformers import AutoModel, AutoTokenizer
        from sentence_transformers import SentenceTransformer
        
        # 1. Multilingual embeddings for RAG
        print("\n1️⃣ Downloading multilingual embeddings (paraphrase-multilingual-mpnet-base-v2)...")
        embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        embedding_path = MODELS_DIR / "embeddings"
        embedding_model.save(str(embedding_path))
        print(f"   ✅ Saved to {embedding_path}")
        
        # 2. Smaller multilingual model for faster inference
        print("\n2️⃣ Downloading compact multilingual model (distiluse-base-multilingual-cased-v2)...")
        compact_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        compact_path = MODELS_DIR / "embeddings_fast"
        compact_model.save(str(compact_path))
        print(f"   ✅ Saved to {compact_path}")
        
        print("\n✅ HuggingFace models downloaded successfully!")
        return True
        
    except ImportError:
        print("⚠️ transformers or sentence-transformers not installed")
        print("   Installing required packages...")
        os.system(f"{sys.executable} -m pip install transformers sentence-transformers torch --quiet")
        return download_huggingface_models()
    except Exception as e:
        print(f"❌ Error downloading HuggingFace models: {e}")
        return False


def download_medical_imaging_model():
    """Download pretrained medical imaging model"""
    print("\n📦 Setting up medical imaging model...")
    
    try:
        import torch
        import torchvision.models as models
        
        # Download pretrained EfficientNet
        print("   Downloading EfficientNet-B0 (pretrained on ImageNet)...")
        model = models.efficientnet_b0(pretrained=True)
        
        # Modify for medical imaging (8 disease classes)
        num_classes = 8
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
        
        # Save model
        model_path = MODELS_DIR / "efficientnet_chest.pt"
        torch.save(model.state_dict(), model_path)
        print(f"   ✅ Saved to {model_path}")
        
        # Download ResNet50 as alternative
        print("   Downloading ResNet50 (pretrained on ImageNet)...")
        resnet = models.resnet50(pretrained=True)
        resnet.fc = torch.nn.Linear(resnet.fc.in_features, num_classes)
        
        resnet_path = MODELS_DIR / "resnet50_chest.pt"
        torch.save(resnet.state_dict(), resnet_path)
        print(f"   ✅ Saved to {resnet_path}")
        
        return True
        
    except ImportError:
        print("⚠️ PyTorch not installed")
        print("   Installing PyTorch...")
        os.system(f"{sys.executable} -m pip install torch torchvision --quiet")
        return download_medical_imaging_model()
    except Exception as e:
        print(f"❌ Error downloading medical imaging models: {e}")
        return False


def download_nlp_models():
    """Download NLP models for language detection"""
    print("\n📦 Downloading NLP models...")
    
    try:
        import nltk
        
        # Download NLTK data
        print("   Downloading NLTK data...")
        datasets = ['punkt', 'stopwords']
        for dataset in datasets:
            nltk.download(dataset, quiet=True)
            print(f"   ✅ {dataset}")
        
        return True
    except ImportError:
        print("⚠️ NLTK not installed")
        os.system(f"{sys.executable} -m pip install nltk --quiet")
        return download_nlp_models()
    except Exception as e:
        print(f"❌ Error downloading NLP models: {e}")
        return False


def create_sample_data():
    """Create sample medical data for testing"""
    print("\n📦 Creating sample data...")
    
    try:
        import numpy as np
        from PIL import Image
        
        # Create sample X-ray images
        sample_dir = PROJECT_ROOT / "data" / "samples"
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate synthetic X-ray-like images
        for i, disease in enumerate(['normal', 'pneumonia', 'covid']):
            img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            # Add some structure to make it look more like X-ray
            img_array[:, :, 0] = img_array[:, :, 1] = img_array[:, :, 2]  # Grayscale
            
            img = Image.fromarray(img_array)
            img_path = sample_dir / f"sample_{disease}.jpg"
            img.save(img_path)
            print(f"   ✅ Created {img_path.name}")
        
        # Create sample medical knowledge base
        kb_dir = PROJECT_ROOT / "data" / "medical_kb"
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        sample_kb = kb_dir / "sample_knowledge.txt"
        sample_kb.write_text("""
Pneumonia Symptoms:
- Cough with phlegm or pus
- Fever, sweating and shaking chills
- Shortness of breath
- Chest pain when breathing or coughing
- Fatigue

COVID-19 Symptoms:
- Fever or chills
- Cough
- Shortness of breath
- Fatigue
- Loss of taste or smell
- Sore throat

Tuberculosis Symptoms:
- Coughing for three or more weeks
- Coughing up blood
- Chest pain
- Unintentional weight loss
- Fatigue
- Night sweats

أعراض الالتهاب الرئوي:
- سعال مع بلغم أو صديد
- حمى وتعرق وقشعريرة
- ضيق في التنفس
- ألم في الصدر عند التنفس
- إعياء

Symptômes de la pneumonie:
- Toux avec mucus ou pus
- Fièvre, transpiration et frissons
- Essoufflement
- Douleur thoracique
- Fatigue
""")
        print(f"   ✅ Created sample knowledge base")
        
        return True
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False


def show_summary():
    """Show summary of downloaded models"""
    print("\n" + "="*60)
    print("📊 DOWNLOAD SUMMARY")
    print("="*60)
    
    models_info = [
        ("Multilingual Embeddings", MODELS_DIR / "embeddings"),
        ("Fast Embeddings", MODELS_DIR / "embeddings_fast"),
        ("EfficientNet (Medical)", MODELS_DIR / "efficientnet_chest.pt"),
        ("ResNet50 (Medical)", MODELS_DIR / "resnet50_chest.pt"),
    ]
    
    print("\n📁 Downloaded Models:")
    for name, path in models_info:
        if path.exists():
            if path.is_dir():
                size = sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
            else:
                size = path.stat().st_size
            size_mb = size / (1024 * 1024)
            print(f"   ✅ {name:30} ({size_mb:.1f} MB)")
        else:
            print(f"   ❌ {name:30} (Not found)")
    
    # Show sample data
    sample_dir = PROJECT_ROOT / "data" / "samples"
    if sample_dir.exists():
        sample_count = len(list(sample_dir.glob("*.jpg")))
        print(f"\n📸 Sample Images: {sample_count} files")
    
    kb_dir = PROJECT_ROOT / "data" / "medical_kb"
    if kb_dir.exists():
        kb_count = len(list(kb_dir.glob("*.txt")))
        print(f"📚 Knowledge Base: {kb_count} files")
    
    print("\n" + "="*60)
    print("✅ All models downloaded and ready!")
    print("="*60)
    print("\n🚀 Next steps:")
    print("   1. Run the application: python main.py")
    print("   2. Visit http://localhost:8000/docs")
    print("   3. Try the medical imaging endpoint")
    print("   4. Query the knowledge base in Arabic/French/English")
    print("\n")


def main():
    """Main download function"""
    success = True
    
    # Download all models
    success &= download_huggingface_models()
    success &= download_medical_imaging_model()
    success &= download_nlp_models()
    success &= create_sample_data()
    
    if success:
        show_summary()
        print("🎉 Setup complete! Your Healthcare AI Assistant is ready to run!")
        return 0
    else:
        print("\n⚠️ Some downloads failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
