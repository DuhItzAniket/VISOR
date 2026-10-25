"""Build provenance follows the frozen source, not an old installed wheel."""

from pathlib import Path

import pytest
from scripts.build_desktop import source_version

from visor import __version__


def _source(tmp_path, content):
    directory = tmp_path / "src/visor"
    directory.mkdir(parents=True)
    (directory / "__init__.py").write_text(content)
    return tmp_path


def test_version_is_read_without_importing_source_or_installed_metadata(tmp_path, monkeypatch):
    import scripts.build_desktop as builder

    monkeypatch.setattr(builder.importlib.metadata, "version", lambda name: "0.1.0")
    root = _source(tmp_path, 'raise RuntimeError("must not execute")\n__version__ = "9.1.2"\n')
    assert source_version(root) == "9.1.2"


@pytest.mark.parametrize("content", ['__version__ = 3', '__version__ = ""',
                                     '__version__ = get_dynamic_version()', '# no version'])
def test_missing_or_nonliteral_source_version_fails_clearly(tmp_path, content):
    with pytest.raises(RuntimeError, match="literal nonempty"):
        source_version(_source(tmp_path, content))


def test_repository_build_and_runtime_version_agree():
    assert source_version(Path(__file__).resolve().parents[1]) == __version__
