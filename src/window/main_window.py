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
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPen, QBrush, QIcon

from utils.paths import get_temp_directory
from utils.config import Config
from capture.frame_capture import FrameCaptureEngine
from cache.frame_cache import FrameCache
from selection.bbox_selector import BBoxSelector
from gallery.frame_gallery import FrameGallery


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, progress_callback=None):
        """Initialize the main window.

        Args:
            progress_callback: Optional callback to report progress during frame loading
        """
        super().__init__()
        self.config = Config()
        self.frame_cache = FrameCache(max_frames=self.config.max_frames, progress_callback=progress_callback)
        self.frame_capture: Optional[FrameCaptureEngine] = None
        self.bbox_selector: Optional[BBoxSelector] = None
        self.gallery: Optional[FrameGallery] = None

        self._bounding_box: Optional[Tuple[int, int, int, int]] = None
        self._capture_running = False

        self._setup_ui()
        # Remove icon from title bar
        self.setWindowIcon(QIcon())
        self._load_config()
        self._load_existing_frames(progress_callback)

        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Windows global hotkey using native API
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL('user32.dll')

            # Register global hotkey - Ctrl+Alt+F8 = ModCtrl + ModAlt + VK_F8
            # ID 1 for capture hotkey
            result = user32.RegisterHotKey(
                int(self.winId()),
                1,  # Hotkey ID
                0x0003,  # MOD_CTRL + MOD_ALT
                0x77  # VK_F8
            )
            # Debug: print result
            print(f"RegisterHotKey result: {result}, error: {ctypes.get_last_error()}")
            if result:
                self._global_hotkey_enabled = True
            else:
                self._global_hotkey_enabled = False
        except Exception as e:
            print(f"Hotkey registration error: {e}")
            self._global_hotkey_enabled = False

    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Frame Capture Tool")
        self.setMinimumSize(1100, 600)

        # Restore saved window geometry
        self._restore_window_geometry()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

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
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ffffff, stop: 1 #f0f4f8);
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(control_bar)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)

        # Row 1: Start/Pause button (full width)
        capture_row = QHBoxLayout()
        capture_row.setSpacing(15)

        # Start/Pause button - modern styling with gradient (full width)
        self.capture_button = QPushButton("Start Capture")
        self.capture_button.clicked.connect(self._on_toggle_capture)
        self.capture_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.capture_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4caf50, stop: 1 #388e3c);
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #66bb6a, stop: 1 #4caf50);
            }
            QPushButton:pressed {
                background: #2e7d32;
            }
        """)
        capture_row.addWidget(self.capture_button)

        layout.addLayout(capture_row)

        # Row 2: Set Bounding Box button and config controls
        config_row = QHBoxLayout()
        config_row.setSpacing(10)
        config_row.setStretch(1, 1)  # Make separators and widgets stretch equally

        # Set Bounding Box button - modern styling
        self.bbox_button = QPushButton("Set Bounding Box")
        self.bbox_button.clicked.connect(self._on_set_bbox)
        self.bbox_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2196f3, stop: 1 #1976d2);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #42a5f5, stop: 1 #2196f3);
            }
            QPushButton:pressed {
                background: #1565c0;
            }
        """)
        config_row.addWidget(self.bbox_button)

        # Separator
        sep_bbox = QFrame()
        sep_bbox.setFrameShape(QFrame.VLine)
        sep_bbox.setFrameShadow(QFrame.Sunken)
        sep_bbox.setMaximumWidth(2)
        config_row.addWidget(sep_bbox)

        # Bounding box coordinate display
        self.bbox_coord_label = QLabel("No region selected")
        self.bbox_coord_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                font-size: 10pt;
                background-color: #e3f2fd;
                padding: 8px 12px;
                border-radius: 4px;
                min-width: 120px;
                border: 1px solid #bbdefb;
            }
        """)
        self.bbox_coord_label.setAlignment(Qt.AlignCenter)
        config_row.addWidget(self.bbox_coord_label)
        config_row.setStretchFactor(self.bbox_coord_label, 1)

        # Separator
        sep_config = QFrame()
        sep_config.setFrameShape(QFrame.VLine)
        sep_config.setFrameShadow(QFrame.Sunken)
        sep_config.setMaximumWidth(2)
        config_row.addWidget(sep_config)

        # Frame interval - modern styling
        interval_label = QLabel("Interval:")
        config_row.addWidget(interval_label)
        config_row.setStretchFactor(interval_label, 1)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 5000)
        self.interval_spin.setValue(self.config.capture_interval)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.valueChanged.connect(self._on_interval_changed)
        self.interval_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: white;
            }
            QSpinBox:hover {
                border-color: #2196f3;
            }
            QSpinBox::up-button {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f5f5f5, stop: 1 #e0e0e0);
                border-radius: 3px;
            }
            QSpinBox::down-button {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f5f5f5, stop: 1 #e0e0e0);
                border-radius: 3px;
            }
        """)
        config_row.addWidget(self.interval_spin)
        config_row.setStretchFactor(self.interval_spin, 1)

        # Separator
        sep_interval = QFrame()
        sep_interval.setFrameShape(QFrame.VLine)
        sep_interval.setFrameShadow(QFrame.Sunken)
        sep_interval.setMaximumWidth(2)
        config_row.addWidget(sep_interval)

        # Max frames - modern styling
        max_frames_label = QLabel("Max Frames:")
        config_row.addWidget(max_frames_label)
        config_row.setStretchFactor(max_frames_label, 1)
        self.max_frames_spin = QSpinBox()
        self.max_frames_spin.setRange(10, 1000)
        self.max_frames_spin.setValue(self.config.max_frames)
        self.max_frames_spin.valueChanged.connect(self._on_max_frames_changed)
        self.max_frames_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: white;
            }
            QSpinBox:hover {
                border-color: #2196f3;
            }
            QSpinBox::up-button {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f5f5f5, stop: 1 #e0e0e0);
                border-radius: 3px;
            }
            QSpinBox::down-button {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f5f5f5, stop: 1 #e0e0e0);
                border-radius: 3px;
            }
        """)
        config_row.addWidget(self.max_frames_spin)
        config_row.setStretchFactor(self.max_frames_spin, 1)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        sep2.setMaximumWidth(2)
        config_row.addWidget(sep2)

        # Frame count display
        self.frame_count_label = QLabel("Frames: 0")
        self.frame_count_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 5px 12px;
                border-radius: 4px;
                color: #1976d2;
                font-weight: bold;
            }
        """)
        config_row.addWidget(self.frame_count_label)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFrameShadow(QFrame.Sunken)
        sep3.setMaximumWidth(2)
        config_row.addWidget(sep3)

        # Clear button - modern styling
        self.clear_button = QPushButton("Clear Gallery")
        self.clear_button.clicked.connect(self._on_clear_gallery)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ff7043, stop: 1 #f4511e);
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ff8a65, stop: 1 #ff7043);
            }
            QPushButton:pressed {
                background: #e64a19;
            }
        """)
        config_row.addWidget(self.clear_button)

        config_row.addStretch()
        layout.addLayout(config_row)

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

        # Update coordinate display
        self.update_bbox_display(x, y, width, height)

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
            self.capture_button.setText("Pause")
        elif self.frame_capture:
            if self.frame_capture._is_paused:
                # Resume capture
                if self.frame_capture.resume_capture():
                    self._capture_running = True
                    self.capture_button.setText("Pause")
                    self._update_capture_button_style("yellow")
            else:
                # Pause capture
                if self.frame_capture.pause_capture():
                    self._capture_running = False
                    self.capture_button.setText("Resume")
                    self._update_capture_button_style("green")

    def _update_capture_button_style(self, state):
        """Update capture button style based on state.

        Args:
            state: "green" for resume, "yellow" for pause
        """
        if state == "green":
            self.capture_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #4caf50, stop: 1 #388e3c);
                    color: white;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #66bb6a, stop: 1 #4caf50);
                }
                QPushButton:pressed {
                    background: #2e7d32;
                }
            """)
        else:  # yellow for resume
            self.capture_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #ffeb3b, stop: 1 #fbc02d);
                    color: black;
                    padding: 12px 20px;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #fff176, stop: 1 #f9a825);
                }
                QPushButton:pressed {
                    background: #f57f17;
                }
            """)
    
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
            self._update_capture_button_style("yellow")
            self.status_label.setText("Status: Capturing frames...")

    def _on_capture_started(self):
        """Handle capture started signal."""
        self.status_label.setText("Status: Capturing frames...")

    def _on_capture_stopped(self):
        """Handle capture stopped signal."""
        self._capture_running = False
        self.capture_button.setText("Start Capture")
        self._update_capture_button_style("green")
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

    def _on_max_frames_changed(self, value: int):
        """Handle max_frames change."""
        self.config.max_frames = value
        if self.frame_cache is not None:
            self.frame_cache.max_frames = value
            # Update frame count display to show new max
            self.frame_count_label.setText(f"Frames: {self.frame_cache.frame_count}/{self.frame_cache.max_frames}")
    
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
                        self.update_bbox_display(x, y, w, h)
                except (ValueError, AttributeError):
                    pass

    def _restore_window_geometry(self):
        """Restore window geometry from saved settings."""
        geometry = self.config.window_geometry
        if geometry:
            self.restoreGeometry(geometry)

    def _save_window_geometry(self):
        """Save current window geometry to settings."""
        self.config.window_geometry = self.saveGeometry()

    def _load_existing_frames(self, progress_callback=None):
        """Load existing frames from cache into the gallery.

        Args:
            progress_callback: Optional callback to report progress (current, total)
        """
        if self.frame_cache is None or self.gallery is None:
            return

        frames = self.frame_cache.get_all_frames()
        if frames:
            self.gallery.load_frames(frames)
            self.frame_count_label.setText(f"Frames: {self.frame_cache.frame_count}/{self.frame_cache.max_frames}")

    def _on_clear_gallery(self):
        """Clear the gallery and delete cached frames."""
        reply = QMessageBox.question(
            self,
            "Clear Gallery",
            "Are you sure you want to clear the gallery and delete all cached frames?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.frame_cache:
                count = self.frame_cache.clear_cache()
                if self.gallery:
                    self.gallery.clear()
                self.status_label.setText(f"Status: Cleared {count} frames")
                self.bbox_coord_label.setText("No region selected")

    def nativeEvent(self, eventType, message):
        """Handle native Windows events for global hotkey."""
        try:
            import ctypes
            import sip
            from ctypes import wintypes

            # Check if this is a hotkey event
            if eventType == 'windows_generic_MSG':
                # Convert sip.voidptr to ctypes pointer
                msg_ptr = sip.voidptr(message)
                msg_ptr_int = int(msg_ptr)
                msg_ptr_casted = ctypes.cast(msg_ptr_int, ctypes.POINTER(wintypes.MSG))
                msg = msg_ptr_casted.contents

                # WM_HOTKEY = 0x0312 = 786
                if msg.message == 786:
                    # Hotkey ID 1 is our capture hotkey
                    if msg.wParam == 1:
                        print("Global hotkey triggered!")
                        self._on_toggle_capture()
                        return True, 0
        except Exception as e:
            print(f"nativeEvent error: {e}")
            import traceback
            traceback.print_exc()
            pass
        return super().nativeEvent(eventType, message)

    def closeEvent(self, event):
        """Handle window close event to save geometry."""
        self._save_window_geometry()
        # Clean up global hotkey
        if getattr(self, '_global_hotkey_enabled', False):
            try:
                import ctypes
                user32 = ctypes.WinDLL('user32.dll')
                user32.UnregisterHotKey(int(self.winId()), 1)
            except Exception:
                pass
        super().closeEvent(event)

    def update_bbox_display(self, x: int, y: int, width: int, height: int):
        """Update the bounding box coordinate display.

        Args:
            x, y: Top-left corner coordinates
            width, height: Dimensions of the selected region
        """
        self.bbox_coord_label.setText(f"({x}, {y}) {width}x{height}")