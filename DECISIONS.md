# DECISIONS — frame-capture-app

*Dated log: decision · alternatives · reason. Newest first. Entries before 2026-07-19 are reconstructed from git history and code only — where the reason isn't recorded anywhere, it says so.*

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

`docs/superpowers/specs/` (design doc + implementation plan) was committed, then deliberately deleted from the repo and gitignored the same night; the files remain on disk. TODO(edgar): reason not recorded anywhere — re-track or keep local-only?

## 2026-05-30 — Initial stack (commit d724024, per design doc)

- **PyQt5** for the GUI (design doc names it as the constraint; alternatives not recorded).
- **mss** for screen capture; **OpenCV/Pillow/numpy** for image handling.
- **Disk-based circular buffer** of up to 200 PNG frames (lossless, ~200–400 MB budget) rather than in-memory frames — chosen in the design doc to balance storage vs. browsing time.
- **Windows Registry via QSettings** (`HKCU\Software\FrameCaptureApp`) for configuration — code truth (`utils/config.py`).
- **PyInstaller single-file exe** as the distribution target (`build/`).
