"""Bounding box selector for the Frame Capture Application.

Provides a full-screen overlay for selecting a screen region via click-and-drag.
"""

from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QCursor


class BBoxSelector(QWidget):
    """Full-screen overlay for bounding box selection.
    
    Signals:
        bboxSelected: Emitted when region is selected
            Args: (x: int, y: int, width: int, height: int)
    """
    
    bboxSelected = Qt.Signal(int, int, int, int)
    
    def __init__(self, parent=None):
        """Initialize the bounding box selector."""
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._selection_started = False
        self._selection_start = QPoint()
        self._selection_end = QPoint()
        self._current_rect = QRect()
        
        # UI elements (overlay, not shown until selection)
        self._init_ui()
        
        # Show full screen
        self.showFullScreen()
    
    def _init_ui(self):
        """Initialize the overlay UI."""
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 100);
            }
        """)
        
        # Help label
        self._help_label = QLabel("Select region by clicking and dragging")
        self._help_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14pt;
                background-color: rgba(0, 0, 0, 200);
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self._help_label.setAlignment(Qt.AlignCenter)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        cancel_button.clicked.connect(self._on_cancel)
        
        # Confirm button
        confirm_button = QPushButton("Confirm Selection")
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        confirm_button.clicked.connect(self._on_confirm)
        confirm_button.setEnabled(False)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(confirm_button)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self._help_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self._cancel_button = cancel_button
        self._confirm_button = confirm_button
    
    def paintEvent(self, event):
        """Handle paint event for drawing selection overlay."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        # Draw selection rectangle
        if self._selection_started:
            painter.setPen(QPen(QColor(231, 76, 60), 3))  # Red border
            painter.setBrush(QColor(231, 76, 60, 50))  # Semi-transparent fill
            painter.drawRect(self._current_rect)
            
            # Draw dimensions label
            self._draw_dimensions_label(painter)
    
    def _draw_dimensions_label(self, painter: QPainter):
        """Draw dimensions label on the selection."""
        if not self._current_rect.isValid():
            return
        
        width = self._current_rect.width()
        height = self._current_rect.height()
        
        label_text = f"{width} x {height} px"
        
        # Calculate label position
        x = self._current_rect.x() + 5
        y = self._current_rect.y() - 20
        if y < 0:
            y = self._current_rect.y() + self._current_rect.height() + 5
        
        # Draw background
        painter.setPen(QPen(QColor(231, 76, 60), 2))
        painter.setBrush(QColor(255, 255, 255, 240))
        label_rect = painter.boundingRect(x, y, 100, 30, Qt.AlignCenter, label_text)
        painter.drawRoundedRect(label_rect.adjusted(-5, -5, 5, 5), 5, 5)
        
        # Draw text
        painter.setPen(QColor(231, 76, 60))
        painter.drawText(label_rect, Qt.AlignCenter, label_text)
    
    def mousePressEvent(self, event):
        """Handle mouse press to start selection."""
        if event.button() == Qt.LeftButton:
            self._selection_started = True
            self._selection_start = event.pos()
            self._selection_end = event.pos()
            self._current_rect = QRect(self._selection_start, self._selection_end)
            self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move to update selection."""
        if self._selection_started:
            self._selection_end = event.pos()
            self._current_rect = QRect(self._selection_start, self._selection_end)
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to finalize selection."""
        if self._selection_started and event.button() == Qt.LeftButton:
            self._selection_started = False
            self._confirm_button.setEnabled(self._current_rect.isValid())
            self.update()
    
    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key_Escape:
            self._on_cancel()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.close()
    
    def _on_confirm(self):
        """Handle confirm button click."""
        if self._current_rect.isValid():
            self.bboxSelected.emit(
                self._current_rect.x(),
                self._current_rect.y(),
                self._current_rect.width(),
                self._current_rect.height()
            )
            self.close()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Restore cursor
        QCursor.setPos(QCursor.pos())
        super().closeEvent(event)