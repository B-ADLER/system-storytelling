

# System Storytelling — Contract-Driven Video Assembly

A deterministic **presentation-to-video** pipeline: declared structure and motion cues, exported **PNG** slides, externally produced **MP3** narration, then **validation** and **FFmpeg** assembly into a single **MP4**. The same ideas as in distributed systems apply here: **contracts, validation, and controlled execution**.

**Narrated video:** run `python scripts/build_video.py 001-system-storytelling`, then open **`dist/001-system-storytelling/<video_name>.mp4`** (default `presentation.mp4` from `episode.yaml`). (`dist/` is gitignored; attach binaries via a release or host a clip if you need a public file.)

## At a glance

**Input**

- Slide images (PNG)
- Narration audio (MP3)
- YAML / Markdown definitions

**Process**

- **`normalize → validate → build_video`** — skip `normalize_slides.py` when PNGs are written directly to `episodes/<episode-id>/assets/slides/`.

**Output**

- **`dist/<episode-id>/<video_name>.mp4`** (FFmpeg)

**Manual (outside repo)**

- Slide authoring (e.g. PowerPoint)
- Audio generation (e.g. ElevenLabs)

> If you use raw PNG exports under `raw/ppt-export/`, run **`normalize_slides.py` before `validate_episode.py --strict-assets`** so slide files exist at the canonical paths first.

## Repository truth

**Source of truth:** **`episodes/<episode-id>/`** — intent (`episode.yaml`, `slides.yaml`, `motion-cues.yaml`, `narration.md`) and execution assets under **`assets/`**.

**Validation:** required before assembly — **`scripts/validate_episode.py`**.

**Output:** **`dist/<episode-id>/<video_name>.mp4`** (default **`presentation.mp4`** via `episode.yaml` → `build.video_name`).

**Supported by this repository**

- Normalize slide PNGs (optional) — `scripts/normalize_slides.py`
- Validate episode structure and assets — `scripts/validate_episode.py`
- Assemble narrated MP4 with FFmpeg — `scripts/build_video.py`

**Not supported**

- Building PPTX or any other editable deck format from this repo
- Exporting PDF (or other deliverables) from this repo
- Authoring slide visuals inside the repository

**Allowed manual external work**

- Design slides in PowerPoint or another tool
- Export PNGs externally
- Generate narration externally (e.g. TTS)

Slides may be authored **externally** in PowerPoint or another tool, then exported as PNGs for this repository. That authoring step is **not** part of the supported build pipeline here—only **normalization, validation, and video assembly** are.

---

## Why this exists

Modern systems don’t fail where the issue starts. They fail where the signal becomes visible.

This project demonstrates that idea through both **storytelling** and a **working system**:

- surface issue → broken output  
- deeper cause → contract violation  
- root cause → mismatch between intent and reality  

---

## Core idea

This is a **deterministic presentation-to-video system**: a **controlled pipeline** where structure is declared (`slides.yaml`, `motion-cues.yaml`, `narration.md`), **reality** is slide PNGs and narration MP3s on disk, validation reconciles intent and reality, and **assembly** runs only when the system is valid.

**Authoring (outside this repo’s scripts):** see **Allowed manual external work** above. This repository **validates** on-disk assets and **assembles** the final MP4 deterministically; it does **not** build PPTX or run slide design tools.

---

## Demo

**Watch:** LinkedIn — https://www.linkedin.com/feed/update/urn:li:activity:7444269728962977792/)


**Local:** after `build_video.py`, open **`dist/001-system-storytelling/<video_name>.mp4`** (default `presentation.mp4`).

---

## Repository structure

```text
system-storytelling-presentation/
├─ episodes/      # per episode: YAML, narration, assets/slides, assets/audio, optional raw/ppt-export
├─ dist/          # generated only (gitignored): <video_name>.mp4 only
├─ scripts/       # normalize_slides, validate_episode, build_video (no PPTX generation)
├─ docs/          # contracts + validation rules; optional images under docs/images/
├─ templates/     # optional local files only; not read by any script in this pipeline
├─ LICENSE        # MIT — scripts
├─ LICENSE-CONTENT # CC BY 4.0 — episodes, docs prose, bundled media
└─ README.md
```

