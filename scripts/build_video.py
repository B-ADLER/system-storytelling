#!/usr/bin/env python3
"""
Assemble dist/<episode-id>/<video_name>.mp4 from slide PNGs + segmented MP3 via FFmpeg.
Slide images are expected from an external authoring/export step (e.g. PowerPoint → PNG).
Narration MP3s are expected from an external recorder or TTS; this script only muxes/times video.

Requires FFmpeg on PATH.

Slide rasters (canonical input): episodes/<episode-id>/assets/slides/

Slide assets (per slide index NNN = 001, 002, … matching slides.yaml order):
- Single mode: slide-NNN.png + episodes/<episode-id>/assets/audio/NNN.mp3 (or silent hold per motion-cue).
- Step mode: slide-NNN-01.png … slide-NNN-KK.png + NNN-01.mp3 … NNN-KK.mp3 (no slide-NNN.png).
  Steps concatenate with stream copy (cuts). Never both slide-NNN.png and slide-NNN-01.png.

Cue behavior (slide-level; applied between combined slide clips):
- fade_in: first segment of the first slide only when that slide's cue is fade_in.
- fade_transition: crossfade when entering a slide whose cue is fade_transition.
- hold: single-image slide only — missing NNN.mp3 uses param.duration_s with silent audio.
- reveal_next, emphasis, none: no extra video effect on top of cuts/xfade above.

audio_mode single (one full.mp3) is not implemented; exit with message.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
EPISODES = REPO_ROOT / "episodes"
DIST = REPO_ROOT / "dist"

XFADE_SEC = 0.5


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_episode_dir(arg: str) -> Path:
    p = Path(arg)
    if p.is_dir():
        return p.resolve()
    d = EPISODES / arg
    if d.is_dir():
        return d.resolve()
    raise FileNotFoundError(f"Episode not found: {arg}")


def probe_duration(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(path),
    ]
    out = subprocess.check_output(cmd, text=True)
    return float(json.loads(out)["format"]["duration"])


def cue_map(episode_dir: Path) -> dict[str, dict]:
    m = load_yaml(episode_dir / "motion-cues.yaml")
    out: dict[str, dict] = {}
    for c in m.get("cues") or []:
        sid = c.get("slide_id")
        if sid:
            out[str(sid)] = c
    return out


def slide_order_ids(episode_dir: Path) -> list[str]:
    data = load_yaml(episode_dir / "slides.yaml")
    return [str(s["id"]) for s in data.get("slides") or []]


def count_step_images(slides_dir: Path, nnn: str) -> int:
    """Return K >= 1 when slide-NNN-01.png exists and TT runs 01..K consecutive."""
    k = 0
    tt = 1
    while (slides_dir / f"slide-{nnn}-{tt:02d}.png").is_file():
        k = tt
        tt += 1
    return k


def discover_slide_plan(
    slides_dir: Path,
    audio_dir: Path,
    n_slides: int,
) -> tuple[list[dict], list[str]]:
    """
    Returns (plan, errors).
    Each plan item: mode 'single' | 'steps', nnn, k_steps (1 for single), image paths, audio paths.
    """
    errors: list[str] = []
    plan: list[dict] = []

    for i in range(n_slides):
        nnn = f"{i + 1:03d}"
        p_single = slides_dir / f"slide-{nnn}.png"
        p_step1 = slides_dir / f"slide-{nnn}-01.png"

        if p_single.is_file() and p_step1.is_file():
            errors.append(
                f"slide {nnn}: cannot have both slide-{nnn}.png and slide-{nnn}-01.png"
            )
            continue

        if p_step1.is_file():
            k = count_step_images(slides_dir, nnn)
            if k < 1:
                errors.append(f"slide {nnn}: slide-{nnn}-01.png present but no consecutive steps")
                continue
            if (audio_dir / f"{nnn}.mp3").is_file():
                errors.append(
                    f"slide {nnn}: step mode must not use {nnn}.mp3 (use {nnn}-01.mp3 …)"
                )
                continue
            imgs = [slides_dir / f"slide-{nnn}-{t:02d}.png" for t in range(1, k + 1)]
            auds = [audio_dir / f"{nnn}-{t:02d}.mp3" for t in range(1, k + 1)]
            slide_errs: list[str] = []
            for a in auds:
                if not a.is_file():
                    slide_errs.append(f"missing audio for step: {a.relative_to(REPO_ROOT)}")
            errors.extend(slide_errs)
            if slide_errs:
                continue
            plan.append(
                {
                    "mode": "steps",
                    "nnn": nnn,
                    "k": k,
                    "images": imgs,
                    "audios": auds,
                }
            )
        elif p_single.is_file():
            bad_step_audio = False
            for t in range(1, 32):
                st = audio_dir / f"{nnn}-{t:02d}.mp3"
                if st.is_file():
                    errors.append(
                        f"slide {nnn}: single-image mode must not use {st.name} "
                        f"(use {nnn}.mp3 or switch to step PNGs)"
                    )
                    bad_step_audio = True
                    break
            if bad_step_audio:
                continue
            plan.append(
                {
                    "mode": "single",
                    "nnn": nnn,
                    "k": 1,
                    "images": [p_single],
                    "audios": [audio_dir / f"{nnn}.mp3"],
                }
            )
        else:
            errors.append(
                f"missing slide image: need slide-{nnn}.png or slide-{nnn}-01.png "
                f"under {slides_dir.relative_to(REPO_ROOT)}"
            )

    return plan, errors


def build_segment(
    image: Path,
    audio: Path | None,
    duration_s: float,
    out_mp4: Path,
    fade_in: bool,
) -> None:
    vf_base = (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24"
    )
    vf = vf_base + (",fade=t=in:st=0:d=0.4" if fade_in else "")

    if audio is not None and audio.is_file():
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-i",
            str(audio),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out_mp4),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-t",
            str(duration_s),
            str(out_mp4),
        ]
    subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)


def concat_segments_copy(segments: list[Path], out_mp4: Path) -> None:
    lst = out_mp4.parent / f"concat_{out_mp4.stem}.txt"
    lst.write_text("\n".join(f"file '{s.as_posix()}'" for s in segments) + "\n", encoding="utf-8")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(lst),
            "-c",
            "copy",
            str(out_mp4),
        ],
        check=True,
        stderr=subprocess.PIPE,
        text=True,
    )
    lst.unlink(missing_ok=True)


def merge_two(
    cur: Path,
    nxt: Path,
    out_path: Path,
    use_xfade: bool,
) -> None:
    if not use_xfade:
        concat_segments_copy([cur, nxt], out_path)
        return

    dur_cur = probe_duration(cur)
    offset = max(0.0, dur_cur - XFADE_SEC)
    filt = (
        f"[0:v][1:v]xfade=transition=fade:duration={XFADE_SEC}:offset={offset}[v];"
        f"[0:a][1:a]acrossfade=d={XFADE_SEC}[a]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(cur),
            "-i",
            str(nxt),
            "-filter_complex",
            filt,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out_path),
        ],
        check=True,
        stderr=subprocess.PIPE,
        text=True,
    )


def main() -> int:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("error: ffmpeg and ffprobe must be on PATH", file=sys.stderr)
        return 1

    p = argparse.ArgumentParser(description="Build presentation.mp4 for an episode.")
    p.add_argument("episode", help="Episode id or path")
    args = p.parse_args()

    try:
        episode_dir = resolve_episode_dir(args.episode)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1

    meta = load_yaml(episode_dir / "episode.yaml")
    episode_id = meta.get("id", episode_dir.name)
    build = meta.get("build") or {}
    video_name = build.get("video_name", "presentation.mp4")
    audio_mode = meta.get("audio_mode", "segmented")

    if audio_mode == "single":
        print(
            "error: audio_mode 'single' is not implemented "
            "(use segmented MP3: NNN.mp3 or step NNN-TT.mp3)",
            file=sys.stderr,
        )
        return 1

    dist_ep = DIST / episode_id
    slides_dir = episode_dir / "assets" / "slides"
    audio_dir = episode_dir / "assets" / "audio"

    slide_ids = slide_order_ids(episode_dir)
    n = len(slide_ids)
    if n == 0:
        print("error: no slides", file=sys.stderr)
        return 1

    plan, plan_errors = discover_slide_plan(slides_dir, audio_dir, n)
    if plan_errors:
        for e in plan_errors:
            print(f"error: {e}", file=sys.stderr)
        return 1
    if len(plan) != n:
        print("error: slide plan incomplete", file=sys.stderr)
        return 1

    cues_by_slide = cue_map(episode_dir)

    tmp = Path(tempfile.mkdtemp(prefix="build_video_"))
    try:
        slide_clips: list[Path] = []

        for si, sid in enumerate(slide_ids):
            entry = plan[si]
            cue = cues_by_slide.get(sid, {})
            cuetype = cue.get("cue", "none")
            step_segs: list[Path] = []

            if entry["mode"] == "single":
                img = entry["images"][0]
                ap = entry["audios"][0]
                if ap.is_file():
                    ap_use: Path | None = ap
                    dur = probe_duration(ap)
                elif cuetype == "hold":
                    param = cue.get("param") or {}
                    ds = param.get("duration_s")
                    if ds is None:
                        print(
                            f"error: missing audio {ap.relative_to(REPO_ROOT)} for slide {sid}; "
                            f"for hold without file set param.duration_s",
                            file=sys.stderr,
                        )
                        return 1
                    ap_use = None
                    dur = float(ds)
                else:
                    print(
                        f"error: missing audio {ap.relative_to(REPO_ROOT)} for slide {sid}",
                        file=sys.stderr,
                    )
                    return 1

                fade_in = si == 0 and cuetype == "fade_in"
                seg_out = tmp / f"slide_{si:03d}_step_000.mp4"
                build_segment(img, ap_use, dur, seg_out, fade_in=fade_in)
                slide_clips.append(seg_out)
                continue

            # steps mode: no hold-without-audio per step in v1
            for j, (img, ap) in enumerate(zip(entry["images"], entry["audios"], strict=True)):
                if not ap.is_file():
                    print(f"error: missing {ap.relative_to(REPO_ROOT)}", file=sys.stderr)
                    return 1
                dur = probe_duration(ap)
                fade_in = si == 0 and j == 0 and cuetype == "fade_in"
                seg_out = tmp / f"slide_{si:03d}_step_{j:03d}.mp4"
                build_segment(img, ap, dur, seg_out, fade_in=fade_in)
                step_segs.append(seg_out)

            if len(step_segs) == 1:
                slide_clips.append(step_segs[0])
            else:
                combined = tmp / f"slide_{si:03d}_combined.mp4"
                concat_segments_copy(step_segs, combined)
                slide_clips.append(combined)

        out_mp4 = dist_ep / video_name
        out_mp4.parent.mkdir(parents=True, exist_ok=True)

        if len(slide_clips) == 1:
            shutil.copy(slide_clips[0], out_mp4)
        else:
            use_xfade_between: list[bool] = []
            for i in range(1, n):
                sid = slide_ids[i]
                c = cues_by_slide.get(sid, {})
                use_xfade_between.append(c.get("cue") == "fade_transition")

            if not any(use_xfade_between):
                concat_segments_copy(slide_clips, out_mp4)
            else:
                cur = slide_clips[0]
                for i in range(1, n):
                    merged = tmp / f"merged_slide_{i:03d}.mp4"
                    merge_two(cur, slide_clips[i], merged, use_xfade=use_xfade_between[i - 1])
                    cur = merged
                shutil.copy(cur, out_mp4)

        print(f"wrote {out_mp4.relative_to(REPO_ROOT)}")
    except subprocess.CalledProcessError as e:
        print("error: ffmpeg failed", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
