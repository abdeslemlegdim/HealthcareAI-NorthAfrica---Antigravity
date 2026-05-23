# Evaluation Framework

Comprehensive evaluation suite for the Healthcare AI North Africa system.

## Overview

This evaluation framework provides systematic assessment of:
1. **RAG System** - Retrieval and generation quality
2. **Multilingual Capabilities** - Cross-lingual performance and bias
3. **Medical Imaging** - Classification accuracy and explainability

## Quick Start

### Run All Evaluations
```bash
python evaluation/run_full_evaluation.py
```

### Run Individual Evaluations

**RAG Evaluation**:
```bash
python evaluation/rag_evaluation.py
```

**Multilingual Evaluation**:
```bash
python evaluation/multilingual_evaluation.py
```

**Imaging Evaluation**:
```bash
python evaluation/imaging_evaluation.py
```

## Evaluation Modules

### 1. RAG Evaluation (`rag_evaluation.py`)

**Retrieval Metrics**:
- **Recall@K**: Fraction of relevant documents retrieved in top K
  - Formula: |Retrieved ∩ Relevant| / |Relevant|
  - Target: >0.85 for K=5
- **MRR** (Mean Reciprocal Rank): 1 / rank of first relevant document
  - Target: >0.80
- **NDCG@K**: Normalized Discounted Cumulative Gain
  - Considers both relevance and ranking
  - Target: >0.85
- **MAP** (Mean Average Precision): Precision at each relevant document
  - Target: >0.75
- **Precision@K**: Fraction of retrieved docs that are relevant
  - Formula: |Retrieved ∩ Relevant| / K
  - Target: >0.70

**Generation Metrics**:
- **Answer Relevance**: Does answer address the question?
  - Method: Keyword overlap + semantic similarity
  - Target: >0.80
- **Faithfulness**: Are claims supported by sources?
  - Method: Sentence-level grounding check
  - Target: >0.90 (CRITICAL - minimize hallucinations)
- **Hallucination Rate**: 1 - Faithfulness
  - Target: <0.10 (less than 10%)
- **Completeness**: Does answer cover expected information?
  - Method: Overlap with ground truth answer
  - Target: >0.75

**Usage**:
```python
from rag_evaluation import RAGEvaluator

evaluator = RAGEvaluator()
results = evaluator.evaluate_full(
    benchmark_path="evaluation/benchmarks/rag_benchmark_en.json",
    output_path="evaluation/results/rag_results.json"
)

print(f"Overall Score: {results['overall_score']:.4f}")
print(f"Recall@5: {results['retrieval_metrics']['recall@5']:.4f}")
print(f"Faithfulness: {results['generation_metrics']['faithfulness']:.4f}")
```

### 2. Multilingual Evaluation (`multilingual_evaluation.py`)

**Cross-Lingual Retrieval**:
- Tests: Query in language X, retrieve docs in language Y
- Directions tested: en→ar, en→fr, ar→en, ar→fr, fr→en, fr→ar
- Metric: Recall@5 for each direction
- Target: Cross-lingual recall ≥ 80% of monolingual recall

**Embedding Alignment**:
- Tests semantic preservation across languages
- Metrics:
  - Parallel similarity: Cosine sim between parallel sentences
    - Target: >0.85
  - Random similarity: Cosine sim between unrelated sentences
    - Target: <0.30
  - Alignment quality: Parallel sim - Random sim
    - Target: >0.50

**Language Detection**:
- Tests: Automatic language identification
- Metrics: Per-language accuracy
- Target: >90% for all languages

**Bias Analysis**:
- Compares performance across languages
- Metrics:
  - Max performance gap between languages
  - Coefficient of variation
  - Pairwise differences
- Target: Gap <0.10 (less than 10% difference)

**Usage**:
```python
from multilingual_evaluation import MultilingualEvaluator

evaluator = MultilingualEvaluator()
results = evaluator.evaluate_full(
    benchmark_path="evaluation/benchmarks/multilingual_benchmark.json",
    parallel_corpus_path="evaluation/benchmarks/parallel_corpus.json"
)

print(f"Language Detection: {results['language_detection']['overall_accuracy']:.4f}")
print(f"Cross-lingual (en→ar): {results['cross_lingual_retrieval']['en→ar']['mean_recall@5']:.4f}")
```

### 3. Imaging Evaluation (`imaging_evaluation.py`)

**Classification Metrics**:
- **Accuracy**: (TP + TN) / Total
  - Target: >0.85
- **Precision**: TP / (TP + FP)
  - Target: >0.80
- **Recall (Sensitivity)**: TP / (TP + FN)
  - **CRITICAL FOR MEDICAL AI**: Target >0.85
  - High sensitivity = fewer missed diagnoses
- **Specificity**: TN / (TN + FP)
  - Target: >0.80
- **F1 Score**: Harmonic mean of precision and recall
  - Target: >0.82
- **AUC-ROC**: Area under ROC curve
  - Target: >0.90 (excellent), >0.85 (good)

**Confusion Matrix**:
- Shows per-class performance
- Identifies systematic misclassifications

**Explainability Validation**:
- **Grad-CAM Quality**:
  - Checks heatmap focuses on relevant regions (lungs)
  - Validates consistency across images
  - Detects degenerate heatmaps
