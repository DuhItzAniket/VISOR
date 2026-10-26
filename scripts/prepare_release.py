"""Prepare validation assets/checksums without publishing or signing a release."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from visor.release_preparation import prepare_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/release-candidate")
    args = parser.parse_args()
    manifest = prepare_candidate(args.dist, args.output)
    print(json.dumps({"source_revision": manifest["source_revision"], "assets": len(manifest["files"]),
                      "output": str(args.output), "release_signing_verified": False}))


if __name__ == "__main__":
    main()
