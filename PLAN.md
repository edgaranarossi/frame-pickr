# PLAN — frame-capture-app

*What happens next. See README.md for what this is; DECISIONS.md for why it's built this way.*

## Next actions

1. **Review and commit the 2026-05-30 uncommitted rework.** Eight `src/` files carry +1769/−284 uncommitted lines (startup loading/progress window in `main.py`, major `bbox_selector.py` and `clipboard.py` overhauls, `main_window.py`/`frame_gallery.py`/`frame_cache.py` changes, new `src/test/headless_test.py`). Run the app end-to-end first, then commit in sensible chunks. Until this lands, the GitHub repo does not reflect the real app.
2. **Verify clipboard actually works now.** `src/frame_capture.log` (2026-05-30) records DIB conversion failures and a missing `pyperclip` module; `clipboard.py` was reworked afterward but never verified/committed. If `pyperclip` is still used, add it to `build/requirements.txt`.
3. **Fix `build/build.bat` self-destruction.** It `rmdir /s /q build` (PyInstaller's default work dir) from the project root — which is also the directory holding `requirements.txt`, `setup.py`, and `build.bat` itself — then tries to `pip install -r build\requirements.txt`. Point PyInstaller's workpath elsewhere (`--workpath`) or stop deleting `build/`.
4. **Stop the runtime cache polluting the source tree.** Captured frames land in `src/cache/` next to `frame_cache.py` (~500 PNGs / ~1 GB currently on disk, now gitignored). `utils/paths.py` exists for app-data/temp paths — route the cache there, then delete the stray PNGs.
5. **Delete stale runtime residue** once confirmed useless: `src/frame_capture.log`, `src/test_output.txt` (empty), the `src/cache/*.png` files.

## Open questions

- TODO(edgar): should `docs/superpowers/specs/` go back into git? It was deliberately removed from GitHub on 2026-05-30 (commit 6ddf0ee) for reasons not recorded; the constitution prefers docs in-repo.
- TODO(edgar): is the standalone exe (`dist/FrameCaptureTool.exe`) still a goal, or is `run.bat` + conda enough for personal use?
- TODO(edgar): the specs' known issues — multi-monitor edge cases and overlay dimming tuning — still open?

## Backlog (future enhancements, from the 2026-05-30 spec)

- Keyboard shortcuts for common actions
- Batch operations (copy multiple frames)
- Frame editing capabilities
- Video recording mode / export frames to video
