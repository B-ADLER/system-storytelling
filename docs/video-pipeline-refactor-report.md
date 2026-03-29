# Video-only pipeline refactor report

> **Historical note:** This file is an **audit log** of a past refactor. **PPTX generation was removed** from the repository; tables below describe what changed at that time, **not** current supported behavior. For the live contract, see `README.md` and `docs/ARCHITECTURE.md`.

Refactor to remove editable-deck generation and align the repository with a **presentation-to-video** path: PNG + MP3 in, validated, FFmpeg MP4 out.

## Removed files

| Path |
|------|
| `scripts/build_pptx.py` |

## Updated files

| Path | Change summary |
|------|------------------|
| `requirements.txt` | Removed `python-pptx`; kept `PyYAML` only. |
| `scripts/validate_episode.py` | Dropped `template_id` from required `episode.yaml` keys. |
| `scripts/build_video.py` | Docstring: external authoring/export and audio; episode-relative audio path note. |
| `episodes/001-system-storytelling/episode.yaml` | Removed `template_id` and `build.pptx_name`; kept `build.video_name`. |
| `README.md` | Video-only narrative, workflow, terminology (external authoring, PNG export, TTS). |
| `episodes/README.md` | Output is MP4 only; removed `build_pptx` step. |
| `docs/ARCHITECTURE.md` | Folder tree, episode schema, pipeline, cues, boundaries; no deck output. |
| `docs/system-contracts.md` | Pipeline definition, audio provenance, execution order, `build_video.py` wording. |
| `docs/validation-spec.md` | Scope line, command order, assembly wording. |
| `templates/README.md` | Optional local authoring only; scripts do not read this folder. |

## Confirmation: substring audit (at time of refactor)

Searched the repository (case-insensitive) for: `pptx`, `PPTX`, `deck.pptx`, `build_pptx`, `python-pptx`, `template_id`, `channel_master`, excluding **this** report file (which documents what was removed).

**Result:** no matches in `scripts/`, `episodes/`, `docs/` (other than this file), `README.md`, `requirements.txt`, or `templates/README.md`. Colloquial English (“deck” as in presentation) may still appear. **PowerPoint** and the folder name **`ppt-export`** remain only as descriptions of authoring / export, not generated Office output.

## Final system definition (summary)

| Stage | Role |
|-------|------|
| **Input** | Exported slide **PNGs** (normalized under `episodes/<id>/assets/slides/`), narration **MP3s** (`assets/audio/`), plus YAML/Markdown intent. |
| **Authoring** | Slides designed externally (e.g. **PowerPoint**); narration produced externally (record / **TTS**). |
| **Processing** | `normalize_slides.py` (optional) → `validate_episode.py` → `build_video.py`. |
| **Output** | Single **MP4** per episode under `dist/<episode-id>/` via **`build_video.py`** + FFmpeg. |

No script writes an editable slide-deck file; **video is the only automated artifact.**
