# Raw PNG export folder (optional)

Use this folder for **slide PNGs exported from an external tool** (e.g. PowerPoint “Save as PNG”) **before** they are renamed to the engine’s contract names. This is **not** a build product of this repository — only an ingestion staging area.

Place exported PNGs here **without renaming** to match engine names. Add **`manifest.txt`** listing lines:

`source_filename target_filename`

Then run:

`python scripts/normalize_slides.py 001-system-storytelling`

Outputs go to `episodes/<episode-id>/assets/slides/` (this episode: `../../assets/slides/` from this folder). **`build_video.py` does not read this folder.**
