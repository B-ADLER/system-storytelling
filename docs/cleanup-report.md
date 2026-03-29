# Repository cleanup report

**Note:** Historical maintenance log only. The repository’s **supported pipeline** is video assembly only (see `README.md`); it does **not** include PPTX generation.

Applied after the legacy-root audit. Date: repository maintenance pass.

## Folders removed

| Path | Reason |
|------|--------|
| `assets/` (repo root) | Non-canonical duplicate of episode `assets/`; scripts only use `episodes/<id>/assets/`. |
| `assets/audio/`, `assets/slides/`, `assets/preview/` | Removed with root `assets/`. |
| `presentation/` (repo root) | Empty legacy folder; canonical video output is `dist/<episode-id>/presentation.mp4`. |

## Files migrated

| From | To |
|------|-----|
| `assets/slides/slide1.png` … `slide4.png` | `docs/images/preview/slide-01.png` … `slide-04.png` |

Canonical slide rasters for **`build_video.py`** were already present under `episodes/001-system-storytelling/assets/slides/`; the root PNGs used non-contract names and were preserved only as optional preview stills.

**Not migrated (redundant / empty):**

- `assets/audio/.keep` — episode audio lives under `episodes/001-system-storytelling/assets/audio/`.
- `assets/preview/.keep` — no public images; nothing to move.

## Configuration

- **`.gitignore`** now includes: `dist/`, `__pycache__/`, `*.pyc`, `.venv/`, `venv/`.

## README and doc path fixes

- **Root `README.md`:** Replaced `presentation/presentation.mp4` link with instructions for `dist/001-system-storytelling/presentation.mp4` and note that `dist/` is gitignored. Clarified `episodes/<episode-id>/` prefixes for `raw/ppt-export`, `assets/slides`, workflow steps; noted optional `docs/images/preview/`; repository tree lists `dist/` as gitignored.
- **`episodes/README.md`:** Clarified paths relative to episode vs `dist/` at repo root.
- **`episodes/001-system-storytelling/raw/ppt-export/README.md`:** Output path points to episode `assets/slides/` (relative path `../../assets/slides/` from this folder).
- **`docs/ARCHITECTURE.md`:** Episode contract table, raw/normalize narrative, pipeline step 3, `normalize_slides` comment; added `docs/images/preview/` to folder tree.
- **`docs/system-contracts.md`**, **`docs/validation-spec.md`:** Execution and raw paths use full `episodes/<episode-id>/…` where shorthand was ambiguous.
- **`scripts/normalize_slides.py`:** Module docstring aligned with episode-relative paths.
- **`scripts/validate_episode.py`:** `validate_strict_assets` docstring clarifies episode-scoped assets.

## Final canonical root structure

```text
system-storytelling-presentation/
├─ .gitignore
├─ README.md
├─ requirements.txt
├─ docs/
├─ episodes/
├─ scripts/
├─ templates/
└─ dist/                 # local only when built; ignored by git
```

No repo-root `assets/` or `presentation/`.
