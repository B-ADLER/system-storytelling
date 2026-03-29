# Architecture — v1

This repository is a **file-based presentation-to-video system**: each episode is a folder of YAML and Markdown **intent**; **execution reality** is normalized **PNG** slides and **MP3** narration under the episode; **`build_video.py`** assembles **`dist/<episode-id>/<video_name>.mp4`** with FFmpeg. Slide visuals are produced **outside** this repo (e.g. design in PowerPoint or another tool, then export PNGs); audio is produced **outside** these scripts (record or TTS). **No script builds PPTX, PDF, or other deck formats** — output is **MP4 only**.

See **[system-contracts.md](system-contracts.md)** for layering (intent vs execution vs raw vault).

## Folder structure

```text
system-storytelling-presentation/
├─ README.md
├─ requirements.txt
├─ docs/
│   ├─ ARCHITECTURE.md          # this file
│   ├─ system-contracts.md
│   └─ images/preview/          # optional stills for docs/readme; not consumed during assembly
├─ templates/
│   └─ README.md                # optional local files; not read by the pipeline
├─ episodes/
│   ├─ README.md
│   └─ <episode-id>/
│       ├─ episode.yaml
│       ├─ narration.md
│       ├─ slides.yaml
│       ├─ motion-cues.yaml
│       ├─ assets/
│       │   ├─ slides/          # canonical PNGs for build_video (normalized names)
│       │   └─ audio/
│       ├─ raw/
│       │   └─ ppt-export/    # optional raw PNG exports from external tools (not read by build_video)
│       └─ README.md
├─ dist/
│   └─ <episode-id>/          # generated: <video_name>.mp4 only (see episode.yaml build.video_name)
└─ scripts/
    ├─ normalize_slides.py    # optional: raw/ppt-export → episode assets/slides
    ├─ validate_episode.py
    └─ build_video.py
```

## Episode package contract

| Path | Role | Source / generated |
|------|------|-------------------|
| `episode.yaml` | Metadata and build hints (`build.video_name`) | **Source** (required) |
| `narration.md` | Full script; anchors `<!-- narration:nXX -->` | **Source** (required) |
| `slides.yaml` | Slide list and content | **Source** (required) |
| `motion-cues.yaml` | Cue list keyed by `slide_id` | **Source** (required) |
| `assets/slides/` | Normalized slide PNGs for `build_video.py` (under episode package) | **Source** (required for video) |
| `assets/audio/` | Segmented MP3 (see **Video assets** below; under episode package) | **Source** (required for video build when using segmented audio) |
| `raw/ppt-export/` | Optional vault for PowerPoint PNG exports before normalization (under episode package) | **Source** (optional; not consumed by `build_video.py`) |
| `dist/<episode-id>/` | Output at **repo root** (`<video_name>.mp4`) | **Generated** |

## `episode.yaml` schema

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | yes | Matches folder name |
| `title` | string | yes | Display title |
| `slug` | string | yes | URL-safe |
| `theme` | string | yes | e.g. `distributed-systems` |
| `audience` | string | yes | e.g. `senior engineers` |
| `thesis` | string | yes | One sentence |
| `status` | string | yes | `draft` \| `script_locked` \| `audio_ready` \| `video_ready` \| `published` |
| `duration_target_min` | number | yes | Target length in minutes |
| `draft_date` | string | no | ISO date |
| `publish_date` | string or null | no | ISO date |
| `tags` | list | yes | Short list |
| `links` | object | no | Optional: `youtube`, `linkedin_post`, `repo` |
| `source_post` | string or null | no | Link or id |
| `audio_mode` | string | yes | `segmented` (required for `build_video.py` in v1) \| `single` (reserved; not implemented in v1 — optional later) |
| `build` | object | no | Optional: `video_name` (default `presentation.mp4`) |

## `slides.yaml` schema

Top-level key `slides`: ordered list of objects:

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Unique in episode, e.g. `s01` |
| `type` | yes | `title` \| `content` \| `section` \| `diagram` \| `closing` |
| `title` | yes | Slide title |
| `body` | no | String or list of strings (bullets) |
| `visual_intent` | no | Short free text |
| `narration_ref` | yes | Anchor id, e.g. `n01` — must appear in `narration.md` |
| `motion_preset` | no | String; informational, aligns with motion vocabulary |
| `notes` | no | Speaker / production notes |

