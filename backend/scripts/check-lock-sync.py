#!/usr/bin/env python3
"""Ensure backend/requirements.txt direct pins exist in requirements.lock.txt."""

from __future__ import annotations

from pathlib import Path
import sys


def _parse_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            continue
        name, version = line.split("==", 1)
        base_name = name.split("[", 1)[0].strip().lower()
        pins[base_name] = version.strip()
    return pins


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    req_path = repo_root / "backend" / "requirements.txt"
    lock_path = repo_root / "backend" / "requirements.lock.txt"

    direct = _parse_pins(req_path)
    locked = _parse_pins(lock_path)

    mismatches: list[str] = []
    for package, version in sorted(direct.items()):
        locked_version = locked.get(package)
        if locked_version != version:
            mismatches.append(
                f"{package}: requirements.txt={version}, requirements.lock.txt={locked_version or 'missing'}"
            )

    if mismatches:
        print("Dependency lock mismatch detected:", file=sys.stderr)
        for line in mismatches:
            print(f"  - {line}", file=sys.stderr)
        print(
            "Regenerate lock file with: ./backend/scripts/lock-requirements.sh",
            file=sys.stderr,
        )
        return 1

    print("requirements.lock.txt is in sync with requirements.txt direct pins.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
