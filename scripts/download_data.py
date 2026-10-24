"""Download (or re-download with --force) every pinned source file and verify its checksum.

Usage:  python scripts/download_data.py [--force]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.constants import SOURCES  # noqa: E402
from utils.io import fetch_and_cache, sha256  # noqa: E402

if __name__ == "__main__":
    force = "--force" in sys.argv
    for key, src in SOURCES.items():
        path = fetch_and_cache(key, force=force)
        ok = sha256(path) == src["sha256"]
        print(f"{'OK ' if ok else 'BAD'} {key:<14} {path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}")
        if not ok:
            sys.exit(f"Checksum mismatch for {key}")
