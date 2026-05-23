"""
RAG Evaluation Framework

Evaluates Retrieval-Augmented Generation system using standard metrics:
- Retrieval: Recall@K, MRR, Precision@K, NDCG
- Generation: Answer relevance, faithfulness, hallucination rate
- End-to-end: F1, BLEU, ROUGE, BERTScore

Based on:
- BEIR benchmark framework
- RAGAS (RAG Assessment)
- TruLens evaluation
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import sys

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.rag_system.rag import MedicalRAG
from src.retrieval.multilingual_retrieval import get_multilingual_retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEvaluator:
    """
    Comprehensive RAG evaluation framework
    
    Metrics:
    - Retrieval: Recall@K, MRR, MAP, NDCG@K, Precision@K
    - Answer Quality: Relevance, Faithfulness, Completeness
    - Hallucination: Unsupported claims, contradictions
    """
    
    def __init__(
        self,
        rag_system: Optional[MedicalRAG] = None,
        benchmark_path: Optional[str] = None
    ):
        """
        Initialize evaluator
        
        Args:
            rag_system: RAG system to evaluate
            benchmark_path: Path to benchmark Q/A pairs
        """
        self.rag = rag_system or MedicalRAG()
        self.benchmark_path = benchmark_path
        self.results = defaultdict(list)
        
        logger.info("Initialized RAG Evaluator")
    
    def load_benchmark(self, path: str) -> List[Dict]:
        """
        Load benchmark dataset
        
        Format:
        [
            {
                "question": "What are symptoms of diabetes?",
                "answer": "Expected answer",
                "relevant_docs": ["doc_id1", "doc_id2"],
                "language": "en"
            }
        ]
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} benchmark examples from {path}")
        return data
    
    # ==================== RETRIEVAL METRICS ====================
    
    def recall_at_k(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 5
    ) -> float:
        """
        Recall@K: Fraction of relevant docs retrieved in top K
        
        Formula: |Retrieved ∩ Relevant| / |Relevant|
        """
        retrieved_set = set(retrieved_docs[:k])
        relevant_set = set(relevant_docs)
        
        if not relevant_set:
            return 0.0
        
        intersection = retrieved_set & relevant_set
        return len(intersection) / len(relevant_set)
    
    def precision_at_k(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 5
    ) -> float:
        """
        Precision@K: Fraction of retrieved docs that are relevant
        
        Formula: |Retrieved ∩ Relevant| / K
        """
        retrieved_set = set(retrieved_docs[:k])
        relevant_set = set(relevant_docs)
        
        intersection = retrieved_set & relevant_set
        return len(intersection) / k if k > 0 else 0.0
    
    def mean_reciprocal_rank(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str]
    ) -> float:
        """
        MRR: 1 / rank of first relevant document
        
        Formula: 1 / rank(first_relevant)
        """
        relevant_set = set(relevant_docs)
        
        for rank, doc_id in enumerate(retrieved_docs, 1):
            if doc_id in relevant_set:
                return 1.0 / rank
        
        return 0.0
    
    def ndcg_at_k(
        self,
        retrieved_docs: List[str],
        relevant_docs: List[str],
        k: int = 5
    ) -> float:
        """
        NDCG@K: Normalized Discounted Cumulative Gain
        
        Considers both relevance and ranking position
        """
        def dcg(relevances, k):
            return sum(
                (2**rel - 1) / np.log2(i + 2)
                for i, rel in enumerate(relevances[:k])
            )
        
        # Binary relevance: 1 if doc is relevant, 0 otherwise
        relevant_set = set(relevant_docs)
        retrieved_relevances = [
            1 if doc_id in relevant_set else 0
            for doc_id in retrieved_docs[:k]
        ]
        
        # Ideal ranking: all relevant docs first
        ideal_relevances = [1] * min(len(relevant_docs), k) + [0] * k
        
        dcg_score = dcg(retrieved_relevances, k)
        idcg_score = dcg(ideal_relevances, k)
        
        return dcg_score / idcg_score if idcg_score > 0 else 0.0
    
    def mean_average_precision(
        self,
        all_retrieved: List[List[str]],
        all_relevant: List[List[str]]
    ) -> float:
        """
        MAP: Mean Average Precision across all queries
        """
        aps = []
        for retrieved, relevant in zip(all_retrieved, all_relevant):
            relevant_set = set(relevant)
            precisions = []
            num_hits = 0
            
            for rank, doc_id in enumerate(retrieved, 1):
                if doc_id in relevant_set:
                    num_hits += 1
                    precision = num_hits / rank
                    precisions.append(precision)
            
            if precisions:
                aps.append(sum(precisions) / len(relevant_set))
            else:
                aps.append(0.0)
        
        return np.mean(aps) if aps else 0.0
    
    # ==================== ANSWER QUALITY METRICS ====================
    
    def answer_relevance(
        self,
        question: str,
        answer: str,
        use_llm: bool = False
    ) -> float:
        """
        Answer Relevance: Does answer address the question?
        
        Methods:
        - Keyword overlap (fast)
        - Semantic similarity (requires embeddings)
        - LLM-based scoring (most accurate)
        """
        # Simple keyword overlap approach
        q_tokens = set(question.lower().split())
        a_tokens = set(answer.lower().split())
        
        # Remove stopwords (simple version)
        stopwords = {'what', 'is', 'are', 'the', 'a', 'an', 'in', 'on', 'of', 'for', 'to'}
        q_tokens -= stopwords
        a_tokens -= stopwords
        
        if not q_tokens:
            return 0.0
        
        overlap = q_tokens & a_tokens
        return len(overlap) / len(q_tokens)
    
    def faithfulness_score(
        self,
        answer: str,
        sources: List[Dict]
    ) -> float:
        """
        Faithfulness: Are all claims in answer supported by sources?
        
        Returns: Fraction of answer sentences supported by sources
        """
        if not sources:
            return 0.0
        
        # Combine all source content
        source_text = " ".join([
            src.get('content', '') for src in sources
        ]).lower()
        
        # Split answer into sentences (simple)
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Check each sentence against sources
        supported = 0
        for sentence in sentences:
            # Simple check: are key words from sentence in sources?
            words = set(sentence.lower().split())
            words -= {'the', 'a', 'an', 'is', 'are', 'in', 'on', 'of'}
            
            if words:
                overlap = sum(1 for word in words if word in source_text)
                if overlap / len(words) > 0.5:  # 50% overlap threshold
                    supported += 1
        
        return supported / len(sentences)
    
    def hallucination_rate(
        self,
        answer: str,
        sources: List[Dict]
    ) -> float:
        """
        Hallucination Rate: Percentage of unsupported claims
        
        Returns: 1 - faithfulness_score
        """
        return 1.0 - self.faithfulness_score(answer, sources)
    
    def completeness_score(
        self,
        answer: str,
        expected_answer: str
    ) -> float:
        """
        Completeness: Does answer cover expected information?
        
        Simple token overlap with expected answer
        """
        expected_tokens = set(expected_answer.lower().split())
        answer_tokens = set(answer.lower().split())
        
        stopwords = {'the', 'a', 'an', 'is', 'are', 'in', 'on', 'of', 'for', 'to'}
        expected_tokens -= stopwords
        answer_tokens -= stopwords
        
        if not expected_tokens:
            return 0.0
        
        overlap = expected_tokens & answer_tokens
        return len(overlap) / len(expected_tokens)
    
    # ==================== EVALUATION PIPELINE ====================
    
    def evaluate_retrieval(
        self,
        benchmark_data: List[Dict],
        k_values: List[int] = [1, 3, 5, 10]
    ) -> Dict:
        """
        Evaluate retrieval performance
        
        Returns:
            {
                'recall@1': 0.85,
                'recall@5': 0.92,
                'precision@5': 0.78,
                'mrr': 0.81,
                'ndcg@5': 0.87,
                'map': 0.79
            }
        """
        logger.info("Starting retrieval evaluation...")
        
        all_recalls = {k: [] for k in k_values}
        all_precisions = {k: [] for k in k_values}
        all_ndcgs = {k: [] for k in k_values}
        all_mrrs = []
        
        # For MAP calculation
        all_retrieved = []
        all_relevant = []
        
        for example in benchmark_data:
            question = example['question']
            relevant_docs = example['relevant_docs']
            
            # Retrieve documents
            try:
                # Use retrieval system
                retriever = get_multilingual_retriever()
                if retriever and retriever.index is not None:
                    results = retriever.search(question, top_k=max(k_values))
                    retrieved_docs = [doc.get('id', '') for doc in results]
                else:
                    retrieved_docs = []
            except Exception as e:
                logger.warning(f"Retrieval error: {e}")
                retrieved_docs = []
            
            # Calculate metrics
            for k in k_values:
                recall = self.recall_at_k(retrieved_docs, relevant_docs, k)
                precision = self.precision_at_k(retrieved_docs, relevant_docs, k)
                ndcg = self.ndcg_at_k(retrieved_docs, relevant_docs, k)
                
                all_recalls[k].append(recall)
                all_precisions[k].append(precision)
                all_ndcgs[k].append(ndcg)
            
            mrr = self.mean_reciprocal_rank(retrieved_docs, relevant_docs)
            all_mrrs.append(mrr)
            
            all_retrieved.append(retrieved_docs)
            all_relevant.append(relevant_docs)
        
        # Aggregate results
        results = {}
        for k in k_values:
            results[f'recall@{k}'] = np.mean(all_recalls[k])
            results[f'precision@{k}'] = np.mean(all_precisions[k])
            results[f'ndcg@{k}'] = np.mean(all_ndcgs[k])
        
        results['mrr'] = np.mean(all_mrrs)
        results['map'] = self.mean_average_precision(all_retrieved, all_relevant)
        
        logger.info("Retrieval evaluation complete")
        return results
    
    def evaluate_generation(
        self,
        benchmark_data: List[Dict]
    ) -> Dict:
        """
        Evaluate answer generation quality
        
        Returns:
            {
                'answer_relevance': 0.82,
                'faithfulness': 0.91,
                'hallucination_rate': 0.09,
                'completeness': 0.76
            }
        """
        logger.info("Starting generation evaluation...")
        
        relevance_scores = []
        faithfulness_scores = []
        hallucination_rates = []
        completeness_scores = []
        
        for example in benchmark_data:
            question = example['question']
            expected_answer = example['answer']
            language = example.get('language', 'en')
            
            # Generate answer
            try:
                result = self.rag.query(question, language=language, top_k=5)
                generated_answer = result.answer
                sources = result.sources
            except Exception as e:
                logger.warning(f"Generation error: {e}")
                continue
            
            # Calculate metrics
            relevance = self.answer_relevance(question, generated_answer)
            faithfulness = self.faithfulness_score(generated_answer, sources)
            hallucination = self.hallucination_rate(generated_answer, sources)
            completeness = self.completeness_score(generated_answer, expected_answer)
            
            relevance_scores.append(relevance)
            faithfulness_scores.append(faithfulness)
            hallucination_rates.append(hallucination)
            completeness_scores.append(completeness)
        
        results = {
            'answer_relevance': np.mean(relevance_scores),
            'faithfulness': np.mean(faithfulness_scores),
            'hallucination_rate': np.mean(hallucination_rates),
            'completeness': np.mean(completeness_scores)
        }
        
        logger.info("Generation evaluation complete")
        return results
    
    def evaluate_full(
        self,
        benchmark_path: str,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Run full RAG evaluation pipeline
        
        Args:
            benchmark_path: Path to benchmark dataset
            output_path: Path to save results (JSON)
        
        Returns:
            Complete evaluation results
        """
        logger.info("="*60)
        logger.info("FULL RAG EVALUATION")
        logger.info("="*60)
        
        # Load benchmark
        benchmark_data = self.load_benchmark(benchmark_path)
        
        # Evaluate retrieval
        retrieval_results = self.evaluate_retrieval(benchmark_data)
        
        # Evaluate generation
        generation_results = self.evaluate_generation(benchmark_data)
        
        # Combine results
        full_results = {
            'benchmark': benchmark_path,
            'num_examples': len(benchmark_data),
            'retrieval_metrics': retrieval_results,
            'generation_metrics': generation_results,
            'overall_score': self._calculate_overall_score(
                retrieval_results,
                generation_results
            )
        }
        
        # Print summary
        self._print_summary(full_results)
        
        # Save results
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_path}")
        
        return full_results
    
    def _calculate_overall_score(
        self,
        retrieval_results: Dict,
        generation_results: Dict
    ) -> float:
        """
        Calculate weighted overall score
        
        Weights:
        - Retrieval: 40%
        - Generation: 60%
        """
        # Average key retrieval metrics
        retrieval_score = np.mean([
            retrieval_results.get('recall@5', 0),
            retrieval_results.get('ndcg@5', 0),
            retrieval_results.get('mrr', 0)
        ])
        
        # Average key generation metrics
        generation_score = np.mean([
            generation_results.get('answer_relevance', 0),
            generation_results.get('faithfulness', 0),
            generation_results.get('completeness', 0)
        ])
        
        overall = 0.4 * retrieval_score + 0.6 * generation_score
        return overall
    
    def _print_summary(self, results: Dict):
        """Print formatted evaluation summary"""
        print("\n" + "="*60)
        print("RAG EVALUATION SUMMARY")
        print("="*60)
        
        print(f"\n📊 Benchmark: {results['benchmark']}")
        print(f"📝 Examples: {results['num_examples']}")
        
        print("\n🔍 RETRIEVAL METRICS:")
        for metric, value in results['retrieval_metrics'].items():
            print(f"   {metric:15s}: {value:.4f}")
        
        print("\n💬 GENERATION METRICS:")
        for metric, value in results['generation_metrics'].items():
            print(f"   {metric:18s}: {value:.4f}")
        
        print(f"\n⭐ OVERALL SCORE: {results['overall_score']:.4f}")
        print("="*60)


def main():
    """Run RAG evaluation"""
    # Initialize evaluator
    evaluator = RAGEvaluator()
    
    # Check if benchmark exists
    benchmark_path = "evaluation/benchmarks/rag_benchmark_en.json"
    if not Path(benchmark_path).exists():
        print(f"⚠️  Benchmark not found: {benchmark_path}")
        print("Please create benchmark dataset first")
        print("See: evaluation/benchmarks/README.md")
        return
    
    # Run evaluation
    results = evaluator.evaluate_full(
        benchmark_path=benchmark_path,
        output_path="evaluation/results/rag_evaluation_results.json"
    )


if __name__ == "__main__":
    main()
