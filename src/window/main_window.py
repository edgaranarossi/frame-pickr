"""Main window for the Frame Capture Application.

Provides the primary GUI interface with all controls and displays.
"""

import os
from typing import Optional, Tuple

from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QGridLayout, QScrollArea, QSizePolicy, QSpinBox,
    QMessageBox
)
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPen, QBrush

from utils.paths import get_temp_directory
from utils.config import Config
from utils.clipboard import copy_to_clipboard
from capture.frame_capture import FrameCaptureEngine
from cache.frame_cache import FrameCache
from selection.bbox_selector import BBoxSelector
from gallery.frame_gallery import FrameGallery


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.config = Config()
        self.frame_cache = FrameCache(max_frames=self.config.max_frames)
        self.frame_capture: Optional[FrameCaptureEngine] = None
        self.bbox_selector: Optional[BBoxSelector] = None
        self.gallery: Optional[FrameGallery] = None
        
        self._bounding_box: Optional[Tuple[int, int, int, int]] = None
        self._capture_running = False
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Frame Capture Tool")
        self.setMinimumSize(900, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title label
        title_label = QLabel("Frame Capture Tool")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Status bar
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #666;")
        main_layout.addWidget(self.status_label)
        
        # Control bar
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # Gallery area
        gallery_container = self._create_gallery_container()
        main_layout.addWidget(gallery_container, stretch=1)
    
    def _create_control_bar(self) -> QWidget:
        """Create the control bar with all buttons."""
        control_bar = QFrame()
        control_bar.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        control_bar.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 5px;
            }
        """)
        
        layout = QHBoxLayout(control_bar)
        layout.setSpacing(15)
        
        # Set Bounding Box button
        self.bbox_button = QPushButton("Set Bounding Box")
        self.bbox_button.clicked.connect(self._on_set_bbox)
        layout.addWidget(self.bbox_button)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep1)
        
        # Start/Pause button
        self.capture_button = QPushButton("Start Capture")
        self.capture_button.clicked.connect(self._on_toggle_capture)
        self.capture_button.setMinimumWidth(120)
        layout.addWidget(self.capture_button)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep2)
        
        # Frame interval
        layout.addWidget(QLabel("Interval:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 5000)
        self.interval_spin.setValue(self.config.capture_interval)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.valueChanged.connect(self._on_interval_changed)
        layout.addWidget(self.interval_spin)
        
        # Frame count display
        self.frame_count_label = QLabel("Frames: 0")
        layout.addWidget(self.frame_count_label)
        
        layout.addStretch()
        
        return control_bar
    
    def _create_gallery_container(self) -> QWidget:
        """Create the gallery container."""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        container.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Gallery title
        title = QLabel("Captured Frames")
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)
        
        # Scroll area for gallery
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.gallery = FrameGallery(self)
        scroll_area.setWidget(self.gallery)
        
        layout.addWidget(scroll_area)
        
        return container
    
    def _on_set_bbox(self):
        """Handle bounding box selection."""
        if self._capture_running:
            QMessageBox.information(self, "Capture Running",
                                   "Please pause or stop capture before selecting a region.")
            return
        
        # Create or update bbox selector
        if self.bbox_selector is None:
            self.bbox_selector = BBoxSelector(self)
            self.bbox_selector.bboxSelected.connect(self._on_bbox_selected)
        
        # Show bbox selector
        self.bbox_selector.show()
        self.bbox_selector.raise_()
    
    def _on_bbox_selected(self, x: int, y: int, width: int, height: int):
        """Handle bounding box selection completion."""
        if width <= 0 or height <= 0:
            return
        
        self._bounding_box = (x, y, width, height)
        self.config.last_bbox = f"{x},{y},{width},{height}"
        self.config.sync()
        
        if self.bbox_selector:
            self.bbox_selector.close()
            self.bbox_selector = None
    
    def _on_toggle_capture(self):
        """Handle capture start/pause toggle."""
        if self._bounding_box is None:
            QMessageBox.warning(self, "No Region",
                              "Please select a bounding box first.")
            return
        
        if not self._capture_running:
            # Start capture
            self._start_capture()
        elif self.frame_capture:
            if self.frame_capture._is_paused:
                # Resume capture
                if self.frame_capture.resume_capture():
                    self._capture_running = True
                    self.capture_button.setText("Pause")
            else:
                # Pause capture
                if self.frame_capture.pause_capture():
                    self._capture_running = False
                    self.capture_button.setText("Resume")
    
    def _start_capture(self):
        """Start frame capture."""
        if self._bounding_box is None:
            return
        
        if self.frame_capture is not None:
            self.frame_capture.stop_capture()
        
        self.frame_capture = FrameCaptureEngine(
            self._bounding_box,
            interval=self.config.capture_interval
        )
        
        # Connect signals
        self.frame_capture.captureStarted.connect(self._on_capture_started)
        self.frame_capture.captureStopped.connect(self._on_capture_stopped)
        self.frame_capture.capturePaused.connect(self._on_capture_paused)
        self.frame_capture.captureResumed.connect(self._on_capture_resumed)
        self.frame_capture.frameCaptured.connect(self._on_frame_captured)
        self.frame_capture.errorOccurred.connect(self._on_capture_error)
        
        if self.frame_capture.start_capture():
            self._capture_running = True
            self.capture_button.setText("Pause")
            self.status_label.setText("Status: Capturing frames...")
    
    def _on_capture_started(self):
        """Handle capture started signal."""
        self.status_label.setText("Status: Capturing frames...")
    
    def _on_capture_stopped(self):
        """Handle capture stopped signal."""
        self._capture_running = False
        self.capture_button.setText("Start Capture")
        self.status_label.setText("Status: Ready")
    
    def _on_capture_paused(self):
        """Handle capture paused signal."""
        self._capture_running = False
        self.capture_button.setText("Resume")
        self.status_label.setText("Status: Paused")
    
    def _on_capture_resumed(self):
        """Handle capture resumed signal."""
        self._capture_running = True
        self.capture_button.setText("Pause")
        self.status_label.setText("Status: Capturing frames...")
    
    def _on_frame_captured(self, frame_data, timestamp):
        """Handle frame captured signal."""
        if self.frame_cache is None:
            return
        
        metadata = self.frame_cache.add_frame(frame_data, timestamp)
        
        # Update gallery if new frame was added
        if metadata:
            self.gallery.update_frame(metadata)
            
            # Update frame count display
            self.frame_count_label.setText(f"Frames: {self.frame_cache.frame_count}/{self.frame_cache.max_frames}")
    
    def _on_capture_error(self, error_message: str):
        """Handle capture error signal."""
        QMessageBox.warning(self, "Capture Error", error_message)
        self.status_label.setText(f"Status: Error - {error_message}")
    
    def _on_interval_changed(self, value: int):
        """Handle interval change."""
        self.config.capture_interval = value
        if self.frame_capture is not None:
            self.frame_capture.interval = value
    
    def _load_config(self):
        """Load saved configuration."""
        if self._bounding_box is None:
            last_bbox = self.config.last_bbox
            if last_bbox:
                try:
                    parts = last_bbox.split(',')
                    if len(parts) == 4:
                        x, y, w, h = map(int, parts)
                        self._bounding_box = (x, y, w, h)
                        self.status_label.setText(f"Status: Region loaded ({w}x{h})")
                except (ValueError, AttributeError):
                    pass