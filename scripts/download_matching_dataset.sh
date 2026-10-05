#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT/Sample/Dataset"
mkdir -p "$DATA_DIR"

python -m pip install --quiet huggingface_hub

python - <<'PY'
from pathlib import Path
from huggingface_hub import snapshot_download
root = Path("Sample/Dataset")
(root / "MegaDepth").mkdir(parents=True, exist_ok=True)
try:
    snapshot_download(
        repo_id="cvg/megadepth",
        repo_type="dataset",
        local_dir=str(root / "MegaDepth"),
        local_dir_use_symlinks=False,
    )
    print("MegaDepth dataset snapshot downloaded.")
except Exception as exc:  # pragma: no cover - network-dependent
    print(f"MegaDepth snapshot fetch skipped or failed: {exc}")
PY

if [ ! -d "$DATA_DIR/HPatches" ]; then
  git clone --depth 1 https://github.com/hpatches/hpatches-dataset.git "$DATA_DIR/HPatches"
fi

printf '\nDataset layout:\n'
find "$DATA_DIR" -maxdepth 2 -type d | sort
