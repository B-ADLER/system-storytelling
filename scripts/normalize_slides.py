#!/usr/bin/env python3
"""
Copy slide PNGs from episodes/<id>/raw/ppt-export/ to episodes/<id>/assets/slides/ using a manifest.

Does not read raw/ in build_video — this is the explicit normalization step.

Manifest path: episodes/<episode-id>/raw/ppt-export/manifest.txt

Format (one mapping per line):
  <source_filename> <target_filename>

- Lines starting with # and empty lines are ignored.
- Source files are relative to raw/ppt-export/; targets are relative to the episode’s assets/slides/.
- Target names must match build contract: slide-NNN.png or slide-NNN-TT.png

Example:
  Slide1.PNG slide-001.png
  Slide2.PNG slide-002-01.png
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EPISODES = REPO_ROOT / "episodes"


def resolve_episode_dir(arg: str) -> Path:
    p = Path(arg)
    if p.is_dir():
        return p.resolve()
    d = EPISODES / arg
    if d.is_dir():
        return d.resolve()
    raise FileNotFoundError(f"Episode not found: {arg}")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Copy PNGs from raw/ppt-export to assets/slides per manifest.txt"
    )
    p.add_argument("episode", help="Episode id or path")
    args = p.parse_args()

    try:
        episode_dir = resolve_episode_dir(args.episode)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    raw_dir = episode_dir / "raw" / "ppt-export"
    manifest = raw_dir / "manifest.txt"
    out_dir = episode_dir / "assets" / "slides"

    if not manifest.is_file():
        print(
            f"error: missing {manifest.relative_to(REPO_ROOT)}",
            file=sys.stderr,
        )
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    lines = manifest.read_text(encoding="utf-8").splitlines()
    n = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            print(f"error: manifest line must be two tokens: {line!r}", file=sys.stderr)
            return 1
        src_name, dst_name = parts
        src = raw_dir / src_name
        dst = out_dir / dst_name
        if not src.is_file():
            print(f"error: missing source file {src.relative_to(REPO_ROOT)}", file=sys.stderr)
            return 1
        shutil.copy2(src, dst)
        print(f"copied {src_name} -> {dst.relative_to(REPO_ROOT)}")
        n += 1

    if n == 0:
        print("error: manifest has no copy directives", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
