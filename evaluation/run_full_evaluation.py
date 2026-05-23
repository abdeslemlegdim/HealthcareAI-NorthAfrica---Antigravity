"""
Full Evaluation Suite Runner

Runs comprehensive evaluation of all system components:
1. RAG Evaluation (retrieval + generation)
2. Multilingual Evaluation (cross-lingual + bias)
3. Imaging Evaluation (classification + explainability)

Generates comprehensive report with all metrics.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
import sys

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import evaluation modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from rag_evaluation import RAGEvaluator
from multilingual_evaluation import MultilingualEvaluator
try:
    from imaging_evaluation import ImagingEvaluator
    IMAGING_AVAILABLE = True
except ImportError:
    IMAGING_AVAILABLE = False
    logging.warning("Imaging evaluation not available (PyTorch not installed)")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FullEvaluationRunner:
    """
    Comprehensive evaluation runner
    
    Runs all evaluation modules and generates unified report
    """
    
    def __init__(self, output_dir: str = "evaluation/results"):
        """
        Initialize evaluation runner
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {
            'timestamp': self.timestamp,
            'evaluations': {}
        }
        
        logger.info("Initialized Full Evaluation Runner")
    
    def run_rag_evaluation(self) -> Dict:
        """
        Run RAG evaluation
        
        Returns:
            RAG evaluation results
        """
        logger.info("="*70)
        logger.info("STEP 1: RAG EVALUATION")
        logger.info("="*70)
        
        benchmark_path = "evaluation/benchmarks/rag_benchmark_en.json"
        
        if not Path(benchmark_path).exists():
            logger.error(f"Benchmark not found: {benchmark_path}")
            return {'status': 'skipped', 'reason': 'benchmark not found'}
        
        try:
            evaluator = RAGEvaluator()
            results = evaluator.evaluate_full(
                benchmark_path=benchmark_path,
                output_path=str(self.output_dir / f"rag_evaluation_{self.timestamp}.json")
            )
            
            logger.info("✅ RAG evaluation complete")
            return {'status': 'success', 'results': results}
        
        except Exception as e:
            logger.error(f"RAG evaluation failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def run_multilingual_evaluation(self) -> Dict:
        """
        Run multilingual evaluation
        
        Returns:
            Multilingual evaluation results
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 2: MULTILINGUAL EVALUATION")
        logger.info("="*70)
        
        benchmark_path = "evaluation/benchmarks/multilingual_benchmark.json"
        parallel_path = "evaluation/benchmarks/parallel_corpus.json"
        
        try:
            evaluator = MultilingualEvaluator()
            results = evaluator.evaluate_full(
                benchmark_path=benchmark_path,
                parallel_corpus_path=parallel_path,
                output_path=str(self.output_dir / f"multilingual_evaluation_{self.timestamp}.json")
            )
            
            logger.info("✅ Multilingual evaluation complete")
            return {'status': 'success', 'results': results}
        
        except Exception as e:
            logger.error(f"Multilingual evaluation failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def run_imaging_evaluation(self) -> Dict:
        """
        Run imaging evaluation
        
        Returns:
            Imaging evaluation results
        """
        logger.info("\n" + "="*70)
        logger.info("STEP 3: IMAGING EVALUATION")
        logger.info("="*70)
        
        if not IMAGING_AVAILABLE:
            logger.warning("Imaging evaluation skipped (dependencies not available)")
            return {'status': 'skipped', 'reason': 'dependencies not available'}
        
        test_dataset_path = "evaluation/benchmarks/imaging_test_dataset.json"
        
        if not Path(test_dataset_path).exists():
            logger.warning(f"Imaging test dataset not found: {test_dataset_path}")
            logger.info("Creating synthetic test dataset for demonstration...")
            
            # Create minimal synthetic dataset
            self._create_synthetic_imaging_dataset(test_dataset_path)
        
        try:
            evaluator = ImagingEvaluator()
            
            # Load test dataset
            with open(test_dataset_path, 'r') as f:
                test_dataset = json.load(f)
            
            # Run evaluation
            results = evaluator.evaluate_on_dataset(test_dataset)
            
            # Save results
            evaluator.generate_report(
                results,
                output_path=str(self.output_dir / f"imaging_evaluation_{self.timestamp}.json")
            )
            
            logger.info("✅ Imaging evaluation complete")
            return {'status': 'success', 'results': results}
        
        except Exception as e:
            logger.error(f"Imaging evaluation failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _create_synthetic_imaging_dataset(self, output_path: str):
        """Create synthetic imaging dataset for testing"""
        # This creates references to test images
        # In production, replace with real medical imaging dataset
        synthetic_dataset = [
            {
                "image_path": "data/test_images/test_chest_xray.jpg",
                "true_label": "Normal",
                "note": "Synthetic dataset for demonstration"
            }
        ]
        
        with open(output_path, 'w') as f:
            json.dump(synthetic_dataset, f, indent=2)
        
        logger.info(f"Created synthetic dataset: {output_path}")
    
    def run_all(self) -> Dict:
        """
        Run all evaluations
        
        Returns:
            Complete evaluation results
        """
        logger.info("\n" + "="*70)
        logger.info("🎯 FULL SYSTEM EVALUATION")
        logger.info("="*70)
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("="*70)
        
        # Run all evaluations
        self.results['evaluations']['rag'] = self.run_rag_evaluation()
        self.results['evaluations']['multilingual'] = self.run_multilingual_evaluation()
        self.results['evaluations']['imaging'] = self.run_imaging_evaluation()
        
        # Generate summary
        self.results['summary'] = self._generate_summary()
        
        # Save complete results
        output_file = self.output_dir / f"full_evaluation_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Full evaluation complete!")
        logger.info(f"Results saved to: {output_file}")
        
        # Print final summary
        self._print_final_summary()
        
        return self.results
    
    def _generate_summary(self) -> Dict:
        """Generate evaluation summary"""
        summary = {
            'evaluations_run': 0,
            'evaluations_succeeded': 0,
            'evaluations_failed': 0,
            'evaluations_skipped': 0,
            'key_metrics': {}
        }
        
        for module, result in self.results['evaluations'].items():
            summary['evaluations_run'] += 1
            
            status = result.get('status')
            if status == 'success':
                summary['evaluations_succeeded'] += 1
            elif status == 'failed':
                summary['evaluations_failed'] += 1
            elif status == 'skipped':
                summary['evaluations_skipped'] += 1
        
        # Extract key metrics
        rag = self.results['evaluations'].get('rag', {})
        if rag.get('status') == 'success':
            rag_results = rag.get('results', {})
            summary['key_metrics']['rag'] = {
                'overall_score': rag_results.get('overall_score'),
                'recall@5': rag_results.get('retrieval_metrics', {}).get('recall@5'),
                'faithfulness': rag_results.get('generation_metrics', {}).get('faithfulness')
            }
        
        multilingual = self.results['evaluations'].get('multilingual', {})
        if multilingual.get('status') == 'success':
            ml_results = multilingual.get('results', {})
            summary['key_metrics']['multilingual'] = {
                'language_detection_accuracy': ml_results.get('language_detection', {}).get('overall_accuracy')
            }
        
        imaging = self.results['evaluations'].get('imaging', {})
        if imaging.get('status') == 'success':
            img_results = imaging.get('results', {})
            summary['key_metrics']['imaging'] = {
                'macro_f1': img_results.get('metrics', {}).get('macro_average', {}).get('f1'),
                'macro_auc': img_results.get('metrics', {}).get('auc_roc', {}).get('macro_auc')
            }
        
        return summary
    
    def _print_final_summary(self):
        """Print final evaluation summary"""
        print("\n" + "="*70)
        print("📊 FINAL EVALUATION SUMMARY")
        print("="*70)
        
        summary = self.results['summary']
        
        print(f"\n✅ Evaluations Succeeded: {summary['evaluations_succeeded']}")
        print(f"❌ Evaluations Failed: {summary['evaluations_failed']}")
        print(f"⏭️  Evaluations Skipped: {summary['evaluations_skipped']}")
        
        print("\n🎯 KEY METRICS:")
        
        if 'rag' in summary['key_metrics']:
            rag = summary['key_metrics']['rag']
            print(f"\n   RAG System:")
            print(f"      Overall Score: {rag.get('overall_score', 0):.4f}")
            print(f"      Recall@5:      {rag.get('recall@5', 0):.4f}")
            print(f"      Faithfulness:  {rag.get('faithfulness', 0):.4f}")
        
        if 'multilingual' in summary['key_metrics']:
            ml = summary['key_metrics']['multilingual']
            print(f"\n   Multilingual:")
            print(f"      Language Detection: {ml.get('language_detection_accuracy', 0):.4f}")
        
        if 'imaging' in summary['key_metrics']:
            img = summary['key_metrics']['imaging']
            print(f"\n   Medical Imaging:")
            print(f"      Macro F1:  {img.get('macro_f1', 0):.4f}")
            print(f"      Macro AUC: {img.get('macro_auc', 0):.4f}")
        
        print("\n" + "="*70)
        print("📝 RECOMMENDATIONS:")
        print("="*70)
        
        self._print_recommendations()
    
    def _print_recommendations(self):
        """Print actionable recommendations based on results"""
        recommendations = []
        
        # Check RAG performance
        rag = self.results['evaluations'].get('rag', {})
        if rag.get('status') == 'success':
            rag_results = rag.get('results', {})
            overall_score = rag_results.get('overall_score', 0)
            
            if overall_score < 0.7:
                recommendations.append(
                    "⚠️  RAG performance below 70% - consider:\n"
                    "   - Expanding knowledge base\n"
                    "   - Fine-tuning embedding model\n"
                    "   - Improving chunking strategy"
                )
            
            hallucination_rate = rag_results.get('generation_metrics', {}).get('hallucination_rate', 0)
            if hallucination_rate > 0.15:
                recommendations.append(
                    "⚠️  High hallucination rate (>15%) - consider:\n"
                    "   - Strengthening answer grounding\n"
                    "   - Adding fact verification step\n"
                    "   - Filtering low-confidence sources"
                )
        
        # Check multilingual performance
        multilingual = self.results['evaluations'].get('multilingual', {})
        if multilingual.get('status') == 'success':
            ml_results = multilingual.get('results', {})
            
            # Check for language bias
            if 'bias_analysis' in ml_results.get('results', {}):
                bias = ml_results['results']['bias_analysis']
                max_gap = bias.get('retrieval_bias', {}).get('max_gap', 0)
                
                if max_gap > 0.15:
                    recommendations.append(
                        f"⚠️  Significant language bias detected (gap={max_gap:.2f}) - consider:\n"
                        "   - Balancing training data across languages\n"
                        "   - Language-specific fine-tuning\n"
                        "   - Analyzing underperforming languages"
                    )
        
        # Check imaging performance
        imaging = self.results['evaluations'].get('imaging', {})
        if imaging.get('status') == 'success':
            img_results = imaging.get('results', {})
            metrics = img_results.get('metrics', {})
            
            # Check if using ImageNet weights (need to verify in actual implementation)
            recommendations.append(
                "📌 CRITICAL: Verify model weights:\n"
                "   - Are you using ImageNet pretrained weights?\n"
                "   - If yes, fine-tune on ChestX-ray14 or CheXpert\n"
                "   - Medical imaging requires domain-specific training!"
            )
            
            # Check sensitivity
            per_class = metrics.get('per_class', {})
            for disease, disease_metrics in per_class.items():
                sensitivity = disease_metrics.get('sensitivity', 0)
                if sensitivity < 0.8 and disease != 'Normal':
                    recommendations.append(
                        f"⚠️  Low sensitivity for {disease} ({sensitivity:.2f}) - CRITICAL for medical AI!\n"
                        "   - Increase positive samples in training\n"
                        "   - Adjust classification threshold\n"
                        "   - Use focal loss for class imbalance"
                    )
        
        # Print recommendations
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec}")
        else:
            print("\n✅ All metrics within acceptable ranges!")
        
        # General recommendations
        print("\n📚 PUBLICATION READINESS:")
        print("="*70)
        print("Before publishing results:")
        print("1. ✅ Expand benchmark datasets to 100+ examples per language")
        print("2. ✅ Fine-tune imaging model on medical dataset (NIH/CheXpert)")
        print("3. ✅ Conduct fairness audit across demographic groups")
        print("4. ✅ Validate Grad-CAM on radiologist-annotated data")
        print("5. ✅ Compare with established baselines (BioGPT, PubMedBERT, etc.)")
        print("6. ✅ Statistical significance testing")
        print("7. ✅ Error analysis and failure case documentation")


def main():
    """Run full evaluation suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run full system evaluation")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="evaluation/results",
        help="Output directory for results"
    )
    args = parser.parse_args()
    
    # Run evaluation
    runner = FullEvaluationRunner(output_dir=args.output_dir)
    results = runner.run_all()
    
    return results


if __name__ == "__main__":
    main()
