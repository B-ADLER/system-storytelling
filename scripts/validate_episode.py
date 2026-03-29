#!/usr/bin/env python3
"""Validate an episode package (v1). Low dependency: PyYAML + stdlib."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
EPISODES = REPO_ROOT / "episodes"

REQUIRED_EPISODE_KEYS = (
    "id",
    "title",
    "slug",
    "theme",
    "audience",
    "thesis",
    "status",
    "duration_target_min",
    "tags",
    "audio_mode",
)

SLIDE_TYPES = frozenset({"title", "content", "section", "diagram", "closing"})
STATUSES = frozenset({"draft", "script_locked", "audio_ready", "video_ready", "published"})
AUDIO_MODES = frozenset({"segmented", "single"})
CUE_TYPES = frozenset({"none", "fade_in", "fade_transition", "reveal_next", "emphasis", "hold"})
CUE_AT = frozenset({"start", "end"})


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def err(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def resolve_episode_dir(arg: str) -> Path:
    p = Path(arg)
    if p.is_dir():
        return p.resolve()
    d = EPISODES / arg
    if d.is_dir():
        return d.resolve()
    raise FileNotFoundError(f"Episode not found: {arg}")


def validate_episode(episode_dir: Path) -> list[str]:
    errors: list[str] = []
    ep = episode_dir
    required_files = [
        ep / "episode.yaml",
        ep / "narration.md",
        ep / "slides.yaml",
        ep / "motion-cues.yaml",
    ]
    for f in required_files:
        if not f.is_file():
            errors.append(f"missing required file: {f.relative_to(REPO_ROOT)}")

    audio_dir = ep / "assets" / "audio"
    if not audio_dir.is_dir():
        errors.append(f"missing directory: {audio_dir.relative_to(REPO_ROOT)}")

    if errors:
        return errors

    meta = load_yaml(ep / "episode.yaml")
    for k in REQUIRED_EPISODE_KEYS:
        if k not in meta:
            errors.append(f"episode.yaml: missing key '{k}'")

    if "id" in meta and meta["id"] != episode_dir.name:
        errors.append(
            f"episode.yaml: id '{meta['id']}' must match folder name '{episode_dir.name}'"
        )

    if meta.get("status") not in STATUSES:
        errors.append(f"episode.yaml: invalid status '{meta.get('status')}'")

    if meta.get("audio_mode") not in AUDIO_MODES:
        errors.append(f"episode.yaml: invalid audio_mode '{meta.get('audio_mode')}'")

    slides_data = load_yaml(ep / "slides.yaml")
    if not isinstance(slides_data, dict) or "slides" not in slides_data:
        errors.append("slides.yaml: top-level key 'slides' (list) required")
        return errors

    slides = slides_data["slides"]
    if not isinstance(slides, list) or not slides:
        errors.append("slides.yaml: 'slides' must be a non-empty list")
        return errors

    slide_ids: list[str] = []
    narration_refs: list[str] = []
    for i, s in enumerate(slides):
        if not isinstance(s, dict):
            errors.append(f"slides.yaml: slides[{i}] must be an object")
            continue
        for req in ("id", "type", "title", "narration_ref"):
            if req not in s:
                errors.append(f"slides.yaml: slide index {i} missing '{req}'")
        if s.get("type") not in SLIDE_TYPES:
            errors.append(f"slides.yaml: slide {s.get('id', i)} invalid type '{s.get('type')}'")
        sid = s.get("id")
        if isinstance(sid, str):
            slide_ids.append(sid)
        nr = s.get("narration_ref")
        if isinstance(nr, str):
            narration_refs.append(nr)

    if len(slide_ids) != len(set(slide_ids)):
        errors.append("slides.yaml: duplicate slide id")

    motion = load_yaml(ep / "motion-cues.yaml")
    if not isinstance(motion, dict) or "cues" not in motion:
        errors.append("motion-cues.yaml: top-level key 'cues' (list) required")
        return errors

    cues = motion["cues"]
    if not isinstance(cues, list):
        errors.append("motion-cues.yaml: 'cues' must be a list")
        return errors

    slide_id_set = set(slide_ids)
    seen_cue_slides: set[str] = set()
    for i, c in enumerate(cues):
        if not isinstance(c, dict):
            errors.append(f"motion-cues.yaml: cues[{i}] must be an object")
            continue
        if "slide_id" not in c or "cue" not in c:
            errors.append(f"motion-cues.yaml: cue index {i} needs slide_id and cue")
            continue
        sid = c["slide_id"]
        if sid not in slide_id_set:
            errors.append(f"motion-cues.yaml: unknown slide_id '{sid}'")
        if sid in seen_cue_slides:
            errors.append(
                f"motion-cues.yaml: duplicate cue for slide_id '{sid}' (v1: one per slide)"
            )
        seen_cue_slides.add(sid)
        if c.get("cue") not in CUE_TYPES:
            errors.append(f"motion-cues.yaml: invalid cue '{c.get('cue')}' for slide_id '{sid}'")
        if "at" in c and c["at"] not in CUE_AT:
            errors.append(f"motion-cues.yaml: invalid at '{c.get('at')}' for slide_id '{sid}'")

    narr_path = ep / "narration.md"
    narr_text = narr_path.read_text(encoding="utf-8")
    for ref in narration_refs:
        token = f"<!-- narration:{ref} -->"
        if token not in narr_text:
            errors.append(
                f"narration.md: missing anchor {token} for narration_ref '{ref}' in slides.yaml"
            )

    for sid in slide_id_set:
        if sid not in seen_cue_slides:
            errors.append(f"motion-cues.yaml: no cue for slide_id '{sid}'")

    return errors


def _load_build_video_module():
    br = Path(__file__).resolve().parent / "build_video.py"
    spec = importlib.util.spec_from_file_location("build_video", br)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def validate_raw_vault_warnings(episode_dir: Path) -> list[str]:
    """Optional checks for raw/ppt-export (never ERROR)."""
    raw_dir = episode_dir / "raw" / "ppt-export"
    if not raw_dir.is_dir():
        return []
    skip = {".gitkeep", "manifest.txt", "README.md"}
    candidates = [
        f
        for f in raw_dir.iterdir()
        if f.is_file() and f.name not in skip and not f.name.startswith(".")
    ]
    if not candidates:
        return [
            f"raw/ppt-export at {raw_dir.relative_to(REPO_ROOT)} exists but has no "
            "source files to ingest (add PowerPoint exports or remove empty vault)"
        ]
    return []


def validate_strict_assets(episode_dir: Path) -> list[str]:
    """Validate slide/audio naming under episode assets/slides vs assets/audio (optional)."""
    errors: list[str] = []
    slides_dir = episode_dir / "assets" / "slides"
    audio_dir = episode_dir / "assets" / "audio"
    if not slides_dir.is_dir():
        errors.append(
            f"strict-assets: missing {slides_dir.relative_to(REPO_ROOT)} "
            "(add normalized PNGs or run scripts/normalize_slides.py from raw/ppt-export)"
        )
        return errors

    slides_data = load_yaml(episode_dir / "slides.yaml")
    slides = slides_data.get("slides") or []
    n = len(slides)
    if n == 0:
        errors.append("strict-assets: slides.yaml has no slides")
        return errors

    bv = _load_build_video_module()
    if bv is None:
        errors.append("strict-assets: could not load build_video.py")
        return errors

    _, plan_errs = bv.discover_slide_plan(slides_dir, audio_dir, n)
    for e in plan_errs:
        errors.append(f"strict-assets: {e}")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description="Validate v1 episode package.")
    p.add_argument("episode", help="Episode folder name (under episodes/) or path")
    p.add_argument(
        "--strict-assets",
        action="store_true",
        help="Also check episodes/<id>/assets/slides PNGs and assets/audio naming; raw/ppt-export warnings",
    )
    args = p.parse_args()

    try:
        episode_dir = resolve_episode_dir(args.episode)
    except FileNotFoundError as e:
        err(str(e))
        return 1

    errors = validate_episode(episode_dir)
    if errors:
        for e in errors:
            err(e)
        return 1

    if args.strict_assets:
        extra = validate_strict_assets(episode_dir)
        if extra:
            for e in extra:
                err(e)
            return 1
        for w in validate_raw_vault_warnings(episode_dir):
            warn(w)

    print(f"ok: {episode_dir.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
