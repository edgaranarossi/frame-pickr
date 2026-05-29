"""Bounding box selector for the Frame Capture Application.

Provides a full-screen overlay for selecting a screen region via click-and-drag.
"""

from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QCursor, QGuiApplication


class BBoxSelector(QWidget):
    """Full-screen overlay for bounding box selection."""
    
    bboxSelected = pyqtSignal(int, int, int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._selection_started = False
        self._selection_start = QPoint()
        self._selection_end = QPoint()
        self._current_rect = QRect()
        
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            self.setGeometry(screen_geometry)
        
        self._init_ui()
        self.show()
    
    def _init_ui(self):
        self.setStyleSheet("""QWidget { background-color: rgba(0, 0, 0, 150); }""")
        
        self._help_label = QLabel("Select region by clicking and dragging")
        self._help_label.setStyleSheet("""QLabel { color: white; font-size: 14pt; background-color: rgba(0, 0, 0, 200); padding: 10px; border-radius: 5px; }""")
        self._help_label.setAlignment(Qt.AlignCenter)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""QPushButton { background-color: #e74c3c; color: white; padding: 8px 20px; border: none; border-radius: 5px; font-size: 10pt; } QPushButton:hover { background-color: #c0392b; }""")
        cancel_button.clicked.connect(self._on_cancel)
        
        confirm_button = QPushButton("Confirm Selection")
        confirm_button.setStyleSheet("""QPushButton { background-color: #27ae60; color: white; padding: 8px 20px; border: none; border-radius: 5px; font-size: 10pt; } QPushButton:hover { background-color: #219a52; }""")
        confirm_button.clicked.connect(self._on_confirm)
        confirm_button.setEnabled(False)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(confirm_button)
        
        layout = QVBoxLayout()
        layout.addWidget(self._help_label)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self._cancel_button = cancel_button
        self._confirm_button = confirm_button
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        
        if self._selection_started and self._current_rect.isValid():
            painter.setPen(QPen(QColor(33, 150, 243), 3))
            painter.setBrush(QColor(33, 150, 243, 50))
            painter.drawRect(self._current_rect)
            self._draw_dimensions_label(painter)
    
    def _draw_dimensions_label(self, painter):
        if not self._current_rect.isValid():
            return
        
        width = self._current_rect.width()
        height = self._current_rect.height()
        label_text = f"{width} x {height} px"
        
        x = self._current_rect.x() + 10
        y = self._current_rect.y() + 10
        
        painter.setPen(QPen(QColor(33, 150, 243), 2))
        painter.setBrush(QColor(255, 255, 255, 240))
        text_width = len(label_text) * 8 + 20
        text_height = 24
        painter.drawRect(x, y, text_width, text_height)
        
        painter.setPen(QColor(33, 150, 243))
        painter.drawText(x + 10, y + 17, label_text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._selection_started = True
            self._selection_start = event.pos()
            self._selection_end = event.pos()
            self._current_rect = QRect(self._selection_start, self._selection_end)
            self.update()
    
    def mouseMoveEvent(self, event):
        if self._selection_started:
            self._selection_end = event.pos()
            self._current_rect = QRect(self._selection_start, self._selection_end)
            self.update()
    
    def mouseReleaseEvent(self, event):
        if self._selection_started and event.button() == Qt.LeftButton:
            self._selection_started = False
            self._confirm_button.setEnabled(self._current_rect.isValid())
            self.update()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_cancel()
    
    def _on_cancel(self):
        self.close()
    
    def _on_confirm(self):
        if self._current_rect.isValid():
            self.bboxSelected.emit(
                self._current_rect.x(),
                self._current_rect.y(),
                self._current_rect.width(),
                self._current_rect.height()
            )
            self.close()
    
    def closeEvent(self, event):
        super().closeEvent(event)