## `motion-cues.yaml` schema

Top-level key `cues`: list of objects:

| Field | Required | Notes |
|-------|----------|-------|
| `slide_id` | yes | Must exist in `slides.yaml` |
| `cue` | yes | See vocabulary below |
| `at` | no | `start` \| `end` (default `start`) |
| `param` | no | e.g. `duration_s` for `hold` |

### Allowed cue values (v1)

| `cue` | Meaning |
|-------|---------|
| `none` | No extra effect |
| `fade_in` | Fade in when entering slide (video: fade from black) |
| `fade_transition` | Crossfade from previous slide (video) |
| `reveal_next` | Staged reveal (authoring concept; video: same timing as `none` in v1) |
| `emphasis` | Highlight moment (authoring concept; video: same as `none` in v1) |
| `hold` | Hold duration; use `param.duration_s` if no audio for segment |

### Video assets (naming, no extra schema)

Slide order follows **`slides.yaml`**. For each slide index `NNN` (`001`, `002`, …), **execution reality** is under **`episodes/<episode-id>/assets/slides/`** (not `dist/`).

| Mode | PNGs under `assets/slides/` | Audio under `assets/audio/` |
|------|----------------------------|-----------------------------|
| **Single-image** | `slide-NNN.png` only | `NNN.mp3` (or silent `hold` via `motion-cues.yaml` as before) |
| **Multi-step** | `slide-NNN-01.png` … `slide-NNN-KK.png` consecutive | `NNN-01.mp3` … `NNN-KK.mp3` (same K) |

Never use both `slide-NNN.png` and `slide-NNN-01.png` for the same `NNN`. Do not mix `NNN.mp3` with step audio `NNN-TT.mp3` on the same slide. Step segments concatenate with **cuts**; **slide-level** transitions (`fade_transition`, etc.) apply between slides as before.

**Raw vs normalized:** Place exported slide PNGs into **`episodes/<episode-id>/raw/ppt-export/`** (unchanged filenames; e.g. from an external authoring tool). Run **`scripts/normalize_slides.py`** (or copy manually) to produce **`episodes/<episode-id>/assets/slides/`** with contract names. **`build_video.py` does not read `raw/`.**

Optional: `python scripts/validate_episode.py <episode-id> --strict-assets` checks episode `assets/slides/` and `assets/audio/` naming; may **warn** if `raw/ppt-export/` exists but is empty.

## Execution order (v1)

Supported scripts only: **`normalize_slides.py`** (optional) → **`validate_episode.py`** → **`build_video.py`**.

1. **Normalize (optional)** — If using `raw/ppt-export/`, run `python scripts/normalize_slides.py <episode-id>` so PNGs land in `episodes/<id>/assets/slides/` with contract names. Skip if PNGs are already there.  
2. **Validate** — `python scripts/validate_episode.py <episode-id>` (add `--strict-assets` before video to verify PNG/audio naming). **Must pass before assembly.**  
3. **Video** — `python scripts/build_video.py <episode-id>` → **`dist/<id>/<video_name>.mp4`** (**segmented clips only**; `audio_mode: single` / one `full.mp3` is still rejected.)

**Video build note:** When transitions do not use crossfade, `build_video.py` may concatenate segments with stream copy (`-c copy`). Crossfade (`xfade`) re-encodes with **H.264 / yuv420p / AAC** and **`+faststart`** for broad playback. Mixed segment encodings (e.g. silent `hold` vs. real audio) can occasionally make concat fail; if that happens, a future option is to re-encode instead of copy—out of scope for minimal v1.

## v1 boundaries

- **Not supported:** generating **PPTX** or other editable decks, **PDF** export, or **in-repo slide authoring** — out of scope; do those externally if needed.  
- No web UI, CI, database, YouTube API.  
- Video assembly uses **FFmpeg** (must be on `PATH`). **`build_video.py` supports `audio_mode: segmented` only** in v1; single-file narration is not built by this script yet.  
- Cues `reveal_next` and `emphasis` are **not** visually distinguished in automated video beyond documentation; treat like `none` unless you refine in post.
