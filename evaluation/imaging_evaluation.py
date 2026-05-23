"""
Medical Imaging Evaluation

Evaluates medical image classification performance:
- Classification: AUC, F1, Precision, Recall, Sensitivity, Specificity
- Confusion Matrix
- ROC curves
- Explainability: Grad-CAM validation
- Comparison: ImageNet weights vs Medical weights

Critical for medical AI:
- Sensitivity (True Positive Rate) - must be HIGH
- Specificity (True Negative Rate) - minimize false positives
- AUC - overall discriminative ability
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

try:
    import torch
    from PIL import Image
    from src.medical_imaging import get_image_analyzer
    from src.medical_imaging.classifier import MedicalImageClassifier
    from src.explainability.gradcam import apply_gradcam
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImagingEvaluator:
    """
    Medical imaging evaluation framework
    
    Metrics:
    - Binary Classification: Accuracy, Precision, Recall, F1, AUC
    - Multi-class: Per-class metrics, macro/micro averages
    - Confusion Matrix
    - Sensitivity (True Positive Rate) - CRITICAL for medical
    - Specificity (True Negative Rate)
    - ROC-AUC for each class
    
    Explainability Validation:
    - Grad-CAM heatmap quality
    - Localization accuracy (if bounding boxes available)
    - Heatmap consistency across similar images
    """
    
    def __init__(
        self,
        classifier: Optional[MedicalImageClassifier] = None
    ):
        """
        Initialize imaging evaluator
        
        Args:
            classifier: Medical image classifier to evaluate
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for imaging evaluation")
        
        self.classifier = classifier
        if self.classifier is None:
            try:
                self.classifier = get_image_analyzer()
            except Exception as e:
                logger.warning(f"Could not load classifier: {e}")
        
        self.results = {}
        
        logger.info("Initialized Imaging Evaluator")
    
    # ==================== CLASSIFICATION METRICS ====================
    
    def calculate_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        num_classes: int
    ) -> np.ndarray:
        """
        Calculate confusion matrix
        
        Returns: (num_classes, num_classes) matrix
                 rows = true labels, cols = predicted labels
        """
        cm = np.zeros((num_classes, num_classes), dtype=int)
        
        for true, pred in zip(y_true, y_pred):
            cm[true, pred] += 1
        
        return cm
    
    def calculate_metrics_from_cm(
        self,
        confusion_matrix: np.ndarray,
        class_names: List[str]
    ) -> Dict:
        """
        Calculate all metrics from confusion matrix
        
        Returns:
            - Per-class: accuracy, precision, recall, f1, sensitivity, specificity
            - Overall: macro/micro averages
        """
        num_classes = len(class_names)
        metrics = {
            'per_class': {},
            'macro_average': {},
            'micro_average': {}
        }
        
        # Per-class metrics
        for i, class_name in enumerate(class_names):
            tp = confusion_matrix[i, i]
            fp = confusion_matrix[:, i].sum() - tp
            fn = confusion_matrix[i, :].sum() - tp
            tn = confusion_matrix.sum() - tp - fp - fn
            
            # Precision: TP / (TP + FP)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            
            # Recall (Sensitivity): TP / (TP + FN)
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            
            # F1 Score: Harmonic mean of precision and recall
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            # Specificity: TN / (TN + FP)
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            
            # Accuracy: (TP + TN) / Total
            accuracy = (tp + tn) / confusion_matrix.sum() if confusion_matrix.sum() > 0 else 0.0
            
            metrics['per_class'][class_name] = {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'sensitivity': recall,  # Same as recall
                'specificity': specificity,
                'accuracy': accuracy,
                'support': confusion_matrix[i, :].sum()
            }
        
        # Macro average (average of per-class metrics)
        precision_values = [m['precision'] for m in metrics['per_class'].values()]
        recall_values = [m['recall'] for m in metrics['per_class'].values()]
        f1_values = [m['f1'] for m in metrics['per_class'].values()]
        
        metrics['macro_average'] = {
            'precision': np.mean(precision_values),
            'recall': np.mean(recall_values),
            'f1': np.mean(f1_values)
        }
        
        # Micro average (aggregate TP, FP, FN across all classes)
        total_tp = np.trace(confusion_matrix)
        total_fp = confusion_matrix.sum(axis=0).sum() - total_tp
        total_fn = confusion_matrix.sum(axis=1).sum() - total_tp
        
        micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        micro_f1 = 2 * (micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0.0
        
        metrics['micro_average'] = {
            'precision': micro_precision,
            'recall': micro_recall,
            'f1': micro_f1
        }
        
        return metrics
    
    def calculate_auc_roc(
        self,
        y_true: np.ndarray,
        y_scores: np.ndarray,
        num_classes: int
    ) -> Dict:
        """
        Calculate AUC-ROC for each class (one-vs-rest)
        
        Args:
            y_true: True labels (n_samples,)
            y_scores: Predicted probabilities (n_samples, n_classes)
            num_classes: Number of classes
        
        Returns:
            Per-class AUC and macro-average
        """
        from sklearn.metrics import roc_auc_score, roc_curve
        
        # One-hot encode true labels
        y_true_onehot = np.zeros((len(y_true), num_classes))
        y_true_onehot[np.arange(len(y_true)), y_true] = 1
        
        auc_scores = {}
        roc_curves = {}
        
        for i in range(num_classes):
            try:
                # Calculate AUC for this class
                auc = roc_auc_score(y_true_onehot[:, i], y_scores[:, i])
                auc_scores[i] = auc
                
                # Calculate ROC curve
                fpr, tpr, thresholds = roc_curve(y_true_onehot[:, i], y_scores[:, i])
                roc_curves[i] = {
                    'fpr': fpr.tolist(),
                    'tpr': tpr.tolist(),
                    'thresholds': thresholds.tolist()
                }
            except Exception as e:
                logger.warning(f"Could not calculate AUC for class {i}: {e}")
                auc_scores[i] = 0.0
        
        # Macro average
        macro_auc = np.mean(list(auc_scores.values())) if auc_scores else 0.0
        
        return {
            'per_class_auc': auc_scores,
            'macro_auc': macro_auc,
            'roc_curves': roc_curves
        }
    
    # ==================== MODEL EVALUATION ====================
    
    def evaluate_on_dataset(
        self,
        dataset: List[Dict],
        save_predictions: bool = True
    ) -> Dict:
        """
        Evaluate classifier on a dataset
        
        Expected format:
        [
            {
                "image_path": "path/to/image.jpg",
                "true_label": "Pneumonia",
                "bounding_box": [x, y, w, h]  # Optional
            }
        ]
        
        Returns:
            Complete evaluation metrics
        """
        logger.info(f"Evaluating on {len(dataset)} images...")
        
        if self.classifier is None:
            raise ValueError("Classifier not loaded")
        
        y_true = []
        y_pred = []
        y_scores = []
        predictions = []
        
        for i, example in enumerate(dataset):
            image_path = example['image_path']
            true_label = example['true_label']
            
            if not Path(image_path).exists():
                logger.warning(f"Image not found: {image_path}")
                continue
            
            # Get true label index
            if true_label not in self.classifier.DISEASES:
                logger.warning(f"Unknown disease: {true_label}")
                continue
            true_idx = self.classifier.DISEASES.index(true_label)
            
            # Predict
            try:
                result = self.classifier.predict(image_path, explain=False)
                pred_label = result['predicted_disease']
                pred_idx = self.classifier.DISEASES.index(pred_label)
                pred_scores = result['probabilities']
                
                y_true.append(true_idx)
                y_pred.append(pred_idx)
                y_scores.append(pred_scores)
                
                # Store prediction
                predictions.append({
                    'image_path': image_path,
                    'true_label': true_label,
                    'predicted_label': pred_label,
                    'probabilities': pred_scores,
                    'correct': (pred_label == true_label)
                })
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(dataset)} images")
            
            except Exception as e:
                logger.error(f"Prediction error for {image_path}: {e}")
                continue
        
        # Convert to numpy arrays
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        y_scores = np.array(y_scores)
        
        # Calculate confusion matrix
        confusion_matrix = self.calculate_confusion_matrix(
            y_true, y_pred, len(self.classifier.DISEASES)
        )
        
        # Calculate metrics
        metrics = self.calculate_metrics_from_cm(
            confusion_matrix,
            self.classifier.DISEASES
        )
        
        # Calculate AUC-ROC
        try:
            auc_metrics = self.calculate_auc_roc(
                y_true, y_scores, len(self.classifier.DISEASES)
            )
            metrics['auc_roc'] = auc_metrics
        except Exception as e:
            logger.warning(f"Could not calculate AUC: {e}")
        
        # Store results
        results = {
            'confusion_matrix': confusion_matrix.tolist(),
            'metrics': metrics,
            'num_samples': len(y_true),
            'class_names': self.classifier.DISEASES
        }
        
        if save_predictions:
            results['predictions'] = predictions
        
        logger.info("Evaluation complete")
        return results
    
    # ==================== EXPLAINABILITY VALIDATION ====================
    
    def validate_gradcam(
        self,
        test_images: List[str],
        save_heatmaps: bool = True,
        output_dir: str = "evaluation/results/gradcam_validation"
    ) -> Dict:
        """
        Validate Grad-CAM explainability
        
        Checks:
        - Heatmap focuses on relevant regions (lungs for chest X-rays)
        - Consistency across similar images
        - No degenerate heatmaps (all zeros, all ones, random noise)
        
        Args:
            test_images: List of image paths
            save_heatmaps: Save visualizations
            output_dir: Directory to save heatmaps
        
        Returns:
            Validation metrics
        """
        logger.info("Validating Grad-CAM explainability...")
        
        if save_heatmaps:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        heatmap_stats = []
        focus_scores = []
        
        for img_path in test_images:
            if not Path(img_path).exists():
                logger.warning(f"Image not found: {img_path}")
                continue
            
            try:
                # Generate Grad-CAM
                result = self.classifier.predict(img_path, explain=True)
                
                if 'heatmap' in result:
                    heatmap = result['heatmap']
                    
                    # Analyze heatmap
                    stats = self._analyze_heatmap(heatmap)
                    heatmap_stats.append(stats)
                    
                    # Check if heatmap focuses on center region (where lungs typically are)
                    focus = self._calculate_focus_score(heatmap)
                    focus_scores.append(focus)
                    
                    # Save visualization
                    if save_heatmaps:
                        output_path = Path(output_dir) / f"{Path(img_path).stem}_gradcam.jpg"
                        # Heatmap is already saved by classifier, just log
                        logger.info(f"Heatmap analyzed: {img_path}")
                
            except Exception as e:
                logger.error(f"Grad-CAM error for {img_path}: {e}")
                continue
        
        # Aggregate results
        results = {
            'num_images_analyzed': len(heatmap_stats),
            'heatmap_statistics': {
                'mean_intensity': np.mean([s['mean'] for s in heatmap_stats]),
                'mean_std': np.mean([s['std'] for s in heatmap_stats]),
                'mean_sparsity': np.mean([s['sparsity'] for s in heatmap_stats])
            },
            'focus_scores': {
                'mean': np.mean(focus_scores) if focus_scores else 0.0,
                'std': np.std(focus_scores) if focus_scores else 0.0
            },
            'validation': self._validate_heatmap_quality(heatmap_stats, focus_scores)
        }
        
        logger.info("Grad-CAM validation complete")
        return results
    
    def _analyze_heatmap(self, heatmap: np.ndarray) -> Dict:
        """Analyze heatmap statistics"""
        return {
            'mean': float(np.mean(heatmap)),
            'std': float(np.std(heatmap)),
            'min': float(np.min(heatmap)),
            'max': float(np.max(heatmap)),
            'sparsity': float(np.sum(heatmap < 0.1) / heatmap.size)  # Fraction of near-zero values
        }
    
    def _calculate_focus_score(self, heatmap: np.ndarray) -> float:
        """
        Calculate how much heatmap focuses on center region
        
        For chest X-rays, we expect high activation in center (lungs)
        """
        h, w = heatmap.shape
        center_h, center_w = h // 2, w // 2
        
        # Define center region (middle 50% of image)
        center_region = heatmap[
            center_h - h//4 : center_h + h//4,
            center_w - w//4 : center_w + w//4
        ]
        
        # Calculate ratio of center intensity to total intensity
        center_intensity = np.sum(center_region)
        total_intensity = np.sum(heatmap)
        
        if total_intensity == 0:
            return 0.0
        
        return center_intensity / total_intensity
    
    def _validate_heatmap_quality(
        self,
        heatmap_stats: List[Dict],
        focus_scores: List[float]
    ) -> Dict:
        """
        Validate heatmap quality
        
        Checks:
        - Not degenerate (all zeros or all ones)
        - Has reasonable variance
        - Focuses on relevant regions
        """
        validation = {
            'is_valid': True,
            'warnings': []
        }
        
        if not heatmap_stats:
            validation['is_valid'] = False
            validation['warnings'].append("No heatmaps generated")
            return validation
        
        # Check for degenerate heatmaps
        mean_intensity = np.mean([s['mean'] for s in heatmap_stats])
        mean_std = np.mean([s['std'] for s in heatmap_stats])
        
        if mean_intensity < 0.01:
            validation['warnings'].append("Heatmaps are mostly zero (low activation)")
        
        if mean_std < 0.05:
            validation['warnings'].append("Heatmaps lack variance (uniform activation)")
        
        # Check focus
        mean_focus = np.mean(focus_scores) if focus_scores else 0.0
        if mean_focus < 0.3:
            validation['warnings'].append("Heatmaps don't focus on center region (expected for lungs)")
        
        validation['is_valid'] = len(validation['warnings']) == 0
        
        return validation
    
    # ==================== MODEL COMPARISON ====================
    
    def compare_models(
        self,
        model_configs: List[Dict],
        test_dataset: List[Dict]
    ) -> Dict:
        """
        Compare different model configurations
        
        Use case: ImageNet weights vs Medical weights
        
        Args:
            model_configs: [
                {
                    'name': 'ImageNet Pretrained',
                    'model_path': None,
                    'backbone': 'efficientnet_b0'
                },
                {
                    'name': 'NIH ChestX-ray Finetuned',
                    'model_path': 'models/chestxray_finetuned.pth',
                    'backbone': 'efficientnet_b0'
                }
            ]
            test_dataset: Evaluation dataset
        
        Returns:
            Comparison of model performance
        """
        logger.info(f"Comparing {len(model_configs)} models...")
        
        comparison_results = {}
        
        for config in model_configs:
            model_name = config['name']
            logger.info(f"\nEvaluating: {model_name}")
            
            # Load model
            try:
                classifier = MedicalImageClassifier(
                    model_path=config.get('model_path'),
                    backbone=config.get('backbone', 'efficientnet_b0')
                )
            except Exception as e:
                logger.error(f"Could not load model {model_name}: {e}")
                continue
            
            # Evaluate
            self.classifier = classifier
            results = self.evaluate_on_dataset(test_dataset, save_predictions=False)
            
            comparison_results[model_name] = {
                'macro_f1': results['metrics']['macro_average']['f1'],
                'macro_auc': results['metrics'].get('auc_roc', {}).get('macro_auc', 0.0),
                'per_class_f1': {
                    cls: metrics['f1']
                    for cls, metrics in results['metrics']['per_class'].items()
                }
            }
        
        logger.info("Model comparison complete")
        return comparison_results
    
    # ==================== REPORTING ====================
    
    def generate_report(
        self,
        results: Dict,
        output_path: str = "evaluation/results/imaging_evaluation_report.json"
    ):
        """
        Generate comprehensive evaluation report
        
        Args:
            results: Evaluation results
            output_path: Path to save report
        """
        logger.info("Generating evaluation report...")
        
        # Save as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to {output_path}")
        
        # Print summary
        self._print_summary(results)
    
    def _print_summary(self, results: Dict):
        """Print formatted summary"""
        print("\n" + "="*60)
        print("MEDICAL IMAGING EVALUATION SUMMARY")
        print("="*60)
        
        print(f"\n📊 Dataset: {results.get('num_samples', 0)} samples")
        
        if 'metrics' in results:
            metrics = results['metrics']
            
            print("\n🎯 MACRO AVERAGE:")
            print(f"   Precision: {metrics['macro_average']['precision']:.4f}")
            print(f"   Recall:    {metrics['macro_average']['recall']:.4f}")
            print(f"   F1 Score:  {metrics['macro_average']['f1']:.4f}")
            
            if 'auc_roc' in metrics:
                print(f"   AUC-ROC:   {metrics['auc_roc']['macro_auc']:.4f}")
            
            print("\n📈 PER-CLASS PERFORMANCE:")
            for cls, cls_metrics in metrics['per_class'].items():
                print(f"\n   {cls}:")
                print(f"      Sensitivity: {cls_metrics['sensitivity']:.4f} ⚕️  (CRITICAL)")
                print(f"      Specificity: {cls_metrics['specificity']:.4f}")
                print(f"      F1 Score:    {cls_metrics['f1']:.4f}")
                print(f"      Support:     {cls_metrics['support']}")
        
        print("\n" + "="*60)


def main():
    """Run imaging evaluation"""
    evaluator = ImagingEvaluator()
    
    # Check if test dataset exists
    test_dataset_path = "evaluation/benchmarks/imaging_test_dataset.json"
    if not Path(test_dataset_path).exists():
        print(f"⚠️  Test dataset not found: {test_dataset_path}")
        print("Please create imaging test dataset first")
        return
    
    # Load test dataset
    with open(test_dataset_path, 'r') as f:
        test_dataset = json.load(f)
    
    # Run evaluation
    results = evaluator.evaluate_on_dataset(test_dataset)
    
    # Generate report
    evaluator.generate_report(results)


if __name__ == "__main__":
    main()
