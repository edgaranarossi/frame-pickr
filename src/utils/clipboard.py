"""Clipboard operations for the Frame Capture Application.

Handles copying images to and from the system clipboard.
"""

import os
import logging
import struct
from datetime import datetime

# Setup logging
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frame_capture.log')


def log_error(message: str):
    """Log an error message with timestamp to the log file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] ERROR: {message}\n"
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception:
        pass  # Silently fail if log can't be written


def copy_image_to_clipboard_windows(image_path: str) -> bool:
    """Copy an image file to the clipboard using Windows API directly.

    Uses ctypes with proper OleInitialize/OleUninitialize calls to copy
    an image to the clipboard. This avoids Qt's problematic clipboard API
    that causes COM errors on Windows.

    Args:
        image_path: Path to the PNG image file

    Returns:
        True if successful, False otherwise
    """
    try:
        import ctypes
        from ctypes import wintypes

        # Load required libraries
        ole32 = ctypes.WinDLL('ole32', use_last_error=True)
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

        # Function prototypes
        ole32.OleInitialize.argtypes = [ctypes.c_long]
        ole32.OleInitialize.restype = wintypes.HRESULT
        ole32.OleUninitialize.argtypes = []
        ole32.OleUninitialize.restype = None

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.argtypes = []
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE

        ole32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        ole32.GlobalAlloc.restype = wintypes.HGLOBAL
        ole32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        ole32.GlobalLock.restype = wintypes.LPVOID
        ole32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        ole32.GlobalUnlock.restype = wintypes.BOOL
        ole32.GlobalSize.argtypes = [wintypes.HGLOBAL]
        ole32.GlobalSize.restype = ctypes.c_size_t

        # Check file exists
        if not os.path.exists(image_path):
            return False

        # Use PIL to load and convert image to BMP format
        try:
            from PIL import Image
            import io

            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save to memory as BMP
            output = io.BytesIO()
            img.save(output, format='BMP')
            bmp_data = output.getvalue()
            output.close()

            # Remove BMP header (14 bytes) + DIB header size (40 bytes = 54 total)
            # The DIB data starts at offset 54
            if len(bmp_data) <= 54:
                log_error(f"Invalid BMP data in {image_path}")
                return False
            bitmap = bmp_data[54:]

        except Exception as e:
            log_error(f"PIL image processing failed: {type(e).__name__}: {e}")
            return False

        # Initialize OLE (required for clipboard operations)
        result = ole32.OleInitialize(0)
        if result < 0:  # S_FALSE or error
            log_error(f"OleInitialize failed with HRESULT: {result:#010x}")
            return False

        try:
            # Open clipboard
            if not user32.OpenClipboard(0):
                error = ctypes.get_last_error()
                log_error(f"OpenClipboard failed with error {error}")
                return False

            try:
                if not user32.EmptyClipboard():
                    error = ctypes.get_last_error()
                    log_error(f"EmptyClipboard failed with error {error}")
                    return False

                # Allocate global memory for the DIB data
                gmem = ole32.GlobalAlloc(0x0042, len(bitmap))  # GHND = 0x0042
                if not gmem:
                    error = ctypes.get_last_error()
                    log_error(f"GlobalAlloc failed with error {error}")
                    return False

                try:
                    # Lock memory and copy data
                    mem = ole32.GlobalLock(gmem)
                    if not mem:
                        error = ctypes.get_last_error()
                        log_error(f"GlobalLock failed with error {error}")
                        return False

                    try:
                        ctypes.memmove(mem, bitmap, len(bitmap))
                    finally:
                        ole32.GlobalUnlock(gmem)

                    # Set clipboard data (CF_DIB = 8)
                    result = user32.SetClipboardData(8, gmem)
                    if not result:
                        error = ctypes.get_last_error()
                        log_error(f"SetClipboardData failed with error {error}")
                        return False

                    # Success - memory is now owned by the clipboard
                    # Don't free it, the system will handle it
                    gmem = None
                    return True

                finally:
                    if gmem:
                        ole32.GlobalFree(gmem)

            finally:
                user32.CloseClipboard()

        finally:
            ole32.OleUninitialize()

    except Exception as e:
        log_error(f"copy_image_to_clipboard_windows failed: {type(e).__name__}: {e}")
        return False


def copy_to_clipboard(image_path: str) -> bool:
    """Copy an image file to the clipboard.

    Args:
        image_path: Path to the PNG image file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check file exists
        if not os.path.exists(image_path):
            return False

        # Try Windows API first (most reliable for images)
        try:
            if copy_image_to_clipboard_windows(image_path):
                return True
        except Exception as e:
            log_error(f"Windows clipboard failed: {type(e).__name__}: {e}")
            pass

        # Try pyperclip as fallback - copies file path as text
        try:
            import pyperclip
            pyperclip.copy(image_path)
            return True
        except Exception as e:
            log_error(f"pyperclip failed: {type(e).__name__}: {e}")
            pass

        return False

    except Exception as e:
        log_error(f"copy_to_clipboard failed: {type(e).__name__}: {e}")
        return False


def get_clipboard_image() -> 'QImage':
    """Get an image from the clipboard.

    Returns:
        QImage if available, otherwise a null QImage
    """
    try:
        from PyQt5.QtGui import QImage
        from PyQt5.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard is None:
            return QImage()

        return clipboard.image()
    except Exception as e:
        log_error(f"get_clipboard_image failed: {type(e).__name__}: {e}")
        return QImage()


def is_image_available() -> bool:
    """Check if there's an image in the clipboard.

    Returns:
        True if an image is available, False otherwise
    """
    try:
        from PyQt5.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard is None:
            return False

        mime_data = clipboard.mimeData()
        return mime_data is not None and mime_data.hasImage()
    except Exception as e:
        log_error(f"is_image_available failed: {type(e).__name__}: {e}")
        return False
