from pathlib import Path
import csv
from typing import List, Dict, Any
from .loader import get_classical_loader


def _get_data_file_for_model(model_name: str) -> Path | None:
    loader = get_classical_loader()
    # derive data file paths relative to loader.model_dir
    base = Path(loader.model_dir)
    mapping = {
        'diabetes': 'diabetes_data.csv',
        'heart_disease': 'heart_disease_data.csv',
        'parkinsons': 'parkinsons_data.csv',
        'lung_cancer': 'prepocessed_lungs_data.csv',
        'thyroid': 'prepocessed_hypothyroid.csv'
    }
    fname = mapping.get(model_name)
    if not fname:
        return None
    path = base / fname
    return path if path.exists() else None


def infer_schema_from_csv(path: Path) -> List[str]:
    with path.open('r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        # strip possible index column
        header = [h.strip() for h in header if h is not None]
        return header


def build_feature_list_for_model(model_name: str) -> List[str]:
    path = _get_data_file_for_model(model_name)
    if not path:
        return []
    header = infer_schema_from_csv(path)
    # exclude common target columns
    excludes = {
        'diabetes': ['Outcome'],
        'heart_disease': ['target'],
        'parkinsons': ['name', 'status'],
        'lung_cancer': ['LUNG_CANCER'],
        'thyroid': ['binaryClass']
    }
    remove = set(excludes.get(model_name, []))
    features = [h for h in header if h not in remove]
    # For parkinsons the first column is an id-like 'name'
    return features


def parse_csv_file_to_feature_rows(file, model_name: str) -> List[List[float]]:
    # file can be a SpooledTemporaryFile or file-like object
    text = file.read().decode('utf-8') if hasattr(file, 'read') else str(file)
    lines = text.splitlines()
    reader = csv.DictReader(lines)
    features = build_feature_list_for_model(model_name)
    rows: List[List[float]] = []
    for r in reader:
        row = []
        for feat in features:
            # allow case-insensitive lookup
            val = None
            if feat in r:
                val = r[feat]
            else:
                # try lower/upper
                for k in r.keys():
                    if k.strip().lower() == feat.strip().lower():
                        val = r[k]
                        break
            try:
                row.append(float(val) if val not in (None, '') else 0.0)
            except Exception:
                # fallback: try to clean commas
                try:
                    row.append(float(str(val).replace(',', '')))
                except Exception:
                    row.append(0.0)
        rows.append(row)
    return rows


def map_payload_to_ordered_features(model_name: str, payload: Dict[str, Any]) -> List[float] | None:
    features = build_feature_list_for_model(model_name)
    if not features:
        return None
    out = []
    for feat in features:
        # accept either exact keys or case-insensitive
        if feat in payload:
            val = payload[feat]
        else:
            val = None
            for k in payload.keys():
                if k.strip().lower() == feat.strip().lower():
                    val = payload[k]
                    break
        try:
            out.append(float(val) if val not in (None, '') else 0.0)
        except Exception:
            try:
                out.append(float(str(val).replace(',', '')))
            except Exception:
                out.append(0.0)
    return out
