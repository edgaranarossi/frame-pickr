"""Bounding box selector for the Frame Capture Application.

Provides a full-screen overlay for selecting a screen region via click-and-drag.
Supports multi-monitor setups and allows resizing after selection.
"""

import mss
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QCursor, QPainterPath, QFont, QRegion
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDesktopWidget


class BBoxSelector(QWidget):
    """Full-screen overlay for bounding box selection with multi-monitor support."""

    bboxSelected = pyqtSignal(int, int, int, int)

    # Corner/edge resize handles
    HANDLE_RADIUS = 8  # Circle handle radius
    BUTTON_SPACING = 10
    BUTTON_HEIGHT = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Multi-monitor support using mss
        with mss.mss() as sct:
            # monitors[0] is the combined bounding box of all monitors
            self.monitor = sct.monitors[0]
            # Get individual monitors for constraint checking
            self.monitors = sct.monitors[1:]  # Skip the combined monitor

        # Set window to cover all monitors
        self.setGeometry(
            self.monitor['left'],
            self.monitor['top'],
            self.monitor['width'],
            self.monitor['height']
        )

        self._selection_started = False
        self._selection_start = QPoint()
        self._selection_end = QPoint()
        self._current_rect = QRect()

        self._resizable = False
        self._resize_start = QPoint()
        self._resize_rect = QRect()
        self._resize_edge = None  # 'left', 'right', 'top', 'bottom', or None

        self._moving_bbox = False
        self._move_offset = QPoint()

        self._button_pos = QPoint()
        self._button_rects = {}

        self._init_ui()
        self.show()

    def _init_ui(self):
        self.setStyleSheet("""QWidget { background-color: transparent; }""")

        self._help_label = QLabel("Click and drag to select region. Use corners/edges to resize. Press ESC to cancel.")
        self._help_label.setStyleSheet("""QLabel { color: white; font-size: 12pt; background-color: rgba(0, 0, 0, 200); padding: 10px; border-radius: 5px; }""")
        self._help_label.setAlignment(Qt.AlignCenter)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""QPushButton { background-color: #e74c3c; color: white; padding: 8px 20px; border: none; border-radius: 5px; font-size: 10pt; } QPushButton:hover { background-color: #c0392b; }""")
        cancel_button.clicked.connect(self._on_cancel)

        confirm_button = QPushButton("Accept")
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

        # Hide child widgets since we draw everything in paintEvent
        self._help_label.hide()
        cancel_button.hide()
        confirm_button.hide()

        self._cancel_button = cancel_button
        self._confirm_button = confirm_button

        # Store final selected rect
        self._final_rect = QRect()

    def paintEvent(self, event):
        # Don't call super().paintEvent() to avoid painting child widgets
        # which would create multiple dimming layers

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # If there's a bounding box, create a "hole" in the dimming
        box_rect = None
        if self._final_rect.isValid():
            box_rect = self._final_rect
        elif self._selection_started and self._current_rect.isValid():
            box_rect = self._current_rect

        if box_rect:
            # Create a path for the full screen
            full_rect_path = QPainterPath()
            full_rect_path.addRect(QRectF(self.rect()))

            # Create a path for the box area
            box_path = QPainterPath()
            box_path.addRect(QRectF(box_rect))

            # Create a "hole" by subtracting box from full rect
            border_path = full_rect_path - box_path

            # Fill only the border region with dim color
            painter.fillPath(border_path, QColor(0, 0, 0, 179))  # Darker dim for border

            # Draw the bounding box (not dimmed) on top
            self._draw_bounding_box(painter, box_rect)

            # Draw action buttons near the bounding box
            self._draw_action_buttons(painter, box_rect)
        else:
            # No box yet - dim the entire screen
            painter.fillRect(self.rect(), QColor(0, 0, 0, 179))

            # Draw help label in the center
            self._draw_help_label(painter)

    def _draw_bounding_box(self, painter, rect):
        """Draw the bounding box with circular handles and dimensions label."""
        # Draw box outline with no fill (transparent)
        painter.setPen(QPen(QColor(33, 150, 243), 2))
        painter.setBrush(QColor(0, 0, 0, 0))  # No fill - transparent
        painter.drawRect(rect)

        # Draw circular resize handles
        self._draw_resize_handles(painter, rect)

        # Draw dimensions label
        self._draw_dimensions_label(painter, rect)

    def _draw_resize_handles(self, painter, rect):
        """Draw circular resize handles at corners."""
        painter.setPen(QPen(QColor(33, 150, 243), 2))
        painter.setBrush(QColor(255, 255, 255))

        x, y = rect.x(), rect.y()
        w, h = rect.width(), rect.height()
        r = self.HANDLE_RADIUS

        # Corner handles as circles (centered on corners)
        for cx, cy in [
            (x, y),  # top-left
            (x + w, y),  # top-right
            (x, y + h),  # bottom-left
            (x + w, y + h),  # bottom-right
        ]:
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

    def _get_handle_center(self, edge, rect):
        """Get the center point of a handle based on edge name."""
        x, y = rect.x(), rect.y()
        w, h = rect.width(), rect.height()
        r = self.HANDLE_RADIUS

        centers = {
            'top-left': (x, y),
            'top-right': (x + w, y),
            'bottom-left': (x, y + h),
            'bottom-right': (x + w, y + h),
        }
        return centers.get(edge, (x, y))

    def _draw_help_label(self, painter):
        """Draw the help label in the center of the screen."""
        text = "Click and drag to select region. Use corners/edges to resize. Press ESC to cancel."
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)

        metrics = painter.fontMetrics()
        text_width = metrics.width(text)
        text_height = metrics.height()

        screen_width = self.monitor['width']
        screen_height = self.monitor['height']

        x = (screen_width - text_width) // 2
        y = screen_height // 2

        # Draw background with some padding
        padding = 10
        bg_width = text_width + padding * 2
        bg_height = text_height + padding * 2

        painter.setPen(QPen(QColor(33, 150, 243), 2))
        painter.setBrush(QColor(0, 0, 0, 200))
        painter.drawRect(x - padding, y - text_height - padding, bg_width, bg_height)

        # Draw text
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(x, y, text)

    def _draw_dimensions_label(self, painter, rect):
        width = rect.width()
        height = rect.height()
        label_text = f"{width} x {height} px"

        x = rect.x() + 10
        y = rect.y() - 30  # Place above the box

        painter.setPen(QPen(QColor(33, 150, 243), 2))
        painter.setBrush(QColor(255, 255, 255, 240))
        text_width = len(label_text) * 8 + 20
        text_height = 24
        painter.drawRect(x, y, text_width, text_height)

        painter.setPen(QColor(33, 150, 243))
        painter.drawText(x + 10, y + 17, label_text)

    def _get_monitor_for_rect(self, rect):
        """Get the individual monitor that contains this rect.

        Args:
            rect: QRect representing the bounding box (in local widget coordinates)

        Returns:
            Monitor dict with 'left', 'top', 'width', 'height' keys, or None
        """
        if not self.monitors:
            return None

        # Convert rect center from local widget coordinates to global screen coordinates
        # Widget is positioned at (self.monitor['left'], self.monitor['top'])
        global_center_x = rect.center().x() + self.monitor['left']
        global_center_y = rect.center().y() + self.monitor['top']

        for monitor in self.monitors:
            monitor_left = monitor['left']
            monitor_right = monitor_left + monitor['width']
            monitor_top = monitor['top']
            monitor_bottom = monitor_top + monitor['height']

            if (monitor_left <= global_center_x < monitor_right and
                monitor_top <= global_center_y < monitor_bottom):
                return monitor

        return None

    def _draw_action_buttons(self, painter, rect):
        """Draw Cancel, Accept, and Move buttons near the bounding box."""
        padding = 5
        btn_width = 70
        btn_height = 25
        btn_spacing = 8

        # Get monitor for constraint checking
        monitor = self._get_monitor_for_rect(rect)
        if monitor:
            # Convert monitor constraints to local widget coordinates
            # Widget is positioned at (self.monitor['left'], self.monitor['top'])
            # So a point at global (gx, gy) is at local (gx - self.monitor['left'], gy - self.monitor['top'])
            screen_width = monitor['width']
            screen_height = monitor['height']
            monitor_left = monitor['left']
            monitor_top = monitor['top']
        else:
            screen_width = self.monitor['width']
            screen_height = self.monitor['height']
            monitor_left = self.monitor['left']
            monitor_top = self.monitor['top']

        # === Move Button (top center of box) ===
        move_btn_width = 60
        move_btn_height = 24

        # Calculate move button position in local widget coordinates
        move_x = rect.x() + (rect.width() - move_btn_width) // 2
        move_y = rect.y() - move_btn_height - 5  # Above the box

        # Check if move button fits above box (within monitor bounds in local coordinates)
        # Monitor's right edge in local coords = monitor['left'] + monitor['width'] - self.monitor['left']
        # Monitor's bottom edge in local coords = monitor['top'] + monitor['height'] - self.monitor['top']
        monitor_right_local = monitor_left + screen_width - self.monitor['left']
        monitor_bottom_local = monitor_top + screen_height - self.monitor['top']

        if move_y < 0 or move_x < 0 or move_x + move_btn_width > monitor_right_local:
            # Put inside box at top-center
            move_x = rect.x() + (rect.width() - move_btn_width) // 2
            move_y = rect.y() + 2

        self._move_button_rect = QRect(move_x, move_y, move_btn_width, move_btn_height)

        # Draw Move button
        painter.setPen(QPen(QColor(241, 196, 15), 2))
        painter.setBrush(QColor(241, 196, 15))
        painter.drawRect(self._move_button_rect.x(), self._move_button_rect.y(),
                        self._move_button_rect.width(), self._move_button_rect.height())
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self._move_button_rect.x() + 10,
                        self._move_button_rect.y() + 17, "Move")

        # === Accept and Cancel buttons (bottom-right inside or outside) ===
        total_btn_width = btn_width * 2 + btn_spacing
        btn_y = rect.bottom() + padding

        # Get monitor bounds in local widget coordinates
        monitor_right_local = monitor_left + screen_width - self.monitor['left']
        monitor_bottom_local = monitor_top + screen_height - self.monitor['top']

        # Try placing inside bottom-right corner first
        inside_x = rect.right() - total_btn_width - padding
        inside_y = rect.bottom() - btn_height - padding

        # Check if buttons fit inside the box
        buttons_fit_inside = (
            inside_x >= rect.x() + 5 and
            inside_y >= rect.y() + 5 and
            inside_x + total_btn_width <= monitor_right_local and
            inside_y + btn_height <= monitor_bottom_local
        )

        if buttons_fit_inside:
            accept_x = inside_x
            cancel_x = inside_x + btn_width + btn_spacing
            accept_y = cancel_y = inside_y
        else:
            # Place outside bottom-right, constrained to monitor
            cancel_x = rect.right() + padding
            cancel_y = rect.bottom() + padding
            accept_y = cancel_y  # Both buttons at same y position

            # If goes off right edge, move left
            if cancel_x + total_btn_width > monitor_right_local:
                cancel_x = monitor_right_local - total_btn_width - padding

            # If goes off bottom edge, move up
            if cancel_y + btn_height > monitor_bottom_local:
                cancel_y = rect.top() - btn_height - padding
                accept_y = cancel_y

            # If still off top, put at top
            if cancel_y < 0:
                cancel_y = padding
                accept_y = padding

            accept_x = cancel_x + btn_width + btn_spacing

        self._accept_button_rect = QRect(accept_x, accept_y, btn_width, btn_height)
        self._cancel_button_rect = QRect(cancel_x, cancel_y, btn_width, btn_height)

        # Draw Accept button with border
        painter.setPen(QPen(QColor(39, 174, 96), 2))
        painter.setBrush(QColor(39, 174, 96))
        accept_rect = QRect(accept_x, accept_y, btn_width, btn_height)
        painter.drawRect(accept_rect)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(accept_rect.x() + 10, accept_rect.y() + 17, "Accept")

        # Draw Cancel button with border
        painter.setPen(QPen(QColor(231, 76, 60), 2))
        painter.setBrush(QColor(231, 76, 60))
        cancel_rect = QRect(cancel_x, cancel_y, btn_width, btn_height)
        painter.drawRect(cancel_rect)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(cancel_rect.x() + 10, cancel_rect.y() + 17, "Cancel")

        # Store button rectangles for hit testing
        self._button_rects = {
            'cancel': self._cancel_button_rect,
            'accept': self._accept_button_rect,
            'move': self._move_button_rect,
        }

    def _update_button_positions(self, rect):
        """Update button positions without full redraw."""
        if not rect:
            self._button_rects = {}
            return

        padding = 5
        btn_width = 70
        btn_height = 25
        btn_spacing = 8

        # Get monitor for constraint checking
        monitor = self._get_monitor_for_rect(rect)
        if monitor:
            screen_width = monitor['width']
            screen_height = monitor['height']
            monitor_left = monitor['left']
            monitor_top = monitor['top']
        else:
            screen_width = self.monitor['width']
            screen_height = self.monitor['height']
            monitor_left = self.monitor['left']
            monitor_top = self.monitor['top']

        # === Move Button (top center of box) ===
        move_btn_width = 60
        move_btn_height = 24

        move_x = rect.x() + (rect.width() - move_btn_width) // 2
        move_y = rect.y() - move_btn_height - 5

        # Monitor bounds in local coordinates
        monitor_right_local = monitor_left + screen_width - self.monitor['left']
        monitor_bottom_local = monitor_top + screen_height - self.monitor['top']

        if move_y < 0 or move_x < 0 or move_x + move_btn_width > monitor_right_local:
            move_x = rect.x() + (rect.width() - move_btn_width) // 2
            move_y = rect.y() + 2

        self._move_button_rect = QRect(move_x, move_y, move_btn_width, move_btn_height)

        # === Accept and Cancel buttons ===
        total_btn_width = btn_width * 2 + btn_spacing
        monitor_right_local = monitor_left + screen_width - self.monitor['left']
        monitor_bottom_local = monitor_top + screen_height - self.monitor['top']

        # Try placing inside bottom-right corner
        inside_x = rect.right() - total_btn_width - padding
        inside_y = rect.bottom() - btn_height - padding

        buttons_fit_inside = (
            inside_x >= rect.x() + 5 and
            inside_y >= rect.y() + 5 and
            inside_x + total_btn_width <= monitor_right_local and
            inside_y + btn_height <= monitor_bottom_local
        )

        if buttons_fit_inside:
            accept_x = inside_x
            cancel_x = inside_x + btn_width + btn_spacing
            accept_y = cancel_y = inside_y
        else:
            # Place outside
            cancel_x = rect.right() + padding
            cancel_y = rect.bottom() + padding
            accept_y = cancel_y  # Both buttons at same y position

            if cancel_x + total_btn_width > monitor_right_local:
                cancel_x = monitor_right_local - total_btn_width - padding

            if cancel_y + btn_height > monitor_bottom_local:
                cancel_y = rect.top() - btn_height - padding
                accept_y = cancel_y

            if cancel_y < 0:
                cancel_y = padding
                accept_y = padding

            accept_x = cancel_x + btn_width + btn_spacing

        self._accept_button_rect = QRect(accept_x, accept_y, btn_width, btn_height)
        self._cancel_button_rect = QRect(cancel_x, cancel_y, btn_width, btn_height)

        self._button_rects = {
            'cancel': self._cancel_button_rect,
            'accept': self._accept_button_rect,
            'move': self._move_button_rect,
        }

    def get_resize_edge(self, pos, rect):
        """Determine which edge/corner is being clicked."""
        x, y = pos.x(), pos.y()

        # Check corners first (with proper handle center detection)
        # Handle radius is 8, so center is at corner coordinates
        # Use larger hit area for easier clicking (3x handle radius = 24px)
        half_handle = self.HANDLE_RADIUS * 3

        corners = [
            ('top-left', rect.x(), rect.y()),
            ('top-right', rect.x() + rect.width(), rect.y()),
            ('bottom-left', rect.x(), rect.y() + rect.height()),
            ('bottom-right', rect.x() + rect.width(), rect.y() + rect.height()),
        ]

        for edge, cx, cy in corners:
            # Check if point is within circular hit area around corner
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy <= half_handle * half_handle:
                return edge

        # Check edges (with tolerance for dragging from edge)
        edge_tolerance = half_handle

        # Top edge (excluding corners)
        if y >= rect.y() - edge_tolerance and y <= rect.y() + edge_tolerance:
            if x > rect.x() + half_handle and x < rect.x() + rect.width() - half_handle:
                return 'top'

        # Bottom edge (excluding corners)
        if y >= rect.y() + rect.height() - edge_tolerance and y <= rect.y() + rect.height() + edge_tolerance:
            if x > rect.x() + half_handle and x < rect.x() + rect.width() - half_handle:
                return 'bottom'

        # Left edge (excluding corners)
        if x >= rect.x() - edge_tolerance and x <= rect.x() + edge_tolerance:
            if y > rect.y() + half_handle and y < rect.y() + rect.height() - half_handle:
                return 'left'

        # Right edge (excluding corners)
        if x >= rect.x() + rect.width() - edge_tolerance and x <= rect.x() + rect.width() + edge_tolerance:
            if y > rect.y() + half_handle and y < rect.y() + rect.height() - half_handle:
                return 'right'

        # Check if inside the box (for moving)
        if rect.contains(pos):
            return 'move'

        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()

            # Check button clicks first
            if self._button_rects:
                cancel_rect = self._button_rects['cancel']
                accept_rect = self._button_rects['accept']
                move_rect = self._button_rects.get('move', QRect())

                if cancel_rect.contains(pos):
                    self._on_cancel()
                    return
                if accept_rect.contains(pos):
                    self._on_confirm()
                    return
                if move_rect.contains(pos):
                    self._moving_bbox = True
                    self._move_offset = pos - self._final_rect.topLeft()
                    return

            # Check if clicking inside the box for moving
            if self._final_rect and self._final_rect.contains(pos):
                self._moving_bbox = True
                self._move_offset = pos - self._final_rect.topLeft()
                return

            if self._final_rect.isValid():
                # Box already exists - check for resize
                self._resizable = True
                self._resize_edge = self.get_resize_edge(pos, self._final_rect)
                self._resize_start = pos
                self._resize_rect = QRect(self._final_rect)
            else:
                # Start new selection
                self._selection_started = True
                self._selection_start = pos
                self._selection_end = pos
                self._current_rect = QRect(self._selection_start, self._selection_end)

            self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()

        if self._resizable and self._resize_edge:
            # Resize the box
            old_rect = self._resize_rect

            if 'left' in self._resize_edge:
                x = min(pos.x(), old_rect.right() - 10)
                width = old_rect.right() - x
                new_rect = QRect(x, old_rect.y(), width, old_rect.height())
            elif 'right' in self._resize_edge:
                x = old_rect.x()
                width = max(pos.x() - x, 10)
                new_rect = QRect(x, old_rect.y(), width, old_rect.height())
            else:
                new_rect = QRect(old_rect)

            if 'top' in self._resize_edge:
                y = min(pos.y(), new_rect.bottom() - 10)
                height = new_rect.bottom() - y
                new_rect = QRect(new_rect.x(), y, new_rect.width(), height)
            elif 'bottom' in self._resize_edge:
                y = new_rect.y()
                height = max(pos.y() - y, 10)
                new_rect = QRect(new_rect.x(), y, new_rect.width(), height)

            self._final_rect = new_rect
            self._update_button_positions(self._final_rect)
            self.update()
        elif self._moving_bbox and self._final_rect.isValid():
            # Move the box
            new_pos = pos - self._move_offset
            self._final_rect.moveTopLeft(new_pos)
            self._update_button_positions(self._final_rect)
            self.update()
        elif self._selection_started:
            # Continue dragging for new selection
            self._selection_end = pos
            # Use normalized() to handle dragging in any direction
            self._current_rect = QRect(self._selection_start, self._selection_end).normalized()
            self._update_button_positions(self._current_rect)
            self.update()
        else:
            # Hover effect
            if self._button_rects:
                if self._button_rects['cancel'].contains(pos):
                    self.setCursor(Qt.PointingHandCursor)
                    return
                if self._button_rects['accept'].contains(pos):
                    self.setCursor(Qt.PointingHandCursor)
                    return
                if self._button_rects.get('move', QRect()).contains(pos):
                    self.setCursor(Qt.ClosedHandCursor)
                    return

            if self._final_rect.isValid():
                edge = self.get_resize_edge(pos, self._final_rect)
                if edge:
                    self.setCursor(self._get_resize_cursor(edge))
                else:
                    self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.CrossCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._resizable:
                self._resizable = False
                self._resize_edge = None
            elif self._moving_bbox:
                self._moving_bbox = False
            elif self._selection_started:
                self._selection_started = False
                if self._current_rect.isValid():
                    self._final_rect = QRect(self._current_rect)
                    self._current_rect = QRect()
                self._update_button_positions(self._final_rect)
            self.update()

    def _get_resize_cursor(self, edge):
        cursors = {
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
            'top-left': Qt.SizeFDiagCursor,
            'top-right': Qt.SizeBDiagCursor,
            'bottom-left': Qt.SizeBDiagCursor,
            'bottom-right': Qt.SizeFDiagCursor,
            'move': Qt.OpenHandCursor,
        }
        return cursors.get(edge, Qt.ArrowCursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_cancel()

    def _on_cancel(self):
        self.close()

    def _on_confirm(self):
        if self._final_rect.isValid():
            # Convert to screen coordinates relative to all monitors
            screen_x = self._final_rect.x() + self.monitor['left']
            screen_y = self._final_rect.y() + self.monitor['top']
            self.bboxSelected.emit(
                screen_x,
                screen_y,
                self._final_rect.width(),
                self._final_rect.height()
            )
            self.close()

    def closeEvent(self, event):
        super().closeEvent(event)
