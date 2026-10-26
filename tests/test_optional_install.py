"""Source setup keeps one cv2 provider and stops at the failed installation stage."""

import subprocess
from types import SimpleNamespace

import pytest

from visor.model_runtime import LIGHTGLUE_REQUIREMENT
from visor.ui.main_window import InstallWorker


@pytest.mark.parametrize("codes,expected_calls,success", [
    ([0, 0, 0], 3, True), ([7], 1, False), ([0, 8], 2, False), ([0, 0, 9], 3, False),
])
def test_optional_setup_preserves_cv2_provider_and_propagates_stage_failure(monkeypatch, codes, expected_calls, success):
    calls = []
    completed = []

    def popen(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=iter(["stage output\n"]), returncode=codes[len(calls) - 1], wait=lambda: None)

    monkeypatch.setattr(subprocess, "Popen", popen)
    worker = InstallWorker("test-python", install_lightglue=True, install_xfeat=True)
    worker.completed.connect(lambda ok, message: completed.append((ok, message)))
    worker.run()
    assert len(calls) == expected_calls
    assert len(completed) == 1 and completed[0][0] is success
    assert not any("opencv" in package for command in calls for package in command)
    assert "kornia>=0.6.11" in calls[0] and LIGHTGLUE_REQUIREMENT not in calls[0]
    if expected_calls >= 2:
        assert "--no-deps" in calls[1] and calls[1][-1] == LIGHTGLUE_REQUIREMENT
    if expected_calls == 3:
        assert calls[2] == ["test-python", "-m", "visor.model_setup", "--xfeat"]
