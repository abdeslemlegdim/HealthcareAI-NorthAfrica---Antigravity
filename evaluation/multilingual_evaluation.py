"""
Multilingual RAG Evaluation

Evaluates cross-lingual retrieval and generation:
- Cross-language retrieval (en→ar, ar→fr, etc.)
- Embedding quality across languages
- Language-specific performance
- Bias analysis
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
import sys

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.multilingual import get_multilingual_embeddings, detect_language
from src.retrieval.multilingual_retrieval import get_multilingual_retriever
from src.rag_system.rag import MedicalRAG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultilingualEvaluator:
    """
    Multilingual RAG evaluation framework
    
    Tests:
    - Cross-lingual retrieval (query in lang X, retrieve docs in lang Y)
    - Embedding alignment across languages
    - Per-language performance
    - Language detection accuracy
    - Bias analysis (performance gap between languages)
    """
    
    LANGUAGES = {
        'en': 'English',
        'ar': 'Arabic',
        'fr': 'French'
    }
    
    def __init__(self):
        """Initialize multilingual evaluator"""
        self.embeddings = get_multilingual_embeddings()
        self.retriever = get_multilingual_retriever()
        self.rag = MedicalRAG(languages=["en", "ar", "fr"])
        self.results = defaultdict(dict)
        
        logger.info("Initialized Multilingual Evaluator")
    
    # ==================== CROSS-LINGUAL RETRIEVAL ====================
    
    def evaluate_cross_lingual_retrieval(
        self,
        benchmark_data: List[Dict]
    ) -> Dict:
        """
        Evaluate cross-lingual retrieval
        
        For each query:
        - Retrieve documents in same language
        - Retrieve documents in different languages
        - Compare relevance scores
        
        Expected format:
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
        """
        logger.info("Evaluating cross-lingual retrieval...")
        
        cross_lingual_scores = defaultdict(list)
        
        for example in benchmark_data:
            for source_lang in self.LANGUAGES:
                query_key = f"query_{source_lang}"
                if query_key not in example:
                    continue
                
                query = example[query_key]
                
                # Retrieve docs
                try:
                    results = self.retriever.search(query, top_k=10)
                except Exception as e:
                    logger.warning(f"Retrieval error: {e}")
                    continue
                
                # Group by language
                for target_lang in self.LANGUAGES:
                    relevant_docs = example['relevant_docs'].get(target_lang, [])
                    relevant_set = set(relevant_docs)
                    
                    # Check if any relevant doc was retrieved
                    retrieved_ids = [doc.get('id', '') for doc in results]
                    retrieved_set = set(retrieved_ids[:5])
                    
                    # Calculate recall
                    if relevant_set:
                        recall = len(retrieved_set & relevant_set) / len(relevant_set)
                        cross_lingual_scores[f"{source_lang}→{target_lang}"].append(recall)
        
        # Aggregate results
        results = {}
        for direction, scores in cross_lingual_scores.items():
            if scores:
                results[direction] = {
                    'mean_recall@5': np.mean(scores),
                    'std': np.std(scores),
                    'count': len(scores)
                }
        
        logger.info("Cross-lingual retrieval evaluation complete")
        return results
    
    # ==================== EMBEDDING ALIGNMENT ====================
    
    def evaluate_embedding_alignment(
        self,
        parallel_corpus: List[Dict]
    ) -> Dict:
        """
        Evaluate embedding quality across languages
        
        Tests semantic alignment using parallel sentences:
        - Cosine similarity between parallel pairs (should be HIGH)
        - Cosine similarity between random pairs (should be LOW)
        
        Expected format:
        [
            {
                "en": "Diabetes is a chronic disease",
                "ar": "السكري مرض مزمن",
                "fr": "Le diabète est une maladie chronique"
            }
        ]
        """
        logger.info("Evaluating embedding alignment...")
        
        parallel_similarities = defaultdict(list)
        random_similarities = defaultdict(list)
        
        for example in parallel_corpus:
            # Get embeddings for all languages
            embeddings = {}
            for lang, text in example.items():
                if lang in self.LANGUAGES:
                    emb = self.embeddings.encode_query(text)
                    embeddings[lang] = emb
            
            # Calculate parallel similarities
            for lang1 in embeddings:
                for lang2 in embeddings:
                    if lang1 != lang2:
                        sim = self._cosine_similarity(
                            embeddings[lang1],
                            embeddings[lang2]
                        )
                        parallel_similarities[f"{lang1}-{lang2}"].append(sim)
        
        # Calculate random similarities (shuffle one language)
        if len(parallel_corpus) > 1:
            for i, example1 in enumerate(parallel_corpus):
                # Get embedding for English
                if 'en' in example1:
                    emb1_en = self.embeddings.encode_query(example1['en'])
                    
                    # Compare with random Arabic text
                    example2 = parallel_corpus[(i + 1) % len(parallel_corpus)]
                    if 'ar' in example2:
                        emb2_ar = self.embeddings.encode_query(example2['ar'])
                        sim = self._cosine_similarity(emb1_en, emb2_ar)
                        random_similarities['en-ar'].append(sim)
        
        # Aggregate results
        results = {
            'parallel_similarities': {},
            'random_similarities': {},
            'alignment_quality': {}
        }
        
        for pair, sims in parallel_similarities.items():
            results['parallel_similarities'][pair] = {
                'mean': np.mean(sims),
                'std': np.std(sims),
                'min': np.min(sims),
                'max': np.max(sims)
            }
        
        for pair, sims in random_similarities.items():
            if sims:
                results['random_similarities'][pair] = {
                    'mean': np.mean(sims),
                    'std': np.std(sims)
                }
        
        # Calculate alignment quality (parallel sim - random sim)
        for pair in parallel_similarities:
            if pair in random_similarities:
                parallel_mean = results['parallel_similarities'][pair]['mean']
                random_mean = results['random_similarities'][pair]['mean']
                results['alignment_quality'][pair] = parallel_mean - random_mean
        
        logger.info("Embedding alignment evaluation complete")
        return results
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    # ==================== LANGUAGE DETECTION ====================
    
    def evaluate_language_detection(
        self,
        test_data: List[Dict]
    ) -> Dict:
        """
        Evaluate language detection accuracy
        
        Expected format:
        [
            {
                "text": "What are the symptoms?",
                "true_language": "en"
            }
        ]
        """
        logger.info("Evaluating language detection...")
        
        correct = 0
        total = 0
        per_language = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        for example in test_data:
            text = example['text']
            true_lang = example['true_language']
            
            # Detect language
            result = detect_language(text)
            detected_lang = result.language
            
            # Check correctness
            is_correct = (detected_lang == true_lang)
            if is_correct:
                correct += 1
                per_language[true_lang]['correct'] += 1
            
            total += 1
            per_language[true_lang]['total'] += 1
        
        # Calculate accuracy
        overall_accuracy = correct / total if total > 0 else 0.0
        
        per_language_accuracy = {}
        for lang, counts in per_language.items():
            per_language_accuracy[lang] = (
                counts['correct'] / counts['total']
                if counts['total'] > 0 else 0.0
            )
        
        results = {
            'overall_accuracy': overall_accuracy,
            'per_language_accuracy': per_language_accuracy,
            'total_samples': total
        }
        
        logger.info(f"Language detection accuracy: {overall_accuracy:.4f}")
        return results
    
    # ==================== BIAS ANALYSIS ====================
    
    def evaluate_language_bias(
        self,
        benchmark_by_language: Dict[str, List[Dict]]
    ) -> Dict:
        """
        Analyze performance bias across languages
        
        Args:
            benchmark_by_language: {
                'en': [...benchmark examples...],
                'ar': [...benchmark examples...],
                'fr': [...benchmark examples...]
            }
        
        Returns:
            Performance metrics per language + bias analysis
        """
        logger.info("Evaluating language bias...")
        
        from rag_evaluation import RAGEvaluator
        
        per_language_results = {}
        
        for lang, examples in benchmark_by_language.items():
            logger.info(f"Evaluating {self.LANGUAGES[lang]} ({lang})...")
            
            evaluator = RAGEvaluator(self.rag)
            
            # Evaluate retrieval
            retrieval_metrics = evaluator.evaluate_retrieval(examples)
            
            # Evaluate generation
            generation_metrics = evaluator.evaluate_generation(examples)
            
            per_language_results[lang] = {
                'retrieval': retrieval_metrics,
                'generation': generation_metrics
            }
        
        # Calculate bias metrics
        bias_analysis = self._calculate_bias_metrics(per_language_results)
        
        results = {
            'per_language_performance': per_language_results,
            'bias_analysis': bias_analysis
        }
        
        logger.info("Language bias evaluation complete")
        return results
    
    def _calculate_bias_metrics(self, per_language_results: Dict) -> Dict:
        """
        Calculate bias metrics
        
        Metrics:
        - Max performance gap
        - Coefficient of variation
        - Pairwise differences
        """
        # Collect recall@5 for each language
        recall_scores = {}
        for lang, results in per_language_results.items():
            recall_scores[lang] = results['retrieval'].get('recall@5', 0)
        
        # Collect faithfulness for each language
        faithfulness_scores = {}
        for lang, results in per_language_results.items():
            faithfulness_scores[lang] = results['generation'].get('faithfulness', 0)
        
        # Calculate gaps
        recall_values = list(recall_scores.values())
        faithfulness_values = list(faithfulness_scores.values())
        
        bias_metrics = {
            'retrieval_bias': {
                'max_gap': max(recall_values) - min(recall_values) if recall_values else 0,
                'mean': np.mean(recall_values) if recall_values else 0,
                'std': np.std(recall_values) if recall_values else 0,
                'cv': np.std(recall_values) / np.mean(recall_values) if np.mean(recall_values) > 0 else 0
            },
            'generation_bias': {
                'max_gap': max(faithfulness_values) - min(faithfulness_values) if faithfulness_values else 0,
                'mean': np.mean(faithfulness_values) if faithfulness_values else 0,
                'std': np.std(faithfulness_values) if faithfulness_values else 0,
                'cv': np.std(faithfulness_values) / np.mean(faithfulness_values) if np.mean(faithfulness_values) > 0 else 0
            },
            'pairwise_gaps': {}
        }
        
        # Pairwise comparisons
        languages = list(recall_scores.keys())
        for i, lang1 in enumerate(languages):
            for lang2 in languages[i+1:]:
                gap = abs(recall_scores[lang1] - recall_scores[lang2])
                bias_metrics['pairwise_gaps'][f"{lang1}-{lang2}"] = gap
        
        return bias_metrics
    
    # ==================== FULL EVALUATION ====================
    
    def evaluate_full(
        self,
        benchmark_path: str,
        parallel_corpus_path: str,
        output_path: str = "evaluation/results/multilingual_evaluation_results.json"
    ) -> Dict:
        """
        Run full multilingual evaluation
        
        Args:
            benchmark_path: Path to multilingual benchmark
            parallel_corpus_path: Path to parallel corpus for alignment
            output_path: Path to save results
        """
        logger.info("="*60)
        logger.info("MULTILINGUAL EVALUATION")
        logger.info("="*60)
        
        results = {}
        
        # 1. Cross-lingual retrieval
        if Path(benchmark_path).exists():
            with open(benchmark_path, 'r', encoding='utf-8') as f:
                benchmark_data = json.load(f)
            results['cross_lingual_retrieval'] = self.evaluate_cross_lingual_retrieval(
                benchmark_data
            )
        else:
            logger.warning(f"Benchmark not found: {benchmark_path}")
        
        # 2. Embedding alignment
        if Path(parallel_corpus_path).exists():
            with open(parallel_corpus_path, 'r', encoding='utf-8') as f:
                parallel_corpus = json.load(f)
            results['embedding_alignment'] = self.evaluate_embedding_alignment(
                parallel_corpus
            )
        else:
            logger.warning(f"Parallel corpus not found: {parallel_corpus_path}")
        
        # 3. Language detection (create test data)
        test_data = [
            {"text": "What are the symptoms of diabetes?", "true_language": "en"},
            {"text": "ما هي أعراض مرض السكري؟", "true_language": "ar"},
            {"text": "Quels sont les symptômes du diabète?", "true_language": "fr"},
        ]
        results['language_detection'] = self.evaluate_language_detection(test_data)
        
        # Print summary
        self._print_summary(results)
        
        # Save results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_path}")
        
        return results
    
    def _print_summary(self, results: Dict):
        """Print formatted evaluation summary"""
        print("\n" + "="*60)
        print("MULTILINGUAL EVALUATION SUMMARY")
        print("="*60)
        
        # Cross-lingual retrieval
        if 'cross_lingual_retrieval' in results:
            print("\n🌍 CROSS-LINGUAL RETRIEVAL:")
            for direction, metrics in results['cross_lingual_retrieval'].items():
                print(f"   {direction:8s}: {metrics['mean_recall@5']:.4f} " +
                      f"(n={metrics['count']})")
        
        # Embedding alignment
        if 'embedding_alignment' in results:
            print("\n🔗 EMBEDDING ALIGNMENT:")
            parallel_sims = results['embedding_alignment']['parallel_similarities']
            for pair, metrics in parallel_sims.items():
                print(f"   {pair:8s}: {metrics['mean']:.4f} ± {metrics['std']:.4f}")
        
        # Language detection
        if 'language_detection' in results:
            print("\n🔍 LANGUAGE DETECTION:")
            print(f"   Overall Accuracy: {results['language_detection']['overall_accuracy']:.4f}")
            for lang, acc in results['language_detection']['per_language_accuracy'].items():
                print(f"   {self.LANGUAGES[lang]:10s}: {acc:.4f}")
        
        print("="*60)


def main():
    """Run multilingual evaluation"""
    evaluator = MultilingualEvaluator()
    
    # Run evaluation
    results = evaluator.evaluate_full(
        benchmark_path="evaluation/benchmarks/multilingual_benchmark.json",
        parallel_corpus_path="evaluation/benchmarks/parallel_corpus.json"
    )


if __name__ == "__main__":
    main()
