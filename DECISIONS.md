# DECISIONS — frame-capture-app

*Dated log: decision · alternatives · reason. Newest first. Entries before 2026-07-19 are reconstructed from git history and code only — where the reason isn't recorded anywhere, it says so.*

## 2026-07-19 — Adopted `tools/fix_bbox.py` (one-shot restore script) from the projects root

- `fix_bbox.py` had sat loose at the projects root since 2026-05-30: a one-shot script that overwrites `src\selection\bbox_selector.py` (at the project's old `C:\Users\edgar\Scripts\frame-capture-app` location) with an embedded early single-screen version of the selector — evidently used to restore or bootstrap the file during initial development, the same day this project was created. Why the restore was needed was never recorded. TODO(edgar): fill in if remembered.
- It was briefly housed in its own `fix-bbox` project earlier today before Edgar decided it belongs here; that folder is deleted and the script now lives under `tools/` as a historical artifact with a DO-NOT-RUN header (its hardcoded path is defunct, and pointing it at the live tree would clobber the current multi-monitor `bbox_selector.py`). The leftover remote `edgaranarossi/fix-bbox` awaits Edgar's manual deletion.

## 2026-07-19 — Doc-set backfill + structure conformance

- Backfilled the constitution doc set (PLAN.md, DECISIONS.md, WISHLIST.md; README conformed with dated status lines) as part of the projects-root migration to `C:\Users\edgar\projects`. No code touched.
- `.gitignore` overhauled: runtime capture PNGs (`src/cache/*.png`), `src/test_output.txt`, and a `.env` *file* pattern added; the blanket `build/` ignore narrowed to `build/*` with explicit un-ignores for `requirements.txt` / `setup.py` / `build.bat` — the old pattern was silently hiding two of the three build scripts from git (only `requirements.txt` was ever tracked).
- `docs/` stays gitignored — that was a deliberate 2026-05-30 decision (see below), not reversed here; revisit is an open question in PLAN.md.
- Note: this project was already gitified on 2026-05-30 with remote `github.com/edgaranarossi/frame-pickr` — no gitification needed.

## 2026-05-30 — Multi-monitor bbox selection (commit d428379)

Bounding-box overlay reworked for multi-monitor support with visible selection feedback, after the initial single-screen version. (A further large uncommitted rework of `bbox_selector.py` followed the same day — see PLAN.md.)

## 2026-05-30 — `run.bat` conda wrapper (commit bd3bed9)

Launch via a batch file that runs `conda activate framecapture` before `python src/main.py`, because the app's deps live in a dedicated conda env and double-click launching otherwise picks up the wrong Python (commits 54474c5, bd3bed9).

## 2026-05-30 — Design docs removed from GitHub (commit 6ddf0ee)

`docs/superpowers/specs/` (design doc + implementation plan) was committed, then deliberately deleted from the repo and gitignored the same night; the files remain on disk. The folder's small `README.md` index was never deleted and is still tracked (gitignore doesn't affect already-tracked files). TODO(edgar): reason not recorded anywhere — re-track or keep local-only?

## 2026-05-30 — Initial stack (commit d724024, per design doc)

- **PyQt5** for the GUI (design doc names it as the constraint; alternatives not recorded).
- **mss** for screen capture; **OpenCV/Pillow/numpy** for image handling.
- **Disk-based circular buffer** of up to 200 PNG frames (lossless, ~200–400 MB budget) rather than in-memory frames — chosen in the design doc to balance storage vs. browsing time.
- **INI-file config via QSettings** (`QSettings.IniFormat`, user scope → `%APPDATA%\FrameCaptureApp\FrameCaptureApp.ini`) — code truth (`utils/config.py`). *(Corrected 2026-07-19: earlier docs claimed Windows Registry storage; the code has used `IniFormat` in every committed version.)*
- **PyInstaller single-file exe** as the distribution target (`build/`).
