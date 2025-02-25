import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QColor


class Logger:
    def __init__(self, console_widget=None, log_file=None):
        self.console = console_widget
        self.log_file = log_file

        # Ensure we have at least one logging destination
        if not console_widget and not log_file:
            print("Warning: Logger initialized without console widget or log file")

        self.setup_logging()
        print(
            f"Logger initialized - Console: {'Yes' if console_widget else 'No'}, File: {'Yes' if log_file else 'No'}"
        )

    def setup_logging(self):
        """Set up logging configuration"""
        try:
            if self.log_file:
                logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[
                        RotatingFileHandler(
                            self.log_file, maxBytes=1024 * 1024, backupCount=5
                        ),
                        logging.StreamHandler(),
                    ],
                )
                print(f"File logging setup complete: {self.log_file}")
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")

    def _log_message(self, msg_type, message, details=None):
        """Log a message to the console widget"""
        try:
            if not self.console:
                # If no console widget, just log to file
                return

            timestamp = datetime.now().strftime("%H:%M:%S")

            # Create the main item with error handling
            try:
                item = QTreeWidgetItem()

                # Set the type icon and color based on entry type
                type_info = {
                    "info": ("ℹ️", "#00A6ED", "Information"),
                    "error": ("❌", "#FF4444", "Error"),
                    "warning": ("⚠️", "#FFD740", "Warning"),
                    "event": ("💫", "#40C4FF", "Event"),
                    "debug": ("🔍", "#808080", "Debug"),
                    "kill": ("💀", "#4CAF50", "Kill"),
                    "death": ("☠️", "#FF4444", "Death"),
                    "suicide": ("💥", "#E040FB", "Suicide"),
                    "npc": ("🤖", "#FFD740", "NPC"),
                }

                icon, color, type_text = type_info.get(
                    msg_type, ("📝", "#FFFFFF", "Log")
                )

                # Set text for each column
                item.setText(0, timestamp)
                item.setText(1, f"{icon} {type_text}")
                item.setText(2, str(message))  # Ensure message is string

                # Set color for the entire row
                for col in range(3):
                    item.setForeground(col, QColor(color))

                # Add details as child items if provided
                if details:
                    for key, value in details.items():
                        detail_item = QTreeWidgetItem()
                        detail_item.setText(0, "")  # Empty timestamp
                        detail_item.setText(1, "")  # Empty type
                        detail_item.setText(2, f"{key}: {value}")
                        item.addChild(detail_item)

                # --- New: Limit the number of log items ---
                max_items = 500  # Set maximum allowed top-level items
                if self.console.topLevelItemCount() >= max_items:
                    # Remove the oldest item before adding a new one
                    self.console.takeTopLevelItem(0)
                # --- End new section ---

                # Add the new item to the console widget
                self.console.addTopLevelItem(item)

                # Expand if it has details
                if details:
                    item.setExpanded(True)

                # Ensure the latest entry is visible
                self.console.scrollToItem(item)

                return item

            except Exception as e:
                print(f"Error formatting log message: {str(e)}")
                # Try a simpler format as fallback
                simple_item = QTreeWidgetItem([timestamp, msg_type, str(message)])
                self.console.addTopLevelItem(simple_item)
                return simple_item

        except Exception as e:
            print(f"Critical error in _log_message: {str(e)}")
            return None

    def log_info(self, message, details=None):
        """Log an info message"""
        try:
            self._log_message("info", message, details)
            if self.log_file:
                logging.info(message)
        except Exception as e:
            print(f"Error in log_info: {str(e)}")

    def log_error(self, message, details=None):
        """Log an error message"""
        try:
            self._log_message("error", message, details)
            if self.log_file:
                logging.error(message)
        except Exception as e:
            print(f"Error in log_error: {str(e)}")

    def log_warning(self, message, details=None):
        """Log a warning message"""
        try:
            self._log_message("warning", message, details)
            if self.log_file:
                logging.warning(message)
        except Exception as e:
            print(f"Error in log_warning: {str(e)}")

    def log_event(self, message, details=None):
        """Log an event message"""
        try:
            self._log_message("event", message, details)
            if self.log_file:
                logging.info(f"EVENT: {message}")
        except Exception as e:
            print(f"Error in log_event: {str(e)}")

    def log_debug(self, message, details=None):
        """Log a debug message"""
        try:
            self._log_message("debug", message, details)
            if self.log_file:
                logging.debug(message)
        except Exception as e:
            print(f"Error in log_debug: {str(e)}")
