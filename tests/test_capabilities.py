"""The selector, status dialog and pipeline agree about executable engines."""

import sys

import pytest

from visor.engine_registry import engine_capabilities, list_engines
from visor.models import VALID_ENGINE_NAMES
from visor.pipeline import analyze
from visor.ui.engine_status import _collect_entries


def test_every_advertised_engine_has_a_factory_and_status():
    capabilities = engine_capabilities()
    assert tuple(item.name for item in capabilities) == VALID_ENGINE_NAMES
    assert set(VALID_ENGINE_NAMES) <= set(list_engines())
    statuses = {entry.name: entry.available for entry in _collect_entries()}
    assert statuses == {item.name: item.available for item in capabilities}
    assert all(item.configuration_fields for item in capabilities)


def test_frozen_registry_never_advertises_learned_support(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert all(not item.available for item in engine_capabilities() if item.category == "Learned")


@pytest.mark.parametrize("name", ["AKAZE", "BRISK"])
def test_available_extra_classical_engine_is_not_silently_orb(textured_pair, name):
    item = next(row for row in engine_capabilities() if row.name == name)
    if not item.available:
        pytest.skip(f"{name} is absent from this OpenCV build")
    reference, target, *_ = textured_pair
    result = analyze(reference, target, name)
    assert result.engine == name
    assert result.geometry.valid
    assert "max_features" not in result.engine_configuration
    assert "threshold" in result.engine_configuration
    assert result.reference_features.descriptor_info.distance == "HAMMING"


def test_dependency_probe_does_not_import_torch_in_clean_process():
    import subprocess

    subprocess.run([sys.executable, "-c", ("from visor.engine_registry import engine_capabilities; "
                    "import sys; engine_capabilities(); assert 'torch' not in sys.modules")], check=True)
