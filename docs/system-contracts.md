# System Contracts

This document defines the authoritative contracts for the System Storytelling **presentation-to-video** pipeline: exported **PNG** slides, externally produced **MP3** narration, validation, and deterministic **FFmpeg** assembly to **MP4**. All contributors and users must adhere strictly to these rules. Ambiguity is eliminated; this is the single source of truth for the system.

**Scope:** These contracts cover **intent files** (`episode.yaml`, `slides.yaml`, `motion-cues.yaml`, `narration.md`), **normalized slide rasters**, **audio assets**, **validation**, and **MP4 assembly** only. They do **not** cover building **PPTX**, exporting **PDF**, or authoring slide graphics **inside** this repository — those are external concerns.

---

## Layering (intent, execution, raw vault)

| Layer | Role |
|-------|------|
| **Intent** | `slides.yaml` — what the episode should contain (slide order, ids, narration refs). Optional future per-slide hints may be added; files on disk remain execution truth for step counts unless specified otherwise. |
| **Execution reality** | `episodes/<episode-id>/assets/slides/` (normalized PNGs) and `episodes/<episode-id>/assets/audio/` — what **`build_video.py`** consumes. Naming must match [validation-spec.md](validation-spec.md). |
| **Raw vault** | `episodes/<episode-id>/raw/ppt-export/` — optional, **immutable** dumps from PowerPoint (or other tools). **`build_video.py` never reads this folder.** Ingestion is a separate **normalization** step into `episodes/<episode-id>/assets/slides/`. |

Slide images are **author-produced** (export, design), not generated from YAML by code. They are **aligned** to `slides.yaml` by naming and validation, not compiled from it.

---

## 1. SOURCE OF TRUTH CONTRACT

### slides.yaml
- **Source of Truth:** YES
- **Derived:** No
- **Optional:** No
- **Notes:** All slide structure, order, and references originate here. All other assets must align with this file.

### narration.md
- **Source of Truth:** No
- **Aligned to slides.yaml:** Yes — written to match `narration_ref` anchors in `slides.yaml`
- **Optional:** No
- **Notes:** Narration blocks must match references in slides.yaml. Narration is required for each slide with a narration_ref.

### Audio Files (e.g., NNN.mp3)
- **Source of Truth:** No
- **Derived:** Yes (from slides.yaml and narration.md)
- **Optional:** No
- **Notes:** Audio is **produced outside** this repository (record, TTS, etc.). Each slide requiring narration must have a corresponding file on disk under `assets/audio/`, named by slide index. Silence is only allowed if explicitly specified in motion-cues.yaml.

### Slide Images (e.g., slide-NNN.png)
- **Source of Truth:** No
- **Derived:** No (author export + normalization)
- **Optional:** No (for video)
- **Notes:** Canonical rasters live under **`episodes/<episode-id>/assets/slides/`** with contract names. Optional raw exports sit in **`raw/ppt-export/`** (under the same episode) and are copied or mapped into `assets/slides/` via `normalize_slides.py` or manual steps—never edit raw in place for assembly consumption.

If unclear, the safest model is: **slides.yaml is always the source of truth. All other assets are derived and required unless explicitly marked optional in this document.**

---

## 2. EXECUTION ORDER CONTRACT

1. **slides.yaml** must exist and be complete first.
2. **narration.md** is created or updated to match slides.yaml.
3. **Audio files** are recorded or generated to match narration.md and slides.yaml.
4. **Slide images:** place exports in **`episodes/<episode-id>/raw/ppt-export/`** (optional) or directly prepare **`episodes/<episode-id>/assets/slides/`**; if using raw, run **normalization** (`normalize_slides.py`) so **`assets/slides/`** under that episode matches naming rules.
5. **Validate** — run **`validate_episode.py`** (required before assembly; use **`--strict-assets`** before video).
6. **`build_video.py`** is run, consuming that episode’s **`assets/slides/`**, **`assets/audio/`**, and YAML—**not** `raw/`.

**Dependencies:**
- slides.yaml → narration.md → audio files → normalized slide images → **validate** → video assembly
- Nothing is assembled until all required assets exist and are validated.

---

## 3. MODE CONTRACT

### Single Mode
- **Definition:** Each slide uses a single image (slide-NNN.png) and a single audio file (NNN.mp3).
- **Naming Rules:**
  - Images: slide-NNN.png (NNN = zero-padded slide index)
  - Audio: NNN.mp3
- **Allowed Combinations:**
  - For each slide, exactly one image and one audio file.
- **Invalid States:**
  - Presence of step images (slide-NNN-01.png, etc.) or step audio files.
  - Missing image or audio for any slide.

### Step Mode
- **Definition:** A slide is split into multiple steps, each with its own image and audio file.
- **Naming Rules:**
  - Images: slide-NNN-SS.png (NNN = slide index, SS = step index, both zero-padded)
  - Audio: NNN-SS.mp3
- **Allowed Combinations:**
  - For each step, exactly one image and one audio file.
  - No slide-NNN.png present for slides in step mode.
- **Invalid States:**
  - Both slide-NNN.png and slide-NNN-01.png exist for the same slide.
  - Step images or audio missing for any defined step.

**General:**
- A slide must be in either single mode or step mode, never both.
- All assets must match the mode strictly.

---

## 4. VALIDATION RULES

### slides.yaml
- **Validation:** Must exist, be valid YAML, and define all slides with unique, sequential indices.
- **Error:** "slides.yaml missing, invalid, or contains duplicate/missing slide indices."

### narration.md
- **Validation:** Must exist. For each slide with a narration_ref, a matching narration block must exist.
- **Error:** "narration.md missing or narration_ref mismatch for slide NNN."

### Audio Files
- **Validation:** For each slide (or step), a corresponding audio file must exist and be readable. No extra or missing files.
- **Error:** "Audio file missing or misnamed for slide NNN (or step SS)."

### Slide Images
- **Validation:** For each slide (or step), a corresponding image file must exist and be readable. No extra or missing files. Mode rules must be strictly enforced.
- **Error:** "Slide image missing, misnamed, or mode conflict for slide NNN."

### Mode Contract
- **Validation:** For each slide, enforce single or step mode strictly. Never both. No mixed assets.
- **Error:** "Mode conflict: both single and step assets present for slide NNN."

### Execution Order
- **Validation:** No video assembly is allowed until all above validations pass.
- **Error:** "Assembly blocked: required assets missing or invalid."

---

This document is the single reference for all contracts in this system. All contributors must follow these rules. Any deviation is an error and must be corrected before proceeding.
