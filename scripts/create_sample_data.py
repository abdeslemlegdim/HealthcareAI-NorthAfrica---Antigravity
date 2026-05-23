"""
Create sample medical data for testing
Generates synthetic X-ray images and test cases
"""
import os
from pathlib import Path


def create_sample_xray_images():
    """Create sample X-ray image placeholders"""
    # Create data directories
    base_dir = Path(__file__).parent.parent / "data"
    xray_dir = base_dir / "xray_images" / "samples"
    xray_dir.mkdir(parents=True, exist_ok=True)
    
    # Disease categories
    diseases = [
        "normal",
        "pneumonia",
        "covid19",
        "tuberculosis",
        "atelectasis",
        "cardiomegaly",
        "effusion",
        "infiltration"
    ]
    
    # Create README explaining sample data
    readme_content = """# Sample X-ray Images

This directory contains sample chest X-ray images for testing the medical imaging classifier.

## Disease Categories:
1. **Normal**: Healthy chest X-rays with no abnormalities
2. **Pneumonia**: Bacterial or viral lung infection
3. **COVID-19**: SARS-CoV-2 infection patterns
4. **Tuberculosis**: TB infection patterns
5. **Atelectasis**: Partial lung collapse
6. **Cardiomegaly**: Enlarged heart
7. **Effusion**: Fluid accumulation in pleural space
8. **Infiltration**: Abnormal substances in lung tissue

## Usage:
```python
from src.medical_imaging.classifier import MedicalImageClassifier

classifier = MedicalImageClassifier()
predictions = classifier.predict("data/xray_images/samples/pneumonia_1.jpg")
print(predictions)
```

## Notes:
- Images should be chest X-rays (PA or lateral view)
- Supported formats: JPG, PNG, DICOM
- Recommended resolution: 512x512 or higher
- Images are automatically resized to 224x224 for classification

## Real Data Sources:
For real medical imaging datasets, see:
- NIH ChestX-ray14: https://nihcc.app.box.com/v/ChestXray-NIHCC
- COVID-19 Image Data Collection: https://github.com/ieee8023/covid-chestxray-dataset
- RSNA Pneumonia Detection: https://www.kaggle.com/c/rsna-pneumonia-detection-challenge
"""
    
    with open(xray_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    # Create placeholder files for each disease
    for disease in diseases:
        placeholder_file = xray_dir / f"{disease}_sample.txt"
        with open(placeholder_file, "w") as f:
            f.write(f"Placeholder for {disease.upper()} X-ray image\n")
            f.write(f"Replace this with actual {disease} chest X-ray images\n")
            f.write(f"Supported formats: .jpg, .png, .dcm\n")
    
    print(f"✓ Created sample data structure in {xray_dir}")
    print(f"✓ Created placeholders for {len(diseases)} disease categories")
    return xray_dir


def create_test_queries():
    """Create test queries for RAG system"""
    base_dir = Path(__file__).parent.parent / "data"
    test_dir = base_dir / "test_cases"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_queries = {
        "english": [
            "What are the symptoms of pneumonia?",
            "How is COVID-19 diagnosed?",
            "What causes tuberculosis?",
            "What is the treatment for pleural effusion?",
            "How can I prevent respiratory infections?",
            "What are the risk factors for cardiomegaly?",
            "What does atelectasis mean?",
            "How long does pneumonia treatment take?",
            "What are the complications of COVID-19?",
            "Is tuberculosis contagious?",
            "What is a normal chest X-ray finding?",
            "When should I see a doctor for a cough?",
            "What are the signs of lung infection?",
            "How is pulmonary infiltrate treated?",
            "What lifestyle changes help prevent heart disease?"
        ],
        "medical_terms": [
            "Define consolidation in chest X-ray",
            "Explain ground-glass opacity",
            "What is cardiothoracic ratio?",
            "Describe cavitation in tuberculosis",
            "What are air bronchograms?",
            "Explain pleural thickening",
            "What is bilateral infiltrate?",
            "Define interstitial markings",
            "What causes pleural effusion blunting?",
            "Explain lobar consolidation"
        ],
        "differential_diagnosis": [
            "Difference between pneumonia and COVID-19 on X-ray",
            "How to distinguish TB from pneumonia?",
            "Normal vs abnormal chest X-ray features",
            "Bacterial vs viral pneumonia symptoms",
            "Cardiomegaly vs pleural effusion appearance"
        ]
    }
    
    # Save test queries
    import json
    with open(test_dir / "test_queries_en.json", "w") as f:
        json.dump(test_queries, f, indent=2)
    
    print(f"✓ Created {sum(len(v) for v in test_queries.values())} test queries")
    print(f"✓ Saved to {test_dir / 'test_queries_en.json'}")
    
    return test_queries


def create_evaluation_dataset():
    """Create evaluation dataset structure"""
    base_dir = Path(__file__).parent.parent / "data"
    eval_dir = base_dir / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    # Create ground truth labels
    ground_truth = {
        "rag_qa_pairs": [
            {
                "question": "What are the main symptoms of pneumonia?",
                "expected_keywords": ["cough", "fever", "chest pain", "shortness of breath"],
                "category": "symptoms"
            },
            {
                "question": "How is COVID-19 transmitted?",
                "expected_keywords": ["respiratory droplets", "airborne", "close contact"],
                "category": "transmission"
            },
            {
                "question": "What diagnostic tests are used for tuberculosis?",
                "expected_keywords": ["skin test", "chest X-ray", "sputum", "culture"],
                "category": "diagnosis"
            }
        ],
        "image_labels": {
            "normal": ["normal_1.jpg", "normal_2.jpg"],
            "pneumonia": ["pneumonia_1.jpg", "pneumonia_2.jpg"],
            "covid19": ["covid_1.jpg", "covid_2.jpg"]
        }
    }
    
    import json
    with open(eval_dir / "ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"✓ Created evaluation dataset structure")
    return eval_dir


def main():
    """Create all sample data"""
    print("Creating sample data for HealthcareAI-NorthAfrica...")
    print("=" * 60)
    
    # Create directories and sample files
    xray_dir = create_sample_xray_images()
    test_queries = create_test_queries()
    eval_dir = create_evaluation_dataset()
    
    print("=" * 60)
    print("Sample data creation complete!")
    print("\nNext steps:")
    print("1. Download real X-ray images from public datasets")
    print("2. Place images in:", xray_dir)
    print("3. Run: python scripts/download_models.py")
    print("4. Test classifier: python demo.py")


if __name__ == "__main__":
    main()
