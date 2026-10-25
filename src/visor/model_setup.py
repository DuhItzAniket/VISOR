"""Developer-only explicit optional model setup: python -m visor.model_setup --xfeat."""

from __future__ import annotations

import argparse
import subprocess
import sys

from visor.model_runtime import XFEAT_REVISION, install_xfeat


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xfeat", action="store_true", required=True)
    parser.parse_args()
    if getattr(sys, "frozen", False):
        print("Optional model setup is unavailable in this desktop distribution.", file=sys.stderr)
        return 1
    try:
        root = install_xfeat()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"XFeat setup failed: {exc}", file=sys.stderr)
        return 1
    print(f"XFeat {XFEAT_REVISION} ready at {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
