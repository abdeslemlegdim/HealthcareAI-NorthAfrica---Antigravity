from pathlib import Path
from src.utils.config import settings
import shutil
import time

models_dir = Path(settings.MODELS_DIR)
if not models_dir.exists():
    print('Models directory not found:', models_dir)
    raise SystemExit(1)

candidates = []
for ext in ('*.pt','*.pth','*_pretrained.pt','*_checkpoint.pt'):
    candidates.extend(models_dir.glob(ext))

if not candidates:
    print('No checkpoints found in', models_dir)
    raise SystemExit(1)

latest = max(candidates, key=lambda p: p.stat().st_mtime)
print('Selected checkpoint:', latest)

target_path = Path(settings.MEDICAL_IMAGE_MODEL_PATH)
if target_path.exists():
    backup = target_path.with_suffix(target_path.suffix + f'.bak.{int(time.time())}')
    target_path.replace(backup)

shutil.copy2(latest, target_path)
print('Deployed to', target_path)
