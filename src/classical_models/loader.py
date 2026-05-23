from pathlib import Path
import pickle
from typing import Dict
import logging


class ClassicalModelLoader:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.models: Dict[str, object] = {}
        self.logger = logging.getLogger(__name__)
        self._load_models()

    def _load_models(self):
        if not self.model_dir.exists():
            return
        # expected filenames in the provided folder
        mapping = {
            'diabetes': 'diabetes_model.sav',
            'heart_disease': 'heart_disease_model.sav',
            'parkinsons': 'parkinsons_model.sav',
            'lung_cancer': 'lungs_disease_model.sav',
            'thyroid': 'Thyroid_model.sav',
        }
        for key, fname in mapping.items():
            path = self.model_dir / fname
            self.logger.debug("Checking classical model path: %s", path)
            if path.exists():
                try:
                    with path.open('rb') as f:
                        self.models[key] = pickle.load(f)
                    self.logger.info("Loaded classical model: %s -> %s", key, path)
                except Exception:
                    self.logger.exception("Failed to load classical model %s from %s", key, path)
                    # skip bad models
                    continue

    def get(self, name: str):
        return self.models.get(name)


# Singleton loader for the project; initialized lazily by API
_loader: ClassicalModelLoader | None = None


def get_classical_loader(model_dir: str | Path = None) -> ClassicalModelLoader:
    global _loader
    if _loader is None:
        if model_dir is None:
            # default to the downloaded folder at the repository root
            model_dir = Path(__file__).resolve().parent.parent.parent / 'mediai-smart-disease-predictor-scikitlearn-healthpredict-ai-powered-disease-detection-v1'
        _loader = ClassicalModelLoader(Path(model_dir))
    return _loader
