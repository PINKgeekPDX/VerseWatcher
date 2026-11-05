from datetime import datetime
import json
import logging
import os
import sys
import warnings
import threading
import webbrowser
import ctypes
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5 import sip
from PyQt5.QtCore import Qt, QSettings, QUrl, QTimer, QSize, QDateTime, QEvent, QPoint
from PyQt5.QtGui import QPalette, QColor, QIcon, QPixmap, QFont, QImage, QPainter, QFontDatabase, QDesktopServices, QCursor
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QFileDialog, QTreeWidget, QTreeWidgetItem, QSplitter,
                             QListWidget, QListWidgetItem, QComboBox, QCheckBox, QDialog, QScrollArea,
                             QGridLayout, QMenu, QSystemTrayIcon, QAction, QStyle, QFrame, QTabWidget,
                             QGroupBox, QFormLayout, QSizePolicy, QProgressBar)
from app_config import AppConfig
from event_history import EventHistory
from logger import Logger
from game_watcher import GameLogWatcher
from toast_manager import ToastManager
from ui_state import apply_watch_ui_state
from watch_controller import start_monitoring, stop_monitoring
from settings_service import load_app_settings, save_app_settings
from settings_tab import build_settings_tab
from party_tab import build_party_tab
from i18n import T

print("Script starting...")

