"""Explicit installation and offline loading of the pinned XFeat runtime."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

XFEAT_REVISION = "e92685f57f8318b18725c5c8c0bd28c7fe188d9a"
LIGHTGLUE_REVISION = "eb42fee2d71449efb0aa5c10549752b5d75384d8"
LIGHTGLUE_REQUIREMENT = f"git+https://github.com/cvg/LightGlue.git@{LIGHTGLUE_REVISION}"
XFEAT_REPOSITORY = "https://github.com/verlab/accelerated_features.git"
RUNTIME_FILES = ("modules/xfeat.py", "modules/model.py", "modules/interpolator.py", "weights/xfeat.pt")


def xfeat_root() -> Path:
    configured = os.environ.get("VISOR_MODEL_HOME")
    if configured:
        base = Path(configured).expanduser()
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "VISOR/models"
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Caches/VISOR/models"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "VISOR/models"
    return base.resolve() / f"xfeat-{XFEAT_REVISION}"


def validate_xfeat(root: Path, *, check_hashes: bool = True) -> None:
    try:
        manifest = json.loads((root / "visor-runtime.json").read_text(encoding="utf-8"))
        if manifest["revision"] != XFEAT_REVISION:
            raise ValueError("XFeat revision does not match the supported pin.")
        for name in RUNTIME_FILES:
            path = root / name
            if not path.is_file():
                raise ValueError(f"XFeat runtime is missing {name}.")
            if check_hashes and hashlib.sha256(path.read_bytes()).hexdigest() != manifest["sha256"][name]:
                raise ValueError(f"XFeat runtime integrity check failed for {name}.")
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("XFeat runtime is missing or incomplete. Run python -m visor.model_setup --xfeat.") from exc


def xfeat_ready() -> bool:
    try:
        validate_xfeat(xfeat_root(), check_hashes=False)
        return True
    except ValueError:
        return False


def install_xfeat() -> Path:
    """Fetch only on explicit setup; analysis never clones or updates code."""
    root = xfeat_root()
    if root.exists():
        validate_xfeat(root)
        return root
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="xfeat-install-", dir=root.parent) as temp:
        checkout = Path(temp) / "checkout"
        subprocess.run(["git", "clone", "--no-checkout", "--filter=blob:none", "--no-tags",
                        XFEAT_REPOSITORY, str(checkout)], check=True)
        subprocess.run(["git", "-C", str(checkout), "-c", "core.autocrlf=false", "checkout", "--detach", XFEAT_REVISION],
                       check=True)
        revision = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if revision != XFEAT_REVISION:
            raise ValueError("Downloaded XFeat revision does not match its pin.")
        hashes = {name: hashlib.sha256((checkout / name).read_bytes()).hexdigest() for name in RUNTIME_FILES}
        (checkout / "visor-runtime.json").write_text(json.dumps({
            "repository": XFEAT_REPOSITORY, "revision": revision, "sha256": hashes,
        }, indent=2), encoding="utf-8")
        validate_xfeat(checkout)
        # Atomic within the same parent filesystem. Never replace an existing runtime.
        checkout.rename(root)
    return root


def load_xfeat(device: Any, max_keypoints: int, threshold: float) -> Any:
    """Load the pinned detectAndCompute API, without network or implicit GPU selection.

    Upstream's constructor chooses CUDA globally and uses a generic `modules`
    package. Initialize its pinned inference state on the requested device and
    reject namespace collisions rather than importing unrelated local code.
    """
    import torch

    root = xfeat_root()
    validate_xfeat(root)
    names = ("modules", "modules.model", "modules.interpolator", "modules.xfeat")
    for name in names:
        existing = sys.modules.get(name)
        if existing is not None:
            locations = [Path(p).resolve() for p in getattr(existing, "__path__", ())]
            module_file = getattr(existing, "__file__", None)
            if module_file:
                locations.append(Path(module_file).resolve())
            if not locations or any(not path.is_relative_to(root) for path in locations):
                raise ValueError(f"XFeat cannot load because another package owns {name!r}. Restart in an isolated environment.")
    sys.path.insert(0, str(root))
    try:
        module = importlib.import_module("modules.xfeat")
    finally:
        sys.path.remove(str(root))
    extractor = module.XFeat.__new__(module.XFeat)
    torch.nn.Module.__init__(extractor)
    extractor.dev = device
    extractor.net = module.XFeatModel().to(device).eval()
    state = torch.load(root / "weights/xfeat.pt", map_location=device, weights_only=True)
    extractor.net.load_state_dict(state)
    extractor.top_k = max_keypoints
    extractor.detection_threshold = threshold
    extractor.interpolator = module.InterpolateSparse2d("bicubic")
    extractor.kornia_available = False
    extractor.lighterglue = None
    return extractor.eval()
