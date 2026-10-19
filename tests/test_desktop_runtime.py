"""A packaged desktop app must not attempt developer package installation."""

import sys
from types import SimpleNamespace

from visor import learned_engines, learned_extra
from visor.ui.main_window import MainWindow


def test_packaged_runtime_does_not_advertise_excluded_learned_engines(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(learned_engines, "_LIGHTGLUE_AVAILABLE", True)
    monkeypatch.setattr(learned_engines, "_XFEAT_AVAILABLE", True)
    assert not learned_engines.is_lightglue_available()
    assert not learned_engines.is_xfeat_available()
    assert not learned_extra.is_disk_available()


def test_packaged_runtime_never_invokes_pip_install_worker(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    messages = []
    window = SimpleNamespace(statusBar=lambda: SimpleNamespace(showMessage=messages.append))
    # This object deliberately has no worker/configuration fields: the frozen
    # guard must return before touching any developer installation machinery.
    MainWindow._install_learned_engines(window)
    assert messages == ["Additional learned engines are unavailable in this desktop distribution."]
