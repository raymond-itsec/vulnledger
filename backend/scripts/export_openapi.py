#!/usr/bin/env python3
"""Export backend OpenAPI schema to a JSON file.

Usage:
  python backend/scripts/export_openapi.py backend/openapi.generated.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

# Ensure imports like `from app.main import app` work both locally and in CI,
# even when invoked from repo root without external PYTHONPATH setup.
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: export_openapi.py <output-path>", file=sys.stderr)
        return 2

    output_path = Path(sys.argv[1]).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Import lazily so env can still be overridden at invocation time.
    from app.main import app  # noqa: WPS433

    schema = app.openapi()
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=True, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Wrote OpenAPI schema to {output_path}")
    return 0


if __name__ == "__main__":
    # Keep PYTHONPATH aligned for any subprocesses that may rely on it.
    if "PYTHONPATH" not in os.environ:
        os.environ["PYTHONPATH"] = str(BACKEND_ROOT)
    raise SystemExit(main())
