"""Frame Capture Application entry point.

Main application module that initializes and runs the Qt application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtGui import QFontDatabase, QPixmap, QColor, QPainter
from PyQt5.QtCore import Qt, QTimer


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from window.main_window import MainWindow
from utils.paths import ensure_directories


class LoadingWindow(QWidget):
    """Loading progress window shown during startup."""

    def __init__(self):
        """Initialize the loading window."""
        super().__init__()
        self.setWindowTitle("Loading...")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)

        # Center on screen
        screen_geometry = QApplication.desktop().screenGeometry()
        window_geometry = self.geometry()
        self.move(
            (screen_geometry.width() - window_geometry.width()) // 2,
            (screen_geometry.height() - window_geometry.height()) // 2
        )

        # Setup UI
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)

        # Loading text
        self.status_label = QLabel("Loading application...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333;")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #4caf50, stop: 1 #388e3c);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def update_status(self, message, progress=None):
        """Update status text and optionally progress.

        Args:
            message: Status message to display
            progress: Optional progress value (0-100)
        """
        self.status_label.setText(message)
        if progress is not None:
            self.progress_bar.setValue(progress)
        QApplication.processEvents()


def main():
    """Main entry point for the application."""
    # Ensure required directories exist
    ensure_directories()

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Frame Capture Tool")
    app.setOrganizationName("FrameCaptureApp")

    # Set application style (modern appearance)
    app.setStyle("Fusion")

    # Load custom stylesheet if available
    styles_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "resources", "styles.qss")
    if os.path.exists(styles_path):
        with open(styles_path, "r") as f:
            app.setStyleSheet(f.read())

    # Create and show loading window
    loading_window = LoadingWindow()
    loading_window.show()

    # Create main window with progress callback
    def load_frames_progress(current, total):
        """Progress callback for frame loading."""
        if total > 0:
            # Scale from 60% to 100% based on progress
            progress = int(60 + (current / total) * 40)
            loading_window.update_status(f"Loading existing frames... ({current}/{total})", progress)
        else:
            loading_window.update_status("Loading existing frames... (0/0)", 100)

    window = MainWindow(progress_callback=load_frames_progress)
    window.show()

    # Close loading window after frames are fully loaded
    loading_window.update_status("Loading existing frames...", 100)
    QTimer.singleShot(100, loading_window.close)

    # Run application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()