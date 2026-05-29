"""Frame gallery for the Frame Capture Application.

Provides thumbnail grid view and preview window for captured frames.
"""

import os
from typing import List, Optional

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QDialog, QScrollArea
)
from PyQt5.QtGui import QPixmap, QImage

from cache.frame_cache import FrameCache, FrameMetadata
from utils.clipboard import copy_to_clipboard


class FrameThumbnail(QLabel):
    """Thumbnail display for a frame."""
    
    def __init__(self, parent=None):
        """Initialize the thumbnail."""
        super().__init__(parent)
        self._metadata: Optional[FrameMetadata] = None
        self.setFixedSize(128, 128)
        self.setAlignment(Qt.AlignCenter)
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
        self._container.setLayout(self._grid_layout)
        
        scroll_area.setWidget(self._container)
        layout.addWidget(scroll_area)
    
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
        
        # Add to grid
        row = len(self._thumbnails) // 4
        col = len(self._thumbnails) % 4
        
        self._grid_layout.addWidget(thumbnail, row, col)
        self._thumbnails.append(thumbnail)
        self._frame_count += 1
    
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
        if dialog.exec_():
            # Copy to clipboard if requested
            if dialog.copy_requested:
                copy_to_clipboard(metadata.file_path)
    
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
        self.copy_requested = False
        
        self.setWindowTitle(f"Frame #{metadata.index}")
        self.setMinimumSize(400, 300)
        self.setModal(True)
        
        self._setup_ui()
        self._load_frame()
    
    def _setup_ui(self):
        """Setup the preview UI."""
        layout = QVBoxLayout(self)
        
        # Image display
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet("background-color: #000; border-radius: 5px;")
        self._image_label.setMinimumSize(300, 200)
        layout.addWidget(self._image_label)
        
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
        
        # Copy button
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        copy_button.clicked.connect(self._on_copy)
        nav_layout.addWidget(copy_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        nav_layout.addWidget(close_button)
        
        layout.addLayout(nav_layout)
    
    def _load_frame(self):
        """Load the frame image."""
        if os.path.exists(self.metadata.file_path):
            try:
                pixmap = QPixmap(self.metadata.file_path)
                if not pixmap.isNull():
                    # Scale to fit in preview area
                    max_width = 600
                    max_height = 400
                    scaled = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self._image_label.setPixmap(scaled)
                    self._nav_label.setText(f"Frame {self.metadata.index}")
            except Exception:
                self._image_label.setText("Failed to load image")
    
    def _on_prev(self):
        """Navigate to previous frame."""
        if self.parentWidget():
            gallery = self.parentWidget()
            if isinstance(gallery, FrameGallery):
                for i, thumb in enumerate(gallery._thumbnails):
                    if thumb._metadata and thumb._metadata.index == self.metadata.index:
                        if i > 0:
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
                            next_thumb = gallery._thumbnails[i + 1]
                            self.metadata = next_thumb._metadata
                            self.setWindowTitle(f"Frame #{self.metadata.index}")
                            self._load_frame()
                            gallery._selected_thumbnail = next_thumb
                            next_thumb.set_selected(True)
                        break
    
    def _on_copy(self):
        """Copy frame to clipboard."""
        if copy_to_clipboard(self.metadata.file_path):
            self.copy_requested = True
            self.accept()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Failed to copy to clipboard")