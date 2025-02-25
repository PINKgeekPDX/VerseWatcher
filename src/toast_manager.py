from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QLinearGradient, QPen
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
import win32api


def get_real_monitor_rect():
    """Get the actual monitor dimensions using Win32 API"""
    monitor = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))
    return monitor["Monitor"]  # (left, top, right, bottom)


class Toast(QWidget):
    def __init__(self, message, bg_color=QColor(11, 18, 24, 230)):
        super().__init__(None)

        # Set window flags for a frameless, always-on-top window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)

        # Process message
        if isinstance(message, dict):
            title = message.get("title", "")
            details = message.get("details", "")
            event_type = message.get("type", "info")

            # For death events, extract only the essential info
            if "weapon" in details:
                weapon = next(
                    (
                        line.split(": ")[1]
                        for line in details.split("\n")
                        if "🔫 Weapon:" in line
                    ),
                    "",
                )
                if weapon:
                    title = f"{title} • {weapon}"
        else:
            title = message
            event_type = "info"

        # Set color based on event type
        text_color = {
            "death": "#FF4444",  # Red for deaths
            "kill": "#4CAF50",  # Green for kills
            "error": "#FF9800",  # Orange for errors
            "info": "#00A6ED",  # SC Blue for info
            "suicide": "#E040FB",  # Purple for suicides
            "npc": "#FFD740",  # Gold for NPC events
        }.get(event_type, "#FFFFFF")

        # Create single line label
        self.label = QLabel(title)
        font_sizes = {"Small": 11, "Medium": 13, "Large": 15}
        # Get default size if parent is not set
        default_size = "Medium"
        toast_size = (
            default_size
            if not hasattr(self, "parent") or not self.parent()
            else self.parent().size
        )

        self.label.setStyleSheet(f"""
            color: {text_color};
            font-size: {font_sizes.get(toast_size, 13)}px;
            font-weight: bold;
            padding: 2px;
            background: transparent;
        """)
        layout.addWidget(self.label)

        self.bg_color = bg_color

        # Set fixed height and minimum width based on size
        heights = {"Small": 28, "Medium": 36, "Large": 44}
        min_widths = {"Small": 200, "Medium": 300, "Large": 400}
        self.setFixedHeight(heights.get(toast_size, 36))
        self.setMinimumWidth(min_widths.get(toast_size, 300))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 6, 6)

        # Create gradient background
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, self.bg_color)
        gradient.setColorAt(
            0.5,
            QColor(
                min(self.bg_color.red() + 20, 255),
                min(self.bg_color.green() + 20, 255),
                min(self.bg_color.blue() + 20, 255),
                self.bg_color.alpha(),
            ),
        )
        gradient.setColorAt(1, self.bg_color)

        # Draw background with gradient
        painter.fillPath(path, gradient)

        # Draw subtle glow effect
        glow = QPainterPath()
        glow.addRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 6, 6)
        painter.strokePath(glow, QPen(QColor(255, 255, 255, 15), 2))

        # Draw border with gradient
        border_gradient = QLinearGradient(0, 0, self.width(), 0)
        border_gradient.setColorAt(0, QColor(255, 255, 255, 40))
        border_gradient.setColorAt(0.5, QColor(255, 255, 255, 80))
        border_gradient.setColorAt(1, QColor(255, 255, 255, 40))
        painter.strokePath(path, QPen(border_gradient, 1))


class ToastManager:
    def __init__(self):
        self.toasts = []
        self.position = "Bottom Right"
        self.size = "Medium"
        self.duration = 5000  # Default 5 seconds
        self.spacing = 10  # Spacing between toasts
        self.max_toasts = 5  # Maximum number of visible toasts

    def update_config(self, position=None, size=None, duration=None):
        if position:
            self.position = position
        if size:
            self.size = size
        if duration:
            self.duration = duration

    def _show_toast(self, message, bg_color=QColor(11, 18, 24, 230)):
        # Create toast widget
        toast = Toast(message, bg_color)
        toast.parent = self  # Set parent reference for size access

        # Add to list and manage maximum toasts
        self.toasts.append(toast)
        if len(self.toasts) > self.max_toasts:
            oldest_toast = self.toasts.pop(0)
            oldest_toast.hide()
            oldest_toast.deleteLater()

        # Show toast
        toast.show()
        self._position_toasts()

        # Set up fade out timer
        QTimer.singleShot(self.duration - 500, lambda: self._fade_out_toast(toast))

    def _fade_out_toast(self, toast):
        try:
            if toast in self.toasts:
                idx = self.toasts.index(toast)
                self.toasts.pop(idx)
                toast.hide()
                toast.deleteLater()
                self._position_toasts()
        except:
            pass

    def _position_toasts(self):
        if not self.toasts:
            return

        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()

        # Calculate base position based on settings
        positions = {
            "Top Left": (self.spacing, self.spacing),
            "Top Right": (
                screen.width() - self.toasts[0].width() - self.spacing,
                self.spacing,
            ),
            "Bottom Left": (self.spacing, screen.height() - self.spacing),
            "Bottom Right": (
                screen.width() - self.toasts[0].width() - self.spacing,
                screen.height() - self.spacing,
            ),
            "Left Middle": (
                self.spacing,
                (screen.height() - self.toasts[0].height()) // 2,
            ),
            "Right Middle": (
                screen.width() - self.toasts[0].width() - self.spacing,
                (screen.height() - self.toasts[0].height()) // 2,
            ),
        }

        base_x, base_y = positions.get(self.position, positions["Bottom Right"])

        # Position each toast
        total_height = sum(toast.height() + self.spacing for toast in self.toasts)

        for i, toast in enumerate(
            reversed(self.toasts)
        ):  # Reverse the order for proper stacking
            # Calculate position
            if "Bottom" in self.position:
                y = base_y - total_height + (i * (toast.height() + self.spacing))
            elif "Middle" in self.position:
                y = base_y - (total_height // 2) + (i * (toast.height() + self.spacing))
            else:  # Top
                y = base_y + (i * (toast.height() + self.spacing))

            toast.move(base_x, y)
            toast.raise_()  # Ensure proper z-order

    def show_death_toast(self, message, event_type="info"):
        """Show a death event toast with appropriate color"""
        colors = {
            "kill": QColor(46, 125, 50, 230),  # Green for kills
            "death": QColor(198, 40, 40, 230),  # Red for deaths
            "suicide": QColor(156, 39, 176, 230),  # Purple for suicides
            "npc": QColor(255, 193, 7, 230),  # Amber for NPC events
            "info": QColor(13, 71, 161, 230),  # Dark blue for other events
        }
        self._show_toast(message, colors.get(event_type, colors["info"]))

    def show_killstreak_toast(self, message):
        """Show a killstreak toast in gold color"""
        self._show_toast(message, QColor(255, 193, 7, 230))  # Amber color

    def show_error_toast(self, message):
        """Show an error toast in red"""
        self._show_toast(
            {"title": "❌ Error", "details": message}, QColor(198, 40, 40, 230)
        )

    def show_info_toast(self, message):
        """Show an info toast in blue"""
        self._show_toast(
            {"title": "🛈 Info", "details": message}, QColor(13, 71, 161, 230)
        )

    def show_success_toast(self, message):
        """Show a success toast in green"""
        self._show_toast(
            {"title": "✔️ Success", "details": message}, QColor(46, 125, 50, 230)
        )
