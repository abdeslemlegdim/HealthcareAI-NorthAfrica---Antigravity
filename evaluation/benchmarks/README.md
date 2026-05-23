# Evaluation Benchmarks

This directory contains benchmark datasets for evaluating the Healthcare AI system.

## Datasets

### 1. RAG Benchmark (`rag_benchmark_en.json`)

**Purpose**: Evaluate retrieval and generation quality

**Format**:
```json
[
  {
    "question": "What are the symptoms of diabetes?",
    "answer": "Expected comprehensive answer...",
    "relevant_docs": ["doc_id1", "doc_id2"],
    "language": "en"
  }
]
```

**Metrics Evaluated**:
- Retrieval: Recall@K, MRR, Precision@K, NDCG@K, MAP
- Generation: Answer relevance, faithfulness, hallucination rate, completeness

**Current Size**: 5 examples (English only)

**TODO**: Expand to 100+ examples per language

### 2. Multilingual Benchmark (`multilingual_benchmark.json`)

**Purpose**: Evaluate cross-lingual retrieval

**Format**:
```json
[
  {
    "query_en": "What are diabetes symptoms?",
    "query_ar": "ما هي أعراض السكري؟",
    "query_fr": "Quels sont les symptômes du diabète?",
    "relevant_docs": {
      "en": ["doc_id_en"],
      "ar": ["doc_id_ar"],
      "fr": ["doc_id_fr"]
    }
  }
]
```

**Metrics Evaluated**:
- Cross-lingual retrieval (en→ar, ar→fr, etc.)
- Embedding alignment quality
- Per-language performance
- Bias analysis

**Current Size**: 3 examples

**TODO**: Expand to 50+ examples

### 3. Parallel Corpus (`parallel_corpus.json`)

**Purpose**: Evaluate multilingual embedding quality

**Format**:
```json
[
  {
    "en": "Diabetes is a chronic disease...",
    "ar": "السكري مرض مزمن...",
    "fr": "Le diabète est une maladie chronique..."
  }
]
```

**Metrics Evaluated**:
- Cosine similarity between parallel sentences
- Embedding alignment quality
- Semantic preservation across languages

**Current Size**: 5 parallel sentences

**TODO**: Expand to 100+ sentences

### 4. Imaging Test Dataset (`imaging_test_dataset.json`)

**Purpose**: Evaluate medical image classification

**Format**:
```json
[
  {
    "image_path": "data/test_images/pneumonia_001.jpg",
    "true_label": "Pneumonia",
    "bounding_box": [x, y, w, h]  // Optional
  }
]
```

**Metrics Evaluated**:
- Classification: AUC, F1, Precision, Recall
- Sensitivity/Specificity (critical for medical AI)
- Confusion matrix
- Grad-CAM validation

**Current Size**: 0 (needs creation)

**TODO**: Create test dataset from:
- NIH ChestX-ray14 test split
- CheXpert test split
- Or synthetic test images

## Creating Benchmark Datasets

### Step 1: Create RAG Benchmark

```python
import json

# Template
benchmark_data = []
for question, answer, docs in medical_qa_pairs:
    benchmark_data.append({
        "question": question,
        "answer": answer,
        "relevant_docs": docs,
        "language": "en"
    })

# Save
with open("rag_benchmark_en.json", "w") as f:
    json.dump(benchmark_data, f, indent=2)
```

### Step 2: Create Multilingual Benchmark

```python
# Translate questions to all languages
multilingual_data = []
for qa in english_qa:
    multilingual_data.append({
        "query_en": qa['question'],
        "query_ar": translate_to_arabic(qa['question']),
        "query_fr": translate_to_french(qa['question']),
        "relevant_docs": {
            "en": qa['docs_en'],
            "ar": qa['docs_ar'],
            "fr": qa['docs_fr']
        }
    })

with open("multilingual_benchmark.json", "w") as f:
    json.dump(multilingual_data, f, indent=2)
```

### Step 3: Create Imaging Dataset

```python
# Collect test images with labels
imaging_data = []
for img_path, label in test_images:
    imaging_data.append({
        "image_path": img_path,
        "true_label": label,
        "bounding_box": None  # Add if available
    })

with open("imaging_test_dataset.json", "w") as f:
    json.dump(imaging_data, f, indent=2)
```

## Running Evaluations

### RAG Evaluation
```bash
python evaluation/rag_evaluation.py
```

### Multilingual Evaluation
```bash
python evaluation/multilingual_evaluation.py
```

### Imaging Evaluation
```bash
python evaluation/imaging_evaluation.py
```

### Full Evaluation Suite
```bash
python evaluation/run_full_evaluation.py
```

## Benchmark Quality Guidelines

### Minimum Requirements

**RAG Benchmark**:
- ✅ At least 100 Q/A pairs per language
- ✅ Diverse medical topics
- ✅ Multiple difficulty levels (easy, medium, hard)
- ✅ Ground truth answers from medical sources

**Multilingual Benchmark**:
- ✅ At least 50 parallel questions
- ✅ Professional translations (not machine-translated)
- ✅ Coverage of all supported languages

**Imaging Dataset**:
- ✅ At least 100 images per class
- ✅ Balanced class distribution
- ✅ High-quality labels (verified by radiologists)
- ✅ Diverse imaging conditions

## Citation

If you use these benchmarks, please cite:
```bibtex
@dataset{healthcare_ai_north_africa_benchmarks,
  title={Healthcare AI North Africa Evaluation Benchmarks},
  year={2026},
  url={https://github.com/your-repo/HealthcareAI-NorthAfrica}
}
```
