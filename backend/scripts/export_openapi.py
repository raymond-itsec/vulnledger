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
    # Help local and CI callers by defaulting PYTHONPATH to backend root when
    # invoked from repo root without extra environment setup.
    if "PYTHONPATH" not in os.environ:
        repo_root = Path(__file__).resolve().parents[2]
        backend_root = repo_root / "backend"
        os.environ["PYTHONPATH"] = str(backend_root)
    raise SystemExit(main())
