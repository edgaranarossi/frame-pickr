"""Frame capture engine for the Frame Capture Application.

Handles screen capture operations using Windows screen capture APIs.
"""

import os
import time
from datetime import datetime
from typing import Optional, Tuple

import numpy as np
from PIL import Image
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot


class FrameCaptureEngine(QObject):
    """Engine for capturing screen frames at a defined region.
    
   Signals:
        frameCaptured: Emitted when a frame is captured
            Args: (frame_data: np.ndarray, timestamp: float)
        captureStarted: Emitted when capture starts
        captureStopped: Emitted when capture stops
        capturePaused: Emitted when capture is paused
        captureResumed: Emitted when capture is resumed
        errorOccurred: Emitted when an error occurs
            Args: (error_message: str)
    """
    
    frameCaptured = pyqtSignal(np.ndarray, float)
    captureStarted = pyqtSignal()
    captureStopped = pyqtSignal()
    capturePaused = pyqtSignal()
    captureResumed = pyqtSignal()
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, bounding_box: Tuple[int, int, int, int], interval: int = 500):
        """Initialize the frame capture engine.
        
        Args:
            bounding_box: Tuple of (x, y, width, height) for capture region
            interval: Capture interval in milliseconds (default: 500ms = 2fps)
        """
        super().__init__()
        self.bounding_box = bounding_box  # (x, y, width, height)
        self.interval = interval
        self._is_running = False
        self._is_paused = False
        self._timer = None
        self._capture_thread = None
        self._latest_frame = None
        self._latest_timestamp = None
        
    def start_capture(self) -> bool:
        """Start frame capture.
        
        Returns:
            True if capture started successfully, False otherwise
        """
        if self._is_running:
            return False
            
        try:
            # Validate bounding box
            x, y, width, height = self.bounding_box
            if width <= 0 or height <= 0:
                self.errorOccurred.emit("Invalid bounding box dimensions")
                return False
            
            self._is_running = True
            self._is_paused = False
            
            # Set up timer for periodic capture
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._on_timer_timeout)
            self._timer.start(self.interval)
            
            self.captureStarted.emit()
            return True
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to start capture: {str(e)}")
            return False
    
    def stop_capture(self) -> bool:
        """Stop frame capture.
        
        Returns:
            True if capture stopped successfully, False otherwise
        """
        if not self._is_running:
            return False
            
        try:
            if self._timer:
                self._timer.stop()
                self._timer = None
                
            self._is_running = False
            self._is_paused = False
            
            self.captureStopped.emit()
            return True
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to stop capture: {str(e)}")
            return False
    
    def pause_capture(self) -> bool:
        """Pause frame capture.
        
        Returns:
            True if capture paused successfully, False otherwise
        """
        if not self._is_running or self._is_paused:
            return False
            
        try:
            if self._timer:
                self._timer.stop()
            self._is_paused = True
            
            self.capturePaused.emit()
            return True
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to pause capture: {str(e)}")
            return False
    
    def resume_capture(self) -> bool:
        """Resume frame capture.
        
        Returns:
            True if capture resumed successfully, False otherwise
        """
        if not self._is_running or not self._is_paused:
            return False
            
        try:
            if self._timer:
                self._timer.start(self.interval)
            self._is_paused = False
            
            self.captureResumed.emit()
            return True
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to resume capture: {str(e)}")
            return False
    
    def capture_frame(self) -> Optional[Tuple[np.ndarray, float]]:
        """Capture a single frame.
        
        Returns:
            Tuple of (frame_data, timestamp) or None if capture fails
        """
        try:
            # Use mss library for screen capture
            frame_data = self._capture_screen_region()
            if frame_data is None:
                self.errorOccurred.emit("Screen capture failed")
                return None
                
            timestamp = time.time()
            self._latest_frame = frame_data
            self._latest_timestamp = timestamp
            
            self.frameCaptured.emit(frame_data, timestamp)
            return (frame_data, timestamp)
            
        except Exception as e:
            self.errorOccurred.emit(f"Frame capture failed: {str(e)}")
            return None
    
    def get_latest_frame(self) -> Optional[Tuple[np.ndarray, float]]:
        """Get the most recently captured frame.
        
        Returns:
            Tuple of (frame_data, timestamp) or None
        """
        if self._latest_frame is not None:
            return (self._latest_frame, self._latest_timestamp)
        return None
    
    def _capture_screen_region(self) -> Optional[np.ndarray]:
        """Capture a region of the screen.
        
        Returns:
            Frame as numpy array (BGR format) or None
        """
        try:
            # Try to use mss for screen capture (cross-platform)
            import mss
            
            x, y, width, height = self.bounding_box
            monitor = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            with mss.mss() as sct:
                screenshot = sct.grab(monitor)
                # Convert to numpy array
                frame = np.array(screenshot)
                # Convert BGRA to BGR (remove alpha channel)
                if frame.shape[2] == 4:
                    frame = frame[:, :, :3]
                return frame
                
        except ImportError:
            # Fallback: Try using win32gui and win32api
            try:
                import win32gui
                import win32ui
                from ctypes import windll
                
                x, y, width, height = self.bounding_box
                
                hdesktop = win32gui.GetDesktopWindow()
                hwindowDC = win32gui.GetWindowDC(hdesktop)
                hcdc = win32ui.CreateDCFromHandle(hwindowDC)
                mcdc = hcdc.CreateCompatibleDC()
                
                bitmaps = win32ui.CreateBitmap()
                bitmaps.CreateCompatibleBitmap(hcdc, width, height)
                mcdc.SelectObject(bitmaps)
                
                # Copy from desktop to memory DC
                result = mcdc.BitBlt((0, 0), (width, height), hcdc, (x, y), win32con.SRCCOPY)
                
                if result:
                    # Get bitmap data
                    bmpinfo = bitmaps.GetInfo()
                    bmpstr = bitmaps.GetBitmapBits(True)
                    
                    # Create image from raw data
                    frame = np.frombuffer(bmpstr, dtype='uint8').reshape((height, width, 4))
                    # Convert BGRA to BGR
                    frame = frame[:, :, :3]
                    return frame
                    
            except ImportError:
                self.errorOccurred.emit("Screen capture libraries not available. Install: pip install mss")
            except Exception as e:
                self.errorOccurred.emit(f"Screen capture failed: {str(e)}")
        
        return None
    
    def _on_timer_timeout(self):
        """Handle timer timeout for periodic capture."""
        if self._is_paused:
            return
        self.capture_frame()