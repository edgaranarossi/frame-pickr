# Frame Capture Application

> **2026-07-19:** Doc set backfilled per projects constitution; stale `Scripts\` paths fixed; `.gitignore` overhauled (runtime PNG cache + logs ignored, `build/` scripts un-ignored). Code untouched since 2026-05-30: v1 is feature-complete and on GitHub (`frame-pickr`), but the working tree carries a large **uncommitted** 2026-05-30 rework (startup loading window, bbox selector + clipboard overhaul, headless test harness) — see PLAN.md.
>
> **2026-05-30:** Initial implementation completed and pushed (per docs/superpowers/specs/README.md).

A Windows GUI application for capturing and browsing screen frames with a configurable bounding box.

Doc set: [PLAN.md](PLAN.md) · [DECISIONS.md](DECISIONS.md) · [WISHLIST.md](WISHLIST.md). Original design + implementation specs live in `docs/superpowers/specs/` (kept local, gitignored — see DECISIONS.md 2026-05-30; only that folder's small `README.md` index is still tracked in git).

## Features

- **Bounding Box Selection**: Select a screen region manually via click-and-drag
- **Frame Capture**: Capture frames at configurable intervals from the selected region
- **Frame Gallery**: Browse captured frames in a thumbnail grid
- **Preview & Navigation**: View frames in full size with Previous/Next navigation
- **Copy to Clipboard**: Copy selected frames directly to clipboard
- **Pause/Resume**: Pause capture to browse frames without losing them
- **Circular Buffer**: Automatically manages up to 200 frames (PNG format)

## Requirements

- Windows 10/11
- Python 3.10+ (Anaconda recommended)

## Installation

### Using Anaconda (Recommended)

```bash
cd C:\Users\edgar\projects\frame-capture-app
conda create -n framecapture python=3.10
conda activate framecapture
pip install -r build/requirements.txt
```

### Using pip

```bash
cd C:\Users\edgar\projects\frame-capture-app
python -m pip install -r build/requirements.txt
```

## Usage

1. Run the application (or just double-click `run.bat`, which activates the `framecapture` conda env for you):
   ```bash
   python src/main.py
   ```

2. **Select Bounding Box**: Click "Set Bounding Box" and drag to select the screen region

3. **Start Capture**: Click "Start Capture" to begin capturing frames

4. **Pause/Resume**: Click "Pause" to pause capture (frames remain in cache) or "Resume" to continue

5. **Browse Frames**: Click on thumbnails in the gallery to view and navigate frames

6. **Copy to Clipboard**: In the preview window, click "Copy to Clipboard"

## Building Executable

Run the build script:

```bash
cd C:\Users\edgar\projects\frame-capture-app
build\build.bat
```

The executable will be created at `dist/FrameCaptureTool.exe`

**Warning:** `build.bat` currently deletes the `build/` directory (its own home, including `requirements.txt`) before building — it self-destructs. Fix it before the next exe build; tracked in PLAN.md.

## Configuration

Configuration is stored via `QSettings` in **INI format** (`QSettings.IniFormat`, user scope), which on Windows lands at:
`%APPDATA%\FrameCaptureApp\FrameCaptureApp.ini` (i.e. `C:\Users\<you>\AppData\Roaming\FrameCaptureApp\FrameCaptureApp.ini`)

Key settings:
- `capture_interval`: Milliseconds between captures (default: 500ms = 2fps)
- `max_frames`: Maximum frames in cache (default: 200)
- `thumbnail_size`: Thumbnail dimension in pixels (default: 128)
- `grid_columns`: Number of columns in gallery (default: 4)

## Project Structure

```
frame-capture-app/
├── src/
│   ├── main.py              # Application entry point
│   ├── window/
│   │   └── main_window.py   # Main window UI
│   ├── selection/
│   │   └── bbox_selector.py # Bounding box selection
│   ├── capture/
│   │   └── frame_capture.py # Screen capture engine
│   ├── cache/
│   │   └── frame_cache.py   # Frame caching system (runtime PNGs land here too — gitignored)
│   ├── gallery/
│   │   └── frame_gallery.py # Gallery and preview
│   ├── test/
│   │   └── headless_test.py # Automated no-GUI capture test (uncommitted)
│   ├── utils/
│   │   ├── clipboard.py     # Clipboard operations
│   │   ├── config.py        # Configuration management
│   │   └── paths.py         # Path utilities
│   └── resources/
│       └── styles.qss       # Qt stylesheet
├── build/
│   ├── requirements.txt
│   ├── setup.py
│   └── build.bat
├── docs/superpowers/specs/  # Design + implementation plan (local only, gitignored; its README.md index is still tracked)
├── run.bat
└── README.md
```

## Development

### Dependencies

Runtime (from `build/requirements.txt`, which also carries the build-time deps `pyinstaller` and `setuptools`):

- pyqt5>=5.15.9
- opencv-python (unpinned)
- pillow>=10.0.0
- numpy>=1.24.0
- mss>=6.1.0

### Module Descriptions

| Module | Purpose |
|--------|---------|
| `main.py` | Application entry point and Qt setup |
| `main_window.py` | Main window with UI controls |
| `bbox_selector.py` | Full-screen overlay for region selection |
| `frame_capture.py` | Screen capture engine using mss |
| `frame_cache.py` | Circular buffer (200 frames) with PNG storage |
| `frame_gallery.py` | Thumbnail grid and preview dialog |
| `clipboard.py` | Copy frames to clipboard |
| `config.py` | Configuration management with QSettings |
| `paths.py` | Path utilities for app data and temp files |
| `test/headless_test.py` | Headless capture test: random bbox, 5s capture, validate |

## License

MIT License
