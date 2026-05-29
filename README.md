# Frame Capture Application

A Windows GUI application for capturing and browsing screen frames with a configurable bounding box.

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
cd C:\Users\edgar\Scripts\frame-capture-app
conda create -n framecapture python=3.10
conda activate framecapture
pip install -r build/requirements.txt
```

### Using pip

```bash
cd C:\Users\edgar\Scripts\frame-capture-app
python -m pip install -r build/requirements.txt
```

## Usage

1. Run the application:
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
cd C:\Users\edgar\Scripts\frame-capture-app
build\build.bat
```

The executable will be created at `dist/FrameCaptureTool.exe`

## Configuration

Configuration is stored in Windows Registry at:
`HKEY_CURRENT_USER\Software\FrameCaptureApp\FrameCaptureApp`

Key settings:
- `capture_interval`: Milliseconds between captures (default: 500ms = 2fps)
- `max_frames`: Maximum frames in cache (default: 200)
- `thumbnail_size`: Thumbnail dimension in pixels (default: 128)
- `grid_columns`: Number of columns in gallery (default: 4)

## Project Structure

```
Scripts/
└── frame-capture-app/
    ├── src/
    │   ├── main.py              # Application entry point
    │   ├── window/
    │   │   └── main_window.py   # Main window UI
    │   ├── selection/
    │   │   └── bbox_selector.py # Bounding box selection
    │   ├── capture/
    │   │   └── frame_capture.py # Screen capture engine
    │   ├── cache/
    │   │   └── frame_cache.py   # Frame caching system
    │   ├── gallery/
    │   │   └── frame_gallery.py # Gallery and preview
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
    └── README.md
```

## Development

### Dependencies

- PyQt5>=5.15.9
- opencv-python>=4.8.0
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

## License

MIT License