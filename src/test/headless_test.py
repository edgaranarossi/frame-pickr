"""Headless testing mode for the Frame Capture Application.

This module provides automated testing capabilities without GUI interaction.
It generates a random bounding box, captures frames for 5 seconds, and validates results.
"""

import os
import sys
import random
import time

# Add parent directories to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(script_dir)
sys.path.insert(0, src_dir)

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QApplication

from capture.frame_capture import FrameCaptureEngine
from cache.frame_cache import FrameCache
import mss


class HeadlessTester(QObject):
    """Headless tester that runs automated capture tests."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_cache = None
        self.capture_engine = None
        self.test_result = {}
        self._capture_start_time = None
        self._frames_captured = 0
        self._expected_frames = 0
        self._run_result = True

    def get_screen_dimensions(self):
        """Get screen dimensions using mss.

        Returns:
            Tuple of (screen_width, screen_height)
        """
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            return monitor['width'], monitor['height']

    def generate_random_bbox(self, screen_width, screen_height):
        """Generate a random bounding box within screen bounds.

        Args:
            screen_width: Width of the screen in pixels
            screen_height: Height of the screen in pixels

        Returns:
            Tuple of (x, y, width, height)
        """
        # Minimum and maximum bounding box sizes
        min_size = 100
        max_size = min(500, min(screen_width, screen_height) // 2)

        width = random.randint(min_size, max_size)
        height = random.randint(min_size, max_size)

        x = random.randint(0, screen_width - width - 1)
        y = random.randint(0, screen_height - height - 1)

        return (x, y, width, height)

    def run_test(self, bounding_box=None, duration_seconds=5):
        """Run the headless capture test.

        Args:
            bounding_box: Optional tuple (x, y, width, height). If None, generates random.
            duration_seconds: Capture duration in seconds (default: 5)

        Returns:
            Dictionary with test results (filled after event loop exits)
        """
        print("=" * 50)
        print("Frame Capture - Headless Test Mode")
        print("=" * 50)

        # Get screen dimensions
        screen_width, screen_height = self.get_screen_dimensions()
        print(f"Screen size: {screen_width}x{screen_height}")

        # Generate or use provided bounding box
        if bounding_box is None:
            bounding_box = self.generate_random_bbox(screen_width, screen_height)
        x, y, width, height = bounding_box
        print(f"Random bounding box: ({x}, {y}, {width}x{height})")

        # Initialize frame cache
        self.frame_cache = FrameCache(max_frames=100)
        print(f"Frame cache initialized (max 100 frames)")

        # Initialize capture engine
        self.capture_engine = FrameCaptureEngine(bounding_box, interval=500)
        self.capture_engine.frameCaptured.connect(self._on_frame_captured)
        self.capture_engine.errorOccurred.connect(self._on_error)
        self.capture_engine.captureStarted.connect(self._on_capture_started)
        self.capture_engine.captureStopped.connect(self._on_capture_stopped)

        # Record start time
        self._capture_start_time = time.time()
        self._frames_captured = 0
        self._expected_frames = int(duration_seconds * 2)  # 2 fps = 500ms interval
        self._run_result = True

        # Start capture
        print(f"Starting capture for {duration_seconds} seconds...")
        success = self.capture_engine.start_capture()

        if not success:
            print("ERROR: Failed to start capture")
            self._run_result = False
            return self._finalize_test()

        # Use QTimer to stop after duration and finalize
        self._stop_timer = QTimer()
        self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self._on_duration_expired)
        self._stop_timer.start(duration_seconds * 1000)

        return self.test_result

    def run_event_loop(self):
        """Run the Qt event loop until test completes."""
        app = QApplication.instance()
        if app:
            app.exec_()
        return self._finalize_test()

    def _on_frame_captured(self, frame_data, timestamp):
        """Handle frame captured signal."""
        self.frame_cache.add_frame(frame_data, timestamp)
        self._frames_captured += 1

    def _on_error(self, error_message):
        """Handle error signal."""
        print(f"Capture error: {error_message}")

    def _on_capture_started(self):
        """Handle capture started signal."""
        print("Capture started")

    def _on_capture_stopped(self):
        """Handle capture stopped signal."""
        elapsed = time.time() - self._capture_start_time
        print(f"Capture stopped after {elapsed:.2f} seconds")

    def _on_duration_expired(self):
        """Handle duration expiration."""
        if self.capture_engine:
            self.capture_engine.stop_capture()

        # Wait a moment for any pending signals, then exit
        QTimer.singleShot(500, self._exit_app)

    def _exit_app(self):
        """Exit the application with appropriate code."""
        result = self._finalize_test()
        exit_code = 0 if result.get('files_exist', 0) > 0 else 1
        QApplication.instance().exit(exit_code)

    def _finalize_test(self):
        """Finalize the test and report results.

        Returns:
            Dictionary with test results
        """
        # Get cache stats
        frames_in_cache = self.frame_cache.frame_count if self.frame_cache else 0
        all_frames = self.frame_cache.get_all_frames() if self.frame_cache else []

        # Check if files were actually saved
        files_exist = 0
        for frame in all_frames:
            if os.path.exists(frame.file_path):
                files_exist += 1

        elapsed = time.time() - self._capture_start_time if self._capture_start_time else 0

        self.test_result = {
            'success': files_exist > 0,
            'frames_captured': self._frames_captured,
            'frames_in_cache': frames_in_cache,
            'files_exist': files_exist,
            'duration_seconds': elapsed,
            'expected_frames': self._expected_frames,
            'bounding_box_used': self.capture_engine.bounding_box if self.capture_engine else None
        }

        # Print results
        print("")
        print("=" * 50)
        print("Frame Capture - Headless Test Mode")
        print("=" * 50)
        if self.capture_engine:
            bb = self.capture_engine.bounding_box
            print(f"Bounding box: {bb[2]}x{bb[3]} at ({bb[0]}, {bb[1]})")
        print(f"Frames captured via signal: {self._frames_captured}")
        print(f"Frame files on disk: {files_exist}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Result: {'PASS' if files_exist > 0 else 'FAIL'}")
        print("=" * 50)

        # Force flush stdout
        sys.stdout.flush()
        sys.stderr.flush()

        return self.test_result


def main():
    """Main entry point for headless testing."""
    # Create headless QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Frame Capture Test")
    app.setOrganizationName("FrameCaptureApp")

    # Run test
    tester = HeadlessTester()
    tester.run_test()

    # Start event loop (this will run until timer expires)
    # app.exec_() returns the exit code passed to QApplication.exit()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
