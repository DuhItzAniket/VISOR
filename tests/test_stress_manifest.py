"""Synthetic research preparation preserves annotations, determinism and inputs."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from visor.evaluation_data import load_evaluation_manifest

spec = importlib.util.spec_from_file_location("stress_generator", Path(__file__).parents[1] / "scripts/create_stress_manifest.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def test_stress_manifest_is_deterministic_and_separates_truth_from_negative_labels(tmp_path):
    first = generator.create_manifest(tmp_path / "one")
    second = generator.create_manifest(tmp_path / "two")
    document, pairs = load_evaluation_manifest(first)
    assert first.read_bytes() == second.read_bytes()
    assert len(pairs) == 21 and sum(pair.expected_match is True for pair in pairs) == 12
    assert sum(pair.expected_match is False for pair in pairs) == 9
    assert len({pair.name for pair in pairs}) == 21
    assert all((pair.homography is not None) == pair.expected_match for pair in pairs)
    assert {pair.condition for pair in pairs} == {
        "textured", "repeated", "low-texture", "occlusion", "independent-scene", "independent-noise", "blank"}
    for image in first.parent.glob("*.png"):
        assert hashlib.sha256(image.read_bytes()).digest() == hashlib.sha256((second.parent / image.name).read_bytes()).digest()
    assert len(document["generator_code_sha256"]) == 64 and len(document["protocol_sha256"]) == 64


def test_generator_does_not_overwrite_existing_inputs(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    original = existing / "manifest.json"
    original.write_text(json.dumps({"user": "existing project"}), encoding="utf-8")
    before = original.read_bytes()
    with pytest.raises(FileExistsError):
        generator.create_manifest(existing)
    assert original.read_bytes() == before and list(existing.iterdir()) == [original]
