"""Capture Linux build-host package/notice evidence without changing the application."""

import argparse
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from visor.system_library_review import collect_system_review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toc", type=Path, default=ROOT / "build/VISOR/COLLECT-00.toc")
    parser.add_argument("--build-info", type=Path, default=ROOT / "dist/build-info.json")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/system-notice-review")
    args = parser.parse_args()
    if platform.system() != "Linux":
        parser.error("Run on the original Linux build host; another host cannot prove original package ownership.")
    info = json.loads(args.build_info.read_text(encoding="utf-8"))
    if info["system"] != "Linux":
        parser.error("Build-info does not identify a Linux build.")
    if any(args.output.resolve().is_relative_to(args.build_info.parent.resolve() / bundle)
           for bundle in ("VISOR", "VISOR.app")):
        parser.error("Review evidence must stay outside the frozen app.")
    report = collect_system_review(args.toc, info, args.output)
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
