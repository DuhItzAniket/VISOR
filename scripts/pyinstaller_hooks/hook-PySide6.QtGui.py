"""Use the upstream dependency collector, excluding unused desktop plugins."""

from pathlib import Path

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries = [entry for entry in binaries
            if not Path(entry[0]).name.lower().removeprefix("lib").startswith(("qpdf.", "qtvirtualkeyboardplugin."))]
