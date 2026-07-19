"""Frame gallery for the Frame Capture Application.

Provides thumbnail grid view and preview window for captured frames.
"""

import os
from typing import List, Optional

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QDialog, QScrollArea, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QImage

from cache.frame_cache import FrameCache, FrameMetadata
from utils.config import Config


class FrameThumbnail(QLabel):
    """Thumbnail display for a frame."""

    def __init__(self, parent=None):
        """Initialize the thumbnail."""
        super().__init__(parent)
        self._metadata: Optional[FrameMetadata] = None
        self.setFixedSize(128, 128)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
        """)

    def set_metadata(self, metadata: FrameMetadata):
        """Set frame metadata and load thumbnail."""
        self._metadata = metadata

        # Load and resize image for thumbnail
        if metadata and os.path.exists(metadata.file_path):
            try:
                image = QImage(metadata.file_path)
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    scaled = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.setPixmap(scaled)
                    self.setToolTip(f"Frame #{metadata.index}\n{metadata.dimensions[0]}x{metadata.dimensions[1]}")
            except Exception:
                pass

    def set_selected(self, selected: bool):
        """Set selection state."""
        if selected:
            self.setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    border: 2px solid #2196f3;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: #f0f0f0;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                }
            """)


class FrameGallery(QWidget):
    """Gallery widget for displaying captured frames.

    Attributes:
        frameSelected: Emitted when a frame is selected
            Args: (frame_metadata: FrameMetadata)
    """

    def __init__(self, parent=None):
        """Initialize the gallery."""
        super().__init__(parent)

        self._thumbnails: List[FrameThumbnail] = []
        self._selected_thumbnail: Optional[FrameThumbnail] = None
        self._frame_count = 0
        self._max_frames = 200

        self._setup_ui()

    def _setup_ui(self):
        """Setup the gallery UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Scroll area for thumbnails
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Thumbnail container
        self._container = QWidget()
        self._container.setStyleSheet("background-color: #fafafa;")

        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(10)
        self._grid_layout.setAlignment(Qt.AlignTop)
        self._container.setLayout(self._grid_layout)

        scroll_area.setWidget(self._container)
        layout.addWidget(scroll_area)

    def resizeEvent(self, event):
        """Handle resize events to update grid layout."""
        super().resizeEvent(event)
        self._resize_grid()

    def update_frame(self, metadata: FrameMetadata):
        """Update gallery with a new frame.

        Args:
            metadata: FrameMetadata for the new frame
        """
        # Create new thumbnail
        thumbnail = FrameThumbnail()
        thumbnail.set_metadata(metadata)
        thumbnail.mouseReleaseEvent = lambda event: self._on_thumbnail_click(event, thumbnail)
        thumbnail.setCursor(Qt.PointingHandCursor)

        # Add to front of list (newest first - index 0 is newest)
        self._thumbnails.insert(0, thumbnail)

        self._frame_count += 1

        # Resize grid - will also be called via resizeEvent when widget is shown
        self._resize_grid()

    def _on_thumbnail_click(self, event, thumbnail: FrameThumbnail):
        """Handle thumbnail click."""
        # Deselect previous
        if self._selected_thumbnail and self._selected_thumbnail != thumbnail:
            self._selected_thumbnail.set_selected(False)

        # Select new
        self._selected_thumbnail = thumbnail
        thumbnail.set_selected(True)

        # Show preview
        if thumbnail._metadata:
            self._show_preview(thumbnail._metadata)

    def _show_preview(self, metadata: FrameMetadata):
        """Show frame preview dialog."""
        dialog = FramePreviewDialog(metadata, self)
        dialog.exec_()

    def _resize_grid(self):
        """Resize the grid to fit available width with auto column count."""
        if not self._thumbnails:
            return

        # Get available width from scroll area's viewport
        scroll_area = self._container.parentWidget()
        if scroll_area and hasattr(scroll_area, 'viewport') and scroll_area.viewport():
            available_width = scroll_area.viewport().width()
        else:
            available_width = 0

        # If width is not yet available, calculate based on gallery width
        if available_width <= 0:
            available_width = self.width() - 20  # Gallery width with margin

        # Calculate how many columns can fit
        # Thumbnail is 128px, spacing is 10px
        thumb_width = 128
        spacing = 10
        # Use 138 = 128 + 10 for spacing between columns
        max_cols = max(1, (available_width - 10) // (thumb_width + spacing))

        # Clear existing layout items
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)

        # Add thumbnails with newest first at top-left
        # Index 0 (newest) should be at row 0, col 0
        # Then fill left-to-right, top-to-bottom
        for idx, thumb in enumerate(self._thumbnails):
            row = idx // max_cols
            col = idx % max_cols
            self._grid_layout.addWidget(thumb, row, col)

    def clear(self):
        """Clear all thumbnails."""
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._thumbnails.clear()
        self._selected_thumbnail = None
        self._frame_count = 0

    def load_frames(self, frames: List[FrameMetadata]):
        """Load existing frames into the gallery.

        Args:
            frames: List of FrameMetadata objects to load (oldest to newest)
        """
        # Reverse to show newest first (matching update_frame behavior)
        for metadata in reversed(frames):
            thumbnail = FrameThumbnail()
            thumbnail.set_metadata(metadata)
            thumbnail.mouseReleaseEvent = lambda event, t=thumbnail: self._on_thumbnail_click(event, t)
            thumbnail.setCursor(Qt.PointingHandCursor)
            self._thumbnails.append(thumbnail)
            self._frame_count += 1

        self._resize_grid()

    def get_selected_frame(self) -> Optional[FrameMetadata]:
        """Get currently selected frame metadata.

        Returns:
            FrameMetadata if a frame is selected, None otherwise
        """
        if self._selected_thumbnail:
            return self._selected_thumbnail._metadata
        return None


class FramePreviewDialog(QDialog):
    """Preview dialog for individual frames."""

    def __init__(self, metadata: FrameMetadata, parent=None):
        """Initialize the preview dialog.

        Args:
            metadata: FrameMetadata to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.metadata = metadata
        self.setWindowTitle(f"Frame #{metadata.index}")
        self.setModal(True)

        # Remove help button from title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._original_pixmap = None  # Store original image for dynamic scaling
        self._config = None
        self._setup_ui()
        self._load_frame()
        self._load_config()

    def _load_config(self):
        """Load saved preview dialog geometry."""
        if self._config is None:
            self._config = Config()
        geometry = self._config.get(Config.PREVIEW_GEOMETRY)
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # Default size if no saved geometry
            self.resize(600, 400)

    def _save_config(self):
        """Save preview dialog geometry."""
        if self._config is None:
            self._config = Config()
        self._config.set(Config.PREVIEW_GEOMETRY, self.saveGeometry())

    def resizeEvent(self, event):
        """Handle resize events to scale the image to fit the window."""
        super().resizeEvent(event)
        if self._original_pixmap:
            self._scale_image()

    def _setup_ui(self):
        """Setup the preview UI."""
        layout = QVBoxLayout(self)

        # Image display - scroll area for large images
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("background-color: #000; border-radius: 5px;")

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.setWidget(self._image_label)
        layout.addWidget(scroll_area, stretch=1)

        # Frame info
        info_label = QLabel()
        info_label.setStyleSheet("color: #666;")
        info_label.setText(f"Frame #{self.metadata.index} | "
                         f"{self.metadata.dimensions[0]}x{self.metadata.dimensions[1]} | "
                         f"Saved: {self.metadata.file_path}")
        layout.addWidget(info_label)

        # Navigation and actions
        nav_layout = QHBoxLayout()

        prev_button = QPushButton("Previous")
        prev_button.clicked.connect(self._on_prev)
        nav_layout.addWidget(prev_button)

        self._nav_label = QLabel()
        nav_layout.addWidget(self._nav_label)

        next_button = QPushButton("Next")
        next_button.clicked.connect(self._on_next)
        nav_layout.addWidget(next_button)

        nav_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        nav_layout.addWidget(close_button)

        # Reveal in Explorer button - modern styling
        reveal_button = QPushButton("Reveal in Explorer")
        reveal_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #607d8b, stop: 1 #455a64);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #78909c, stop: 1 #607d8b);
            }
            QPushButton:pressed {
                background: #37474f;
            }
        """)
        reveal_button.clicked.connect(self._on_reveal_in_explorer)
        nav_layout.addWidget(reveal_button)

        layout.addLayout(nav_layout)

    def _load_frame(self):
        """Load the frame image."""
        if os.path.exists(self.metadata.file_path):
            try:
                self._original_pixmap = QPixmap(self.metadata.file_path)
                if not self._original_pixmap.isNull():
                    self._scale_image()
                    self._nav_label.setText(f"Frame {self.metadata.index}")
            except Exception:
                self._image_label.setText("Failed to load image")

    def closeEvent(self, event):
        """Handle dialog close event to save geometry."""
        self._save_config()
        super().closeEvent(event)

    def _scale_image(self):
        """Scale the original image to fit the current window size."""
        if not self._original_pixmap:
            return

        # Get available space (subtract margin)
        available_width = self.width() - 40
        available_height = self.height() - 150

        if available_width > 0 and available_height > 0:
            scaled = self._original_pixmap.scaled(
                available_width, available_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self._image_label.setPixmap(scaled)

    def _on_prev(self):
        """Navigate to previous frame."""
        if self.parentWidget():
            gallery = self.parentWidget()
            if isinstance(gallery, FrameGallery):
                for i, thumb in enumerate(gallery._thumbnails):
                    if thumb._metadata and thumb._metadata.index == self.metadata.index:
                        if i > 0:
                            # Deselect current before switching
                            if gallery._selected_thumbnail:
                                gallery._selected_thumbnail.set_selected(False)

                            prev_thumb = gallery._thumbnails[i - 1]
                            self.metadata = prev_thumb._metadata
                            self.setWindowTitle(f"Frame #{self.metadata.index}")
                            self._load_frame()
                            gallery._selected_thumbnail = prev_thumb
                            prev_thumb.set_selected(True)
                        break

    def _on_next(self):
        """Navigate to next frame."""
        if self.parentWidget():
            gallery = self.parentWidget()
            if isinstance(gallery, FrameGallery):
                for i, thumb in enumerate(gallery._thumbnails):
                    if thumb._metadata and thumb._metadata.index == self.metadata.index:
                        if i < len(gallery._thumbnails) - 1:
                            # Deselect current before switching
                            if gallery._selected_thumbnail:
                                gallery._selected_thumbnail.set_selected(False)

                            next_thumb = gallery._thumbnails[i + 1]
                            self.metadata = next_thumb._metadata
                            self.setWindowTitle(f"Frame #{self.metadata.index}")
                            self._load_frame()
                            gallery._selected_thumbnail = next_thumb
                            next_thumb.set_selected(True)
                        break

    def _on_reveal_in_explorer(self):
        """Open the folder containing the frame in Windows Explorer and select the file."""
        file_path = self.metadata.file_path
        if os.path.exists(file_path):
            # Use Windows Shell API to select the file
            import ctypes
            from ctypes import wintypes, POINTER

            # HRESULT is just an int
            HRESULT = wintypes.LONG

            # SHOpenFolderAndSelectItems method
            shell32 = ctypes.WinDLL('shell32.dll', use_last_error=True)

            # Convert file path to wide string (UTF-16)
            file_path_w = ctypes.c_wchar_p(file_path)

            # Parse the file path to get PIDL
            shell32.SHParseDisplayName.argtypes = [ctypes.c_wchar_p, wintypes.LPVOID, POINTER(ctypes.c_void_p), wintypes.ULONG, POINTER(ctypes.c_void_p)]
            shell32.SHParseDisplayName.restype = HRESULT

            pidl = ctypes.c_void_p()
            result = shell32.SHParseDisplayName(file_path_w, None, ctypes.byref(pidl), 0, None)

            if result == 0 and pidl.value:
                try:
                    # Open folder and select item
                    shell32.SHOpenFolderAndSelectItems.argtypes = [ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p, wintypes.ULONG]
                    shell32.SHOpenFolderAndSelectItems.restype = HRESULT

                    result = shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
                finally:
                    # Free the PIDL
                    ole32 = ctypes.WinDLL('ole32.dll', use_last_error=True)
                    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
                    ole32.CoTaskMemFree.restype = None
                    ole32.CoTaskMemFree(pidl)
