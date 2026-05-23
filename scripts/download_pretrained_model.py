"""
Download Pretrained Medical Imaging Model

CLI script to download and cache pretrained models for chest X-ray classification.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.medical_imaging.model_downloader import ModelDownloader
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Main entry point for model download script."""
    parser = argparse.ArgumentParser(
        description="Download pretrained medical imaging model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download EfficientNet-B0 (default)
  python scripts/download_pretrained_model.py
  
  # Force re-download
  python scripts/download_pretrained_model.py --force
  
  # Specify number of classes
  python scripts/download_pretrained_model.py --num-classes 14
  
  # List available models
  python scripts/download_pretrained_model.py --list
        """
    )
    
    parser.add_argument(
        "--model-name",
        type=str,
        default="efficientnet_b0",
        choices=["efficientnet_b0"],
        help="Model architecture to download (default: efficientnet_b0)"
    )
    
    parser.add_argument(
        "--num-classes",
        type=int,
        default=33,
        help="Number of disease classes (default: 33)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if model exists"
    )
    
    parser.add_argument(
        "--models-dir",
        type=str,
        default="models",
        help="Directory to save models (default: models)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available models and exit"
    )
    
    parser.add_argument(
        "--info",
        type=str,
        metavar="MODEL_PATH",
        help="Show information about a specific model"
    )
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = ModelDownloader(models_dir=args.models_dir)
    
    # List models
    if args.list:
        print("\n📦 Available Models:")
        print("=" * 60)
        models = downloader.list_available_models()
        if models:
            for model_path in models:
                info = downloader.get_model_info(Path(model_path))
                print(f"\n  {Path(model_path).name}")
                print(f"    Size: {info.get('size_mb', 'N/A')} MB")
                print(f"    Parameters: {info.get('num_parameters_millions', 'N/A')}M")
        else:
            print("  No models found.")
        print()
        return 0
    
    # Show model info
    if args.info:
        model_path = Path(args.info)
        if not model_path.exists():
            print(f"❌ Model not found: {model_path}")
            return 1
        
        print(f"\n📊 Model Information:")
        print("=" * 60)
        info = downloader.get_model_info(model_path)
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
        return 0
    
    # Download model
    try:
        print(f"\n🚀 Downloading {args.model_name}...")
        print("=" * 60)
        print(f"  Model: {args.model_name}")
        print(f"  Classes: {args.num_classes}")
        print(f"  Force: {args.force}")
        print(f"  Output: {args.models_dir}")
        print()
        
        model_path, model = downloader.download_efficientnet_pretrained(
            num_classes=args.num_classes,
            force=args.force
        )
        
        # Show model info
        print("\n✅ Download Complete!")
        print("=" * 60)
        info = downloader.get_model_info(model_path)
        print(f"  Path: {info['path']}")
        print(f"  Size: {info['size_mb']} MB")
        print(f"  Parameters: {info['num_parameters_millions']}M")
        print()
        
        # Test model
        print("🧪 Testing model...")
        import torch
        test_input = torch.randn(1, 3, 224, 224)
        model.eval()
        with torch.no_grad():
            output = model(test_input)
        print(f"  Input shape: {test_input.shape}")
        print(f"  Output shape: {output.shape}")
        print(f"  Output classes: {output.shape[1]}")
        print()
        
        print("✅ Model is ready to use!")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        logger.error(f"Model download failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
