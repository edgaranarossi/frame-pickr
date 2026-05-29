"""Frame Capture Application entry point.

Main application module that initializes and runs the Qt application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from window.main_window import MainWindow
from utils.paths import ensure_directories


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
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()