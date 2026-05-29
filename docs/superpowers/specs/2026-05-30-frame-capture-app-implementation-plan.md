# Frame Capture Application - Implementation Plan

**Version:** 1.0  
**Date:** 2026-05-30  
**Author:** AI Assistant  
**Status:** Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Implementation Order](#implementation-order)
4. [Module Specifications](#module-specifications)
5. [Dependencies](#dependencies)
6. [Integration Points](#integration-points)
7. [Testing Strategy](#testing-strategy)
8. [Build Process](#build-process)

---

## Overview

This document provides a comprehensive implementation plan for the Frame Capture Application, a Windows-only GUI application for capturing screen frames within user-defined bounding boxes.

### Project Goals
- Enable users to select screen regions with click-and-drag
- Capture frames at configurable intervals (1-2 fps default)
- Store up to 200 frames in a circular buffer (PNG format)
- Provide intuitive gallery browsing with preview functionality
- Enable clipboard copying of selected frames
- Create a polished, modern UI with PyQt5
- Generate standalone Windows executable

### Technical Constraints
- Platform: Windows 10/11
- Language: Python 3.10+ (Anaconda environment)
- UI Toolkit: PyQt5
- Image Processing: OpenCV, Pillow
- Distribution: PyInstaller single-file executable

---

## Project Structure

```
Scripts/
└── frame-capture-app/
    ├── src/
    │   ├── main.py                     # Application entry point
    │   ├── window/
    │   │   └── main_window.py         # Main window UI
    │   ├── selection/
    │   │   └── bbox_selector.py       # Bounding box selection
    │   ├── capture/
    │   │   └── frame_capture.py       # Screen capture logic
    │   ├── cache/
    │   │   └── frame_cache.py         # Frame caching system
    │   ├── gallery/
    │   │   └── frame_gallery.py       # Gallery and preview
    │   ├── utils/
    │   │   ├── clipboard.py           # Clipboard operations
    │   │   ├── config.py              # Configuration management
    │   │   └── paths.py               # Path utilities
    │   └── resources/
    │       └── styles.qss             # Qt stylesheet
    ├── docs/
    │   └── superpowers/
    │       └── specs/
    │           ├── 2026-05-30-frame-capture-app-design.md
    │           └── 2026-05-30-frame-capture-app-implementation-plan.md
    ├── build/
    │   ├── requirements.txt
    │   ├── setup.py                   # PyInstaller configuration
    │   └── build.bat                  # Windows batch script
    ├── README.md
    ├── LICENSE
    └── .gitignore
```

---

## Implementation Order

Implement modules in the following order to ensure dependencies are resolved:

### Phase 1: Foundation (Week 1)
1. **Project setup and configuration**
   - Create project structure
   - Set up `requirements.txt`
   - Implement `paths.py` and `config.py`
   - Create initial Qt application skeleton in `main.py`

2. **Core utilities**
   - Implement `utils/clipboard.py`
   - Implement `utils/config.py`
   - Implement `utils/paths.py`

### Phase 2: Core Engine (Week 2)
3. **Frame capture engine**
   - Implement `capture/frame_capture.py`
   - Integrate Windows screen capture API (Windows.Graphics.Capture)
   - Implement frame encoding to PNG format
   - Add basic error handling

4. **Frame cache system**
   - Implement `cache/frame_cache.py`
   - Create circular buffer logic (200-frame limit)
   - Implement file management for PNG storage
   - Add index tracking and metadata storage

### Phase 3: UI Components (Week 3)
5. **Bounding box selector**
   - Implement `selection/bbox_selector.py`
   - Create full-screen overlay with semi-transparent mask
   - Implement click-and-drag selection
   - Add visual feedback and confirmation

6. **Main window**
   - Implement `window/main_window.py`
   - Create main UI layout with controls
   - Integrate thumbnail grid
   - Add status bar and info display

7. **Frame gallery**
   - Implement `gallery/frame_gallery.py`
   - Create thumbnail generation system
   - Implement grid layout (16 frames)
   - Add navigation functionality

### Phase 4: Integration and Polish (Week 4)
8. **Full integration**
   - Connect all modules
   - Implement state management
   - Add error handling and recovery
   - Test capture workflow end-to-end

9. **UI refinement**
   - Implement `resources/styles.qss`
   - Polish visual appearance
   - Add animations and transitions
   - Optimize performance

10. **Testing and documentation**
    - Write unit and integration tests
    - Create user documentation
    - Test on different hardware configurations
    - Document API and architecture

### Phase 5: Build and Distribution (Week 5)
11. **Build system**
    - Create `build/setup.py`
    - Configure PyInstaller for Windows
    - Create `build/build.bat`
    - Test executable creation

12. **Final deployment**
    - Create final build
    - Test standalone execution
    - Prepare for GitHub release
    - Document installation instructions

---

## Module Specifications

### 1. `src/utils/paths.py`

**Purpose:** Centralize path management for the application

**Key Functions:**
- `get_app_directory()` - Get application data directory
- `get_temp_directory()` - Get temporary frames directory
- `get_resource_path(filename)` - Get resource file paths
- `get_cache_directory()` - Get cache storage directory

**Implementation Notes:**
- Use `QStandardPaths` for Windows compatibility
- Handle Anaconda environment path resolution
- Ensure directories exist on first access

**Dependencies:** `PyQt5.QtCore`, `os`, `pathlib`

---

### 2. `src/utils/config.py`

**Purpose:** Manage application configuration

**Configuration Parameters:**
- `CAPTURE_INTERVAL` (int): Milliseconds between captures (default: 500ms = 2fps)
- `MAX_FRAMES` (int): Maximum frames in circular buffer (default: 200)
- `THUMBNAIL_SIZE` (int): Thumbnail dimension in pixels (default: 128)
- `GRID_COLUMNS` (int): Number of columns in gallery (default: 4)
- `PREVIEW_SCALE` (float): Preview scaling factor (default: 0.8)
- `AUTO_SAVE` (bool): Whether to auto-save settings (default: true)
- `THEME` (str): UI theme name (default: 'modern')

**Implementation Notes:**
- Use `QSettings` for persistent configuration
- Provide sensible defaults
- Support runtime configuration changes
- Validate configuration values

**Dependencies:** `PyQt5.QtCore`

---

### 3. `src/utils/clipboard.py`

**Purpose:** Handle clipboard operations

**Key Functions:**
- `copy_to_clipboard(image_path)` - Copy PNG file to clipboard
- `get_clipboard_image()` - Get image from clipboard
- `is_image_available()` - Check clipboard for image content

**Implementation Notes:**
- Use `QApplication.clipboard()` for cross-platform support
- Implement error handling for large files
- Convert formats as needed (QImage → clipboard format)
- Handle Windows-specific clipboard issues

**Dependencies:** `PyQt5.QtGui`, `PyQt5.QtWidgets`

---

### 4. `src/capture/frame_capture.py`

**Purpose:** Handle screen capture operations

**Key Classes:**
- `FrameCaptureEngine` - Main capture engine class

**Key Methods:**
- `__init__(bounding_box, interval)` - Initialize with capture parameters
- `start_capture()` - Begin frame capture
- `stop_capture()` - Stop frame capture
- `pause_capture()` - Pause capture (keeps frames)
- `resume_capture()` - Resume capture
- `capture_frame()` - Capture single frame
- `get_latest_frame()` - Get most recent frame data

**Implementation Notes:**
- Use Windows.Graphics.Capture API via `winrt` or `pywinrt`
- Alternative: `mss` library as fallback
- Convert captured frames to PNG format
- Store frames temporarily before cache integration
- Implement frame rate control with QTimer
- Handle screen protection scenarios (e.g., UAC prompts)

**Dependencies:** `PyQt5.QtCore`, `PIL`, `numpy`, `opencv-python`

---

### 5. `src/cache/frame_cache.py`

**Purpose:** Implement circular buffer for frame storage

**Key Classes:**
- `FrameCache` - Circular buffer implementation
- `FrameMetadata` - Data class for frame information

**Key Methods:**
- `__init__(max_frames=200)` - Initialize cache with capacity
- `add_frame(frame_data, metadata)` - Add new frame to cache
- `get_frame(index)` - Get frame by index
- `get_all_frames()` - Get all frames in order
- `get_frame_count()` - Get current frame count
- `clear_cache()` - Clear all cached frames
- `save_frame_to_disk(index)` - Save specific frame to disk
- `load_frame_from_disk(index)` - Load specific frame from disk

**Implementation Notes:**
- Use OrderedDict or deque for efficient circular buffer
- Implement FIFO behavior when full
- Store metadata separately (index, timestamp, dimensions)
- Use hash-based indexing for fast access
- Implement thread-safe operations if needed
- Store frames as PNG in temp directory

**Data Structure:**
```python
{
    0: {
        'timestamp': datetime,
        'path': 'temp/frame_0000.png',
        'dimensions': (width, height),
        'data': np.ndarray  # Optional in-memory copy
    },
    # ... up to MAX_FRAMES
}
```

**Dependencies:** `PyQt5.QtCore`, `PIL`, `numpy`

---

## Build Process

### Build Dependencies Setup

1. **Install build tools:**
   ```bash
   pip install pyinstaller setuptools
   ```

2. **Verify Anaconda environment:**
   ```bash
   conda list pyqt
   conda list numpy
   ```

### PyInstaller Configuration

**build/setup.py**
```python
# (PyInstaller configuration code here)
```

**build/build.bat**
```batch
# (Build script here)
```

### Build Process Steps

1. **Clean previous builds:**
   ```bash
   rm -rf dist/ build/ __pycache__/
   ```

2. **Run build script:**
   ```bash
   cd build
   ./build.bat
   ```

3. **Test executable:**
   ```bash
   dist/FrameCaptureTool.exe
   ```

4. **Verify functionality:**
   - Launch application
   - Test all features
   - Check for errors in console output
   - Verify standalone operation (no Python required)

### Executable Size Optimization

- Use UPX compression
- Exclude unused Qt modules
- Use one-file mode
- Strip debug symbols
- Compress resources

**Expected Final Size:** 15-30 MB

---

## Deployment Checklist

### Pre-Deployment
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing completed
- [ ] Documentation reviewed
- [ ] License file included
- [ ] README.md updated

### Build Verification
- [ ] Executable builds without errors
- [ ] Executable size is reasonable (15-30 MB)
- [ ] Application launches without Python
- [ ] All features work correctly
- [ ] No external dependencies required

### Distribution
- [ ] Create GitHub repository
- [ ] Commit all source code
- [ ] Tag release version
- [ ] Upload executable to releases
- [ ] Write release notes

### Post-Deployment
- [ ] Test on clean Windows machine
- [ ] Verify uninstall process
- [ ] Collect user feedback
- [ ] Plan future enhancements

---

## Troubleshooting Guide

### Common Issues

**Issue:** Application fails to start
- **Solution:** Check Python installation, verify PyQt5 dependencies

**Issue:** Screen capture fails
- **Solution:** Run as administrator, check screen protection settings

**Issue:** Performance is slow
- **Solution:** Reduce capture interval, close other applications

**Issue:** Cache fills up quickly
- **Solution:** Increase MAX_FRAMES in config, reduce capture interval

**Issue:** Executable is too large
- **Solution:** Enable UPX compression, exclude unused modules

### Debug Mode
Add `--debug` flag to main.py for verbose logging.

---

## Maintenance Plan

### Version Control Strategy
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Create feature branches for new functionality
- Merge to main after testing
- Tag releases for stability

### Update Process
1. Create feature branch
2. Implement and test changes
3. Update documentation
4. Create pull request
5. Review and merge
6. Create new release

### Known Limitations
- Windows-only (intentional)
- Maximum 200 frames in cache
- Single capture region at a time
- No frame editing capabilities (yet)
- No batch operations (yet)

---

## Appendix A: Quick Reference

### File Locations
- Main application: `src/main.py`
- Window UI: `src/window/main_window.py`
- Bounding box: `src/selection/bbox_selector.py`
- Capture engine: `src/capture/frame_capture.py`
- Cache system: `src/cache/frame_cache.py`
- Gallery: `src/gallery/frame_gallery.py`
- Styles: `src/resources/styles.qss`

### Configuration File Location
Windows AppData: `%APPDATA%\FrameCaptureApp\settings.ini`

### Temporary Files Location
Windows Temp: `%TEMP%rame-capture-cache\`

---

## Appendix B: Resource Links

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Windows.Graphics.Capture API](https://learn.microsoft.com/en-us/windows/win32/api/windowsgraphicscapture/)
- [PyInstaller Documentation](https://pyinstaller.org/)
- [Anaconda Documentation](https://docs.anaconda.com/)

---

**Document Version:** 1.0
**Last Updated:** 2026-05-30
**Status:** Ready for Implementation

---

*This implementation plan provides a comprehensive roadmap for building the Frame Capture Application. Follow the phased approach to ensure a robust, maintainable codebase that meets all specified requirements.*/