**Slide rasters** live under **`episodes/<episode-id>/assets/slides/`** (normalized names). Optional **raw PNG export folder** (e.g. files saved from an external tool) may sit in **`episodes/<episode-id>/raw/ppt-export/`** and are copied into **`assets/slides/`** via **`scripts/normalize_slides.py`** (see `docs/system-contracts.md`). **`dist/`** holds **only** rendered **`*.mp4`** — not PPTX or PDF.

Optional marketing stills (not assembly inputs) may live under **`docs/images/preview/`**.

---

## Workflow

Canonical pipeline: **`normalize → validate → build_video`**. Omit **`normalize_slides.py`** when PNGs are already in **`assets/slides/`** with contract names. **Validation must pass before `build_video.py`.** If you use **`raw/ppt-export/`**, run **`normalize_slides.py` before `validate_episode.py --strict-assets`**.

### 1. Define an episode

```text
episodes/<episode-id>/
```

Includes `slides.yaml`, `narration.md`, `motion-cues.yaml`, `episode.yaml`, slide PNGs under `assets/slides/` (after export/normalize), and narration MP3s under `assets/audio/`.

### 2. (Optional) Normalize slide PNGs

If you exported from PowerPoint into `episodes/<episode-id>/raw/ppt-export/`:

```bash
python scripts/normalize_slides.py <episode-id>
```

Requires `episodes/<episode-id>/raw/ppt-export/manifest.txt` (see script docstring). Skip if you write directly to `episodes/<episode-id>/assets/slides/`.

### 3. Validate

```bash
python scripts/validate_episode.py <episode-id>
```

Before video, run with **`--strict-assets`** to check PNG/audio naming. Any **ERROR** blocks assembly.

### 4. Assemble video

```bash
python scripts/build_video.py <episode-id>
```

Output: **`dist/<episode-id>/<video_name>.mp4`** (default **`presentation.mp4`** from `episode.yaml` → `build.video_name`).

---

## Validation rules (summary)

| Condition              | Result  |
|------------------------|---------|
| Missing required assets| ERROR   |
| Sequence gaps          | ERROR   |
| Invalid naming / mode  | ERROR   |
| Extra or unused files  | WARNING |
| Narration mismatch     | WARNING |

- **ERROR → blocks assembly**
- **WARNING → allowed**

---

## Example validation output

```text
[ERROR] Slide 2: expected 3 steps, found 2 audio files
[ERROR] Slide 2: missing slide-002-03.png
[WARNING] Slide 3: unused audio file 003-extra.mp3
```

---

## What this demonstrates

- distributed systems thinking  
- debugging depth and root cause analysis  
- contract-driven design  
- validation-first execution  
- technical storytelling  

---

## Requirements

- **Python** 3.x
- **FFmpeg** (must be available on `PATH`)

On Windows, use **`py -3`** instead of **`python`** if `python` is not on PATH.

```bash
pip install -r requirements.txt
```

## Guarantees

- Deterministic output for same inputs.
- Fails fast on contract violations.
- No partial builds.

---

## Reference

- `docs/system-contracts.md`
- `docs/validation-spec.md`
- `docs/ARCHITECTURE.md`

---

## Notes

Manual by design (external; not performed by repo scripts):

- slide design and PNG export (any external tool)
- placing files under `raw/ppt-export/` or directly under `assets/slides/`
- narration production (record or TTS outside this repo)
- fine timing beyond segmented audio

---

## License

**Code** (`scripts/`): [MIT License](LICENSE)

**Content** (episodes, docs prose, bundled slide/audio assets): [CC BY 4.0](LICENSE-CONTENT)

Commercial use is allowed with **attribution to Björn Adler**.
