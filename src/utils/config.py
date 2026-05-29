"""Configuration management for the Frame Capture Application.

Manages application configuration with persistent storage using QSettings.
"""

from PyQt5.QtCore import QSettings
from typing import Any, Optional


class Config:
    """Application configuration manager."""
    
    # Configuration parameter names
    CAPTURE_INTERVAL = "capture_interval"
    MAX_FRAMES = "max_frames"
    THUMBNAIL_SIZE = "thumbnail_size"
    GRID_COLUMNS = "grid_columns"
    PREVIEW_SCALE = "preview_scale"
    AUTO_SAVE = "auto_save"
    THEME = "theme"
    LAST_BBOX = "last_bbox"
    WINDOW_GEOMETRY = "window_geometry"
    
    def __init__(self):
        """Initialize configuration with settings file."""
        self.settings = QSettings(
            QSettings.IniFormat,
            QSettings.UserScope,
            "FrameCaptureApp",
            "FrameCaptureApp"
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self.settings.value(key, defaultValue=default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.settings.setValue(key, value)
    
    def remove(self, key: str) -> None:
        """Remove a configuration key.
        
        Args:
            key: Configuration key to remove
        """
        self.settings.remove(key)
    
    def sync(self) -> None:
        """Sync changes to disk."""
        self.settings.sync()
    
    def reset(self) -> None:
        """Reset all configuration to defaults."""
        self.settings.clear()
    
    # Convenience methods for specific configuration values
    
    @property
    def capture_interval(self) -> int:
        """Get capture interval in milliseconds."""
        return self.get(self.CAPTURE_INTERVAL, 500)
    
    @capture_interval.setter
    def capture_interval(self, value: int) -> None:
        """Set capture interval in milliseconds."""
        self.set(self.CAPTURE_INTERVAL, max(100, value))  # Minimum 100ms
    
    @property
    def max_frames(self) -> int:
        """Get maximum frames in cache."""
        return self.get(self.MAX_FRAMES, 200)
    
    @max_frames.setter
    def max_frames(self, value: int) -> None:
        """Set maximum frames in cache."""
        self.set(self.MAX_FRAMES, max(10, value))  # Minimum 10 frames
    
    @property
    def thumbnail_size(self) -> int:
        """Get thumbnail size in pixels."""
        return self.get(self.THUMBNAIL_SIZE, 128)
    
    @thumbnail_size.setter
    def thumbnail_size(self, value: int) -> None:
        """Set thumbnail size in pixels."""
        self.set(self.THUMBNAIL_SIZE, max(64, value))  # Minimum 64px
    
    @property
    def grid_columns(self) -> int:
        """Get number of columns in gallery grid."""
        return self.get(self.GRID_COLUMNS, 4)
    
    @grid_columns.setter
    def grid_columns(self, value: int) -> None:
        """Set number of columns in gallery grid."""
        self.set(self.GRID_COLUMNS, max(1, value))  # Minimum 1 column
    
    @property
    def preview_scale(self) -> float:
        """Get preview scaling factor."""
        return self.get(self.PREVIEW_SCALE, 0.8)
    
    @preview_scale.setter
    def preview_scale(self, value: float) -> None:
        """Set preview scaling factor."""
        self.set(self.PREVIEW_SCALE, max(0.1, min(1.0, value)))  # Clamp 0.1-1.0
    
    @property
    def auto_save(self) -> bool:
        """Get auto-save setting."""
        return self.get(self.AUTO_SAVE, True)
    
    @auto_save.setter
    def auto_save(self, value: bool) -> None:
        """Set auto-save setting."""
        self.set(self.AUTO_SAVE, value)
    
    @property
    def theme(self) -> str:
        """Get UI theme name."""
        return self.get(self.THEME, "modern")
    
    @theme.setter
    def theme(self, value: str) -> None:
        """Set UI theme name."""
        self.set(self.THEME, value)
    
    @property
    def last_bbox(self) -> Optional[str]:
        """Get last saved bounding box coordinates."""
        return self.get(self.LAST_BBOX)
    
    @last_bbox.setter
    def last_bbox(self, value: str) -> None:
        """Set last saved bounding box coordinates.
        
        Format: "x,y,width,height"
        """
        self.set(self.LAST_BBOX, value)
    
    @property
    def window_geometry(self) -> Optional[bytes]:
        """Get window geometry as bytes."""
        return self.get(self.WINDOW_GEOMETRY)
    
    @window_geometry.setter
    def window_geometry(self, value: bytes) -> None:
        """Set window geometry from bytes."""
        self.set(self.WINDOW_GEOMETRY, value)