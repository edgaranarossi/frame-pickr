# Frame Capture Application Design

## Overview
A Windows-only GUI application for capturing and browsing screen frame sequences with a configurable bounding box, designed to help users select specific frames from ongoing screen activity.

## Purpose
Enable users to:
- Select a screen region (bounding box) manually via click-and-drag
- Capture frames from screen recording at that region
- Browse through recently captured frames with preview
- Copy selected frames to clipboard
- Pause/resume capture to balance storage usage vs. browsing time

## Constraints
- Platform: Windows only
- UI Toolkit: PyQt5 (Python)
- Language: Python 3.10+ (Anaconda environment)
- Storage: Temporary files on disk (fixed cache of 200 frames, ~200-400MB)
- Frame format: PNG (lossless)
- Frame rate: Variable based on system performance and screen area size
- Distribution: Standalone Windows executable

## Success Criteria
- Bounding box selection works intuitively with visual feedback
- Frames are captured and stored within 100ms per frame on modern hardware
- Gallery browsing is smooth with instant preview loading
- Pause/resume works reliably without frame loss
- UI is polished and modern in appearance
- Single-file executable runs without requiring Python installation
- Code pushed to GitHub repository

---

## Architecture

### Component Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    FrameCaptureApp                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │   Main Window    │  │  Frame Cache     │               │
│  │   (UI Manager)   │  │  (Storage Mgr)   │               │
│  └──────────────────┘  └──────────────────┘               │
│         │                       │                          │
│         ▼                       ▼                          │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  BBox Selector   │  │  Frame Capture   │               │
│  │   (Preview)      │  │  (Screen API)    │               │
│  └──────────────────┘  └──────────────────┘               │
│                              │                             │
│                              ▼                             │
│                    ┌──────────────────┐                    │
│                    │  Disk Cache      │                    │
│                    │  (PNG Files)     │                    │
│                    └──────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Core Modules

1. **main.py** - Application entry point, Qt application setup
2. **window/main_window.py** - Main window with UI layout
3. **selection/bbox_selector.py** - Bounding box selection overlay
4. **capture/frame_capture.py** - Screen capture using Windows APIs
5. **cache/frame_cache.py** - Fixed-size circular buffer with disk persistence
6. **gallery/frame_gallery.py** - Gallery view and preview window
7. **utils/clipboard.py** - Clipboard operations
8. **utils/config.py** - Configuration management
9. **utils/paths.py** - Path management for Anaconda environment

---

## Component Details

### 1. Main Window (main_window.py)
```
┌─────────────────────────────────────────────────────────────┐
│  Frame Capture Tool                            [ minimize ] │
│                                                [ maximize ] │
│                                                [   X    ]   │
├─────────────────────────────────────────────────────────────┤
│  [Set Bounding Box]  [Start Capture]  [Pause/Resume]       │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │             Frame Gallery (Thumbnail View)            │  │
│  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐     │  │
│  │  │[1]│ │[2]│ │[3]│ │[4]│ │[5]│ │[6]│ │[7]│ │[8]│     │  │
│  │  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘     │  │
│  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐     │  │
│  │  │[9]│ │[10]││[11]││[12]││[13]││[14]││[15]││[16]│    │  │
│  │  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘     │  │
│  │  Pagination controls for more frames                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Status: Capture paused • Frames: 0/200                     │
└─────────────────────────────────────────────────────────────┘
```

**Controls:**
- **Set Bounding Box**: Opens overlay for region selection
- **Start Capture**: Begins screen capture (changes to Pause button)
- **Pause/Resume**: Toggles capture state

**Gallery:**
- 16-frame thumbnail grid (4x4)
- Click thumbnail for full preview
- Selected frame highlighted with border
- Pagination controls for additional frames

### 2. Bounding Box Selector (bbox_selector.py)
**Features:**
- Full-screen semi-transparent overlay with red border
- Click-and-drag selection with live preview of selection rectangle
- Visual feedback showing dimensions and area size
- Confirm button after selection

### 3. Frame Capture (frame_capture.py)
**Implementation:**
- Uses Windows.Graphics.Capture API (via Windows SDK or Python wrapper)
- Captures only the defined bounding box region
- Converts frames to PNG format
- Stores in temporary directory

### 4. Frame Cache (frame_cache.py)
**Circular Buffer Behavior:**
- Fixed capacity: 200 frames
- When full, oldest frame deleted when new frame added
- Each frame: {index, timestamp, file_path, dimensions}
- Index tracking for ordered browsing