# Set up logging configuration
try:
    # Create logs directory in the Documents folder
    documents_path = os.path.expanduser("~\\Documents")
    app_dir = os.path.join(documents_path, "PINK", "VerseWatcher")
    logs_dir = os.path.join(app_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(logs_dir, "app.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Logging system initialized")
except Exception as e:
    print(f"Error setting up logging: {str(e)}")
    import traceback
    print(traceback.format_exc())

warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    if hasattr(sip, "setapi"):
        sip.setapi("QVariant", 2)
        sip.setapi("QString", 2)
except Exception as e:
    print(f"Error configuring sip: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = AppConfig()
        self.app_dir = self.config.app_dir
        self.settings_file = self.config.settings_file
        self.history_dir = self.config.history_dir
        self.logs_dir = self.config.logs_dir
        self.log_file = os.path.join(self.logs_dir, "versewatcher_log.log")
        
        # Get Documents path
        self.documents_path = os.path.expanduser("~/Documents")
        
        # Initialize CRITICAL core attributes first
        self.is_watching = False
        self.watcher = None
        self.tray_icon = None
        self.console_output = None
        self.player_name = None
        self.session_history = {"kills": []}
        self.party_session_history = {}
        self.event_history = EventHistory(self.app_dir, getattr(self, 'logger', None))
        self.party_members = []  # Initialize party_members list FIRST before UI initialization
        self.party_members_list = None
        
        # Initialize UI elements
        self.path_input = None
        self.name_input = None
        self.toast_position_combo = None
        self.toast_size_combo = None
        self.toast_duration_combo = None
        self.party_toast_position_combo = None
        self.party_toast_size_combo = None
        self.party_toast_duration_combo = None
        self.self_events_check = None
        self.other_events_check = None
        self.npc_events_check = None
        self.suicide_events_check = None
        self.party_events_check = None
        
        # Stay on top action
        self.stay_on_top_action = QAction(T("STAY_ON_TOP"), self)
        self.stay_on_top_action.setCheckable(True)
        self.stay_on_top_action.triggered.connect(self.toggle_stay_on_top)
        
        # Initialize logger first - but without console_widget which will be set after UI init
        self.logger = Logger(log_file=self.log_file)
        self.event_history.logger = self.logger
        self.logger.log_info("VERSEWATCHER - STARTED SUCCESSFULLY")
        
        # Initialize toast manager with self as parent
        self.toast_manager = ToastManager(self)
        
        # Initialize UI and other components
        self.init_ui()

        screen = QApplication.primaryScreen()
        if screen is not None:
            available_geometry = screen.availableGeometry()
            frame_margins = self._get_window_frame_margins()
            client_width = max(
                1, available_geometry.width() - frame_margins[0] - frame_margins[2]
            )
            client_height = max(
                1, available_geometry.height() - frame_margins[1] - frame_margins[3]
            )
            self.setMinimumSize(
                min(900, client_width),
                min(600, client_height),
            )
        else:
            self.setMinimumSize(900, 600)
        
        # Now that console_output widget exists, update the logger to use it
        if hasattr(self, 'console_output') and self.console_output:
            self.logger.console_widget = self.console_output
            self.logger.log_info("Console output connected")
        
        self.setup_tray_icon()
        self.load_window_geometry()
        self.load_settings()
        
        # Set window title and show window
        self.setWindowTitle(T("APP_WINDOW_TITLE"))
        self.show()
        self.raise_()
        self.activateWindow()

    def _get_window_frame_margins(self):
        """Return the native window frame margins as left, top, right, bottom."""
        self.winId()
        handle = self.windowHandle()
        if handle is None:
            return 0, 0, 0, 0

        margins = handle.frameMargins()
        return margins.left(), margins.top(), margins.right(), margins.bottom()

    def load_window_geometry(self):
        """Load and apply window geometry before window is shown"""
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                self.setGeometry(100, 100, 1200, 800)
                return

            available = screen.availableGeometry()
            margin_left, margin_top, margin_right, margin_bottom = (
                self._get_window_frame_margins()
            )
            maximum_width = max(1, available.width() - margin_left - margin_right)
            maximum_height = max(1, available.height() - margin_top - margin_bottom)
            minimum_width = min(900, maximum_width)
            minimum_height = min(600, maximum_height)
            default_width = min(1200, maximum_width)
            default_height = min(800, maximum_height)

            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                    geometry = settings.get("window_geometry", {})
                    if geometry:
                        width = min(
                            max(int(geometry.get("width", default_width)), minimum_width),
                            maximum_width,
                        )
                        height = min(
                            max(int(geometry.get("height", default_height)), minimum_height),
                            maximum_height,
                        )
                        x = int(geometry.get("x", available.x() + (available.width() - width) // 2))
                        y = int(geometry.get("y", available.y() + (available.height() - height) // 2))
                        x = max(
                            available.x(),
                            min(
                                x,
                                available.x() + available.width() - width - margin_left - margin_right,
                            ),
                        )
                        y = max(
                            available.y(),
                            min(
                                y,
                                available.y() + available.height() - height - margin_top - margin_bottom,
                            ),
                        )

                        # Apply geometry
                        self.setGeometry(x, y, width, height)
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.log_info(f"Loaded window geometry: x={x}, y={y}, w={width}, h={height}")
                        else:
                            print(f"Loaded window geometry: x={x}, y={y}, w={width}, h={height}")
                        return

            # If no geometry loaded, set default centered position
            x = available.x() + (
                available.width() - default_width - margin_left - margin_right
            ) // 2
            y = available.y() + (
                available.height() - default_height - margin_top - margin_bottom
            ) // 2
            self.setGeometry(x, y, default_width, default_height)
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_info(
                    f"Set default centered geometry: x={x}, y={y}, "
                    f"w={default_width}, h={default_height}"
                )
            else:
                print(
                    f"Set default centered geometry: x={x}, y={y}, "
                    f"w={default_width}, h={default_height}"
                )

        except Exception as e:
            error_msg = f"Error loading window geometry: {str(e)}"
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_error(error_msg)
                import traceback
                self.logger.log_error(traceback.format_exc())
            else:
                print(error_msg)
            # Set safe default geometry
            screen = QApplication.primaryScreen()
            if screen is not None:
                available = screen.availableGeometry()
                width = min(1200, available.width())
                height = min(800, available.height())
                x = available.x() + (available.width() - width) // 2
                y = available.y() + (available.height() - height) // 2
                self.setGeometry(x, y, width, height)
            else:
                self.setGeometry(100, 100, 1200, 800)

    def save_window_geometry(self):
        """Save just the window geometry"""
        try:
            # Don't save if the window is minimized
            if self.isMinimized():
                return
                
            # Ensure app directory exists
            os.makedirs(self.app_dir, exist_ok=True)
            
            # Load existing settings if they exist
            current_settings = {}
            if os.path.exists(self.settings_file):
                try:
                    with open(self.settings_file, 'r') as f:
                        current_settings = json.load(f)
                except Exception as e:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.log_warning(f"Error reading settings file for geometry save: {str(e)}")
                    # If there's an error loading the file, start with empty settings
                    pass
            
            # Get current window geometry
            frame_geometry = self.frameGeometry()
            x, y, width, height = (
                frame_geometry.x(),
                frame_geometry.y(),
                self.width(),
                self.height(),
            )
            
            # Check if values have actually changed to avoid unnecessary writes
            current_geometry = current_settings.get("window_geometry", {})
            if (current_geometry.get("x") == x and 
                current_geometry.get("y") == y and 
                current_geometry.get("width") == width and
                current_geometry.get("height") == height):
                # No change, skip save
                return
                
            # Update just the window geometry portion
            current_settings["window_geometry"] = {
                "x": x,
                "y": y,
                "width": width,
                "height": height
            }
            
            # Save back to file
            with open(self.settings_file, 'w') as f:
                json.dump(current_settings, f, indent=4)
                
            # Debug logging removed to prevent console spam
            # Window position changes now happen silently
                
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_error(f"Error saving window geometry: {str(e)}")
                import traceback
                self.logger.log_error(traceback.format_exc())

    def init_ui(self):
        print("Starting UI initialization...")
        # Create main widget and layout
        print("Creating main widget...")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        # Create stay on top action
        self.stay_on_top_action = QAction(T("STAY_ON_TOP"), self)
        self.stay_on_top_action.setCheckable(True)
        self.stay_on_top_action.triggered.connect(self.toggle_stay_on_top)
        print("Creating header...")
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(30)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 5, 5)
        title_label = QLabel("[ Alpha 1.0.12 ]")
        title_label.setFixedHeight(15)
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        layout.addWidget(header)
        # Control panel (always visible)
        print("Creating control panel...")
        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_panel.setFixedHeight(46)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(20, 3, 20, 3)
        
        status_label = QLabel(T("STATUS_INACTIVE"))
        status_label.setObjectName("statusLabel")
        status_label.setStyleSheet("background-color: rgba(8, 41, 66, 0.7); color: #F44336; font-size: 12px; font-weight: bold; margin-right: 15px; padding: 4px 8px; border-radius: 3px;")
        self.status_label = status_label
        self.start_button = QPushButton(T("START"))
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.toggle_watching)
        self.start_button.setToolTip(T("START_STOP_TOOLTIPS"))
        self.start_button.setStyleSheet("""
            QPushButton#startButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #C62828,
                    stop:1 #D32F2F
                );
                border: 1px solid #F44336;
                border-radius: 3px;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton#startButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #D32F2F,
                    stop:1 #E53935
                );
                border: 1px solid #EF5350;
            }
        """)
        
        control_layout.addWidget(status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.start_button)
        layout.addWidget(control_panel)
        print("Creating content area...")
        content_area = QFrame()
        content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(5)
        print("Creating tab widget...")
        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabWidget")
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #00A6ED;
                background: rgba(4, 11, 17, 0.98);
                border-radius: 1px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #040B11,
                    stop:1 #0D1F2D
                );
                color: #00A6ED;
                border: 1px solid #00A6ED;
                padding: 9px 12px;
                min-width: 148px;
                border-radius: 1px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0A1721,
                    stop:1 #152F3E
                );
            }
        """)
        # Create and add tabs
        print("Creating tabs...")
        watcher_tab = self.create_watcher_tab()
        history_tab = self.create_history_tab()
        party_tab = self.create_party_tab()
        settings_tab = self.create_settings_tab()
        about_tab = self.create_about_tab()
        self.tabs.addTab(watcher_tab, T("DASHBOARD"))
        self.tabs.addTab(history_tab, T("TRACKING"))
        self.tabs.addTab(party_tab, T("PARTY_TRACKING"))
        self.tabs.addTab(settings_tab, T("SETTINGS"))
        self.tabs.addTab(about_tab, T("ABOUT"))
        self.tabs.tabBar().setExpanding(True)
        content_layout.addWidget(self.tabs)
        layout.addWidget(content_area)
        self.apply_theme()
        print("UI initialization completed")

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(4, 16, 25, 0.95);
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #statusLabel {
                color: #00A6ED;
                font-size: 12px;
                font-weight: bold;
                text-shadow: 0 0 10px rgba(64, 196, 255, 0.6);
            }
            #contentArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(0, 15, 25, 0.5);
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                min-height: 20px;
                border-radius: 5px;
                border: 1px solid #00A6ED;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: rgba(0, 15, 25, 0.95);
                border: 1px solid #00A6ED;
                border-radius: 2px;
                color: #E0E0E0;
                padding: 6px;
                selection-background-color: #0077AA;
            }
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #40C4FF;
                background-color: rgba(0, 20, 30, 0.95);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: white;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
                text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
                border: 1px solid #40C4FF;
                box-shadow: 0 0 8px rgba(64, 196, 255, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00A6ED,
                    stop:1 #40C4FF
                );
                padding-left: 17px;
                padding-top: 10px;
            }
            #startButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00695C,
                    stop:1 #00897B
                );
                border: 1px solid #26A69A;
                padding: 8px 20px;
                font-size: 14px;
                text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
            }
            #startButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00897B,
                    stop:1 #26A69A
                );
                border: 1px solid #4DB6AC;
                box-shadow: 0 0 8px rgba(77, 182, 172, 0.5);
            }
            QComboBox {
                background: rgba(0, 15, 25, 0.95);
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: #E0E0E0;
                padding: 5px 10px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #40C4FF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #00A6ED;
                background: rgba(0, 60, 90, 0.5);
            }
            QComboBox::down-arrow {
                image: url(down-arrow.png);
            }
            QComboBox QAbstractItemView {
                background-color: rgba(0, 15, 25, 0.98);
                border: 1px solid #00A6ED;
                color: #E0E0E0;
                selection-background-color: rgba(0, 119, 170, 0.5);
                selection-color: #FFFFFF;
            }
            QCheckBox {
                color: #E0E0E0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #00A6ED;
                border-radius: 2px;
                background: rgba(0, 15, 25, 0.95);
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
                image: url(checkmark.png);
            }
            QCheckBox::indicator:hover {
                border: 1px solid #40C4FF;
            }
            QRadioButton {
                color: #E0E0E0;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #00A6ED;
                border-radius: 9px;
                background: rgba(0, 15, 25, 0.95);
            }
            QRadioButton::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
                border: 4px solid rgba(0, 15, 25, 0.95);
            }
            QRadioButton::indicator:hover {
                border: 1px solid #40C4FF;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: rgba(0, 15, 25, 0.95);
                border: 1px solid #00A6ED;
                border-radius: 4px;
                margin: 0px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
                border: 1px solid #40C4FF;
                border-radius: 6px;
                width: 18px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00A6ED,
                    stop:1 #40C4FF
                );
                border: 1px solid #80D8FF;
                box-shadow: 0 0 8px rgba(128, 216, 255, 0.5);
            }
            QGroupBox {
                border: 1px solid #00A6ED;
                border-radius: 3px;
                margin-top: 12px;
                padding: 15px;
                font-weight: bold;
                color: #E0E0E0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #E0E0E0;
                font-size: 14px;
            }
        """)

    def create_about_tab(self):
        about_tab = QWidget()
        about_tab.setStyleSheet("""
            QWidget {
                background-color: rgba(4, 16, 25, 0.95);
            }
            #aboutPanel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(4, 16, 25, 0.98),
                    stop:0.5 rgba(10, 30, 48, 0.95),
                    stop:1 rgba(13, 42, 64, 0.98)
                );
                border: 2px solid #00A6ED;
                border-radius: 6px;
                padding: 30px;
                margin: 10px 0;
                max-width: 800px;
            }
            #appLogo {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00426A,
                    stop:0.5 #0077AA,
                    stop:1 #00A6ED
                );
                border: 3px solid #00A6ED;
                border-radius: 60px;
                padding: 8px;
                box-shadow: 0 0 15px rgba(0, 166, 237, 0.7);
            }
            #appLogo:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #005388,
                    stop:0.5 #0088BF,
                    stop:1 #40C4FF
                );
                border: 3px solid #40C4FF;
                box-shadow: 0 0 25px rgba(rgba(64, 196, 255, 0.9), rgba(64, 196, 255, 0.9), rgba(64, 196, 255, 0.9), 0.9);
            }
            #appTitle {
                color: #00A6ED;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 6px;
                text-shadow: 0 0 15px rgba(0, 166, 237, 0.7);
                margin-top: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: transparent;
            }
            #versionLabel {
                color: #80D8FF;
                font-size: 14px;
                letter-spacing: 3px;
                margin: 8px 0 20px 0;
                text-shadow: 0 0 10px rgba(128, 216, 255, 0.5);
                font-family: 'Consolas', monospace;
                background: transparent;
            }
            #descriptionLabel {
                color: #E0E0E0;
                font-size: 14px;
                margin: 15px 0;
                line-height: 1.5;
                text-shadow: 0 0 8px rgba(224, 224, 224, 0.3);
                letter-spacing: 0.5px;
                background: transparent;
            }
            #sectionHeader {
                color: #00A6ED;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 3px;
                margin: 20px 0 15px 0;
                padding-bottom: 8px;
                border-bottom: 2px solid #00A6ED;
                text-shadow: 0 0 10px rgba(0, 166, 237, 0.6);
                box-shadow: 0 8px 6px -6px rgba(0, 166, 237, 0.2);
                background: transparent;
            }
            #featureLabel {
                color: #90CAF9;
                font-size: 14px;
                padding: 6px 0;
                margin-left: 20px;
                text-shadow: 0 0 6px rgba(64, 196, 255, 0.3);
                transition: all 0.3s ease;
                letter-spacing: 0.5px;
                background: transparent;
            }
            #featureLabel:hover {
                color: #40C4FF;
                text-shadow: 0 0 10px rgba(64, 196, 255, 0.7);
                margin-left: 25px;
                letter-spacing: 0.7px;
                background: transparent;
            }
            #creditsLabel {
                color: #E0E0E0;
                font-size: 14px;
                margin: 15px 0;
                text-align: center;
                font-style: italic;
                text-shadow: 0 0 6px rgba(224, 224, 224, 0.3);
                background: transparent;
            }
            #versionHistory {
                color: #90CAF9;
                font-size: 13px;
                margin-top: 15px;
                line-height: 1.5;
                padding: 15px;
                background: rgba(0, 77, 115, 0.35);
                border-left: 3px solid #00A6ED;
                border-radius: 4px;
                box-shadow: 0 0 10px rgba(0, 166, 237, 0.3);
            }
            #linkLabel {
                color: #00A6ED;
                text-decoration: none;
                font-weight: bold;
                font-size: 14px;
                text-shadow: 0 0 6px rgba(0, 166, 237, 0.4);
                transition: all 0.3s ease;
                padding: 6px 12px;
                border-radius: 4px;
                background: rgba(0, 77, 115, 0.2);
                border: 1px solid rgba(0, 166, 237, 0.3);
            }
            #linkLabel:hover {
                color: #40C4FF;
                text-shadow: 0 0 10px rgba(64, 196, 255, 0.7);
                background: rgba(0, 77, 115, 0.4);
                border: 1px solid rgba(64, 196, 255, 0.6);
                box-shadow: 0 0 12px rgba(64, 196, 255, 0.4);
            }
            #footerLabel {
                color: #90CAF9;
                font-size: 12px;
                margin-top: 20px;
                text-align: center;
                opacity: 0.7;
                letter-spacing: 0.5px;
            }
            #footerLabel:hover {
                opacity: 1.0;
                text-shadow: 0 0 8px rgba(64, 196, 255, 0.5);
                letter-spacing: 0.7px;
            }
            #aboutSection {
                background: transparent;
                border: 1px solid rgba(0, 166, 237, 0.4);
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;
                box-shadow: inset 0 0 15px rgba(0, 166, 237, 0.1);
            }
            #aboutSection:hover {
                background: rgba(0, 77, 115, 0.15);
                border: 1px solid rgba(64, 196, 255, 0.6);
                box-shadow: 0 0 15px rgba(64, 196, 255, 0.3), inset 0 0 20px rgba(0, 166, 237, 0.15);
            }
        """)
        
        # Create a scroll area to handle different screen sizes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(4, 16, 25, 0.6);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 166, 237, 0.7);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(64, 196, 255, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create content widget for the scroll area
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)    
        # Main layout for the tab
        main_layout = QVBoxLayout(about_tab)
        main_layout.setContentsMargins(10, 10, 10, 10)     
        # Content layout
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignHCenter)      
        # Main about panel
        about_panel = QFrame()
        about_panel.setObjectName("aboutPanel")
        panel_layout = QVBoxLayout(about_panel)
        panel_layout.setSpacing(20)
        panel_layout.setContentsMargins(20, 20, 20, 20)       
        # App Logo and Title Section (centered)
        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)       
        # Create a horizontal layout for the two images
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_layout.setSpacing(10)  # Space between the two boxes      
        # Left box with logo.png
        left_logo_label = QLabel()
        left_logo_label.setObjectName("appLogo")
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            left_logo_label.setPixmap(logo_pixmap)
            left_logo_label.setFixedSize(150, 150)
            left_logo_label.setAlignment(Qt.AlignCenter)
        else:
            # Fallback text if image can't be found
            left_logo_label.setText("logo.png")
            left_logo_label.setAlignment(Qt.AlignCenter)
            left_logo_label.setFixedSize(150, 150)
            left_logo_label.setStyleSheet("color: white; font-size: 16px;")  
        # Right box with pg.png
        right_logo_label = QLabel()
        right_logo_label.setObjectName("appLogo")
        pg_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.dirname(__file__)), "pg.png"))
        if not pg_pixmap.isNull():
            pg_pixmap = pg_pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            right_logo_label.setPixmap(pg_pixmap)
            right_logo_label.setFixedSize(150, 150)
            right_logo_label.setAlignment(Qt.AlignCenter)
        else:
            # Fallback text if image can't be found
            right_logo_label.setText("pg.png")
            right_logo_label.setAlignment(Qt.AlignCenter)
            right_logo_label.setFixedSize(150, 150)
            right_logo_label.setStyleSheet("color: white; font-size: 16px;")     
        # Add both images to the horizontal layout
        logo_layout.addWidget(left_logo_label)
        logo_layout.addWidget(right_logo_label)      
        # Add the horizontal layout to the title layout
        title_layout.addLayout(logo_layout)      
        # App Name
        app_title = QLabel(T("APP_TITLE"))
        app_title.setObjectName("appTitle")
        app_title.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(app_title)      
        # Version
        version_label = QLabel(T("APP_VERSION"))
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(version_label)
        panel_layout.addLayout(title_layout) 
        # Description Section
        about_section = QFrame()
        about_section.setObjectName("aboutSection")
        about_layout = QVBoxLayout(about_section)
        about_layout.setContentsMargins(10, 10, 10, 10)
        description = QLabel(T("ABOUT_DESCRIPTION"))
        description.setObjectName("descriptionLabel")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignJustify)
        about_layout.addWidget(description)
        panel_layout.addWidget(about_section)
        # Features Section
        features_header = QLabel(T("CURRENT_FEATURES_AND_PLANNED"))
        features_header.setObjectName("sectionHeader")
        panel_layout.addWidget(features_header)
        features_frame = QFrame()
        features_frame.setObjectName("aboutSection")
        features_layout = QVBoxLayout(features_frame)
        features_layout.setContentsMargins(5, 5, 5, 5)
        features_layout.setSpacing(2)
        features = [
            "-----------------------",
            "## CARACTERÍSTICAS ACTUALES ##",
            "-----------------------",
            " ",
            "> Seguimiento en tiempo real de los eventos de Game.log",
            "> Estadísticas detalladas de muertes y enfrentamientos",
            "> Monitorización y notificaciones de la actividad del grupo",
            "> Notificaciones emergentes discretas pero visibles",
            "> Historial persistente de sesiones y eventos",
            " ",
            "------------------------------------------",
            "## FUNCIONES PREVISTAS ##",
            "------------------------------------------",
            " ",
            "> Mejoras en la superposición en tiempo real y métricas del juego",
            "> Personalización más avanzada del tema y la interfaz",
            "> Notificaciones con alertas de sonido para eventos y toasts",
            "> Más tipos de eventos y análisis de combate",
            "> Instalador y actualizador oficiales de la aplicación",
            " ",
            "---------------------------------------------------------------------",
            "¿Tienes ideas de nuevas funciones? ¿Estás desarrollando algo parecido?",
            "             ¡Hablemos de ello!",
            "---------------------------------------------------------------------",
        ]
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setObjectName("featureLabel")
            features_layout.addWidget(feature_label)
        panel_layout.addWidget(features_frame)   
        usage_header = QLabel(T("GETTING_STARTED"))
        usage_header.setObjectName("sectionHeader")
        panel_layout.addWidget(usage_header)
        usage_section = QFrame()
        usage_section.setObjectName("aboutSection")
        usage_layout = QVBoxLayout(usage_section)
        usage_layout.setContentsMargins(10, 10, 10, 10)
        usage_text = QLabel(T("ABOUT_USAGE_TEXT"))
        usage_text.setObjectName("descriptionLabel")
        usage_text.setWordWrap(True)
        usage_layout.addWidget(usage_text)
        panel_layout.addWidget(usage_section)       
        # Credits
        credits_header = QLabel(T("DEVELOPMENT_AND_CONTRIBUTORS"))
        credits_header.setObjectName("sectionHeader")
        panel_layout.addWidget(credits_header)
        credits = QLabel(
            "-------------------------------------------------------------------------------\n"
            "| Desarrollo y diseño multimedia:\n"
            "-------------------------------------------------------------------------------\n"
            "|\n"
            "|   - PINKgeekPDX\n"
            "|\n"
            "-------------------------------------------------------------------------------\n"
            "| Colaboradores:\n"
            "-------------------------------------------------------------------------------\n"
            "|\n"
            "|   - Anemoi\n"
            "|    (Pruebas exhaustivas y grandes ideas convertidas en funciones reales)\n"
            "|\n"
            "|   -----------------------\n"
            "|\n"
            "|   - rouvipouvi\n"
            "|    (Amiga muy querida que ayuda a pulir esta herramienta)\n"
            "|\n"
            "-------------------------------------------------------------------------------\n"
            "| Agradecimientos especiales:\n"
            "-------------------------------------------------------------------------------\n"
            "|\n"
            "|   - Toda la comunidad de Star Citizen por su feedback e ideas.\n"
            "|\n"
            "|   -----------------------\n"
            "|\n"
            "|   - CIG por crear un juego tan grande y complicado y por su compromiso continuo\n"
            "|\n"
            "|   -----------------------\n"
            "|\n"
            "|   - CIG por su apoyo a la comunidad y por ofrecer una experiencia única.\n"
        )
        credits.setObjectName("creditsLabel")
        panel_layout.addWidget(credits)
        # Links
        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignCenter)
        links_layout.setSpacing(25)
        github_link = QLabel("<a href='https://github.com/PINKgeekPDX/VerseWatcher' style='text-decoration:none; color:#00A6ED;'>{}</a>".format(T("PROJECT_GITHUB_REPO")))
        github_link.setObjectName("linkLabel")
        github_link.setOpenExternalLinks(True)
        links_layout.addWidget(github_link)
        report_link = QLabel("<a href='https://github.com/PINKgeekPDX/VerseWatcher/issues' style='text-decoration:none; color:#00A6ED;'>{}</a>".format(T("SUBMIT_ISSUES")))
        report_link.setObjectName("linkLabel")
        report_link.setOpenExternalLinks(True)
        links_layout.addWidget(report_link)
        docs_link = QLabel("<a href='https://github.com/PINKgeekPDX/VerseWatcher/wiki' style='text-decoration:none; color:#00A6ED;'>{}</a>".format(T("DOCUMENTATION")))
        docs_link.setObjectName("linkLabel")
        docs_link.setOpenExternalLinks(True)
        links_layout.addWidget(docs_link)
        panel_layout.addLayout(links_layout)       
        # Footer
        footer = QLabel(T("ABOUT_FOOTER"))
        footer.setObjectName("footerLabel")
        footer.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(footer)
        layout.addWidget(about_panel)      
        # Add the scroll area to the main layout
        main_layout.addWidget(scroll_area)
        return about_tab

    def create_watcher_tab(self):
        watcher_tab = QWidget()
        layout = QVBoxLayout(watcher_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(30)
        header_layout = QHBoxLayout()
        header_label = QLabel(T("CONSOLE_HEADER"))
        header_label.setStyleSheet("""
            color: #00A6ED;
            font-size: 20px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 1px;
            text-shadow: 0 0 10px rgba(0, 166, 237, 1.0);
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        description = QLabel(T("CONSOLE_DESCRIPTION"))
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #90CAF9;
            font-size: 12px;
            margin-bottom: 4px;
            text-shadow: 0 0 5px rgba(0, 166, 237, 0.7);
            background: rgba(0, 60, 90, 0.3);
            border-radius: 4px;
            padding: 10px;
            border-left: 3px solid #00A6ED;
        """)
        layout.addWidget(description)
        # Console output
        console_frame = QFrame()
        console_frame.setObjectName("consoleFrame")
        console_frame.setStyleSheet("""
            #consoleFrame {
                background-color: rgba(106, 110, 130, 0.5);
                border: 1px solid #00A6ED;
                border-radius: 4px;
                padding: 2px;
            }
            #consoleFrame:hover {
                border: 1px solid #0AE5EF;
                box-shadow: 0 0 10px rgba(64, 196, 255, 0.4);
            }
        """)  
        console_layout = QVBoxLayout(console_frame)
        console_layout.setContentsMargins(2, 2, 2, 2)
        # Replace QListWidget with QTreeWidget for expandable items
        self.console_output = QTreeWidget()
        self.console_output.setObjectName("consoleOutput")
        self.console_output.setHeaderHidden(True)  # Hide the header
        self.console_output.setIndentation(20)     # Set indentation for child items
        self.console_output.setAnimated(True)      # Enable animations for expanding/collapsing
        
        # Ensure model updates trigger a view update - helps with autoscroll
        self.console_output.model().rowsInserted.connect(
            lambda: QTimer.singleShot(10, self.console_output.scrollToBottom) 
            if self.autoscroll_check.isChecked() else None
        )
        self.console_output.setStyleSheet("""
            #consoleOutput {
                background-color: rgba(37, 49, 95, 0.95);
                border: none;
                border-radius: 1px;
                color: #E0E0E0;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                padding: 5px;
                selection-background-color: rgba(0, 166, 237, 0.4);
            }
            #consoleOutput::item {
                border-bottom: 1px solid rgba(0, 166, 237, 0.1);
                padding: 4px 8px;
            }
            #consoleOutput::item:hover {
                background: rgba(0, 166, 237, 0.1);
            }
            #consoleOutput::item:selected {
                background: rgba(0, 166, 237, 0.2);
                border-left: 2px solid #00A6ED;
            }
            #consoleOutput QScrollBar:vertical {
                background: rgba(0, 15, 25, 0.6);
                width: 10px;
                margin: 0px;
            }
            #consoleOutput QScrollBar::handle:vertical {
                background: rgba(0, 166, 237, 0.7);
                min-height: 20px;
                border-radius: 5px;
            }
            #consoleOutput QScrollBar::handle:vertical:hover {
                background: rgba(64, 196, 255, 0.8);
            }
        """)
        console_layout.addWidget(self.console_output)
        layout.addWidget(console_frame, 1)
        # Button Bar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        # Clear Button
        clear_button = QPushButton(f"🗑️ {T('CLEAR_CONSOLE')}")
        clear_button.setObjectName("clearButton")
        clear_button.setStyleSheet("""
            QPushButton#clearButton {
                background: #1976D2;
                border: 1px solid #2196F3;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton#clearButton:hover {
                background: #2196F3;
                border: 1px solid #42A5F5;
            }
        """)
        clear_button.clicked.connect(self.clear_console)
        
        # Save Button
        save_button = QPushButton(f"💾 {T('SAVE_LOG')}")
        save_button.setObjectName("saveButton")
        save_button.setStyleSheet("""
            QPushButton#saveButton {
                background: #455A64;
                border: 1px solid #607D8B;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton#saveButton:hover {
                background: #546E7A;
                border: 1px solid #78909C;
            }
        """)
        save_button.clicked.connect(self.save_console_log)
        # Filter options for console output
        filter_layout = QHBoxLayout()
        filter_label = QLabel(T("FILTER"))
        filter_label.setStyleSheet("color: #E0E0E0; font-size: 13px;")
        # Message filter dropdown
        self.console_filter_combo = QComboBox()
        self.console_filter_combo.setObjectName("consoleFilterCombo")
        self.console_filter_combo.addItems([T("ALL_MESSAGES"), T("INFO_ONLY"), T("WARNINGS_ONLY"), T("ERRORS_ONLY"), T("EVENTS_ONLY")])
        self.console_filter_combo.setStyleSheet("""
            QComboBox {
                background: rgba(37, 49, 95, 0.95);
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: #E0E0E0;
                padding: 5px 10px;
                min-width: 120px;
                font-size: 12px;
            }
            QComboBox:hover {
                background: rgba(63, 75, 118, 0.95);
                border: 1px solid #40C4FF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #00A6ED;
                background: rgba(0, 60, 90, 0.5);
            }
            QComboBox::down-arrow {
                image: url(down-arrow.png);
            }
            QComboBox QAbstractItemView {
                background-color: rgba(0, 15, 25, 0.98);
                border: 1px solid #00A6ED;
                color: #E0E0E0;
                selection-background-color: rgba(0, 119, 170, 0.5);
                selection-color: #FFFFFF;
            }
        """)
        self.console_filter_combo.currentIndexChanged.connect(self.filter_console_output)
        # Autoscroll checkbox
        self.autoscroll_check = QCheckBox(T("AUTO_SCROLL"))
        self.autoscroll_check.setChecked(True)
        self.autoscroll_check.setObjectName("autoscrollCheck")
        
        # Connect the autoscroll toggle to scroll immediately when enabled
        self.autoscroll_check.toggled.connect(self.handle_autoscroll_toggle)
        self.autoscroll_check.setStyleSheet("""
            QCheckBox#autoscrollCheck {
                color: #E0E0E0;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox#autoscrollCheck::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #00A6ED;
                border-radius: 2px;
                background: rgba(0, 60, 90, 0.3);
            }
            QCheckBox#autoscrollCheck::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
            }
            QCheckBox#autoscrollCheck::indicator:hover {
                border: 1px solid #40C4FF;
                background: rgba(0, 77, 115, 0.4);
            }
        """)
        
        # Add filter dropdown to the layout
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.console_filter_combo)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(self.autoscroll_check)
        # Add widgets to button layout
        button_layout.addWidget(clear_button)
        button_layout.addWidget(save_button)
        # Add Expand All / Collapse All buttons
        expand_all_button = QPushButton(T("EXPAND_ALL"))
        expand_all_button.setObjectName("expandAllButton")
        expand_all_button.setStyleSheet("""
            QPushButton#expandAllButton {
                background: #1976D2;
                border: 1px solid #2196F3;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#expandAllButton:hover {
                background: #2196F3;
                border: 1px solid #42A5F5;
            }
        """)
        expand_all_button.clicked.connect(self.expand_all_console_items)
        collapse_all_button = QPushButton(T("COLLAPSE_ALL"))
        collapse_all_button.setObjectName("collapseAllButton")
        collapse_all_button.setStyleSheet("""
            QPushButton#collapseAllButton {
                background: #455A64;
                border: 1px solid #607D8B;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#collapseAllButton:hover {
                background: #546E7A;
                border: 1px solid #78909C;
            }
        """)
        collapse_all_button.clicked.connect(self.collapse_all_console_items)
        
        # Add expand/collapse buttons to layout
        expand_collapse_layout = QHBoxLayout()
        expand_collapse_layout.addWidget(expand_all_button)
        expand_collapse_layout.addWidget(collapse_all_button)
        expand_collapse_layout.setSpacing(5)
        
        button_layout.addLayout(expand_collapse_layout)
        button_layout.addLayout(filter_layout)
        
        layout.addLayout(button_layout)
        
        # Add a footer note or status indicator
        footer = QLabel(T("MONITORING_INACTIVE_TEXT"))
        footer.setObjectName("consoleFooter")
        footer.setStyleSheet("""
            #consoleFooter {
                color: #A8394B;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 2px;
                text-align: center;
                border-top: 1px solid rgba(0, 166, 237, 0.3);
                margin-top: 5px;
            }
        """)
        layout.addWidget(footer)
        self.console_footer = footer
        
        # Setup context menu for console tree
        self.setup_console_tree_context_menu()
        
        return watcher_tab
        
    def clear_console(self):
        """Clear the console output"""
        if self.console_output:
            self.console_output.clear()
            if self.logger:

                self.logger.log_info("Console cleared")
    
    def save_console_log(self):
        """Save the console output to a file"""
        if not self.console_output:
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                T("SAVE_LOG_DIALOG"), 
                os.path.join(self.documents_path, "console_log.txt"),
                "Text Files (*.txt)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Recursive function to extract all text from tree items
                    def extract_item_text(item, level=0):
                        # Write the item's text with proper indentation
                        indent = "  " * level
                        f.write(f"{indent}{item.text(0)}\n")
                        
                        # Write all children
                        for i in range(item.childCount()):
                            extract_item_text(item.child(i), level + 1)
                    
                    # Process all top-level items
                    for i in range(self.console_output.topLevelItemCount()):
                        extract_item_text(self.console_output.topLevelItem(i))
                        
                if self.logger:

                        
                    self.logger.log_info(f"Console log saved to: {file_path}")
        except Exception as e:
                if self.logger:

                    self.logger.log_error(f"Error saving console log: {str(e)}")
    
    def filter_console_output(self):
        """Filter console output based on selected filter"""
        if not self.console_output:
            return
            
        filter_type = self.console_filter_combo.currentText()
        
        for i in range(self.console_output.topLevelItemCount()):
            item = self.console_output.topLevelItem(i)
            
            # Get the item's type from data role
            item_type = item.data(0, Qt.UserRole)
            
            if filter_type == T("ALL_MESSAGES"):
                item.setHidden(False)
            elif filter_type == T("INFO_ONLY") and item_type != "info":
                item.setHidden(True)
            elif filter_type == T("WARNINGS_ONLY") and item_type != "warning":
                item.setHidden(True)
            elif filter_type == T("ERRORS_ONLY") and item_type != "error":
                item.setHidden(True)
            elif filter_type == T("EVENTS_ONLY") and item_type != "event":
                item.setHidden(True)
            else:
                item.setHidden(False)

    def add_kill_event(self, event_details):
        """Add a kill event to the event history"""
        if not event_details:
            return
            
        try:
            # Extract the event data
            timestamp = event_details.get("timestamp", datetime.now().strftime("%H:%M:%S"))
            victim = event_details.get("vname", "Unknown")
            killer = event_details.get("kname", "Unknown") 
            weapon = event_details.get("kwep", "Unknown")
            ship = event_details.get("vship", "Unknown")
            damage_type = event_details.get("dtype", "Unknown")           
            self.session_history = self.event_history.session_history
            self.event_history.record(event_details)
            self.session_history = self.event_history.session_history
            
            # Update event tree in history tab if available
            if hasattr(self, 'events_tree'):
                item = QTreeWidgetItem()
                
                # Determine event type and formatting
                if victim == killer:
                    event_text = f"{victim} committed suicide"
                    item.setForeground(1, QColor("#9C27B0"))  # Purple for suicides
                    event_icon = "💀"
                elif victim == self.player_name:
                    event_text = f"You were killed by {killer}"
                    item.setForeground(1, QColor("#F44336"))  # Red for player deaths
                    event_icon = "☠️"
                elif killer == self.player_name:
                    event_text = f"You killed {victim}"
                    item.setForeground(1, QColor("#4CAF50"))  # Green for player kills
                    event_icon = "🎯"
                elif ("NPC" in victim) or victim.startswith("PU_"):
                    event_text = f"{killer} killed NPC {victim}"
                    item.setForeground(1, QColor("#FF9800"))  # Orange for NPC deaths
                    event_icon = "🤖"
                elif ("NPC" in killer) or killer.startswith("PU_"):
                    event_text = f"{victim} killed by NPC {killer}"
                    item.setForeground(1, QColor("#FF9800"))  # Orange for NPC kills
                    event_icon = "🤖"
                else:
                    event_text = f"{victim} killed by {killer}"
                    item.setForeground(1, QColor("#2196F3"))  # Blue for other kills
                    event_icon = "⚔️"
                
                # Set item text and add to tree
                item.setText(0, timestamp)
                item.setText(1, f"{event_icon} {event_text}")               
                # Add details as child items
                weapon_item = QTreeWidgetItem()
                weapon_item.setText(0, "")
                weapon_item.setText(1, f"🔫 Weapon: {weapon}")             
                ship_item = QTreeWidgetItem()
                ship_item.setText(0, "")
                ship_item.setText(1, f"🚀 Ship: {ship}")              
                damage_item = QTreeWidgetItem()
                damage_item.setText(0, "")
                damage_item.setText(1, f"💥 Damage: {damage_type}")               
                # Add all child items
                item.addChild(weapon_item)
                item.addChild(ship_item)
                item.addChild(damage_item)               
                # Add to events tree
                self.events_tree.insertTopLevelItem(0, item)
                
                # Update the history tab footer
                if hasattr(self, 'history_footer'):
                    kill_count = len(self.session_history.get("kills", []))
                    self.history_footer.setText(T("SESSION_EVENTS", count=kill_count))
                
                # Check if this is a party member event
                victim_member = None
                killer_member = None
                
                # More robust check for party members that handles both data formats
                for member in self.party_members:
                    if isinstance(member, dict) and 'name' in member:
                        if member['name'] == victim:
                            victim_member = member
                        elif member['name'] == killer:
                            killer_member = member
                    elif isinstance(member, str):
                        if member == victim:
                            victim_member = {'name': victim, 'muted': False}
                        elif member == killer:
                            killer_member = {'name': killer, 'muted': False}
                
                is_party_event = victim_member is not None or killer_member is not None
                
                # Update party events if applicable
                if is_party_event and hasattr(self, 'party_events_tree'):
                    party_item = QTreeWidgetItem()
                    
                    # If victim is party member
                    if victim_member is not None:
                        party_item.setText(0, timestamp)
                        party_item.setText(1, victim)
                        party_item.setText(2, f"Killed by {killer}")
                        party_item.setForeground(2, QColor("#F44336"))  # Red for deaths
                        
                        # Show toast notification if not muted
                        if not victim_member['muted'] and hasattr(self, 'toast_manager'):
                            title = f"🎮 Party Member Death"
                            details = f"{victim} was killed by {killer}\n🔫 Weapon: {weapon}\n🚀 Ship: {ship}"
                            self.toast_manager.show_party_toast({"title": title, "details": details})
                    
                    # If killer is party member
                    elif killer_member is not None:
                        party_item.setText(0, timestamp)
                        party_item.setText(1, killer)
                        party_item.setText(2, f"Killed {victim}")
                        party_item.setForeground(2, QColor("#4CAF50"))  # Green for kills
                        
                        # Show toast notification if not muted
                        if not killer_member['muted'] and hasattr(self, 'toast_manager'):
                            title = f"🎮 Party Member Kill"
                            details = f"{killer} killed {victim}\n🔫 Weapon: {weapon}\n🚀 Ship: {ship}"
                            self.toast_manager.show_party_toast({"title": title, "details": details})
                    
                    # Add to party events tree
                    self.party_events_tree.insertTopLevelItem(0, party_item)
                    
                    # Update party footer
                    if hasattr(self, 'party_footer'):
                        member_count = len(self.party_members)
                        event_count = self.party_events_tree.topLevelItemCount()
                        self.party_footer.setText(T("PARTY_FOOTER_TEMPLATE", member_count=member_count, event_count=event_count))
            
        except Exception as e:
                if self.logger:

                    self.logger.log_error(f"Error adding kill event: {str(e)}")
                    import traceback
                    self.logger.log_error(traceback.format_exc())

    def toggle_stay_on_top(self):
        """Toggle whether the window stays on top of other windows"""
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            if self.logger:

                self.logger.log_info("Always on top: Disabled")
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            if self.logger:

                self.logger.log_info("Always on top: Enabled")
                
        # Re-show the window after changing flags
        self.show()
        
        # Save the setting
        if hasattr(self, 'settings'):
            self.settings.setValue("stay_on_top", bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
            
    def validate_toast_positions(self):
        """Ensure that normal toasts and party toasts don't use the same position"""
        if not hasattr(self, 'toast_position_combo') or not hasattr(self, 'party_toast_position_combo'):
            return
            
        # Get current selected positions
        normal_pos = self.toast_position_combo.currentText()
        party_pos = self.party_toast_position_combo.currentText()
        
        # If they're the same, adjust the party position
        if normal_pos == party_pos:
            # Get all available positions
            all_positions = [self.party_toast_position_combo.itemText(i) 
                            for i in range(self.party_toast_position_combo.count())]
            
            # Choose a different position for party toasts
            for pos in all_positions:
                if pos != normal_pos:
                    # Block signals to prevent infinite recursion
                    self.party_toast_position_combo.blockSignals(True)
                    self.party_toast_position_combo.setCurrentText(pos)
                    self.party_toast_position_combo.blockSignals(False)                  
                    # Log the change
                    if self.logger:
                        self.logger.log_info(f"Changed party toast position to {pos} to avoid overlap with normal toasts")
                    break
                    
    def toggle_watching(self):
        """Toggle monitoring without keeping watch lifecycle logic in the UI layer."""
        try:
            if not self.is_watching:
                started = start_monitoring(self)
                if not started:
                    self.save_settings()
                    return
            else:
                stop_monitoring(self)

            self.save_settings()
        except Exception as e:
            self.logger.log_error(f"Error toggling watch state: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())
            self.is_watching = False
            apply_watch_ui_state(self, False, error_message=str(e))

    def create_history_tab(self):
        """Create the history tab with events tracking"""
        history_tab = QWidget()     
        # Create tab layout
        layout = QVBoxLayout(history_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)     
        # Create header with icon
        header_layout = QHBoxLayout()
        header_label = QLabel(T("EVENT_TRACKING_HEADER"))
        header_label.setStyleSheet("""
            color: #00A6ED;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 3px;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)   
        # Description
        description = QLabel(T("EVENT_TRACKING_DESCRIPTION"))
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #90CAF9;
            font-size: 13px;
            margin-bottom: 15px;
            background: rgba(0, 60, 90, 0.3);
            border-radius: 4px;
            padding: 8px;
            border-left: 3px solid #00A6ED;
        """)
        layout.addWidget(description)
        
        # Events Tree
        events_frame = QFrame()
        events_frame.setObjectName("eventsFrame")
        events_frame.setStyleSheet("""
            #eventsFrame {
                background-color: rgba(4, 16, 25, 0.9);
                border: 1px solid #00A6ED;
                border-radius: 4px;
                padding: 2px;
            }
            #eventsFrame:hover {
                border: 1px solid #40C4FF;
                box-shadow: 0 0 10px rgba(64, 196, 255, 0.4);
            }
        """)
        
        events_layout = QVBoxLayout(events_frame)
        events_layout.setContentsMargins(2, 2, 2, 2)
        
        # Set up the events tree with columns for timestamp and event details
        self.events_tree = QTreeWidget()
        self.events_tree.setObjectName("eventsTree")
        self.events_tree.setHeaderLabels(["Time", "Event"])
        self.events_tree.setColumnWidth(0, 80)  # Set timestamp column width
        self.events_tree.setIndentation(20)     # Set indentation for nested items
        self.events_tree.setAnimated(True)      # Enable animations for expanding/collapsing
        self.events_tree.setAlternatingRowColors(True)
        self.events_tree.setStyleSheet("""
            #eventsTree {
                background-color: rgba(0, 15, 25, 0.95);
                border: none;
                border-radius: 2px;
                color: #E0E0E0;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                padding: 5px;
                selection-background-color: rgba(0, 166, 237, 0.4);
            }
            #eventsTree::item {
                border-bottom: 1px solid rgba(0, 166, 237, 0.1);
                padding: 4px 8px;
            }
            #eventsTree::item:hover {
                background: rgba(0, 166, 237, 0.1);
            }
            #eventsTree::item:selected {
                background: rgba(0, 166, 237, 0.2);
                border-left: 2px solid #00A6ED;
            }
            #eventsTree::item:alternate {
                background: rgba(0, 25, 40, 0.4);
            }
            #eventsTree QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                color: white;
                padding: 5px;
                border: 1px solid #00A6ED;
                font-weight: bold;
            }
        """)
        events_layout.addWidget(self.events_tree)
        layout.addWidget(events_frame, 1)
        
        # Button Bar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Clear Button
        clear_button = QPushButton("🗑️ Clear Events")
        clear_button.setObjectName("clearHistoryButton")
        clear_button.setStyleSheet("""
            QPushButton#clearHistoryButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                border: 1px solid #00A6ED;
                border-radius: 4px;
                color: white;
                padding: 2px 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#clearHistoryButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
                border: 1px solid #40C4FF;
            }
        """)
        clear_button.clicked.connect(self.clear_history)
        
        # Export Button
        export_button = QPushButton("💾 Export Events")
        export_button.setObjectName("exportButton")
        export_button.setStyleSheet("""
            QPushButton#exportButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #004D40,
                    stop:1 #00796B
                );
                border: 1px solid #00897B;
                border-radius: 4px;
                color: white;
                padding: 2px 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#exportButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00796B,
                    stop:1 #009688
                );
                border: 1px solid #4DB6AC;
            }
        """)
        export_button.clicked.connect(self.export_events)
        
        # Add widgets to button layout
        button_layout.addWidget(clear_button)
        button_layout.addWidget(export_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Add a footer note or status indicator
        footer = QLabel(T("SESSION_EVENTS", count=0))
        footer.setObjectName("historyFooter")
        footer.setStyleSheet("""
            #historyFooter {
                color: #90CAF9;
                font-size: 12px;
                font-style: italic;
                padding: 5px;
                text-align: center;
                border-top: 1px solid rgba(0, 166, 237, 0.3);
                margin-top: 5px;
            }
        """)
        layout.addWidget(footer)
        self.history_footer = footer
        
        # Setup events tree context menu
        self.setup_events_tree_context_menu()
        
        return history_tab
        
    def clear_history(self):
        """Clear the event history."""
        if hasattr(self, 'events_tree'):
            self.events_tree.clear()
        self.event_history.clear()
        self.session_history = self.event_history.session_history
        if hasattr(self, 'history_footer'):
            self.history_footer.setText(T("SESSION_EVENTS", count=0))
        if self.logger:
            self.logger.log_info("Event history cleared")

    def export_events(self):
        """Export event history to a file."""
        if not hasattr(self, 'events_tree') or self.events_tree.topLevelItemCount() == 0:
            if self.logger:
                self.logger.log_warning("No events to export")
            return

        try:
            export_dir = os.path.join(self.app_dir, "exports")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"events_export_{timestamp}.txt"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Events",
                os.path.join(export_dir, default_filename),
                "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)"
            )

            if file_path:
                if self.event_history.export_tree(self.events_tree, file_path):
                    if self.logger:
                        self.logger.log_info(f"Events exported to: {file_path}")

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error exporting events: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())

    def create_party_tab(self):
        """Create the party tracking tab."""
        return build_party_tab(self)

    def add_party_member(self):
        """Add a new party member to the list"""
        name = self.party_member_input.text().strip()
        if not name:
            if self.logger:
                self.logger.log_warning("Party member name cannot be empty")
            return
            
        # Check if already in the list
        if name in [member['name'] for member in self.party_members]:
            if self.logger:
                self.logger.log_warning(f"Party member '{name}' already exists")
            return
            
        # Add to the list with default unmuted status
        self.party_members.append({'name': name, 'muted': False})
        
        # Clear the input field
        self.party_member_input.clear()
        
        # Update the list widget
        self.update_party_members_list()
        
        # Update footer
        if hasattr(self, 'party_footer'):
            event_count = self.party_events_tree.topLevelItemCount() if hasattr(self, 'party_events_tree') else 0
            self.party_footer.setText(f"Party Members: {len(self.party_members)}, Events tracked: {event_count}")
            
        # Log the addition
        if self.logger:
            self.logger.log_info(f"Added party member: {name}")
            
        # Save settings
        self.save_settings()
    
    def remove_party_member(self):
        """Remove the selected party member from the list"""
        selected_items = self.party_members_list.selectedItems()
        if not selected_items:
            if self.logger:
                self.logger.log_warning("No party member selected for removal")
            return
            
        # Get the selected name
        item = selected_items[0]
        name = item.text()
        
        # Remove from the list - handle both data structures
        for i in range(len(self.party_members) - 1, -1, -1):  # Iterate backwards for safe removal
            member = self.party_members[i]
            if (isinstance(member, dict) and member.get('name') == name) or member == name:
                self.party_members.pop(i)
                break
        
        # Update the list widget
        self.update_party_members_list()
        
        # Update footer
        if hasattr(self, 'party_footer'):
            event_count = self.party_events_tree.topLevelItemCount() if hasattr(self, 'party_events_tree') else 0
            self.party_footer.setText(f"Party Members: {len(self.party_members)}, Events tracked: {event_count}")
        
        # Log the removal
        if self.logger:
            self.logger.log_info(f"Removed party member: {name}")
        
        # Save settings
        self.save_settings()

    def clear_party_members(self):
        """Clear all party members from the list"""
        # Clear the list
        self.party_members = []
        
        # Update the list widget
        self.update_party_members_list()
        
        # Update footer
        if hasattr(self, 'party_footer'):
            event_count = self.party_events_tree.topLevelItemCount() if hasattr(self, 'party_events_tree') else 0
            self.party_footer.setText(f"Party Members: {len(self.party_members)}, Events tracked: {event_count}")
            
        # Log the clear action
        if self.logger:
            self.logger.log_info("Cleared all party members")
            
        # Save settings
        self.save_settings()
    
    def clear_party_events(self):
        """Clear all party event tracking"""
        try:
            if hasattr(self, 'party_events_tree'):
                self.party_events_tree.clear()
            
            # Reset the event count in the footer
            if hasattr(self, 'party_footer'):
                member_count = len(self.party_members) if hasattr(self, 'party_members') else 0
                self.party_footer.setText(f"Party Members: {member_count}, Events tracked: 0")
            
            if self.logger:
                self.logger.log_info("Party events cleared")
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error clearing party events: {str(e)}")
    
    def export_party_events(self):
        """Export party event history to a file"""
        if not hasattr(self, 'party_events_tree') or self.party_events_tree.topLevelItemCount() == 0:
            if self.logger:
                self.logger.log_warning("No party events to export")
            return
            
        try:
            export_dir = os.path.join(self.app_dir, "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Default filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"party_events_export_{timestamp}.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Party Events", 
                os.path.join(export_dir, default_filename),
                "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("VERSEWATCHER - PARTY EVENT EXPORT\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Write all party events
                    for i in range(self.party_events_tree.topLevelItemCount()):
                        item = self.party_events_tree.topLevelItem(i)
                        time_str = item.text(0)
                        member = item.text(1)
                        event = item.text(2)
                        f.write(f"{time_str} | {member} | {event}\n")
                    
                    f.write("\n" + "=" * 50 + "\n")
                    f.write(f"Total Events: {self.party_events_tree.topLevelItemCount()}")
                
                self.logger.log_info(f"Party events exported to {file_path}")
                
                # Open the exports folder
                if os.path.exists(os.path.dirname(file_path)):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(file_path)))
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error exporting party events: {str(e)}")
    
    def update_party_members_list(self):
        """Update the party members list widget from the array"""
        try:
            # Make sure party_members is initialized
            if not hasattr(self, 'party_members'):
                self.party_members = []
            
            # Ensure proper format for party_members (handle legacy data)
            if self.party_members and isinstance(self.party_members[0], str):
                self.party_members = [{'name': name, 'muted': False} for name in self.party_members]
                if self.logger:
                    self.logger.log_info("Fixed party members format during update")
                
            # Make sure party_members_list exists
            if not hasattr(self, 'party_members_list') or self.party_members_list is None:
                return
                    
            # Clear current items
            self.party_members_list.clear()
            
            # Add each member
            for member in self.party_members:
                # Handle both dict and string formats just to be safe
                if isinstance(member, dict) and 'name' in member:
                    name = member['name']
                    muted = member.get('muted', False)
                elif isinstance(member, str):
                    name = member
                    muted = False
                else:
                    continue  # Skip invalid entries
                
                item = QListWidgetItem(name)
                
                # Set text color to yellow if muted
                if muted:
                    item.setForeground(QColor("#FFC107"))  # Yellow color for muted players
                
                self.party_members_list.addItem(item)
                
            # Update footer if available
            if hasattr(self, 'party_footer'):
                event_count = 0
                if hasattr(self, 'party_events_tree'):
                    event_count = self.party_events_tree.topLevelItemCount()
                self.party_footer.setText(f"Party Members: {len(self.party_members)}, Events tracked: {event_count}")
                
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_error(f"Error updating party members list: {str(e)}")
                import traceback
                self.logger.log_error(traceback.format_exc())

    def show_party_context_menu(self, position):
        """Show context menu for party members list"""
        # Get the selected item
        selected_items = self.party_members_list.selectedItems()
        if not selected_items:
            return
            
        selected_name = selected_items[0].text()
        
        # Find the member in the list - handle multiple formats
        selected_member = None
        for member in self.party_members:
            if isinstance(member, dict) and member.get('name') == selected_name:
                selected_member = member
                break
            elif isinstance(member, str) and member == selected_name:
                # Convert to dict if it's a string
                selected_member = {'name': selected_name, 'muted': False}
                # Replace the string with dict in the list
                index = self.party_members.index(member)
                self.party_members[index] = selected_member
                break
                
        if not selected_member:
            return
            
        # Create context menu
        menu = QMenu()
        
        # Add dossier action - only for real players
        if not selected_name.startswith("PU_") and "NPC" not in selected_name:
            dossier_action = menu.addAction("👤 View Dossier")
        
        remove_action = menu.addAction("🗑️ Remove")
        
        # Add Mute/Unmute action based on current status
        if selected_member.get('muted', False):
            mute_action = menu.addAction("🔊 Unmute")
        else:
            mute_action = menu.addAction("🔇 Mute")
        
        # Get action
        action = menu.exec_(self.party_members_list.mapToGlobal(position))
        
        # Handle action
        if action == remove_action:
            self.remove_party_member()
        elif action == mute_action:
            self.toggle_party_member_mute(selected_name)
        elif 'dossier_action' in locals() and action == dossier_action:
            self.open_player_dossier(selected_name)
    
    def toggle_party_member_mute(self, member_name):
        """Toggle mute status for a party member"""
        for i, member in enumerate(self.party_members):
            # Handle both dict and string formats
            if isinstance(member, dict) and member.get('name') == member_name:
                # Toggle mute status
                member['muted'] = not member.get('muted', False)
                
                # Log the action
                status = "muted" if member['muted'] else "unmuted"
                if self.logger:
                    self.logger.log_info(f"Party member '{member_name}' {status}")
                
                # Update the list to reflect the change
                self.update_party_members_list()
                
                # Save settings
                self.save_settings()
                break
            elif isinstance(member, str) and member == member_name:
                # Convert string to dict and set muted to True
                new_member = {'name': member_name, 'muted': True}
                self.party_members[i] = new_member
                
                # Log the action
                if self.logger:
                    self.logger.log_info(f"Party member '{member_name}' muted")
                
                # Update the list to reflect the change
                self.update_party_members_list()
                
                # Save settings
                self.save_settings()
                break

    def create_settings_tab(self):
        """Create the settings tab with app configuration options."""
        return build_settings_tab(self)
        settings_tab = QWidget()
        
        # Create tab layout
        layout = QVBoxLayout(settings_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Create header with icon
        header_layout = QHBoxLayout()
        header_icon = QLabel("⚙️")
        header_icon.setStyleSheet("""
            font-size: 24px;
            margin-right: 10px;
        """)
        header_label = QLabel("SETTINGS")
        header_label.setStyleSheet("""
            color: #00A6ED;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 3px;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Create content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)

        # General settings group
        general_group = QGroupBox("GENERAL SETTINGS")
        general_group.setObjectName("settingsGroup")
        general_group.setStyleSheet("""
            QGroupBox#settingsGroup {
                border: 1px solid #00A6ED;
                border-radius: 5px;
                margin-top: 15px;
                font-size: 14px;
                font-weight: bold;
                color: #00A6ED;
            }
            QGroupBox#settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        general_layout = QFormLayout(general_group)
        general_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        general_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        general_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        general_layout.setContentsMargins(15, 25, 15, 15)
        general_layout.setSpacing(15)
        
        # Game log path
        path_label = QLabel(T("GAME_INSTALL_DIRECTORY"))
        path_label.setStyleSheet("font-weight: bold;")
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText(T("DEFAULT_GAME_PATH"))
        self.path_input.setStyleSheet("""
            padding: 8px;
            font-family: 'Consolas', monospace;
        """)
        
        browse_button = QPushButton("📂 Browse")
        browse_button.setFixedWidth(120)
        browse_button.clicked.connect(self.browse_game_dir)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        
        general_layout.addRow(path_label, path_layout)
        
        # Player name
        name_label = QLabel(T("YOUR_PLAYER_NAME"))
        name_label.setStyleSheet("font-weight: bold;")
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(T("ENTER_YOUR_HANDLE"))
        self.name_input.setStyleSheet("""
            padding: 8px;
        """)
        
        general_layout.addRow(name_label, self.name_input)
        
        # Always on top option
        ontop_label = QLabel(T("STAY_ON_TOP_LABEL"))
        ontop_label.setStyleSheet("font-weight: bold;")
        
        ontop_check = QCheckBox("Keep app window on top of other windows")
        ontop_check.setChecked(bool(self.windowFlags() & Qt.WindowStaysOnTopHint))
        ontop_check.stateChanged.connect(self.toggle_stay_on_top)
        
        general_layout.addRow(ontop_label, ontop_check)
        
        content_layout.addWidget(general_group)
        
        # Toast Notifications Group
        toast_group = QGroupBox("TOAST NOTIFICATIONS")
        toast_group.setObjectName("settingsGroup")
        toast_group.setStyleSheet("""
            QGroupBox#settingsGroup {
                border: 1px solid #00A6ED;
                border-radius: 5px;
                margin-top: 15px;
                font-size: 14px;
                font-weight: bold;
                color: #00A6ED;
            }
            QGroupBox#settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        toast_layout = QFormLayout(toast_group)
        toast_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        toast_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        toast_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        toast_layout.setContentsMargins(15, 25, 15, 15)
        toast_layout.setSpacing(15)
        
        # Toast position
        position_label = QLabel("Toast Position:")
        position_label.setStyleSheet("font-weight: bold;")
        
        self.toast_position_combo = QComboBox()
        self.toast_position_combo.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Left Middle", "Right Middle"])
        self.toast_position_combo.setCurrentText("Bottom Right")  # Default
        self.toast_position_combo.setStyleSheet("""
            padding: 6px;
                min-width: 150px;
        """)
        
        toast_layout.addRow(position_label, self.toast_position_combo)
        
        # Toast size
        size_label = QLabel("Toast Size:")
        size_label.setStyleSheet("font-weight: bold;")
        
        self.toast_size_combo = QComboBox()
        self.toast_size_combo.addItems(["Very Small", "Small", "Medium", "Large", "Very Large"])
        self.toast_size_combo.setCurrentText("Medium")  # Default
        self.toast_size_combo.setStyleSheet("""
            padding: 6px;
                min-width: 150px;
        """)
        
        toast_layout.addRow(size_label, self.toast_size_combo)
        
        # Toast duration
        duration_label = QLabel("Toast Duration:")
        duration_label.setStyleSheet("font-weight: bold;")
        
        self.toast_duration_combo = QComboBox()
        self.toast_duration_combo.addItems(["2 seconds", "3 seconds", "5 seconds", "8 seconds", "10 seconds"])
        self.toast_duration_combo.setCurrentText("5 seconds")  # Default
        self.toast_duration_combo.setStyleSheet("""
            padding: 6px;
                min-width: 150px;
        """)
        
        toast_layout.addRow(duration_label, self.toast_duration_combo)
        
        # Maximum toast stack
        max_stack_label = QLabel("Max Toast Stack:")
        max_stack_label.setStyleSheet("font-weight: bold;")
        
        self.toast_max_stack_combo = QComboBox()
        self.toast_max_stack_combo.addItems([str(i) for i in range(1, 11)])  # 1-10
        self.toast_max_stack_combo.setCurrentText("5")  # Default
        self.toast_max_stack_combo.setStyleSheet("""
            padding: 6px;
            min-width: 150px;
        """)
        
        toast_layout.addRow(max_stack_label, self.toast_max_stack_combo)
        
        content_layout.addWidget(toast_group)
        
        # Party Toast Notifications Group
        party_toast_group = QGroupBox("PARTY TOAST NOTIFICATIONS")
        party_toast_group.setObjectName("settingsGroup")
        party_toast_group.setStyleSheet("""
            QGroupBox#settingsGroup {
                border: 1px solid #00A6ED;
                border-radius: 5px;
                margin-top: 15px;
            font-size: 14px;
            font-weight: bold;
                color: #00A6ED;
            }
            QGroupBox#settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        party_toast_layout = QFormLayout(party_toast_group)
        party_toast_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        party_toast_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        party_toast_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        party_toast_layout.setContentsMargins(15, 25, 15, 15)
        party_toast_layout.setSpacing(15)
        
        # Party toast position
        party_position_label = QLabel(T("PARTY_TOAST_POSITION"))
        party_position_label.setStyleSheet("font-weight: bold;")
        
        self.party_toast_position_combo = QComboBox()
        self.party_toast_position_combo.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Left Middle", "Right Middle"])
        self.party_toast_position_combo.setCurrentText("Top Right")  # Default
        self.party_toast_position_combo.setStyleSheet("""
            padding: 6px;
                min-width: 150px;
        """)
        
        # Connect signal to ensure party toast position is different from regular toast position
        self.toast_position_combo.currentIndexChanged.connect(self.validate_toast_positions)
        self.party_toast_position_combo.currentIndexChanged.connect(self.validate_toast_positions)
        
        party_toast_layout.addRow(party_position_label, self.party_toast_position_combo)
        
        # Party toast size
        party_size_label = QLabel(T("PARTY_TOAST_SIZE"))
        party_size_label.setStyleSheet("font-weight: bold;")
        
        self.party_toast_size_combo = QComboBox()
        self.party_toast_size_combo.addItems(["Very Small", "Small", "Medium", "Large", "Very Large"])
        self.party_toast_size_combo.setCurrentText("Medium")  # Default
        self.party_toast_size_combo.setStyleSheet("""
            padding: 6px;
                min-width: 150px;
        """)
        
        
        party_toast_layout.addRow(party_size_label, self.party_toast_size_combo)
        
        # Party toast duration
        party_duration_label = QLabel(T("PARTY_TOAST_DURATION"))
        party_duration_label.setStyleSheet("font-weight: bold;")
        
        self.party_toast_duration_combo = QComboBox()
        self.party_toast_duration_combo.addItems(["2 seconds", "3 seconds", "5 seconds", "8 seconds", "10 seconds"])
        self.party_toast_duration_combo.setCurrentText("5 seconds")  # Default
        self.party_toast_duration_combo.setStyleSheet("""
            padding: 6px;
                min-width: 150px;
        """)
        
        party_toast_layout.addRow(party_duration_label, self.party_toast_duration_combo)
        
        # Maximum party toast stack
        party_max_stack_label = QLabel(T("PARTY_TOAST_MAX_STACK"))
        party_max_stack_label.setStyleSheet("font-weight: bold;")
        
        self.party_toast_max_stack_combo = QComboBox()
        self.party_toast_max_stack_combo.addItems([str(i) for i in range(1, 11)])  # 1-10
        self.party_toast_max_stack_combo.setCurrentText("5")  # Default
        self.party_toast_max_stack_combo.setStyleSheet("""
            padding: 6px;
            min-width: 150px;
        """)
        
        party_toast_layout.addRow(party_max_stack_label, self.party_toast_max_stack_combo)
        
        content_layout.addWidget(party_toast_group)
        
        # Event Filtering group
        event_group = QGroupBox("EVENT FILTERING")
        event_group.setObjectName("settingsGroup")
        event_group.setFixedHeight(200)  # Fixed height
        event_group.setStyleSheet("""
            QGroupBox#settingsGroup {
                border: 1px solid #00A6ED;
                border-radius: 5px;
                margin-top: 15px;
                font-size: 14px;
                font-weight: bold;
                color: #00A6ED;
            }
            QGroupBox#settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        event_layout = QVBoxLayout(event_group)
        event_layout.setContentsMargins(15, 25, 15, 15)
        event_layout.setSpacing(10)
        
        event_desc = QLabel(T("SELECT_EVENT_TYPES"))
        event_desc.setWordWrap(True)
        event_desc.setStyleSheet("""
            color: #90CAF9;
            font-size: 13px;
        """)
        event_layout.addWidget(event_desc)
        
        # Create a grid layout for checkboxes to make them more compact
        check_grid = QGridLayout()
        check_grid.setContentsMargins(0, 10, 0, 0)
        check_grid.setSpacing(10)
        
        # Event type checkboxes
        self.self_events_check = QCheckBox("Your own kills & deaths")
        self.self_events_check.setChecked(True)
        check_grid.addWidget(self.self_events_check, 0, 0)
        
        self.other_events_check = QCheckBox("Other player kills & deaths")
        self.other_events_check.setChecked(True)
        check_grid.addWidget(self.other_events_check, 0, 1)
        
        self.npc_events_check = QCheckBox("NPC kills & deaths")
        self.npc_events_check.setChecked(True)
        check_grid.addWidget(self.npc_events_check, 1, 0)
        
        self.suicide_events_check = QCheckBox("Suicide events")
        self.suicide_events_check.setChecked(True)
        check_grid.addWidget(self.suicide_events_check, 1, 1)
        
        self.party_events_check = QCheckBox("Party member events")
        self.party_events_check.setChecked(True)
        check_grid.addWidget(self.party_events_check, 2, 0)
        
        event_layout.addLayout(check_grid)
        event_layout.addStretch()
        
        content_layout.addWidget(event_group)
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        return settings_tab
        
    def browse_game_directory(self):
        """Backward-compatible alias for the directory picker callback."""
        return self.browse_game_dir()

    def browse_game_dir(self):
        """Open dialog to browse for Star Citizen installation directory"""
        try:
            # Common locations to check for the Star Citizen installation
            common_paths = [
                "C:\\Program Files\\Roberts Space Industries\\StarCitizen",
                "D:\\Program Files\\Roberts Space Industries\\StarCitizen",
                "E:\\Program Files\\Roberts Space Industries\\StarCitizen",
                os.path.expanduser("~/Roberts Space Industries/StarCitizen")
            ]
            
            # Find the first existing path to use as default
            default_dir = None
            for path in common_paths:
                if os.path.exists(path):
                    default_dir = path
                    break
                    
            # If no common path found, use Documents folder
            if not default_dir:
                default_dir = self.documents_path
            
            # Open directory selection dialog
            directory = QFileDialog.getExistingDirectory(
            self,
                "Select Star Citizen Installation Directory",
                default_dir
            )
            
            if directory:
                # Update the input field
                self.path_input.setText(directory)
                
                # Check if the directory contains Game.log
                game_log_path = os.path.join(directory, "Game.log")
                if not os.path.exists(game_log_path):
                    # Check if it's the parent directory
                    live_dir = os.path.join(directory, "LIVE")
                    if os.path.exists(live_dir):
                        self.path_input.setText(live_dir)
                        self.logger.log_info(f"Selected LIVE directory: {live_dir}")
                    else:
                        self.logger.log_warning(f"Game.log not found in selected directory. Please make sure you select the correct Star Citizen installation directory.")
                else:
                    self.logger.log_info(f"Selected game directory: {directory}")
                
                # Save settings
                self.save_settings()
                
        except Exception as e:
                if self.logger:

                    self.logger.log_error(f"Error browsing for game directory: {str(e)}")
                import traceback
                self.logger.log_error(traceback.format_exc())
                
    def save_settings(self):
        """Save settings to file."""
        return save_app_settings(self)

    def load_settings(self):
        """Load settings from file."""
        return load_app_settings(self)

    def reset_settings(self):
        """Reset settings to defaults"""
        try:
            # Reset game path
            if hasattr(self, 'path_input'):
                self.path_input.clear()           
            # Reset player name
            if hasattr(self, 'name_input'):
                self.name_input.clear()
                self.player_name = None           
            # Reset event filters
            if hasattr(self, 'self_events_check'):
                self.self_events_check.setChecked(True)        
            if hasattr(self, 'other_events_check'):
                self.other_events_check.setChecked(True)       
            if hasattr(self, 'npc_events_check'):
                self.npc_events_check.setChecked(True)           
            if hasattr(self, 'suicide_events_check'):
                self.suicide_events_check.setChecked(True)            
            if hasattr(self, 'party_events_check'):
                self.party_events_check.setChecked(True)            
            # Reset toast config
            if hasattr(self, 'toast_position_combo'):
                self.toast_position_combo.setCurrentText("Bottom Right")           
            if hasattr(self, 'toast_size_combo'):
                self.toast_size_combo.setCurrentText("Medium")           
            if hasattr(self, 'toast_duration_combo'):
                self.toast_duration_combo.setCurrentText("5 seconds")               
            if hasattr(self, 'toast_max_stack_combo'):
                self.toast_max_stack_combo.setCurrentText("5")           
            # Reset party toast config
            if hasattr(self, 'party_toast_position_combo'):
                self.party_toast_position_combo.setCurrentText("Top Right")          
            if hasattr(self, 'party_toast_size_combo'):
                self.party_toast_size_combo.setCurrentText("Medium")           
            if hasattr(self, 'party_toast_duration_combo'):
                self.party_toast_duration_combo.setCurrentText("5 seconds")               
            if hasattr(self, 'party_toast_max_stack_combo'):
                self.party_toast_max_stack_combo.setCurrentText("5")
            # Update toast manager
            if hasattr(self, 'toast_manager') and self.toast_manager:
                self.toast_manager.update_config(
                    position="Bottom Right",
                    size="Medium",
                    duration=5000,
                    max_stack=5
                )              
                self.toast_manager.update_party_config(
                    position="Top Right",
                    size="Medium",
                    duration=5000,
                    max_stack=5
                )
            
            if self.logger:           
                self.logger.log_info("Settings reset to defaults")
                
        except Exception as e:
                if self.logger:
                    self.logger.log_error(f"Error resetting settings: {str(e)}")
                import traceback
                self.logger.log_error(traceback.format_exc())
    
    def setup_tray_icon(self):
        """Setup system tray icon and menu"""
        try:
            # Initialize tray icon first
            self.tray_icon = QSystemTrayIcon(self)
            
            # Load icons for different states
            self.icon_yellow = QIcon()  # Not watching
            self.icon_green = QIcon()   # Watching
            self.icon_red = QIcon()     # Error
            
            # Get paths to icon files
            icon_yellow_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon-y.ico")
            icon_green_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon-g.ico")
            icon_red_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon-r.ico")
            
            # Load icons if files exist, otherwise use fallback
            if os.path.exists(icon_yellow_path):
                self.icon_yellow.addFile(icon_yellow_path)
            else:
                self.logger.log_warning(f"Yellow icon not found at {icon_yellow_path}, using fallback")
                self.icon_yellow = QIcon(self.style().standardIcon(QStyle.SP_MessageBoxWarning))
                
            if os.path.exists(icon_green_path):
                self.icon_green.addFile(icon_green_path)
            else:
                self.logger.log_warning(f"Green icon not found at {icon_green_path}, using fallback")
                self.icon_green = QIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
                
            if os.path.exists(icon_red_path):
                self.icon_red.addFile(icon_red_path)
            else:
                self.logger.log_warning(f"Red icon not found at {icon_red_path}, using fallback")
                self.icon_red = QIcon(self.style().standardIcon(QStyle.SP_MessageBoxCritical))
           
            # Create tray icon menu
            tray_menu = QMenu()
            
            # Create dynamic show/hide action
            self.show_hide_action = QAction(T("HIDE_TO_TRAY"), self)
            self.show_hide_action.triggered.connect(self.toggle_show_hide)
            tray_menu.addAction(self.show_hide_action)
            
            tray_menu.addSeparator()
            
            # Create dynamic monitoring action
            self.monitoring_tray_action = QAction(T("START_MONITORING"), self)
            self.monitoring_tray_action.triggered.connect(self.toggle_watching)
            tray_menu.addAction(self.monitoring_tray_action)
            
            tray_menu.addSeparator()
            
            # Add stay on top action
            tray_menu.addAction(self.stay_on_top_action)
            
            tray_menu.addSeparator()
            
            # Add exit action that truly exits the app
            exit_action = QAction(T("EXIT"), self)
            exit_action.triggered.connect(self.force_exit)
            tray_menu.addAction(exit_action)
            
            # Set initial icon (yellow for not watching)
            self.tray_icon.setIcon(self.icon_yellow)
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.setToolTip(T("TRAY_INACTIVE"))
            self.tray_icon.activated.connect(self.tray_icon_activated)
            
            # Show the tray icon
            self.tray_icon.show()
            
            if self.logger:
                self.logger.log_info("Tray icon initialized successfully")
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error setting up tray icon: {str(e)}")
            # Set tray_icon to None so we don't try to use it
            self.tray_icon = None
            
    def toggle_show_hide(self):
        """Toggle between showing and hiding the application"""
        if self.isVisible():
            # Currently visible, hide it
            # Important: Don't call hide() directly because closeEvent handles tray behavior
            # Instead we'll set our own internal flag to keep the application running in the background
            self.hide()
            
            # Make sure our toast manager stays active when minimized
            if hasattr(self, 'toast_manager') and self.toast_manager:
                # Refresh any existing toasts to ensure they remain visible
                self.toast_manager._position_toasts()
            
            self.show_hide_action.setText(T("SHOW_FROM_TRAY"))
            if self.logger:
                self.logger.log_info("Application hidden to tray")
        else:
            # Currently hidden, show it
            self.show()
            self.show_hide_action.setText(T("HIDE_TO_TRAY"))
            self.raise_()
            self.activateWindow()
            if self.logger:
                self.logger.log_info("Application shown from tray")
    
    def force_exit(self):
        """Force exit the application completely, bypassing tray icon hide behavior"""
        try:
            # Clean up resources
            if self.is_watching and self.watcher:
                self.watcher.stop()
                
            if hasattr(self, 'toast_manager'):
                self.toast_manager.cleanup()
                
            # Save window geometry first
            self.save_window_geometry()
            
            # Save other settings 
            self.save_settings()
            
            # Exit the application
            QApplication.instance().quit()
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error during force exit: {str(e)}")
            # Ensure we exit even if there's an error
            import sys
            sys.exit(0)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            # If window is hidden, show it
            if not self.isVisible():
                self.show()
                
                # Update the show/hide action text
                if hasattr(self, 'show_hide_action'):
                    self.show_hide_action.setText(T("HIDE_TO_TRAY"))
            
            # Bring window to front and give it focus
            self.showNormal()  # In case it was minimized
            self.raise_()
            self.activateWindow()
            
            if self.logger:
                self.logger.log_info("Window shown from tray icon")
    
    def closeEvent(self, event):
        """Handle window close event"""
        try:
            # Save window geometry - do this first in case later steps fail
            try:
                self.save_window_geometry()
            except Exception as e:
                if self.logger:
                    self.logger.log_error(f"Error saving window geometry during close: {str(e)}")

            # Make sure to clean up the watcher first to avoid timer issues
            if self.is_watching and self.watcher:
                try:
                    self.watcher.stop()
                    self.is_watching = False
                except Exception as e:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.log_error(f"Error stopping watcher during close: {str(e)}")
            
            # Check if window was closed by X button - hide to tray if tray icon is available
            # Close action from menu will use force_exit and bypass this
            if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
                self.hide()
                
                # DO NOT clean up toast manager when hiding to tray
                # This is key to keep toast notifications working while minimized
                
                # Make sure any existing toasts remain visible by refreshing their positions
                if hasattr(self, 'toast_manager') and self.toast_manager:
                    self.toast_manager._position_toasts()
                
                # Update the show/hide action text
                if hasattr(self, 'show_hide_action'):
                    self.show_hide_action.setText(T("SHOW_FROM_TRAY"))
                    
                if hasattr(self, 'logger') and self.logger:
                    self.logger.log_info("Window hidden to tray")
                event.ignore()

            else:
                # No tray icon, perform final cleanup
                # First check if there is still a toast_manager (might have been freed)
                if hasattr(self, 'toast_manager') and self.toast_manager:
                    try:
                        self.toast_manager.cleanup()
                    except Exception as e:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.log_error(f"Error cleaning up toast manager: {str(e)}")
                            
                if hasattr(self, 'watcher') and self.watcher:
                    try:
                        self.watcher.stop()
                    except Exception:
                        pass
                        
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    try:
                        self.tray_icon.hide()
                    except Exception:
                        pass
                        
                if hasattr(self, 'logger') and self.logger:
                    self.logger.log_info("Application closing")
                event.accept()
                
        except Exception as e:
            # Super fallback for any unexpected errors
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_error(f"Unexpected error during close: {str(e)}")
                import traceback
                self.logger.log_error(traceback.format_exc())
                
            # Do minimal cleanup and accept close
            if hasattr(self, 'watcher') and self.watcher:
                try:
                    self.watcher.stop()
                except Exception:
                    pass
                    
            if hasattr(self, 'toast_manager') and self.toast_manager:
                try:
                    self.toast_manager.cleanup()
                except Exception:
                    pass
                    
            event.accept()

    def expand_all_console_items(self):
        """Expand all items in the console output tree"""
        if not self.console_output:
            return
            
        try:
            # Expand all top-level items and their children
            for i in range(self.console_output.topLevelItemCount()):
                item = self.console_output.topLevelItem(i)
                self.console_output.expandItem(item)
                
                # Recursively expand all child items
                def expand_children(parent_item):
                    for j in range(parent_item.childCount()):
                        child = parent_item.child(j)
                        self.console_output.expandItem(child)
                        if child.childCount() > 0:
                            expand_children(child)
                
                expand_children(item)
                
            if self.logger:
                self.logger.log_info("Expanded all console items")
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error expanding console items: {str(e)}")
    
    def collapse_all_console_items(self):
        """Collapse all items in the console output tree"""
        if not self.console_output:
            return
            
        try:
            # Collapse all top-level items (which collapses their children as well)
            for i in range(self.console_output.topLevelItemCount()):
                item = self.console_output.topLevelItem(i)
                self.console_output.collapseItem(item)
                
            if self.logger:
                self.logger.log_info("Collapsed all console items")
                
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error collapsing console items: {str(e)}")

    def moveEvent(self, event):
        """Handle window move event to save geometry"""
        # Call parent class implementation first
        super().moveEvent(event)
        # Save position after a short delay to avoid too frequent saves
        QTimer.singleShot(500, self.save_window_geometry)
        
    def resizeEvent(self, event):
        """Handle window resize event to save geometry"""
        # Call parent class implementation first
        super().resizeEvent(event)
        # Save size after a short delay to avoid too frequent saves
        QTimer.singleShot(500, self.save_window_geometry)

    def handle_autoscroll_toggle(self, checked):
        """Handle toggling of the autoscroll checkbox"""
        if checked and self.console_output:
            # If autoscroll is enabled, immediately scroll to the bottom
            QTimer.singleShot(10, self.console_output.scrollToBottom)

    def open_player_dossier(self, player_name):
        """Open the RSI dossier page for a player in the default web browser"""
        if not player_name or player_name.startswith("PU_") or "NPC" in player_name:
            # Don't open for NPCs or invalid names
            if self.logger:
                self.logger.log_warning(f"Cannot open dossier for NPC or invalid name: {player_name}")
            return
        
        try:
            # Construct the RSI citizen URL
            url = f"https://robertsspaceindustries.com/en/citizens/{player_name}"
            
            # Open in default browser
            webbrowser.open(url)
            
            if self.logger:
                self.logger.log_info(f"Opened dossier for player: {player_name}")
        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error opening dossier for {player_name}: {str(e)}")

    def extract_player_name_from_event(self, item_text):
        """Extract a player name from an event text string"""
        if not item_text:
            return None
            
        # Common text patterns in event descriptions:
        # "{victim} committed suicide"
        # "You were killed by {killer}"
        # "You killed {victim}"
        # "{killer} killed NPC {victim}" - NPC case, should be ignored for killer
        # "{victim} killed by NPC {killer}" - NPC case, should be ignored for victim
        # "{victim} killed by {killer}"
        
        # Ignore items about NPCs
        if "NPC" in item_text or "PU_" in item_text:
            # Check if there's a real player name in there
            if "killed NPC" in item_text:
                # Extract the player who killed the NPC
                parts = item_text.split("killed NPC")
                if parts and len(parts) > 0:
                    player = parts[0].strip()
                    if player and "NPC" not in player and not player.startswith("PU_"):
                        return player
            elif "killed by NPC" in item_text:
                # Extract the player who was killed by the NPC
                parts = item_text.split("killed by NPC")
                if parts and len(parts) > 0:
                    player = parts[0].strip()
                    if player and "NPC" not in player and not player.startswith("PU_"):
                        return player
            return None
        
        # Handle "You killed" or "You were killed by" case
        if item_text.startswith("You killed "):
            return item_text.replace("You killed ", "").strip()
        elif "killed by" in item_text:
            if item_text.startswith("You were killed by "):
                return item_text.replace("You were killed by ", "").strip()
            else:
                parts = item_text.split("killed by")
                if len(parts) == 2:
                    victim = parts[0].strip()
                    killer = parts[1].strip()
                    # Return the name being clicked on (this depends on context)
                    return victim  # Default to victim, context menu will need to handle both
        elif "committed suicide" in item_text:
            return item_text.split("committed suicide")[0].strip()
        elif "killed" in item_text and "NPC" not in item_text:
            parts = item_text.split("killed")
            if len(parts) == 2:
                killer = parts[0].strip()
                return killer
                
        return None

    def setup_events_tree_context_menu(self):
        """Set up context menu for events tree"""
        if not hasattr(self, 'events_tree'):
            return
            
        # Set custom context menu policy
        self.events_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.events_tree.customContextMenuRequested.connect(self.show_events_context_menu)
        
    def show_events_context_menu(self, position):
        """Show context menu for events tree"""
        if not self.events_tree:
            return
            
        # Get selected item
        item = self.events_tree.itemAt(position)
        if not item:
            return
            
        # Try to extract player name from item text
        item_text = item.text(1)
        if not item_text:
            return
            
        # Remove emojis for parsing
        clean_text = ""
        for c in item_text:
            if ord(c) < 0x10000:  # Simple way to skip emojis
                clean_text += c
                
        player_name = self.extract_player_name_from_event(clean_text.strip())
        if not player_name or player_name == "You":
            return
            
        # Create menu
        menu = QMenu()
        dossier_action = menu.addAction(f"👤 View Dossier for {player_name}")
        
        # Show menu and get selected action
        action = menu.exec_(self.events_tree.mapToGlobal(position))
        
        # Handle action
        if action == dossier_action:
            self.open_player_dossier(player_name)

    def setup_party_events_tree_context_menu(self):
        """Set up context menu for party events tree"""
        if not hasattr(self, 'party_events_tree'):
            return
            
        # Set custom context menu policy
        self.party_events_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.party_events_tree.customContextMenuRequested.connect(self.show_party_events_context_menu)
    
    def show_party_events_context_menu(self, position):
        """Show context menu for party events tree"""
        if not self.party_events_tree:
            return
            
        # Get selected item
        item = self.party_events_tree.itemAt(position)
        if not item:
            return
            
        # Get player names from the item
        # Party events tree has columns: [Time, Member, Event]
        party_member = item.text(1)  # Member column
        event_text = item.text(2)    # Event column
        
        # Check if we have valid player names
        players = []
        
        # Add party member (always a player)
        if party_member and not party_member.startswith("PU_") and "NPC" not in party_member:
            players.append(("Party Member", party_member))
        
        # Extract other player from event text
        if event_text:
            if event_text.startswith("Killed "):
                # Member killed someone - extract victim
                victim = event_text.replace("Killed ", "").strip()
                if victim and not victim.startswith("PU_") and "NPC" not in victim:
                    players.append(("Target", victim))
            elif event_text.startswith("Killed by "):
                # Member was killed by someone - extract killer
                killer = event_text.replace("Killed by ", "").strip()
                if killer and not killer.startswith("PU_") and "NPC" not in killer:
                    players.append(("Killer", killer))
        
        if not players:
            return
            
        # Create menu
        menu = QMenu()
        
        # Add actions for each player
        actions = []
        for label, player in players:
            action = menu.addAction(f"👤 View Dossier for {label}: {player}")
            actions.append((action, player))
        
        # Show menu and get selected action
        action = menu.exec_(self.party_events_tree.mapToGlobal(position))
        
        # Handle action
        for act, player in actions:
            if action == act:
                self.open_player_dossier(player)
                break

    def setup_console_tree_context_menu(self):
        """Set up context menu for console tree"""
        if not hasattr(self, 'console_output'):
            return
            
        # Set custom context menu policy
        self.console_output.setContextMenuPolicy(Qt.CustomContextMenu)
        self.console_output.customContextMenuRequested.connect(self.show_console_context_menu)
    
    def show_console_context_menu(self, position):
        """Show context menu for console tree"""
        if not self.console_output:
            return
            
        # Get selected item
        item = self.console_output.itemAt(position)
        if not item:
            return
            
        # Look for event text in this item or its parent
        item_text = item.text(0)  # Console tree has only one column
        
        # If this is a child item (details), get the parent's text
        if item.parent():
            # This is a child item (details like weapon, ship)
            item_text = item.parent().text(0)
        
        # Try to extract player names
        # Clean text of emojis for parsing
        clean_text = ""
        for c in item_text:
            if ord(c) < 0x10000:  # Simple way to skip emojis
                clean_text += c
        
        # Try to extract a player name
        player_name = self.extract_player_name_from_event(clean_text.strip())
        if not player_name or player_name == "You":
            return
            
        # Create menu
        menu = QMenu()
        dossier_action = menu.addAction(f"👤 View Dossier for {player_name}")
        
        # Show menu and get selected action
        action = menu.exec_(self.console_output.mapToGlobal(position))
        
        # Handle action
        if action == dossier_action:
            self.open_player_dossier(player_name)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app_icon = QIcon()
        app_icon.addFile("icon.ico", QSize(16, 16))
        app_icon.addFile("icon.ico", QSize(24, 24))
        app_icon.addFile("icon.ico", QSize(32, 32))
        app_icon.addFile("icon.ico", QSize(48, 48))
        app_icon.addFile("icon.ico", QSize(64, 64))
        app.setWindowIcon(app_icon)
        window = MainWindow()
        window.show()       
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
        
