# Episodes

Each subdirectory under `episodes/` is one **episode package**. Paths below are relative to `episodes/<episode-id>/`: **`assets/slides/`** (normalized PNGs), **`assets/audio/`** (MP3), optional **`raw/ppt-export/`** (raw PNG exports from an external tool; not read by `build_video.py`). Generated video goes to **`dist/<episode-id>/`** at the **repository root** as **`/<video_name>.mp4`** (from `episode.yaml`).

You may author slides **externally** (e.g. in PowerPoint or another app), export PNGs, then place or normalize them into this package — that authoring is not performed by repo scripts.

## Add a new episode

1. Copy `001-system-storytelling/` as a **starting scaffold** and rename the folder to a new `id` (e.g. `002-my-topic`).
2. Edit `episode.yaml` — set `id` to match the folder name.
3. Write `narration.md` with anchors `<!-- narration:n01 -->`, `<!-- narration:n02 -->`, … matching `narration_ref` in `slides.yaml`.
4. Fill `slides.yaml` and `motion-cues.yaml`.
5. Add narration audio under `assets/audio/` (see `episode.yaml` `audio_mode`).
6. Place normalized slide PNGs under `assets/slides/` (or export to `raw/ppt-export/` and run `scripts/normalize_slides.py`).
7. Run **`normalize_slides.py`** if needed, then **`validate_episode.py`** (`--strict-assets` recommended before video), then **`build_video.py`**.

See `docs/ARCHITECTURE.md` for schemas and pipeline details.