- **Metrics**:
  - Mean heatmap intensity
  - Heatmap variance
  - Focus score (center region activation)

**Usage**:
```python
from imaging_evaluation import ImagingEvaluator

evaluator = ImagingEvaluator()

# Load test dataset
with open("evaluation/benchmarks/imaging_test_dataset.json") as f:
    test_dataset = json.load(f)

# Run evaluation
results = evaluator.evaluate_on_dataset(test_dataset)

# Check sensitivity (CRITICAL)
for disease, metrics in results['metrics']['per_class'].items():
    print(f"{disease} Sensitivity: {metrics['sensitivity']:.4f}")
```

## Benchmarks

See [benchmarks/README.md](benchmarks/README.md) for details on:
- Benchmark dataset formats
- Creating custom benchmarks
- Dataset quality guidelines

**Current Benchmarks**:
- `rag_benchmark_en.json`: 5 English Q/A pairs (expand to 100+)
- `multilingual_benchmark.json`: 3 cross-lingual examples (expand to 50+)
- `parallel_corpus.json`: 5 parallel sentences (expand to 100+)
- `imaging_test_dataset.json`: Not yet created (needs medical imaging data)

## Results

Evaluation results are saved to `evaluation/results/`:
- `rag_evaluation_YYYYMMDD_HHMMSS.json`
- `multilingual_evaluation_YYYYMMDD_HHMMSS.json`
- `imaging_evaluation_YYYYMMDD_HHMMSS.json`
- `full_evaluation_YYYYMMDD_HHMMSS.json`

## Interpretation Guidelines

### RAG System

| Metric | Excellent | Good | Needs Improvement |
|--------|-----------|------|-------------------|
| Recall@5 | >0.90 | 0.80-0.90 | <0.80 |
| MRR | >0.85 | 0.75-0.85 | <0.75 |
| Faithfulness | >0.95 | 0.85-0.95 | <0.85 |
| Hallucination | <0.05 | 0.05-0.15 | >0.15 |

### Multilingual

| Metric | Excellent | Good | Needs Improvement |
|--------|-----------|------|-------------------|
| Cross-lingual recall | >0.85 | 0.75-0.85 | <0.75 |
| Embedding alignment | >0.90 | 0.80-0.90 | <0.80 |
| Language bias (gap) | <0.05 | 0.05-0.10 | >0.10 |

### Medical Imaging

| Metric | Excellent | Good | Needs Improvement |
|--------|-----------|------|-------------------|
| AUC-ROC | >0.90 | 0.85-0.90 | <0.85 |
| Sensitivity | >0.90 | 0.85-0.90 | <0.85 |
| F1 Score | >0.85 | 0.80-0.85 | <0.80 |

## Critical Validation Checklist

Before claiming production readiness:

### ✅ RAG System
- [ ] Evaluated on ≥100 Q/A pairs per language
- [ ] Hallucination rate <10%
- [ ] Faithfulness >90%
- [ ] Compared to baseline (BioGPT, PubMedBERT)

### ✅ Multilingual
- [ ] Cross-lingual retrieval ≥80% of monolingual
- [ ] Language bias <10%
- [ ] Evaluated on all supported languages (ar, fr, en)
- [ ] Professional translation validation

### ✅ Medical Imaging
- [ ] **Fine-tuned on medical dataset (NOT ImageNet only!)**
- [ ] Sensitivity >85% for all disease classes
- [ ] AUC >0.85
- [ ] Grad-CAM validated by radiologists
- [ ] Tested on external dataset (generalization)

### ✅ Fairness & Bias
- [ ] Demographic parity analysis
- [ ] Language bias <10%
- [ ] Subgroup performance documented
- [ ] Failure cases analyzed

## Publication-Ready Metrics

For academic publication, you MUST include:

1. **Dataset Details**:
   - Size (train/val/test splits)
   - Sources and licenses
   - Quality assurance process

2. **Baseline Comparisons**:
   - Established medical AI systems
   - Statistical significance tests
   - Ablation studies

3. **Error Analysis**:
   - Failure case examples
   - Common error patterns
   - Limitations discussion

4. **Reproducibility**:
   - Hyperparameters
   - Random seeds
   - Hardware specifications
   - Inference time

5. **Clinical Validation** (if applicable):
   - Radiologist agreement (imaging)
   - Medical expert review (RAG answers)
   - Real-world deployment results

## Citation

If you use this evaluation framework:
```bibtex
@misc{healthcare_ai_north_africa_eval,
  title={Evaluation Framework for Multilingual Medical AI Systems},
  author={Healthcare AI North Africa Team},
  year={2026},
  url={https://github.com/your-repo/HealthcareAI-NorthAfrica}
}
```

## References

- **BEIR**: Thakur et al., "BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models" (2021)
- **RAGAS**: "RAG Assessment (RAGAS) Framework"
- **ChestX-ray14**: Wang et al., "ChestX-ray8: Hospital-scale Chest X-ray Database">
- **CheXpert**: Irvin et al., "CheXpert: A Large Chest Radiograph Dataset" (2019)
- **Medical AI Fairness**: Chen et al., "Algorithmic Fairness in Medical AI" (2021)
