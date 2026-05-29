"""Path utilities for the Frame Capture Application.

Centralizes path management for the application to ensure consistent
file locations across different environments.
"""

import os
import sys
from pathlib import Path
from PyQt5.QtCore import QStandardPaths


def get_app_directory() -> Path:
    """Get application data directory.
    
    Returns the user's application data directory where settings
    and persistent data should be stored.
    """
    app_data = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    return Path(app_data) / "FrameCaptureApp"


def get_temp_directory() -> Path:
    """Get temporary frames directory.
    
    Returns a directory for temporary frame storage during capture.
    """
    temp_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
    return Path(temp_dir) / "frame-capture-cache"


def get_resource_path(filename: str) -> Path:
    """Get resource file path.
    
    Args:
        filename: Name of the resource file
        
    Returns:
        Full path to the resource file
    """
    # Try to get resource from bundled app first (PyInstaller)
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent / "resources"
    else:
        base_path = Path(__file__).parent.parent / "resources"
    
    return base_path / filename


def get_cache_directory() -> Path:
    """Get cache storage directory.
    
    Returns the directory where cached frames are stored.
    """
    return get_temp_directory()


def ensure_directories() -> None:
    """Ensure all required directories exist.
    
    Creates necessary directories if they don't exist.
    """
    dirs = [
        get_app_directory(),
        get_temp_directory(),
        get_resource_path("").parent,
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)