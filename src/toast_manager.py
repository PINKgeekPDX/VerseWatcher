try:
    import win32api
    WIN32API_AVAILABLE = True
except ImportError:
    WIN32API_AVAILABLE = False

from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from datetime import datetime, timedelta
import sip


def get_real_monitor_rect():
    """Get the actual monitor dimensions using Win32 API"""
    try:
        if WIN32API_AVAILABLE:
            monitor = win32api.GetMonitorInfo(win32api.MonitorFromPoint((0, 0)))
            return monitor["Monitor"]  # (left, top, right, bottom)
    except Exception:
        pass
    # Fallback to Qt screen geometry
    screen = QApplication.primaryScreen().geometry()
    return (screen.left(), screen.top(), screen.right(), screen.bottom())


class Toast(QWidget):
    def __init__(self, message, bg_color=QColor(11, 18, 24, 230)):
        super().__init__(None)

        # Set window flags to ensure toast appears even when app is minimized
        # Tool flag ensures it doesn't appear in taskbar
        # Qt.WindowDoesNotAcceptFocus ensures it doesn't steal focus
        # SubWindow flag ensures it appears above other windows
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool | 
            Qt.WindowDoesNotAcceptFocus | 
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        # Prevent toast from stealing focus from games
        self.setAttribute(Qt.WA_X11DoNotAcceptFocus, True)

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
                    (line.split(": ")[1] for line in details.split("\n") if "🔫 Weapon:" in line),
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
            default_size if not hasattr(self, "parent") or not self.parent() else self.parent().size
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
        
    def showEvent(self, event):
        """Ensure toast is shown even when app is minimized"""
        super().showEvent(event)
        # Make sure the toast is always on top, even over fullscreen games
        self.raise_()
        