### 5. Frame Gallery (frame_gallery.py)
**Gallery View:**
- Thumbnail grid with configurable size (default 16 frames visible)
- Click to open full preview window

**Preview Window:**
- Full-size frame display
- Navigation buttons (Prev/Next)
- Keyboard shortcuts (←/→ arrows)
- Copy to clipboard button
- Frame info (index, timestamp, dimensions)

### 6. Clipboard Utility (clipboard.py)
**Functions:**
- Copy PNG frame to Windows clipboard
- Error handling for large files

---

## Data Flow

### Initial Setup
1. User launches app
2. Clicks "Set Bounding Box"
3. Selects region on screen overlay
4. App saves coordinates (x, y, width, height)

### Capture Workflow
```
User clicks Start → Capture loop begins
    ↓
Timer triggers (configurable interval, default 1-2 fps)
    ↓
Screen capture of bounding box region
    ↓
Frame converted to PNG
    ↓
Saved to temp directory with index naming
    ↓
Frame metadata added to cache ring
    ↓
Old frame deleted if cache full
    ↓
Gallery updated with new frame
```

### Pause Behavior
```
User clicks Pause → Capture timer stops
    ↓
No new frames captured
    ↓
Current frames remain in cache
    ↓
User can browse existing frames
```

### Preview/Navigation
1. User clicks thumbnail
2. Preview window opens with selected frame
3. User navigates with buttons or arrow keys
4. User clicks "Copy to Clipboard"
5. Frame loaded as QImage, copied to clipboard

---

## Error Handling

| Scenario | Response |
|----------|----------|
| Capture fails (screen protected) | Show warning dialog, allow retry |
| Disk full | Show error, pause capture |
| Invalid bounding box | Validate dimensions before capture |
| Clipboard copy fails | Show error message |
| Cache corruption | Clear cache and restart |

---

## Testing Strategy

### Unit Tests
- Bounding box selection logic
- Frame cache circular buffer behavior
- PNG encoding/decoding
- Clipboard operations

### Integration Tests
- Full capture workflow
- Pause/resume cycle
- Gallery navigation
- Multiple frame selections

### Manual Testing
- Visual inspection of UI polish
- Frame quality verification
- Performance under different screen sizes

---

## Project Structure

```
Scripts/
└── frame-capture-app/
    ├── src/
    │   ├── main.py
    │   ├── window/
    │   │   └── main_window.py
    │   ├── selection/
    │   │   └── bbox_selector.py
    │   ├── capture/
    │   │   └── frame_capture.py
    │   ├── cache/
    │   │   └── frame_cache.py
    │   ├── gallery/
    │   │   └── frame_gallery.py
    │   ├── utils/
    │   │   ├── clipboard.py
    │   │   ├── config.py
    │   │   └── paths.py
    │   └── resources/
    │       └── styles.qss
    ├── docs/
    │   └── superpowers/
    │       └── specs/
    │           └── 2026-05-30-frame-capture-app-design.md
    ├── build/
    │   ├── requirements.txt
    │   ├── setup.py
    │   └── build.bat
    ├── README.md
    ├── LICENSE
    └── .gitignore
```

---

## Deliverables

1. **Source Code** (`src/` directory)
   - main.py - Entry point
   - window/main_window.py - Main window UI
   - selection/bbox_selector.py - Bounding box selection
   - capture/frame_capture.py - Screen capture logic
   - cache/frame_cache.py - Frame caching system
   - gallery/frame_gallery.py - Gallery and preview
   - utils/clipboard.py - Clipboard operations
   - utils/config.py - Configuration
   - utils/paths.py - Path utilities
   - resources/styles.qss - Qt stylesheet for modern UI

2. **Dependencies** (`build/requirements.txt`)
   - pyqt5>=5.15.9
   - opencv-python>=4.8.0
   - pillow>=10.0.0
   - numpy>=1.24.0
   - windows-curses (for Anaconda)

3. **Build Configuration** (`build/`)
   - setup.py - PyInstaller configuration
   - build.bat - Windows batch script for building EXE

4. **Documentation**
   - README.md with usage instructions
   - This design document

5. **Executable**
   - frame-capture-tool.exe (single-file, no Python required)

6. **GitHub Repository**
   - New repository for frame-capture-app
   - Initial commit with complete project structure