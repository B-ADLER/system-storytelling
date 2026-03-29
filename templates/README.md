# Templates (optional, out of pipeline)

This folder is **optional** and **not part of the supported repository pipeline**. No script under `scripts/` reads it.

You may keep local files here while authoring slides in an external tool (e.g. a presentation app). The **only** automated steps in this repository are:

- optional **normalization** of slide PNGs (`normalize_slides.py`),
- **validation** (`validate_episode.py`),
- **MP4 assembly** (`build_video.py` + FFmpeg).

There is **no** PPTX generation or PDF export from this repo.
