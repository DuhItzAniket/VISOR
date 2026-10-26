"""Identify the cv2 provider and enforce the desktop packaging profile."""

import platform
from importlib import metadata

OPENCV_DISTRIBUTIONS = (
    "opencv-contrib-python-headless", "opencv-contrib-python", "opencv-python-headless", "opencv-python",
)
DESKTOP_OPENCV = OPENCV_DISTRIBUTIONS[0]


def desktop_opencv_version(*, version=metadata.version) -> str:
    """Reject overlapping cv2 providers rather than freeze mixed package files."""
    installed = {}
    for name in OPENCV_DISTRIBUTIONS:
        try:
            installed[name] = version(name)
        except metadata.PackageNotFoundError:
            pass
    if set(installed) != {DESKTOP_OPENCV}:
        names = ", ".join(installed) or "none"
        raise RuntimeError(
            f"Desktop packaging requires only {DESKTOP_OPENCV}; found: {names}. "
            "Use a clean environment with requirements/desktop-build.txt."
        )
    return installed[DESKTOP_OPENCV]


def validate_opencv_build(build_information: str, *, system: str | None = None,
                          opencv_version: str | None = None) -> str:
    """Reject additional GUI toolkits, recording the pinned Mac wheel exception."""
    backend = next((line.split(":", 1)[1].strip() for line in build_information.splitlines()
                    if line.strip().startswith("GUI:")), None)
    # Upstream wheel build 86 explicitly retains Cocoa on macOS even when
    # build_headless is selected. Do not relabel that backend as NONE.
    # https://github.com/opencv/opencv-python/blob/255564a37c4a23275485e827abbe19031347d458/setup.py
    cocoa_exception = (system or platform.system()) == "Darwin" and opencv_version == "4.11.0" and backend == "COCOA"
    if backend != "NONE" and not cocoa_exception:
        raise RuntimeError(f"Expected OpenCV GUI backend NONE; found {backend!r}.")
    assert backend is not None
    return backend
