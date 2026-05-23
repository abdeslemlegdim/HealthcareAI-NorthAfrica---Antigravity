"""Test Medical Imaging Classifier with PyTorch"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

import torch
from torchvision import transforms
from PIL import Image
import numpy as np

from src.medical_imaging.classifier import MedicalImageClassifier

def create_synthetic_xray(filename: str):
    """Create a synthetic grayscale X-ray image for testing"""
    # Create a 512x512 grayscale image
    img_array = np.random.randint(30, 220, (512, 512), dtype=np.uint8)
    
    # Add some features to make it look more like an X-ray
    # Add lung fields (brighter areas)
    center_y, center_x = 256, 256
    for y in range(512):
        for x in range(512):
            dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            if dist_from_center < 150:  # Lung field
                img_array[y, x] = min(255, img_array[y, x] + 50)
    
    img = Image.fromarray(img_array, mode='L')
    img.save(filename)
    print(f"✓ Created synthetic X-ray: {filename}")
    return filename

def test_classifier():
    print("="*80)
    print("Testing Medical Image Classifier with PyTorch")
    print("="*80)
    
    try:
        # Create synthetic test image
        test_image_path = "test_xray.png"
        create_synthetic_xray(test_image_path)
        
        # Initialize classifier
        print("\n1. Initializing EfficientNet-B0 classifier...")
        classifier = MedicalImageClassifier(backbone="efficientnet_b0")
        print(f"   ✓ Model: {classifier.backbone}")
        print(f"   ✓ Device: {classifier.device}")
        print(f"   ✓ Number of classes: {classifier.num_classes}")
        print(f"   ✓ Disease classes: {classifier.DISEASES}")
        
        # Test prediction
        print("\n2. Running prediction on synthetic X-ray...")
        predictions = classifier.predict(test_image_path, top_k=5)
        
        print("\n   Predictions:")
        for i, pred in enumerate(predictions, 1):
            disease = pred['disease']
            confidence = pred['confidence']
            percentage = pred.get('percentage', f"{confidence*100:.2f}%")
            print(f"   {i}. {disease:<20} - {percentage} (confidence: {confidence:.4f})")
        
        # Test batch prediction
        print("\n3. Testing batch prediction...")
        batch_results = classifier.batch_predict([test_image_path] * 3)
        print(f"   ✓ Processed {len(batch_results)} images in batch")
        
        # Model info
        print("\n4. Model Information:")
        total_params = sum(p.numel() for p in classifier.model.parameters())
        trainable_params = sum(p.numel() for p in classifier.model.parameters() if p.requires_grad)
        print(f"   ✓ Total parameters: {total_params:,}")
        print(f"   ✓ Trainable parameters: {trainable_params:,}")
        
        # Cleanup
        import os
        os.remove(test_image_path)
        
        print("\n" + "="*80)
        print("✅ Medical Imaging Classifier Test PASSED!")
        print("="*80)
        print("\n📌 Next steps:")
        print("   1. Replace synthetic images with real chest X-rays")
        print("   2. Fine-tune model on medical dataset (ChestX-ray14, COVID-19 datasets)")
        print("   3. Add Grad-CAM visualization")
        print("   4. Implement model evaluation metrics")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_classifier()
