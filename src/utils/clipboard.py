"""Clipboard operations for the Frame Capture Application.

Handles copying images to and from the system clipboard.
"""

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication
import os


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
        
        # Load image
        image = QImage(image_path)
        if image.isNull():
            return False
        
        # Get clipboard and set image
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return False
        
        clipboard.setPixmap(QPixmap.fromImage(image))
        return True
        
    except Exception:
        return False


def get_clipboard_image() -> QImage:
    """Get an image from the clipboard.
    
    Returns:
        QImage if available, otherwise a null QImage
    """
    clipboard = QApplication.clipboard()
    if clipboard is None:
        return QImage()
    
    mime_data = clipboard.mimeData()
    if mime_data is None or not mime_data.hasImage():
        return QImage()
    
    return clipboard.image()


def is_image_available() -> bool:
    """Check if there's an image in the clipboard.
    
    Returns:
        True if an image is available, False otherwise
    """
    clipboard = QApplication.clipboard()
    if clipboard is None:
        return False
    
    mime_data = clipboard.mimeData()
    return mime_data is not None and mime_data.hasImage()