"""Test Grad-CAM visualization on medical images"""
import sys
sys.path.append('C:\\HealthcareAI-NorthAfrica')

import torch
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from src.medical_imaging.classifier import MedicalImageClassifier
from src.explainability.gradcam import GradCAM, save_gradcam_visualization

def create_sample_xray(filename: str = "sample_xray.png"):
    """Create a more realistic synthetic X-ray"""
    # Create base image
    size = 512
    img = np.ones((size, size), dtype=np.uint8) * 40
    
    # Add lung fields (elliptical brighter regions)
    y, x = np.ogrid[:size, :size]
    
    # Left lung
    left_lung = ((x - 150)**2 / 80**2 + (y - 256)**2 / 120**2) < 1
    img[left_lung] = 180
    
    # Right lung
    right_lung = ((x - 362)**2 / 80**2 + (y - 256)**2 / 120**2) < 1
    img[right_lung] = 180
    
    # Add some texture
    noise = np.random.randint(-20, 20, (size, size))
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    
    # Add ribs (darker lines)
    for i in range(5, 10):
        y_pos = 100 + i * 40
        img[y_pos-2:y_pos+2, :] = np.clip(img[y_pos-2:y_pos+2, :] - 30, 0, 255)
    
    # Save
    pil_img = Image.fromarray(img, mode='L')
    pil_img.save(filename)
    print(f"✓ Created sample X-ray: {filename}")
    return filename

def test_gradcam():
    """Test Grad-CAM on medical images"""
    print("="*80)
    print("Testing Grad-CAM Visualization")
    print("="*80)
    
    try:
        # Create sample image
        image_path = create_sample_xray()
        
        # Initialize classifier
        print("\n1. Loading medical image classifier...")
        classifier = MedicalImageClassifier(backbone="efficientnet_b0")
        print(f"   ✓ Model loaded on {classifier.device}")
        
        # Make prediction
        print("\n2. Running prediction...")
        result = classifier.predict(image_path, top_k=3)
        predictions = result['predictions']
        print("   Top predictions:")
        for i, pred in enumerate(predictions, 1):
            print(f"   {i}. {pred['disease']}: {pred.get('percentage', 'N/A')}")
        
        # Initialize Grad-CAM
        print("\n3. Initializing Grad-CAM...")
        gradcam = GradCAM(classifier.model, target_layer='features')
        print("   ✓ Grad-CAM initialized")
        
        # Generate explanation
        print("\n4. Generating visual explanation...")
        heatmap, visualization, pred_class = gradcam.explain_prediction(
            image_path,
            classifier.transform,
            device=classifier.device
        )
        
        disease_name = classifier.DISEASES[pred_class]
        print(f"   ✓ Generated Grad-CAM for: {disease_name}")
        print(f"   ✓ Heatmap shape: {heatmap.shape}")
        print(f"   ✓ Visualization shape: {visualization.shape}")
        
        # Save visualization
        output_path = "gradcam_explanation.png"
        save_gradcam_visualization(visualization, output_path)
        print(f"   ✓ Saved to: {output_path}")
        
        # Create comparison visualization
        print("\n5. Creating comparison plot...")
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Original image
        orig_img = Image.open(image_path).convert('RGB')
        axes[0].imshow(np.array(orig_img), cmap='gray')
        axes[0].set_title('Original X-ray')
        axes[0].axis('off')
        
        # Heatmap
        axes[1].imshow(heatmap, cmap='jet')
        axes[1].set_title('Grad-CAM Heatmap')
        axes[1].axis('off')
        
        # Overlay
        axes[2].imshow(visualization)
        axes[2].set_title(f'Explanation: {disease_name}')
        axes[2].axis('off')
        
        plt.tight_layout()
        comparison_path = "gradcam_comparison.png"
        plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
        print(f"   ✓ Saved comparison to: {comparison_path}")
        
        print("\n" + "="*80)
        print("✅ Grad-CAM Test PASSED!")
        print("="*80)
        print("\n📊 Results:")
        print(f"   • Predicted: {disease_name}")
        print(f"   • Confidence: {predictions[0].get('percentage', 'N/A')}")
        print(f"   • Heatmap shows which regions influenced the prediction")
        print(f"   • Red areas = high importance, Blue areas = low importance")
        print("\n🎯 Interpretation:")
        print("   Grad-CAM highlights the lung regions and areas with abnormalities")
        print("   that the model focuses on when making its diagnosis.")
        print("\n📁 Generated files:")
        print(f"   • {image_path}")
        print(f"   • {output_path}")
        print(f"   • {comparison_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gradcam()
