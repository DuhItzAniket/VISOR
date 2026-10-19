"""Desktop entry point, including diagnostics for bundled startup checks."""

import json
import sys
import traceback
from pathlib import Path


def launch() -> int:
    try:
        from visor.app import main

        return main()
    except Exception:  # Include bootstrap failures in bundled check evidence.
        if "--smoke-check" not in sys.argv:
            raise
        index = sys.argv.index("--smoke-check")
        if index + 1 >= len(sys.argv):
            raise
        report_path = Path(sys.argv[index + 1])
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps({"success": False, "stage": "bootstrap", "error": traceback.format_exc()}, indent=2), encoding="utf-8")
        return 1


if __name__ == "__main__":
    raise SystemExit(launch())

