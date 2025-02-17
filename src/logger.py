import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


class Logger:
    def __init__(self, console_widget, log_file=None):
        self.console = console_widget
        self.log_file = log_file

        # Configure logging
        self.file_logger = logging.getLogger("versewatcher")
        self.file_logger.setLevel(logging.INFO)

        # Clear any existing handlers
        self.file_logger.handlers.clear()

        # Add file handler if log file is specified
        if self.log_file:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(self.log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.file_logger.addHandler(handler)
        else:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            self.log_file = os.path.join(
                log_dir, f"versewatcher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )

            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.file_logger.addHandler(handler)

    def info(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #00ff00; font-weight: 500;">🔹 [{timestamp}] INFO: {message}</span>'
        self.console.append(html)
        self.file_logger.info(message)

    def error(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #ff3333; font-weight: 600;">❌ [{timestamp}] ERROR: {message}</span>'
        self.console.append(html)
        self.file_logger.error(message)

    def warning(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #ffff00; font-weight: 500;">⚠️ [{timestamp}] WARNING: {message}</span>'
        self.console.append(html)
        self.file_logger.warning(message)

    def event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color: #00ffff; font-weight: 500;">💫 [{timestamp}] EVENT: {message}</span>'
        self.console.append(html)
        self.file_logger.info(f"[EVENT] {message}")

    def debug(self, message):
        if self.file_logger.level <= logging.DEBUG:
            timestamp = datetime.now().strftime("%H:%M:%S")
            html = f'<span style="color: #808080; font-weight: 500;">🔍 [{timestamp}] DEBUG: {message}</span>'
            self.console.append(html)
            self.file_logger.debug(message)
