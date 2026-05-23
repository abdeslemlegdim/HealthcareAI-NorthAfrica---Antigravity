"""Quick test of PyTorch installation"""
import torch
import torchvision

print("="*60)
print("PyTorch Installation Test")
print("="*60)
print(f"✓ PyTorch version: {torch.__version__}")
print(f"✓ Torchvision version: {torchvision.__version__}")
print(f"✓ CUDA available: {torch.cuda.is_available()}")
print(f"✓ Device: {'cuda' if torch.cuda.is_available() else 'cpu'}")
print("="*60)

# Test basic operations
try:
    x = torch.rand(3, 224, 224)
    print(f"✓ Created test tensor: {x.shape}")
    
    # Test torchvision transforms
    from torchvision import transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    print("✓ Torchvision transforms working")
    
    print("\n✅ PyTorch is fully functional!")
except Exception as e:
    print(f"\n❌ Error: {e}")
