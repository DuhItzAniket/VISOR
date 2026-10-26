"""Compatibility entry point for VISOR's portable, CPU-default evaluator.

Use the same arguments as ``python -m visor.evaluate``. The old private-folder
CSV runner is retired; no dataset path or optional learned engine is implicit.
"""

from visor.evaluate import main

if __name__ == "__main__":
    raise SystemExit(main())
