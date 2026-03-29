# Validation Specification

This document defines the authoritative validation rules for the System Storytelling **presentation-to-video** pipeline (PNG slides, MP3 narration, FFmpeg → MP4). All validation must be minimal, strict, and deterministic. No auto-correction is permitted. This is the single reference for validation behavior.

Validation exists to gate **video assembly** only: YAML presence and shape, narration anchors, canonical PNG/MP3 naming (single vs step mode), consistency with `build_video.py`’s `discover_slide_plan`, and motion-cue coverage. It does **not** validate or enable any **PPTX** (or other deck) build target — this repository does not have one.

---

## Purpose of Validation
- Ensure that the declared INTENT (`slides.yaml`) matches the REALITY (assets/files) **for MP4 assembly**.
- Detect and report all discrepancies before any assembly.
- Guarantee deterministic, production-grade video outputs.

---

## Intent vs Reality Model
- **INTENT:** Defined by `slides.yaml` (slide structure, order, references).
- **REALITY:** All assets/files present (images, audio, narration, etc.).
- **VALIDATION:** Reconciliation of INTENT and REALITY. All mismatches are reported.

---

## Validation layers (no auto-fix)

Validation **never** renames, copies, or deletes files.

1. **YAML and narrative** — `episode.yaml`, `slides.yaml`, `motion-cues.yaml`, `narration.md` structure and anchors. **ERROR** when required keys or anchors are missing or invalid.
2. **Execution assets** — `episodes/<episode-id>/assets/slides/` and `episodes/<episode-id>/assets/audio/` vs single/step naming rules (`discover_slide_plan` in `build_video.py`). **ERROR** when assembly cannot run; mismatches block assembly.
3. **Raw vault (optional)** — `episodes/<episode-id>/raw/ppt-export/` may be checked when present. **WARNING** only (e.g. folder exists but contains no ingestible source files). Never **ERROR** on raw alone; raw is not consumed during assembly.

---

## Severity Model
- **ERROR:** Blocks assembly. Must be fixed before proceeding.
- **WARNING:** Does not block assembly. Advisory only.

---

## Full-Report Behavior
- Validation must always produce a full report of all detected issues (ERROR and WARNING) in a single run.
- No assembly may proceed if any ERROR is present.

---

## Validation Rules

### Single Mode
- Each slide must have exactly one image (`slide-NNN.png`) and one audio file (`NNN.mp3`).
- No step images or step audio files may exist for slides in single mode.
- **ERROR:** Missing or extra/misnamed required files, or presence of step assets.

### Step Mode
- Each slide in step mode must have a sequence of images (`slide-NNN-SS.png`) and audio files (`NNN-SS.mp3`) with no gaps in numbering.
- No single-mode image (`slide-NNN.png`) may exist for slides in step mode.
- **ERROR:** Missing required step files, sequence gaps, or presence of single-mode assets.

### Missing Required Files
- Any required file (image, audio, narration) referenced by `slides.yaml` must exist and be readable.
- **ERROR:** Missing required file.

### Extra Files
- Any file in the asset directories not referenced by `slides.yaml` is considered extra.
- **WARNING:** Extra/unreferenced file.

### Sequence Gaps (Step Mode)
- Step indices must be contiguous and start at 01. Any missing index is a gap.
- **ERROR:** Sequence gap in step assets.

### Ambiguous Asset States
- A slide must be in either single mode or step mode, never both. Mixed assets are not allowed.
- **ERROR:** Ambiguous or conflicting asset state.

### Naming Mismatches
- All asset files must strictly follow the naming conventions defined by the mode.
- **ERROR:** Misnamed file that cannot be matched to a slide or step.

### Narration Mismatches
- If a slide references a narration block that does not exist, or vice versa, but the required audio file exists, this is a mismatch.
- **WARNING:** Narration mismatch (advisory only).
- If narration is required for an assembly step and missing, this is an ERROR.

---

## Example Validation Outputs

- [ERROR] Slide 2: expected 3 step audio files, found 2
- [ERROR] Slide 2: missing slide-002-03.png
- [ERROR] Slide 4: ambiguous asset state (both slide-004.png and slide-004-01.png present)
- [WARNING] Slide 3: unreferenced audio file 003-extra.mp3
- [WARNING] Slide 5: narration block n05 not referenced by any slide

---

## Assembly behavior
- Video assembly must not proceed if any ERROR exists in the validation report.
- Assembly may proceed if only WARNINGS exist.

---

This specification is minimal, strict, and authoritative. All contributors and scripts must comply fully. Any deviation is an error and must be corrected before proceeding.

---

## Execution Integration

- **Validation is a required step before video assembly.**
- No assembly script (e.g., `build_video.py`) should be run unless validation has completed and returned no ERROR.
- If validation returns any ERROR, assembly must abort immediately.
- Validation can be run independently at any time for debugging or asset preparation.

### Recommended Command Order

1. `normalize_slides.py` (optional, when using `episodes/<id>/raw/ppt-export/` — run before strict asset checks)
2. `validate_episode.py` (use `--strict-assets` before video to check `episodes/<id>/assets/slides/` + audio)
3. `build_video.py` (after successful validation)

### Minimal CLI Expectations

- `validate_episode.py` must:
	- Scan intent (`slides.yaml`) vs reality (assets/files)
	- Output a full report of all issues (ERROR and WARNING)
	- Exit with non-zero status code if any ERROR is present

**Validation is not optional. All video assembly must be gated by successful validation.**
