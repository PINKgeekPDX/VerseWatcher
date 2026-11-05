import logging
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem


class Logger:
    """Provide rich console formatting and file output."""
    
    def __init__(self, console_widget=None, log_file=None):
        self.console_widget = console_widget
        self.log_file = log_file
        self.file_logger = None
        self.pending_ui_updates = []  # Store pending updates for batch processing
        
        # Initialize file logger if path provided
        if log_file:
            self.file_logger = logging.getLogger("file_logger")
            handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.file_logger.addHandler(handler)
            self.file_logger.setLevel(logging.DEBUG)
            
        # Set up a timer for batched UI updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.process_pending_updates)
    
    def ensure_autoscroll(self, item=None):
        """Scroll to the latest log entry when autoscroll is enabled."""
        if not self.console_widget:
            return
            
        try:
            if self._is_autoscroll_enabled():
                QTimer.singleShot(10, lambda: self._do_scroll())
        except Exception:
            # If there's any error, just force a scroll to bottom after a delay
            QTimer.singleShot(50, lambda: self._do_scroll())

    def _is_autoscroll_enabled(self):
        """Check the console widget's parent hierarchy for the autoscroll option."""
        parent = self.console_widget.parent()
        if parent is None:
            return False

        for ancestor in (parent, parent.parent()):
            checkbox = getattr(ancestor, "autoscroll_check", None)
            if checkbox is not None:
                return checkbox.isChecked()

        return False
    
    def _do_scroll(self):
        """Scroll the console to its latest top-level item."""
        if not self.console_widget:
            return
            
        try:
            # Get the count of top-level items
            count = self.console_widget.topLevelItemCount()
            if count > 0:
                # Scroll to the last top-level item
                last_item = self.console_widget.topLevelItem(count - 1)
                self.console_widget.scrollToItem(last_item, QTreeWidget.PositionAtBottom)
                
                # Make sure to update the view immediately
                self.console_widget.update()
                
                # Use a timer to ensure UI updates again after scrolling
                QTimer.singleShot(50, self.console_widget.update)
        except Exception:
            pass # Silently fail if scrolling fails
    
    def process_pending_updates(self):
        """Process all pending UI updates in a batch."""
        if not self.console_widget or not self.pending_ui_updates:
            return
            
        try:
            # Add all pending items to the console
            for item_func in self.pending_ui_updates:
                try:
                    item_func()
                except Exception:
                    pass  # Skip failed item additions
                    
            # Clear the pending updates
            self.pending_ui_updates.clear()
            
            # Ensure autoscroll happens after all items are added
            self.ensure_autoscroll()
            
        except Exception:
            # If batch processing fails, clear the queue to prevent backup
            self.pending_ui_updates.clear()
    
    def queue_console_update(self, update_func):
        """Queue a console update to be processed in a batch."""
        if not self.console_widget:
            return
            
        # Add the update function to the pending list
        self.pending_ui_updates.append(update_func)
        
        # If the timer isn't already running, start it
        if not self.update_timer.isActive():
            self.update_timer.start(10)  # Process updates every 10ms

    def log_debug(self, message):
        """Log a debug message containing verbose technical details."""
        # Log to file
        if self.file_logger:
            self.file_logger.debug(message)
        
        # Add to console with rich formatting
        if self.console_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Queue the UI update
            def add_debug_item():
                item = QTreeWidgetItem(self.console_widget)
                item.setText(0, f"[{timestamp}] 🔍 DEBUG: {message}")
                item.setForeground(0, QColor("#607D8B"))  # Blue-gray for debug
                item.setData(0, Qt.UserRole, "debug")  # Store type for filtering
                return item
                
            self.queue_console_update(add_debug_item)
    
    def log_info(self, message):
        """Log an informational message."""
        # Log to file
        if self.file_logger:
            self.file_logger.info(message)
        
        # Add to console with rich formatting
        if self.console_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Queue the UI update
            def add_info_item():
                item = QTreeWidgetItem(self.console_widget)
                item.setText(0, f"[{timestamp}] ℹ️ {message}")
                item.setForeground(0, QColor("#00A6ED"))  # Light blue for info
                item.setData(0, Qt.UserRole, "info")  # Store type for filtering
                return item
                
            self.queue_console_update(add_info_item)
    
    def log_warning(self, message):
        """Log a warning message."""
        # Log to file
        if self.file_logger:
            self.file_logger.warning(message)
        
        # Add to console with rich formatting
        if self.console_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Queue the UI update
            def add_warning_item():
                item = QTreeWidgetItem(self.console_widget)
                item.setText(0, f"[{timestamp}] ⚠️ {message}")
                item.setForeground(0, QColor("#FFC107"))  # Amber for warnings
                item.setData(0, Qt.UserRole, "warning")  # Store type for filtering
                return item
                
            self.queue_console_update(add_warning_item)
    
    def log_error(self, message):
        """Log an error message."""
        # Log to file
        if self.file_logger:
            self.file_logger.error(message)
        
        # Add to console with rich formatting
        if self.console_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Queue the UI update
            def add_error_item():
                item = QTreeWidgetItem(self.console_widget)
                item.setText(0, f"[{timestamp}] ❌ {message}")
                item.setForeground(0, QColor("#F44336"))  # Red for errors
                item.setData(0, Qt.UserRole, "error")  # Store type for filtering
                return item
                
            self.queue_console_update(add_error_item)
    
    def log_event(self, message, event_details=None):
        """Log a game event with detailed information."""
        # Log to file
        if self.file_logger:
            if event_details:
                details_str = ", ".join([f"{k}={v}" for k, v in event_details.items() if k != "dirvecx" and k != "dirvecy" and k != "dirvecz"])
                self.file_logger.info(f"EVENT: {message} - {details_str}")
            else:
                self.file_logger.info(f"EVENT: {message}")
        
        # Add to console with rich formatting
        if self.console_widget:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Queue the UI update
            def add_event_item():
                item = QTreeWidgetItem(self.console_widget)
                item.setText(0, f"[{timestamp}] 🎮 {message}")
                item.setForeground(0, QColor("#4CAF50"))  # Green for events
                item.setData(0, Qt.UserRole, "event")  # Store type for filtering
                
                # Add details as children if provided
                if event_details and isinstance(event_details, dict):
                    details_parent = QTreeWidgetItem(item)
                    details_parent.setText(0, "📋 Event Details")
                    details_parent.setForeground(0, QColor("#66BB6A"))  # Mid green for details header
                    
                    for key, value in event_details.items():
                        # Skip direction vectors that are typically not useful to display
                        if key in ["dirvecx", "dirvecy", "dirvecz"]:
                            continue
                            
                        detail_item = QTreeWidgetItem(details_parent)
                        detail_item.setText(0, f"{key}: {value}")
                        detail_item.setForeground(0, QColor("#C8E6C9"))  # Very light green for details
                
                return item
                
            self.queue_console_update(add_event_item)
                
    def log_kill(self, vname, kname, kwep, vship, dtype):
        """Log a kill event to the console with detailed information."""
        try:
            player_name = self._get_player_name()
            message, color_name, event_type = self._get_kill_presentation(
                vname, kname, player_name
            )
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_formatted_console(
                timestamp,
                message,
                color_name,
                event_type,
                f"🔫 Weapon: {kwep}",
                f"🚀 Ship: {vship}",
                f"💥 Damage: {dtype}",
            )

            if self.log_file:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[KILL] {timestamp} - {message} | Weapon: {kwep}, Ship: {vship}, Damage: {dtype}\n")
                    
        except Exception as e:
            self.log_error(f"Error logging kill: {str(e)}")
            import traceback
            self.log_error(traceback.format_exc())

    def _get_player_name(self):
        """Find the player name in the console widget's parent hierarchy."""
        player_name = "Unknown"
        if not hasattr(self, "console_widget") or not hasattr(self.console_widget, "parent"):
            return player_name

        main_window = self.console_widget.parent()
        while main_window and not hasattr(main_window, "player_name"):
            if not hasattr(main_window, "parent"):
                return player_name
            main_window = main_window.parent()

        if main_window and hasattr(main_window, "player_name"):
            return main_window.player_name
        return player_name

    @staticmethod
    def _get_kill_presentation(vname, kname, player_name):
        """Return the message, color, and category for a kill event."""
        if vname == kname:
            return f"💀 {vname} committed suicide", "purple", "suicide"
        if "NPC" in vname or vname.startswith("PU_"):
            return f"🤖 NPC {vname} killed by {kname}", "orange", "npc"
        if "NPC" in kname or kname.startswith("PU_"):
            return f"🤖 {vname} killed by NPC {kname}", "orange", "npc"
        if vname == player_name:
            return f"☠️ You were killed by {kname}", "red", "death"
        if kname == player_name:
            return f"🎯 You killed {vname}", "green", "kill"
        return f"⚔️ {vname} killed by {kname}", "blue", "info"

    def log_formatted_console(self, timestamp, message, color_name, event_type, *details):
        """
        Format and log a message to the console with optional details as child items.
        
        Args:
            timestamp (str): Timestamp for the message
            message (str): Main message text
            color_name (str): Name of color to use (red, green, blue, orange, purple)
            event_type (str): Type of event for filtering
            *details: Variable number of detail strings to add as child items
        """
        if not hasattr(self, 'console_widget') or not self.console_widget:
            return
            
        # Map color names to QColor objects
        colors = {
            "red": QColor("#F44336"),
            "green": QColor("#4CAF50"),
            "blue": QColor("#2196F3"),
            "orange": QColor("#FF9800"),
            "purple": QColor("#9C27B0"),
            "light_blue": QColor("#90CAF9"),
            "details": QColor("#64B5F6"),
            "detail_item": QColor("#BBDEFB")
        }
        
        # Get the color or default to white
        color = colors.get(color_name, QColor("#FFFFFF"))
        final_details = details  # Store details for closure
        
        # Queue the UI update
        def add_formatted_item():
            # Create the main item
            item = QTreeWidgetItem(self.console_widget)
            item.setText(0, f"[{timestamp}] {message}")
            item.setForeground(0, color)
            item.setData(0, Qt.UserRole, event_type)  # Store type for filtering
            
            # Add details as child items if provided
            if final_details:
                details_parent = QTreeWidgetItem(item)
                details_parent.setText(0, "📋 Details")
                details_parent.setForeground(0, colors.get("details"))
                
                for detail in final_details:
                    detail_item = QTreeWidgetItem(details_parent)
                    detail_item.setText(0, detail)
                    detail_item.setForeground(0, colors.get("detail_item"))
            
            return item
            
        self.queue_console_update(add_formatted_item)
