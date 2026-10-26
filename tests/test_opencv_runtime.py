"""Packaging must reject mixed cv2 ownership and retain actual provenance."""

from importlib import metadata

import pytest

from visor.opencv_runtime import DESKTOP_OPENCV, desktop_opencv_version, validate_opencv_build


@pytest.mark.parametrize("installed", [
    {}, {"opencv-contrib-python": "4.11.0.86"},
    {DESKTOP_OPENCV: "4.11.0.86", "opencv-python": "4.11.0.86"},
    {DESKTOP_OPENCV: "4.11.0.86", "opencv-contrib-python": "4.11.0.86"},
    {DESKTOP_OPENCV: "4.11.0.86"},
])
def test_desktop_profile_rejects_missing_wrong_or_overlapping_providers(installed):
    def version(name):
        if name not in installed:
            raise metadata.PackageNotFoundError(name)
        return installed[name]

    if set(installed) == {DESKTOP_OPENCV}:
        assert desktop_opencv_version(version=version) == "4.11.0.86"
    else:
        with pytest.raises(RuntimeError, match="clean environment"):
            desktop_opencv_version(version=version)


@pytest.mark.parametrize("information", ["  GUI: QT5\n", "  GUI: WIN32UI\n", "No GUI record"])
def test_gui_backend_cannot_silently_return(information):
    with pytest.raises(RuntimeError, match="backend NONE"):
        validate_opencv_build(information)


def test_none_backend_is_accepted():
    validate_opencv_build("Build information\n  GUI:                           NONE\n  Media I/O:")


def test_evaluation_records_the_actual_opencv_distribution(monkeypatch):
    from visor import evaluate

    def version(name):
        if name == DESKTOP_OPENCV:
            return "4.11.0.86"
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(evaluate.importlib.metadata, "version", version)
    versions = evaluate.runtime_versions()
    assert versions[DESKTOP_OPENCV] == "4.11.0.86"
    assert versions["opencv-contrib-python"] is None