class ToastManager:
    def __init__(self, parent=None):
        self.parent = parent  # Store parent reference
        self.toasts = []  # Currently displayed toasts
        self.position = "Bottom Right"
        self.size = "Medium"
        self.duration = 5000  # Default 5 seconds
        self.spacing = 10  # Spacing between toasts
        self.max_toasts = 5  # Maximum number of visible toasts
        
        # Party toast configuration
        self.party_position = "Top Right"
        self.party_size = "Medium"
        self.party_duration = 5000
        self.party_max_toasts = 5
        
        # IMPORTANT: No more separate queue or timer-based processing
        # This avoids the keyboard interrupt and threading issues
        
        # Create a single shot timer for initial positioning
        # This doesn't use a recurring timer which can cause crashes
        self.safe_timer = QTimer(parent)
        self.safe_timer.setSingleShot(True)
        self.safe_timer.timeout.connect(lambda: None)  # No-op connection to prevent errors

    def cleanup(self):
        """Clean up resources before destruction"""
        try:
            # Stop any remaining timer
            if hasattr(self, 'safe_timer') and self.safe_timer:
                self.safe_timer.stop()
            
            # Clean up any remaining toasts
            for toast in list(self.toasts):  # Make a copy of the list to avoid modification during iteration
                try:
                    if toast and not sip.isdeleted(toast):
                        toast.hide()
                        toast.deleteLater()
                except Exception:
                    pass
            
            # Clear lists
            self.toasts = []
        except Exception as e:
            print(f"Error during toast manager cleanup: {str(e)}")

    def update_config(self, position=None, size=None, duration=None, max_stack=None):
        if position:
            self.position = position
        if size:
            self.size = size
        if duration:
            self.duration = duration
        if max_stack is not None:
            self.max_toasts = max_stack

    def update_party_config(self, position=None, size=None, duration=None, max_stack=None):
        if position:
            self.party_position = position
        if size:
            self.party_size = size
        if duration:
            self.party_duration = duration
        if max_stack is not None:
            self.party_max_toasts = max_stack

    def _show_toast(self, message, bg_color=QColor(11, 18, 24, 230), is_party=False):
        """Show a toast immediately rather than queuing it"""
        try:
            # Remove old toasts if we've reached max
            while len([t for t in self.toasts if hasattr(t, 'is_party') and t.is_party == is_party]) >= (self.party_max_toasts if is_party else self.max_toasts):
                # Find oldest toast of same type
                for i, toast in enumerate(self.toasts):
                    if hasattr(toast, 'is_party') and toast.is_party == is_party:
                        # Remove it
                        try:
                            if not sip.isdeleted(toast):
                                toast.hide()
                                toast.deleteLater()
                            self.toasts.pop(i)
                            break
                        except Exception:
                            # If we can't remove one, just continue with showing the new toast
                            pass
            
            # Create toast widget with appropriate configuration
            toast = Toast(message, bg_color)
            toast.parent = self  # Set parent reference for size access
            toast.is_party = is_party
            
            # Configure toast size based on whether it's a party toast
            if is_party:
                toast.size = self.party_size
            else:
                toast.size = self.size
                
            # Add to active toasts list
            self.toasts.append(toast)
            
            # Show toast - make sure to set always on top
            toast.show()
            
            # Make sure the toast is always raised above other windows
            toast.raise_()
            
            # Position all toasts
            self._position_toasts()
            
            # Schedule this toast for removal using single-shot timer
            duration = self.party_duration if is_party else self.duration
            QTimer.singleShot(duration, lambda t=toast: self._remove_toast(t))
            
        except Exception as e:
            print(f"Error showing toast: {str(e)}")
            import traceback
            traceback.print_exc()

    def _remove_toast(self, toast):
        """Remove a specific toast"""
        try:
            if toast in self.toasts:
                self.toasts.remove(toast)
                
            # Even if it's not in the list, try to clean it up
            if not sip.isdeleted(toast):
                toast.hide()
                toast.deleteLater()
                
            # Reposition remaining toasts
            self._position_toasts()
        except Exception as e:
            print(f"Error removing toast: {str(e)}")

    def _position_toasts(self):
        """Position all active toasts based on their configuration"""
        if not self.toasts:
            return
            
        try:
            # Get screen geometry
            screen = QApplication.primaryScreen().geometry()
            
            # Group toasts by type (party and normal)
            party_toasts = [t for t in self.toasts if hasattr(t, 'is_party') and t.is_party and not sip.isdeleted(t)]
            regular_toasts = [t for t in self.toasts if (not hasattr(t, 'is_party') or not t.is_party) and not sip.isdeleted(t)]
            
            # Position party toasts
            self._position_toast_group(party_toasts, self.party_position, screen)
            
            # Position regular toasts
            self._position_toast_group(regular_toasts, self.position, screen)
        except Exception as e:
            print(f"Error positioning toasts: {str(e)}")
            
    def _position_toast_group(self, toasts, position, screen):
        """Position a group of toasts based on position setting"""
        if not toasts:
            return
        
        try:    
            # Calculate base position based on settings
            positions = {
                "Top Left": (self.spacing, self.spacing),
                "Top Right": (
                    screen.width() - (toasts[0].width() if toasts else 100) - self.spacing,
                    self.spacing,
                ),
                "Bottom Left": (self.spacing, screen.height() - self.spacing),
                "Bottom Right": (
                    screen.width() - (toasts[0].width() if toasts else 100) - self.spacing,
                    screen.height() - self.spacing,
                ),
                "Left Middle": (
                    self.spacing,
                    (screen.height() - (toasts[0].height() if toasts else 50)) // 2,
                ),
                "Right Middle": (
                    screen.width() - (toasts[0].width() if toasts else 100) - self.spacing,
                    (screen.height() - (toasts[0].height() if toasts else 50)) // 2,
                ),
            }

            base_x, base_y = positions.get(position, positions["Bottom Right"])

            # Position each toast
            total_height = sum(toast.height() + self.spacing for toast in toasts if not sip.isdeleted(toast))
            
            # Apply opacity based on position in stack
            for i, toast in enumerate(toasts):
                if sip.isdeleted(toast):
                    continue
                    
                # Calculate fade factor - most recent toast is most opaque
                fade_factor = 1.0 - (i / max(1, len(toasts)) * 0.5)  # Max 50% fade
                toast.setWindowOpacity(max(0.5, fade_factor))  # Minimum 50% opacity

            # Position all toasts
            for i, toast in enumerate(reversed(toasts)):  # Reverse for proper stacking
                if sip.isdeleted(toast):
                    continue
                    
                try:
                    # Calculate position
                    if "Bottom" in position:
                        y = base_y - total_height + (i * (toast.height() + self.spacing))
                    elif "Middle" in position:
                        y = base_y - (total_height // 2) + (i * (toast.height() + self.spacing))
                    else:  # Top
                        y = base_y + (i * (toast.height() + self.spacing))

                    toast.move(base_x, y)
                    toast.raise_()  # Ensure proper z-order
                except Exception:
                    # Skip positioning this toast if there's an error
                    pass
        except Exception as e:
            print(f"Error positioning toast group: {str(e)}")

    # Public methods for showing toasts
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
        self._show_toast({"title": "❌ Error", "details": message}, QColor(198, 40, 40, 230))

    def show_info_toast(self, message):
        """Show an info toast in blue"""
        self._show_toast({"title": "🛈 Info", "details": message}, QColor(13, 71, 161, 230))

    def show_success_toast(self, message):
        """Show a success toast in green"""
        self._show_toast({"title": "✓ Success", "details": message}, QColor(76, 175, 80, 230))

    def show_party_toast(self, message):
        """Show a party event toast with special styling"""
        self._show_toast(message, QColor(255, 64, 129, 230), is_party=True)  # Pink for party events
