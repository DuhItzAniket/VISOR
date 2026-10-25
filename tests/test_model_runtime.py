"""Pinned cache integrity and matcher semantics, without network or models."""

import hashlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from visor.learned_engines import XFeatEngine
from visor.model_runtime import RUNTIME_FILES, XFEAT_REVISION, install_xfeat, validate_xfeat, xfeat_ready, xfeat_root
from visor.models import DescriptorInfo, FeatureSet, KeypointInfo


def _cache(monkeypatch, tmp_path):
    monkeypatch.setenv("VISOR_MODEL_HOME", str(tmp_path))
    root = xfeat_root()
    hashes = {}
    for name in RUNTIME_FILES:
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(name.encode())
        hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    (root / "visor-runtime.json").write_text(json.dumps({"revision": XFEAT_REVISION, "sha256": hashes}))
    return root


def test_missing_cache_has_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setenv("VISOR_MODEL_HOME", str(tmp_path))
    assert not xfeat_ready()
    with pytest.raises(ValueError, match="model_setup --xfeat"):
        validate_xfeat(xfeat_root())


def test_cache_is_pinned_and_setup_reuses_it_without_network(monkeypatch, tmp_path):
    import subprocess

    root = _cache(monkeypatch, tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("setup unexpectedly executed git"))
    assert xfeat_ready()
    assert install_xfeat() == root
    assert XFEAT_REVISION in root.name


def test_modified_runtime_is_rejected(monkeypatch, tmp_path):
    root = _cache(monkeypatch, tmp_path)
    (root / RUNTIME_FILES[0]).write_text("unexpected changes")
    with pytest.raises(ValueError, match="integrity"):
        validate_xfeat(root)
    # Setup must report corruption rather than overwriting existing local files.
    with pytest.raises(ValueError, match="integrity"):
        install_xfeat()


def test_wrong_revision_is_not_available(monkeypatch, tmp_path):
    root = _cache(monkeypatch, tmp_path)
    (root / "visor-runtime.json").write_text(json.dumps({"revision": "wrong"}))
    assert not xfeat_ready()


def test_xfeat_matching_requires_mutual_neighbors():
    def features(descriptors):
        count = len(descriptors)
        return FeatureSet(tuple(KeypointInfo(float(i), 0., 1., 0., 0., 0, -1) for i in range(count)),
                          np.array(descriptors, dtype=np.float32), DescriptorInfo(count, 2, "FLOAT32", 0, "L2"), 1.)

    ref = features([[1., 0.], [1.01, 0.]])
    tgt = features([[1., 0.], [50., 50.]])
    engine = XFeatEngine.__new__(XFeatEngine)
    outputs = iter([ref, tgt])
    engine.extract = lambda gray: next(outputs)
    engine._device = "cpu"
    result = engine.match_pair(np.zeros((2, 2), np.uint8), np.zeros((2, 2), np.uint8))
    assert result.match_set.matcher == "Brute force / L2"
    assert result.match_set.good_count == 1
    assert result.match_set.matches[0].query_index == result.match_set.matches[0].train_index == 0
    assert result.match_set.matches[0].distance == 0
    assert result.match_set.matches[0].confidence is None


def test_conflicting_modules_namespace_is_rejected(monkeypatch, tmp_path):
    import sys

    from visor.model_runtime import load_xfeat

    _cache(monkeypatch, tmp_path)
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "modules", SimpleNamespace(__file__=str(tmp_path / "unrelated.py")))
    with pytest.raises(ValueError, match="another package owns"):
        load_xfeat("cpu", 128, 0.005)
