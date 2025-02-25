import datetime
import json
import logging
import os
import sys
import warnings

import sip
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QIcon, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSplitter,
    QSystemTrayIcon,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from game_watcher import GameLogWatcher
from logger import Logger
from toast_manager import ToastManager

warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    if hasattr(sip, "setapi"):
        sip.setapi("QVariant", 2)
        sip.setapi("QString", 2)
except Exception:
    pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("MainWindow initialization started")

        # Initialize state variables first
        self.is_watching = False

        # Initialize tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.setup_tray_icon()

        # Initialize attributes
        self.party_members = []
        self.session_history = {}
        self.watcher = None
        self.console_output = None
        self.player_name = None  # Initialize player_name attribute
        self.logger = None  # Initialize logger as None first
        self.path_input = None  # Initialize UI elements as None
        self.name_input = None
        self.toast_position_combo = None
        self.toast_size_combo = None
        self.toast_duration_combo = None
        self.self_events_check = None
        self.other_events_check = None
        self.npc_events_check = None
        self.suicide_events_check = None
        self.party_events_check = None
        self.party_members_list = None
        self.kill_list = None
        self.kill_details = None
        self.party_event_list = None
        self.party_event_details = None
        self.session_combo = None

        # Setup app directories
        self.app_dir = os.path.join(os.path.expanduser("~"), "Documents", "PINK", "VerseWatcher")
        self.settings_file = os.path.join(self.app_dir, "settings.json")
        self.logs_dir = os.path.join(self.app_dir, "logs")
        self.history_dir = os.path.join(self.app_dir, "history")

        print("Creating directories...")
        # Create directories if they don't exist
        os.makedirs(self.app_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)

        # Generate unique session ID for logs
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.logs_dir, f"log_{self.session_id}.txt")

        # Initialize file logger first
        try:
            self.logger = Logger(log_file=self.log_file)
            print("File logger initialized")
        except Exception as e:
            print(f"Error initializing file logger: {str(e)}")
            import traceback

            print(traceback.format_exc())

        self.load_window_geometry()
        print("Initializing UI...")
        self.init_ui()

        # Now that console_output exists, update logger with console widget
        if self.console_output is not None:
            try:
                self.logger = Logger(self.console_output, log_file=self.log_file)
                self.logger.log_info("Logger initialized with console widget")
            except Exception as e:
                print(f"Error updating logger with console widget: {str(e)}")
                import traceback

                print(traceback.format_exc())

        print("Setting window properties...")
        self.setWindowTitle("Verse Watcher - A Star Citizen Tool")
        self.setMinimumSize(900, 600)
        print("Initializing managers...")
        self.toast_manager = ToastManager()
        self.load_settings()

        # Update toast manager configuration
        if self.toast_position_combo and self.toast_size_combo and self.toast_duration_combo:
            self.toast_manager.update_config(
                position=self.toast_position_combo.currentText(),
                size=self.toast_size_combo.currentText(),
                duration=int(self.toast_duration_combo.currentText().split()[0]) * 1000,
            )

        print("MainWindow initialization completed")

    def load_window_geometry(self):
        """Load and apply window geometry before window is shown"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                    geometry = settings.get("window_geometry", {})
                    if geometry:
                        # Get the screen geometry
                        screen = QApplication.primaryScreen().geometry()

                        # Get saved values with defaults that keep window visible
                        x = geometry.get("x", (screen.width() - 1200) // 2)
                        y = geometry.get("y", (screen.height() - 800) // 2)
                        width = geometry.get("width", 1200)
                        height = geometry.get("height", 800)

                        # Ensure minimum size
                        width = max(width, 900)  # minimum width
                        height = max(height, 600)  # minimum height

                        # Ensure window is not larger than screen
                        width = min(width, screen.width())
                        height = min(height, screen.height())

                        # Ensure window is visible on screen
                        if x < 0:
                            x = 0
                        if y < 0:
                            y = 0
                        if x + width > screen.width():
                            x = screen.width() - width
                        if y + height > screen.height():
                            y = screen.height() - height

                        # Apply geometry
                        self.setGeometry(x, y, width, height)
                        print(f"Loaded window geometry: x={x}, y={y}, w={width}, h={height}")
                        return

            # If no geometry loaded, set default centered position
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 1200) // 2
            y = (screen.height() - 800) // 2
            self.setGeometry(x, y, 1200, 800)
            print(f"Set default centered geometry: x={x}, y={y}, w=1200, h=800")

        except Exception as e:
            print(f"Error loading window geometry: {str(e)}")
            # Set safe default geometry
            self.setGeometry(100, 100, 1200, 800)

    def init_ui(self):
        print("Starting UI initialization...")

        # Create main widget and layout
        print("Creating main widget...")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        print("Creating header...")
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(55)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 15, 15, 15)
        title_label = QLabel("VERSE WATCHER | alpha 1.0.1")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        layout.addWidget(header)

        # Control panel (always visible)
        print("Creating control panel...")
        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_panel.setFixedHeight(50)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(12, 3, 12, 3)
        status_label = QLabel("⛔️ STATUS: NOT MONITORING")
        status_label.setObjectName("statusLabel")
        self.status_label = status_label
        self.start_button = QPushButton("▶️️ START MONITORING")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.toggle_watching)
        self.start_button.setToolTip("Start/Stop monitoring game events")
        control_layout.addWidget(status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.start_button)
        layout.addWidget(control_panel)

        # Content area
        print("Creating content area...")
        content_area = QFrame()
        content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(5)
        # Tabs
        print("Creating tab widget...")
        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabWidget")

        # Set tab bar to expand tabs
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
        self.tabs.addTab(watcher_tab, "👁‍🗨 Console")
        self.tabs.addTab(history_tab, "🌌 Tracking")
        self.tabs.addTab(party_tab, "👀 Party Tracking")
        self.tabs.addTab(settings_tab, "⚙️ Settings")
        self.tabs.addTab(about_tab, "❓ About")
        self.tabs.tabBar().setExpanding(True)
        content_layout.addWidget(self.tabs)
        layout.addWidget(content_area)
        print("Applying theme...")
        self.apply_theme()
        print("UI initialization completed")

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #040B11,
                    stop:0.5 #0A1721,
                    stop:1 #0D1F2D
                );
            }
            #header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(4, 11, 17, 0.95),
                    stop:0.5 rgba(10, 23, 33, 0.95),
                    stop:1 rgba(13, 31, 45, 0.95)
                );
                border-bottom: 1px solid #00A6ED;
                border-image: none;
                padding: 2px;
            }        
            #titleLabel {
                color: #E7E5E6;
                font-size: 18px;
                font-weight: 800;
                letter-spacing: 8px;
            }
            #controlPanel {
                background: rgba(4, 11, 17, 0.98);
                border-bottom: 1px solid #00A6ED;
                border-image: none;
                padding: 2px 10px;
            }  
            #statusLabel {
                color: #E7E5E6;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
            }            
            #startButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                border: 1px solid #00A6ED;
                border-radius: 5px;
                color: white;
                padding: 8px 10px;
                font-size: 12px;
                font-weight: bold;
                min-width: 150px;
            }      
            #startButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
                border: 2px solid #40C4FF;
            }
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background: rgba(4, 11, 17, 0.95);
                border: none;
                border-bottom: 1px solid #003D5C;
                padding: 8px 20px;
                min-width: 120px;
                color: #90CAF9;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
                margin-right: 1px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FE9E0F,
                    stop:1 #4C3717
                );
                border-bottom: 3px solid #00A6ED;
                color: white;
            }      
            QTabBar::tab:hover:!selected {
                background: rgba(0, 166, 237, 0.15);
                border-bottom: 1px solid #0077AA;
                color: #40C4FF;
            }
            #contentSection {
                background-color: rgba(4, 11, 17, 0.98);
                border: 1px solid #00A6ED;
                border-radius: 2px;
                padding: 8px;
                margin: 4px 0;
            }          
            #contentSection:hover {
                border: 1px solid #40C4FF;
                background: rgba(4, 11, 17, 0.99);
            }
            QListWidget, QTreeWidget {
                background-color: rgba(4, 11, 17, 0.98);
                border: 1px solid #00A6ED;
                border-radius: 2px;
                color: #FFFFFF;
                font-size: 12px;
                padding: 4px;
            }
            QListWidget::item, QTreeWidget::item {
                padding: 4px 8px;
                border-radius: 2px;
                margin: 1px 0;
                border: 1px solid transparent;
            }
            QListWidget::item:hover, QTreeWidget::item:hover {
                background: rgba(0, 166, 237, 0.15);
                color: #40C4FF;
                border: 1px solid #0077AA;
            }       
            QListWidget::item:selected, QTreeWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                color: white;
                border: 1px solid #00A6ED;
            }    
            QScrollBar:vertical {
                background-color: rgba(4, 11, 17, 0.98);
                width: 8px;
                margin: 0;
                border-radius: 4px;
            }         
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                min-height: 20px;
                border-radius: 4px;
            }            
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
            }           
            QComboBox {
                background: rgba(4, 11, 17, 0.98);
                border: 1px solid #00A6ED;
                border-radius: 2px;
                color: #FFFFFF;
                padding: 4px 8px;
                min-width: 120px;
                font-size: 12px;
            }          
            QComboBox:hover {
                border: 1px solid #40C4FF;
                color: #40C4FF;
                background: rgba(4, 11, 17, 0.99);
            }         
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }         
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDYiIHN0cm9rZT0iIzJiN2FmZiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                width: 12px;
                height: 12px;
            }       
            QComboBox QAbstractItemView {
                background-color: rgba(4, 11, 17, 0.98);
                border: 1px solid #00A6ED;
                selection-background-color: #0077AA;
                selection-color: white;
            }          
            QLineEdit {
                background: rgba(4, 11, 17, 0.98);
                border: 1px solid #00A6ED;
                border-radius: 2px;
                color: #FFFFFF;
                padding: 6px 10px;
                font-size: 12px;
            }          
            QLineEdit:focus {
                border: 1px solid #40C4FF;
                background: rgba(4, 11, 17, 0.99);
            }        
            QLineEdit:hover {
                border: 1px solid #40C4FF;
            }           
            #consoleOutput {
                background-color: rgba(4, 11, 17, 0.98);
                border: 1px solid #00A6ED;
                border-radius: 2px;
                color: #90CAF9;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 8px;
                line-height: 1.2;
            }           
            #consoleOutput:focus {
                border: 1px solid #40C4FF;
            }          
            #sectionHeader {
                color: #00A6ED;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
                margin-bottom: 4px;
            }          
            QSplitter::handle {
                background: #00A6ED;
                width: 1px;
                margin: 1px;
            }         
            QSplitter::handle:hover {
                background: #40C4FF;
            }        
            QHeaderView::section {
                background: rgba(4, 11, 17, 0.98);
                color: #00A6ED;
                padding: 4px;
                border: 1px solid #00A6ED;
                font-size: 12px;
                font-weight: bold;
            }           
            QHeaderView::section:hover {
                background: rgba(0, 166, 237, 0.15);
                color: #40C4FF;
            }      
            QGroupBox {
                font-size: 12px;
                padding-top: 16px;
                margin-top: 4px;
            }       
            QGroupBox::title {
                color: #00A6ED;
                padding: 0 3px;
            }            
            #actionButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                border: 1px solid #00A6ED;
                border-radius: 2px;
                color: white;
                padding: 4px 15px;
                font-size: 12px;
                font-weight: bold;
                min-width: 120px;
            }            
            #actionButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0077AA,
                    stop:1 #00A6ED
                );
                border: 1px solid #40C4FF;
            }            
            #actionButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00A6ED,
                    stop:1 #40C4FF
                );
                border: 1px solid #80D8FF;
            }
        """)

    def toggle_watching(self):
        """Handle starting/stopping the game log watcher"""
        try:
            # Check if required UI elements exist
            if not all([self.path_input, self.name_input]):
                print("Error: UI elements not initialized")
                return
            # Ensure logger exists
            if not self.logger:
                print("Creating fallback logger...")
                self.logger = Logger(log_file=self.log_file)

            if self.watcher is None:
                # Starting watcher
                try:
                    # Validate inputs
                    game_path = self.path_input.text().strip()
                    player_name = self.name_input.text().strip()

                    if not game_path or not player_name:
                        self.logger.log_error("Please set both Game Path and Player Name")
                        return

                    if not os.path.exists(game_path):
                        self.logger.log_error(f"Game directory does not exist: {game_path}")
                        return

                    game_log = os.path.join(game_path, "Game.log")
                    if not os.path.exists(game_log):
                        self.logger.log_error(f"Game.log not found in directory: {game_path}")
                        return

                    # Set player name and create watcher
                    self.player_name = player_name
                    self.watcher = GameLogWatcher(
                        game_path=game_path,
                        player_name=player_name,
                        logger=self.logger,
                        toast_manager=self.toast_manager,
                        main_window=self,
                    )

                    # Start watching
                    if self.watcher.start():
                        self.start_button.setText("🛑 STOP MONITORING")
                        self.start_button.setStyleSheet("""
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #c62828,
                                stop:1 #ff5252
                            );
                            color: white;
                            border: none;
                        """)
                        self.status_label.setText("✔️ STATUS: MONITORING")
                        self.status_label.setStyleSheet("color: #4caf50;")
                        self.logger.log_info(f"Started watching Game.log at: {game_log}")
                        # Update tray icon state
                        self.is_watching = True
                        self.watcher_action.setText("Stop Watcher")
                        self.update_tray_icon()
                    else:
                        self.watcher = None
                        self.player_name = None
                        self.logger.log_error("Failed to start watching Game.log")
                        # Update tray icon state
                        self.is_watching = False
                        self.watcher_action.setText("Start Watcher")
                        self.update_tray_icon()

                except Exception as e:
                    error_msg = f"Error starting watcher: {str(e)}"
                    print(error_msg)
                    if self.logger:
                        self.logger.log_error(error_msg)
                        import traceback

                        self.logger.log_error(traceback.format_exc())
                    self.watcher = None
                    self.player_name = None
                    # Update tray icon state
                    self.is_watching = False
                    self.watcher_action.setText("Start Watcher")
                    self.update_tray_icon()
            else:
                # Stopping watcher
                try:
                    if self.watcher:
                        self.watcher.stop()
                    self.watcher = None
                    self.player_name = None
                    self.start_button.setText("▶️️ START MONITORING")
                    self.start_button.setStyleSheet("")
                    self.status_label.setText("⛔️ STATUS: NOT MONITORING")
                    self.status_label.setStyleSheet("")
                    if self.logger:
                        self.logger.log_info("Stopped watching Game.log")
                    # Update tray icon state
                    self.is_watching = False
                    self.watcher_action.setText("Start Watcher")
                    self.update_tray_icon()

                except Exception as e:
                    error_msg = f"Error stopping watcher: {str(e)}"
                    print(error_msg)
                    if self.logger:
                        self.logger.log_error(error_msg)
                        import traceback

                        self.logger.log_error(traceback.format_exc())
                    self.watcher = None
                    self.player_name = None
                    # Update tray icon state
                    self.is_watching = False
                    self.watcher_action.setText("Start Watcher")
                    self.update_tray_icon()

        except KeyboardInterrupt:
            # Handle keyboard interrupt gracefully
            if self.watcher:
                self.watcher.stop()
            self.watcher = None
            self.player_name = None
            self.start_button.setText("▶️ START MONITORING")
            self.start_button.setStyleSheet("")
            self.status_label.setText("⛔️ STATUS: NOT MONITORING")
            self.status_label.setStyleSheet("")
            if self.logger:
                self.logger.log_info("Monitoring stopped by user")
            # Update tray icon state
            self.is_watching = False
            self.watcher_action.setText("Start Watcher")
            self.update_tray_icon()

        except Exception as e:
            error_msg = f"Critical error in toggle_watching: {str(e)}"
            print(error_msg)
            if hasattr(self, "logger") and self.logger:
                self.logger.log_error(error_msg)
                import traceback

                self.logger.log_error(traceback.format_exc())
            if hasattr(self, "toast_manager"):
                self.toast_manager.show_error_toast(f"Error: {str(e)}")
            self.watcher = None
            self.player_name = None
            # Update tray icon state
            self.is_watching = False
            self.watcher_action.setText("Start Watcher")
            self.update_tray_icon()

    def browse_game_path(self):
        """Handle browsing for game directory"""
        try:
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)

            if dialog.exec_():
                path = dialog.selectedFiles()[0]
                if path:
                    self.path_input.setText(path)
                    self.save_settings()
        except Exception as e:
            self.logger.log_error(f"Error in browse_game_path: {str(e)}")
            import traceback

            self.logger.log_error(traceback.format_exc())
            self.toast_manager.show_error_toast(f"Error: {str(e)}")

    def on_path_input_change(self, text):
        """Handle path input changes"""
        try:
            if text.strip():
                self.path_input.setPlaceholderText("")  # Clear placeholder when we have text
            else:
                self.path_input.setPlaceholderText("Select directory containing Game.log")
            self.save_settings()
        except Exception as e:
            self.logger.log_error(f"Error in on_path_input_change: {str(e)}")
            import traceback

            self.logger.log_error(traceback.format_exc())
            self.toast_manager.show_error_toast(f"Error: {str(e)}")

    def on_name_input_change(self, text):
        """Handle name input changes"""
        try:
            if text.strip():
                self.name_input.setPlaceholderText("")  # Clear placeholder when we have text
            else:
                self.name_input.setPlaceholderText("Your in-game playername (case sensitive!)")
            self.save_settings()
        except Exception as e:
            self.logger.log_error(f"Error in on_name_input_change: {str(e)}")
            import traceback

            self.logger.log_error(traceback.format_exc())
            self.toast_manager.show_error_toast(f"Error: {str(e)}")

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            # Update window geometry in settings before saving
            geometry = self.geometry()
            self.settings = {
                "game_path": self.path_input.text(),
                "player_name": self.name_input.text(),
                "window_geometry": {
                    "x": geometry.x(),
                    "y": geometry.y(),
                    "width": geometry.width(),
                    "height": geometry.height(),
                },
                "toast_config": {
                    "position": self.toast_position_combo.currentText(),
                    "size": self.toast_size_combo.currentText(),
                    "duration": int(self.toast_duration_combo.currentText().split()[0]) * 1000,
                },
                "event_filters": {
                    "self_events": self.self_events_check.isChecked(),
                    "other_events": self.other_events_check.isChecked(),
                    "npc_events": self.npc_events_check.isChecked(),
                    "suicide_events": self.suicide_events_check.isChecked(),
                    "party_events": self.party_events_check.isChecked(),
                },
                "party_members": self.party_members,
                "session_history": self.session_history,
            }

            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)

        except Exception as e:
            self.logger.log_error(f"Error saving settings: {str(e)}")
            import traceback

            self.logger.log_error(traceback.format_exc())
            self.toast_manager.show_error_toast(f"Error: {str(e)}")

    def load_settings(self):
        """Load settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)

                # Load and set game path
                game_path = settings.get("game_path", "")
                if game_path:
                    self.path_input.setText(game_path)

                # Load and set player name
                player_name = settings.get("player_name", "")
                if player_name:
                    self.name_input.setText(player_name)
                    self.player_name = player_name

                # Load and apply window geometry with screen bounds checking
                geometry = settings.get("window_geometry", {})
                if geometry:
                    # Get the screen geometry
                    screen = QApplication.primaryScreen().geometry()

                    # Get saved values with defaults that keep window visible
                    x = geometry.get("x", (screen.width() - 1200) // 2)
                    y = geometry.get("y", (screen.height() - 800) // 2)
                    width = geometry.get("width", 1200)
                    height = geometry.get("height", 800)

                    # Ensure minimum size
                    width = max(width, self.minimumWidth())
                    height = max(height, self.minimumHeight())

                    # Ensure window is not larger than screen
                    width = min(width, screen.width())
                    height = min(height, screen.height())

                    # Ensure window is visible on screen
                    if x < 0:
                        x = 0
                    if y < 0:
                        y = 0
                    if x + width > screen.width():
                        x = screen.width() - width
                    if y + height > screen.height():
                        y = screen.height() - height

                    # Apply geometry
                    self.setGeometry(x, y, width, height)
                    print(f"Restored window geometry: x={x}, y={y}, w={width}, h={height}")

                # Load toast configuration
                toast_config = settings.get("toast_config", {})
                if toast_config:
                    position = toast_config.get("position", "Bottom Right")
                    size = toast_config.get("size", "Medium")
                    duration_ms = toast_config.get("duration", 5000)

                    # Update UI
                    self.toast_position_combo.setCurrentText(position)
                    self.toast_size_combo.setCurrentText(size)
                    duration_sec = f"{duration_ms // 1000} seconds"
                    self.toast_duration_combo.setCurrentText(duration_sec)

                    # Update toast manager configuration
                    self.toast_manager.update_config(
                        position=position, size=size, duration=duration_ms
                    )

                # Load event filters
                event_filters = settings.get("event_filters", {})
                if event_filters:
                    self.self_events_check.setChecked(event_filters.get("self_events", True))
                    self.other_events_check.setChecked(event_filters.get("other_events", False))
                    self.npc_events_check.setChecked(event_filters.get("npc_events", False))
                    self.suicide_events_check.setChecked(event_filters.get("suicide_events", True))
                    self.party_events_check.setChecked(event_filters.get("party_events", True))

                # Load party members and update UI list
                self.party_members = settings.get("party_members", [])
                self.party_members_list.clear()
                for member in self.party_members:
                    self.party_members_list.addItem(member)

                # Load session histories from files
                self.load_session_histories()

        except Exception as e:
            self.logger.log_error(f"Error loading settings: {str(e)}")
            import traceback

            self.logger.log_error(traceback.format_exc())
            self.toast_manager.show_error_toast(f"Error: {str(e)}")

    def closeEvent(self, event):
        """Save settings when closing the application"""
        try:
            # Hide the tray icon before closing
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()

            # Get current window geometry BEFORE closing
            geometry = self.geometry()

            # Save all settings including current window geometry
            settings_data = {
                "game_path": self.path_input.text(),
                "player_name": self.name_input.text(),
                "window_geometry": {
                    "x": geometry.x(),
                    "y": geometry.y(),
                    "width": geometry.width(),
                    "height": geometry.height(),
                },
                "toast_config": {
                    "position": self.toast_position_combo.currentText(),
                    "size": self.toast_size_combo.currentText(),
                    "duration": int(self.toast_duration_combo.currentText().split()[0]) * 1000,
                },
                "event_filters": {
                    "self_events": self.self_events_check.isChecked(),
                    "other_events": self.other_events_check.isChecked(),
                    "npc_events": self.npc_events_check.isChecked(),
                    "suicide_events": self.suicide_events_check.isChecked(),
                    "party_events": self.party_events_check.isChecked(),
                },
                "party_members": self.party_members,
                "session_history": self.session_history,
            }

            # Save settings to file BEFORE accepting the close event
            with open(self.settings_file, "w") as f:
                json.dump(settings_data, f, indent=4)

            print(
                f"Saved window geometry: x={geometry.x()}, y={geometry.y()}, w={geometry.width()}, h={geometry.height()}"
            )

            # Only accept the close event after successfully saving
            event.accept()

        except Exception as e:
            print(f"Error saving settings in closeEvent: {str(e)}")
            import traceback

            traceback.print_exc()
            event.accept()  # Still close even if save fails

    def add_kill_event(self, event_data, update_session=True):
        """Add a kill event to the history list and session history"""
        try:
            # Get current player name from input if not set
            if not self.player_name:
                self.player_name = self.name_input.text()

            # Check event filters
            vname = event_data.get("vname", "")
            kname = event_data.get("kname", "")

            # Determine event type
            is_suicide = vname == kname
            is_npc = "NPC" in vname or "NPC" in kname
            is_self_event = vname == self.player_name or kname == self.player_name
            is_party_event = vname in self.party_members or kname in self.party_members
            is_other_event = not (is_self_event or is_party_event or is_suicide or is_npc)

            # Check if event should be processed based on filters
            should_process = (
                (is_self_event and self.self_events_check.isChecked())
                or (is_other_event and self.other_events_check.isChecked())
                or (is_npc and self.npc_events_check.isChecked())
                or (is_suicide and self.suicide_events_check.isChecked())
                or (is_party_event and self.party_events_check.isChecked())
            )

            if not should_process:
                return

            # Format list item text
            timestamp = event_data.get("timestamp", "")

            if is_suicide:
                item_text = f"🚫 {timestamp} - {vname} committed suicide"
                event_data["type"] = "suicide"
            elif is_npc:
                if "NPC" in vname:
                    item_text = f"👾 {timestamp} - NPC killed by {kname}"
                else:
                    item_text = f"👾 {timestamp} - {vname} killed by NPC"
                event_data["type"] = "npc"
            elif vname == self.player_name:
                item_text = f"💀 {timestamp} - Killed by {kname}"
                event_data["type"] = "death"
            elif kname == self.player_name:
                item_text = f"😈 {timestamp} - Killed {vname}"
                event_data["type"] = "kill"
            else:
                item_text = f"☠️ {timestamp} - {vname} killed by {kname}"
                event_data["type"] = "info"

            # Add to appropriate list based on event type
            if is_party_event:
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, event_data)
                self.party_event_list.insertItem(0, item)
                self.party_event_list.setCurrentItem(item)

                # Update party event details
                self.on_party_event_selected(item, None)

            # Always add to main kill list
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, event_data)
            self.kill_list.insertItem(0, item)
            self.kill_list.setCurrentItem(item)

            # Update session history
            if update_session:
                current_date = datetime.datetime.now().strftime("%Y%m%d")
                current_hour = datetime.datetime.now().strftime("%H")
                session_key = f"{current_date} {current_hour}:00"

                if session_key not in self.session_history:
                    self.session_history[session_key] = []
                    self.session_combo.addItem(session_key)
                    self.session_combo.setCurrentText(session_key)

                self.session_history[session_key].append(event_data)
                # Save session to file
                self.save_session_history(session_key, [event_data])

        except Exception as e:
            self.logger.log_error(f"Error adding kill event to history: {str(e)}")

    def on_kill_selected(self, current, previous):
        """Update kill details when a kill is selected"""
        try:
            self.kill_details.clear()

            if not current:
                return

            # Get stored event data
            event_data = current.data(Qt.UserRole)
            if not event_data:
                return

            # Create tree items for each field
            fields = [
                ("Timestamp", "timestamp", "🕒"),
                ("Victim", "vname", "💀"),
                ("Killer", "kname", "😈"),
                ("Weapon", "kwep", "🔫"),
                ("Ship", "vship", "🚀"),
                ("Damage Type", "dtype", "💥"),
            ]

            for label, key, emoji in fields:
                if key in event_data:
                    item = QTreeWidgetItem([f"{emoji} {label}", str(event_data[key])])
                    self.kill_details.addTopLevelItem(item)

            self.kill_details.expandAll()

        except Exception as e:
            self.logger.log_error(f"Error updating kill details: {str(e)}")

    def create_settings_tab(self):
        """Create the settings tab with scrollable content"""
        settings_tab = QWidget()
        settings_tab.setStyleSheet("""
            QWidget {
                background-color: #0a1017;
            }
            QComboBox {
                background-color: #0d1b2a;
                border: 1px solid #1e4d8f;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 5px 10px;
                min-width: 200px;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid #2979ff;
                background-color: #162b45;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDEwTDEyIDYiIHN0cm9rZT0iIzJiN2FmZiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                width: 16px;
                height: 16px;
            }
            QComboBox:on {
                border: 1px solid #2979ff;
                background-color: #162b45;
            }
            QComboBox QAbstractItemView {
                background-color: #0d1b2a;
                border: 1px solid #1e4d8f;
                selection-background-color: #2979ff;
                selection-color: white;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 10px;
                padding: 2px;
                font-size: 12px;
            }
            QCheckBox:hover {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #0d1b2a;
                border: 2px solid #1e4d8f;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #2979ff;
                background-color: #162b45;
            }
            QCheckBox::indicator:checked {
                background-color: #2979ff;
                border: 2px solid #2979ff;
                border-radius: 4px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgOEw3IDEyTDEzIDQiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #448aff;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            #settingsSection {
                background-color: #0d1b2a;
                border: 1px solid #1e4d8f;
                border-radius: 6px;
                padding: 20px;
                margin: 5px 0;
            }
            #settingsSection:hover {
                border: 1px solid #2979ff;
                background-color: #162b45;
            }
            #settingsSection QLabel {
                background-color: transparent;
            }
            #sectionHeader {
                color: #4a9eff;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
                margin-bottom: 10px;
                background-color: transparent;
            }
            #sectionLabel {
                color: #90caf9;
                font-size: 12px;
                margin: 5px 0;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #0d1b2a;
                border: 1px solid #1e4d8f;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #2979ff;
                background-color: #162b45;
            }
            QLineEdit:hover {
                border: 1px solid #2979ff;
            }
        """)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Create container widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        scroll_layout.setContentsMargins(20, 20, 20, 20)

        # Game Installation section
        game_container = self.create_game_installation_section()
        game_container.setMinimumHeight(120)
        scroll_layout.addWidget(game_container)

        # Player Identity section
        name_container = self.create_player_identity_section()
        name_container.setMinimumHeight(120)
        scroll_layout.addWidget(name_container)

        # Toast Configuration section
        toast_container = self.create_toast_configuration_section()
        toast_container.setMinimumHeight(200)
        scroll_layout.addWidget(toast_container)

        # Event Filters section
        event_filters_container = self.create_event_filters_section()
        event_filters_container.setMinimumHeight(200)
        scroll_layout.addWidget(event_filters_container)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)

        # Main layout for settings tab
        main_layout = QVBoxLayout(settings_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        return settings_tab

    def create_game_installation_section(self):
        container = QFrame()
        container.setObjectName("settingsSection")
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        header = QLabel("GAME INSTALLATION")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        path_label = QLabel("Game.log location:")
        path_label.setObjectName("sectionLabel")
        layout.addWidget(path_label)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setObjectName("pathInput")
        self.path_input.setPlaceholderText("Select directory containing Game.log")
        self.path_input.textChanged.connect(self.on_path_input_change)
        self.path_input.setMinimumHeight(30)

        browse_button = QPushButton("⋯")
        browse_button.setObjectName("browseButton")
        browse_button.setFixedWidth(40)
        browse_button.setMinimumHeight(30)
        browse_button.clicked.connect(self.browse_game_path)

        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)

        layout.addLayout(path_layout)

        return container

    def create_player_identity_section(self):
        container = QFrame()
        container.setObjectName("settingsSection")
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        header = QLabel("PLAYER IDENTITY")
        header.setObjectName("sectionHeader")

        name_label = QLabel("In-game player name:")
        name_label.setObjectName("sectionLabel")

        self.name_input = QLineEdit()
        self.name_input.setObjectName("nameInput")
        self.name_input.setPlaceholderText("Your in-game playername (case sensitive!)")
        self.name_input.textChanged.connect(self.on_name_input_change)
        self.name_input.setMinimumHeight(30)

        layout.addWidget(header)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        return container

    def create_toast_configuration_section(self):
        container = QFrame()
        container.setObjectName("settingsSection")
        layout = QGridLayout(container)
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(15)

        header = QLabel("TOAST NOTIFICATIONS")
        header.setObjectName("sectionHeader")
        layout.addWidget(header, 0, 0, 1, 2)

        # Position selection
        position_label = QLabel("Position:")
        position_label.setObjectName("sectionLabel")
        self.toast_position_combo = QComboBox()
        self.toast_position_combo.addItems(
            [
                "Top Left",
                "Top Right",
                "Bottom Left",
                "Bottom Right",
                "Left Middle",
                "Right Middle",
            ]
        )
        self.toast_position_combo.setCurrentText("Bottom Right")
        self.toast_position_combo.currentTextChanged.connect(self.on_toast_config_changed)
        self.toast_position_combo.setMinimumHeight(30)

        # Size selection
        size_label = QLabel("Size:")
        size_label.setObjectName("sectionLabel")
        self.toast_size_combo = QComboBox()
        self.toast_size_combo.addItems(["Small", "Medium", "Large"])
        self.toast_size_combo.setCurrentText("Medium")
        self.toast_size_combo.currentTextChanged.connect(self.on_toast_config_changed)
        self.toast_size_combo.setMinimumHeight(30)

        # Duration selection
        duration_label = QLabel("Duration:")
        duration_label.setObjectName("sectionLabel")
        self.toast_duration_combo = QComboBox()
        self.toast_duration_combo.addItems(
            [
                "3 seconds",
                "5 seconds",
                "7 seconds",
                "10 seconds",
                "15 seconds",
                "20 seconds",
            ]
        )
        self.toast_duration_combo.setCurrentText("5 seconds")
        self.toast_duration_combo.currentTextChanged.connect(self.on_toast_config_changed)
        self.toast_duration_combo.setMinimumHeight(30)

        # Add to grid layout with proper spacing
        layout.addWidget(position_label, 1, 0)
        layout.addWidget(self.toast_position_combo, 1, 1)
        layout.addWidget(size_label, 2, 0)
        layout.addWidget(self.toast_size_combo, 2, 1)
        layout.addWidget(duration_label, 3, 0)
        layout.addWidget(self.toast_duration_combo, 3, 1)

        # Set column stretch
        layout.setColumnStretch(1, 1)

        return container

    def create_event_filters_section(self):
        container = QFrame()
        container.setObjectName("settingsSection")
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        header = QLabel("EVENT FILTERS")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        description = QLabel("Select which events to display in the history:")
        description.setObjectName("sectionLabel")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Create grid for checkboxes with better spacing
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(20)

        # Create checkboxes for event types with improved labels
        self.self_events_check = QCheckBox("👤 Events involving you")
        self.other_events_check = QCheckBox("👥 Events between others")
        self.npc_events_check = QCheckBox("🤖 NPC events")
        self.suicide_events_check = QCheckBox("💥 Suicide events")
        self.party_events_check = QCheckBox("👥 Party member events")

        # Set initial states
        self.self_events_check.setChecked(True)
        self.party_events_check.setChecked(True)

        # Add to grid layout with better organization
        checkboxes = [
            (self.self_events_check, 0, 0),
            (self.other_events_check, 0, 1),
            (self.npc_events_check, 1, 0),
            (self.suicide_events_check, 1, 1),
            (self.party_events_check, 2, 0),
        ]

        for checkbox, row, col in checkboxes:
            checkbox.stateChanged.connect(self.on_event_filter_changed)
            grid.addWidget(checkbox, row, col)

        layout.addLayout(grid)
        return container

    def on_toast_config_changed(self):
        """Handle changes to toast configuration"""
        try:
            self.save_settings()
            # Update toast manager with new settings
            self.toast_manager.update_config(
                position=self.toast_position_combo.currentText(),
                size=self.toast_size_combo.currentText(),
                duration=int(self.toast_duration_combo.currentText().split()[0]) * 1000,
            )
        except Exception as e:
            self.logger.log_error(f"Error updating toast config: {str(e)}")

    def on_event_filter_changed(self):
        """Handle changes to event filters"""
        try:
            self.save_settings()
        except Exception as e:
            self.logger.log_error(f"Error updating event filters: {str(e)}")

    def show_add_member_dialog(self):
        """Show dialog to add party member"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Add Party Member")
            dialog.setModal(True)
            dialog.setMinimumWidth(300)
            dialog.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #040B11,
                        stop:0.5 #0A1721,
                        stop:1 #0D1F2D
                    );
                    border: 1px solid #00A6ED;
                    border-radius: 4px;
                }
                QLabel {
                    color: #00A6ED;
                    font-size: 12px;
                    font-weight: bold;
                    background: transparent;
                }
                QLineEdit {
                    background: rgba(4, 11, 17, 0.98);
                    border: 1px solid #00A6ED;
                    border-radius: 2px;
                    color: #FFFFFF;
                    padding: 8px 12px;
                    font-size: 12px;
                    margin: 4px 0;
                }
                QLineEdit:focus {
                    border: 1px solid #40C4FF;
                    background: rgba(13, 27, 42, 0.99);
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #003D5C,
                        stop:1 #0077AA
                    );
                    border: 1px solid #00A6ED;
                    border-radius: 2px;
                    color: white;
                    padding: 8px 15px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #0077AA,
                        stop:1 #00A6ED
                    );
                    border: 1px solid #40C4FF;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00A6ED,
                        stop:1 #40C4FF
                    );
                    border: 1px solid #80D8FF;
                }
                #cancelButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1A1A1A,
                        stop:1 #333333
                    );
                    border: 1px solid #666666;
                }
                #cancelButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #333333,
                        stop:1 #4D4D4D
                    );
                    border: 1px solid #808080;
                }
            """)

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(10)

            name_label = QLabel("Player Name (case sensitive):")
            layout.addWidget(name_label)

            name_input = QLineEdit()
            name_input.setPlaceholderText("Enter player name...")
            layout.addWidget(name_input)

            button_layout = QHBoxLayout()
            button_layout.setSpacing(10)

            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda: self.add_party_member(name_input.text(), dialog))

            cancel_button = QPushButton("Cancel")
            cancel_button.setObjectName("cancelButton")
            cancel_button.clicked.connect(dialog.reject)

            button_layout.addWidget(add_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)

            dialog.exec_()

        except Exception as e:
            self.logger.log_error(f"Error showing add member dialog: {str(e)}")

    def add_party_member(self, name, dialog):
        """Add a new party member"""
        try:
            if not name:
                self.toast_manager.show_error_toast("Please enter a player name")
                return

            if name in self.party_members:
                self.toast_manager.show_error_toast("Player already in party")
                return

            self.party_members.append(name)
            self.party_members_list.addItem(name)  # Update UI list
            self.save_settings()
            self.toast_manager.show_info_toast(f"Added {name} to party")
            dialog.accept()

        except Exception as e:
            self.logger.log_error(f"Error adding party member: {str(e)}")

    def remove_party_member(self):
        """Remove selected party member"""
        try:
            current_item = self.party_members_list.currentItem()
            if not current_item:
                self.toast_manager.show_error_toast("Please select a party member to remove")
                return

            name = current_item.text()
            self.party_members.remove(name)
            self.party_members_list.takeItem(self.party_members_list.row(current_item))
            self.save_settings()
            self.toast_manager.show_info_toast(f"Removed {name} from party")

        except Exception as e:
            self.logger.log_error(f"Error removing party member: {str(e)}")

    def show_clear_history_dialog(self):
        """Show confirmation dialog for clearing history"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Clear History")
            dialog.setModal(True)
            dialog.setMinimumWidth(400)
            dialog.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #040B11,
                        stop:0.5 #0A1721,
                        stop:1 #0D1F2D
                    );
                    border: 1px solid #00A6ED;
                    border-radius: 4px;
                }
                QLabel {
                    color: #FFFFFF;
                    font-size: 13px;
                    padding: 10px;
                    background: transparent;
                }
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #003D5C,
                        stop:1 #0077AA
                    );
                    border: 1px solid #00A6ED;
                    border-radius: 2px;
                    color: white;
                    padding: 8px 15px;
                    font-size: 12px;
                    font-weight: bold;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #0077AA,
                        stop:1 #00A6ED
                    );
                    border: 1px solid #40C4FF;
                }
                #warningLabel {
                    color: #FF4444;
                    font-weight: bold;
                }
            """)

            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            # Warning icon and message
            warning_label = QLabel("⚠️ Warning")
            warning_label.setObjectName("warningLabel")
            warning_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(warning_label)

            message = QLabel(
                "You are about to permanently delete all stored history data.\n\n"
                "This includes:\n"
                "• All session records\n"
                "• All event logs\n"
                "• All tracking statistics\n\n"
                "This action cannot be undone. Are you sure you want to proceed?"
            )
            message.setWordWrap(True)
            message.setAlignment(Qt.AlignCenter)
            layout.addWidget(message)

            button_layout = QHBoxLayout()
            button_layout.setSpacing(10)

            clear_button = QPushButton("Clear History")
            clear_button.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c62828,
                    stop:1 #ff5252
                );
                border: 1px solid #ff5252;
            """)
            clear_button.clicked.connect(lambda: self.clear_history(dialog))

            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(dialog.reject)

            button_layout.addWidget(cancel_button)
            button_layout.addWidget(clear_button)
            layout.addLayout(button_layout)

            dialog.exec_()

        except Exception as e:
            self.logger.log_error(f"Error showing clear history dialog: {str(e)}")

    def clear_history(self, dialog):
        """Clear all session history"""
        try:
            # Clear session history dictionary
            self.session_history = {}

            # Delete all history files
            history_files = [
                f
                for f in os.listdir(self.history_dir)
                if f.startswith("vw_history_") and f.endswith(".txt")
            ]
            for filename in history_files:
                try:
                    file_path = os.path.join(self.history_dir, filename)
                    os.remove(file_path)
                    self.logger.log_info(f"Deleted history file: {filename}")
                except Exception as e:
                    self.logger.log_error(f"Error deleting history file {filename}: {str(e)}")

            # Clear all event lists and details
            self.kill_list.clear()
            self.kill_details.clear()
            self.party_event_list.clear()
            self.party_event_details.clear()
            self.session_combo.clear()

            self.toast_manager.show_success_toast("History cleared successfully")
            dialog.accept()

        except Exception as e:
            self.logger.log_error(f"Error clearing history: {str(e)}")

    def on_session_changed(self, session_text):
        """Load events from selected session"""
        try:
            if not session_text:
                return

            # Clear all event lists and details
            self.kill_list.clear()
            self.kill_details.clear()
            self.party_event_list.clear()
            self.party_event_details.clear()

            session_data = self.session_history.get(session_text, [])
            for event in session_data:
                self.add_kill_event(event, update_session=False)

        except Exception as e:
            self.logger.log_error(f"Error changing session: {str(e)}")

    def on_party_event_selected(self, current, previous):
        """Update party event details when an event is selected"""
        try:
            self.party_event_details.clear()

            if not current:
                return

            # Get stored event data
            event_data = current.data(Qt.UserRole)
            if not event_data:
                return

            # Create tree items for each field
            fields = [
                ("Timestamp", "timestamp", "🕒"),
                ("Victim", "vname", "💀"),
                ("Killer", "kname", "😈"),
                ("Weapon", "kwep", "🔫"),
                ("Ship", "vship", "🚀"),
                ("Damage Type", "dtype", "💥"),
            ]

            for label, key, emoji in fields:
                if key in event_data:
                    item = QTreeWidgetItem([f"{emoji} {label}", str(event_data[key])])
                    self.party_event_details.addTopLevelItem(item)

            self.party_event_details.expandAll()

            # Add double-click and context menu functionality
            self.party_event_details.itemDoubleClicked.connect(self.on_party_details_double_clicked)
            self.party_event_details.setContextMenuPolicy(Qt.CustomContextMenu)
            self.party_event_details.customContextMenuRequested.connect(
                self.show_party_details_context_menu
            )

        except Exception as e:
            self.logger.log_error(f"Error updating party event details: {str(e)}")

    def on_party_details_double_clicked(self, item, column):
        """Handle double-click events on party event details"""
        try:
            if not item or column != 1:  # Only handle clicks on the value column
                return

            field = item.text(0)
            value = item.text(1)

            if field in ["💀 Victim", "😈 Killer"]:
                if "NPC" in value:
                    self.toast_manager.show_info_toast("No dossier available for NPC")
                else:
                    self.open_dossier(value)

            elif field == "🚀 Ship":
                ship_name = value
                url = f"https://www.spviewer.eu/performance?ship={ship_name}"
                QDesktopServices.openUrl(QUrl(url))

        except Exception as e:
            self.logger.log_error(f"Error handling party details double-click: {str(e)}")

    def show_party_details_context_menu(self, position):
        """Show context menu for party event details"""
        try:
            item = self.party_event_details.itemAt(position)
            if not item:
                return

            field = item.text(0)
            value = item.text(1)

            if field in ["💀 Victim", "😈 Killer"]:
                menu = QMenu()

                if "NPC" in value:
                    action = menu.addAction("No dossier available")
                    action.setEnabled(False)
                else:
                    action = menu.addAction("View Dossier")
                    action.triggered.connect(lambda: self.open_dossier(value))

                menu.exec_(self.party_event_details.viewport().mapToGlobal(position))

        except Exception as e:
            self.logger.log_error(f"Error showing party details context menu: {str(e)}")

    def create_about_tab(self):
        """Create the about tab with app information"""
        print("Creating about tab...")
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create a scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(30)

        # Header section with logos
        header_widget = QFrame()
        header_widget.setObjectName("aboutHeader")
        header_widget.setStyleSheet("""
            #aboutHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(4, 11, 17, 0.8),
                    stop:0.5 rgba(10, 23, 33, 0.8),
                    stop:1 rgba(13, 31, 45, 0.8)
                );
                border: 1px solid #00A6ED;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(30)

        # App logo
        logo_frame = QFrame()
        logo_frame.setObjectName("logoFrame")
        logo_frame.setStyleSheet("""
            #logoFrame {
                background: rgba(0, 166, 237, 0.1);
                border: 2px solid #00A6ED;
                border-radius: 10px;
            }
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_size = 128

        logo_label = QLabel()
        try:
            possible_icon_paths = [
                os.path.join(os.path.dirname(__file__), "..", "vw.ico"),
                os.path.join(os.path.dirname(sys.executable), "vw.ico"),
                "vw.ico",
            ]

            icon_found = False
            for icon_path in possible_icon_paths:
                if os.path.exists(icon_path):
                    logo = QIcon(icon_path)
                    logo_label.setPixmap(logo.pixmap(logo_size, logo_size))
                    icon_found = True
                    break

            if not icon_found:
                logo_label.setText("VW")
                logo_label.setStyleSheet("""
                    color: #00A6ED;
                    font-size: 48px;
                    font-weight: bold;
                """)
        except Exception as e:
            print(f"Error setting logo: {str(e)}")
            logo_label.setText("VW")
            logo_label.setStyleSheet("""
                color: #00A6ED;
                font-size: 48px;
                font-weight: bold;
            """)

        logo_label.setFixedSize(logo_size, logo_size)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        header_layout.addWidget(logo_frame)

        # Developer logo/profile
        dev_frame = QFrame()
        dev_frame.setObjectName("devFrame")
        dev_frame.setStyleSheet("""
            #devFrame {
                background: rgba(0, 166, 237, 0.1);
                border: 2px solid #00A6ED;
                border-radius: 10px;
            }
        """)
        dev_layout = QVBoxLayout(dev_frame)

        dev_label = QLabel()
        try:
            dev_pic_path = os.path.join(os.path.dirname(__file__), "..", "pg.png")
            if os.path.exists(dev_pic_path):
                dev_label.setPixmap(QIcon(dev_pic_path).pixmap(logo_size, logo_size))
            else:
                dev_label.setText("PINK")
                dev_label.setStyleSheet("""
                    color: #00A6ED;
                    font-size: 48px;
                    font-weight: bold;
                """)
        except Exception as e:
            print(f"Error setting dev pic: {str(e)}")
            dev_label.setText("PINK")
            dev_label.setStyleSheet("""
                color: #00A6ED;
                font-size: 48px;
                font-weight: bold;
            """)

        dev_label.setFixedSize(logo_size, logo_size)
        dev_label.setAlignment(Qt.AlignCenter)
        dev_layout.addWidget(dev_label)

        header_layout.addWidget(dev_frame)
        header_layout.addStretch()
        content_layout.addWidget(header_widget)

        # App info section
        info_widget = QFrame()
        info_widget.setObjectName("aboutInfo")
        info_widget.setStyleSheet("""
            #aboutInfo {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(4, 11, 17, 0.8),
                    stop:0.5 rgba(10, 23, 33, 0.8),
                    stop:1 rgba(13, 31, 45, 0.8)
                );
                border: 1px solid #00A6ED;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(15)

        # Title and version
        title_label = QLabel("VERSE WATCHER")
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #00A6ED;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(title_label)

        version_label = QLabel("Version 1.0.0 alpha")
        version_label.setStyleSheet("""
            font-size: 16px;
            color: #90CAF9;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(version_label)

        # Description
        desc_label = QLabel("A real-time game.log monitoring tool for Star Citizen")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 14px;
            color: #FFFFFF;
            line-height: 1.6;
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(desc_label)
        content_layout.addWidget(info_widget)

        # Links section
        links_widget = QFrame()
        links_widget.setObjectName("aboutLinks")
        links_widget.setStyleSheet("""
            #aboutLinks {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(4, 11, 17, 0.8),
                    stop:0.5 rgba(10, 23, 33, 0.8),
                    stop:1 rgba(13, 31, 45, 0.8)
                );
                border: 1px solid #00A6ED;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        links_layout = QVBoxLayout(links_widget)
        links_layout.setSpacing(15)

        links_title = QLabel("Links & Resources")
        links_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #00A6ED;
        """)
        links_title.setAlignment(Qt.AlignCenter)
        links_layout.addWidget(links_title)

        # Links with hover effects
        link_style = """
            QLabel {
                font-size: 14px;
                color: #90CAF9;
                padding: 8px;
                border-radius: 5px;
            }
            QLabel:hover {
                color: #40C4FF;
                background: rgba(0, 166, 237, 0.1);
            }
        """

        github_link = QLabel(
            '<a href="https://github.com/PINKgeekPDX/VerseWatcher" '
            'style="color: inherit; text-decoration: none;">'
            "🔗 GitHub Repository</a>"
        )
        github_link.setOpenExternalLinks(True)
        github_link.setStyleSheet(link_style)
        github_link.setAlignment(Qt.AlignCenter)
        links_layout.addWidget(github_link)
        issues_link = QLabel(
            '<a href="https://github.com/PINKgeekPDX/VerseWatcher/issues" '
            'style="color: inherit; text-decoration: none;">'
            "🐛 Report Issues</a>"
        )
        issues_link.setOpenExternalLinks(True)
        issues_link.setStyleSheet(link_style)
        issues_link.setAlignment(Qt.AlignCenter)
        links_layout.addWidget(issues_link)
        content_layout.addWidget(links_widget)

        # Credits section
        credits_widget = QFrame()
        credits_widget.setObjectName("aboutCredits")
        credits_widget.setStyleSheet("""
            #aboutCredits {
                background: rgba(4, 11, 17, 0.5);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        credits_layout = QVBoxLayout(credits_widget)
        credits_layout.setSpacing(15)
        credits_title = QLabel("Credits")
        credits_title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #00A6ED;
        """)
        credits_title.setAlignment(Qt.AlignCenter)
        credits_layout.addWidget(credits_title)
        credits_text = QLabel(
            "Developed by: {PINKgeekPDX}\n"
            "Design: {PINKgeekPDX}\n"
            "\n"
            "Special thanks to the Star Citizen community for helping guide "
            "and test with the development of this tool!"
        )
        credits_text.setStyleSheet("""
            font-size: 14px;
            color: #FFFFFF;
            line-height: 1.6;
        """)
        credits_text.setAlignment(Qt.AlignCenter)
        credits_layout.addWidget(credits_text)
        content_layout.addWidget(credits_widget)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        print("About tab created")
        return tab

    def create_watcher_tab(self):
        """Create and return the watcher tab"""
        try:
            tab = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # Create console output widget (QTreeWidget)
            self.console_output = QTreeWidget()
            self.console_output.setObjectName("consoleOutput")
            self.console_output.setColumnCount(3)
            self.console_output.setHeaderLabels(["Time", "Type", "Message"])

            # Set column widths
            self.console_output.setColumnWidth(0, 100)  # Time column
            self.console_output.setColumnWidth(1, 120)  # Type column
            self.console_output.setColumnWidth(2, 600)  # Message column

            # Apply specific styling for the console tree widget
            self.console_output.setStyleSheet("""
                QTreeWidget {
                    background-color: rgba(4, 11, 17, 0.98);
                    border: 1px solid #00A6ED;
                    border-radius: 2px;
                    color: #FFFFFF;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                    padding: 4px;
                }
                QTreeWidget::item {
                    border: none;
                    padding: 4px;
                    margin: 2px 0;
                }
                QTreeWidget::item:hover {
                    background: rgba(0, 166, 237, 0.15);
                    color: #40C4FF;
                }
                QTreeWidget::item:selected {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #003D5C,
                        stop:1 #0077AA
                    );
                    color: white;
                }
                QTreeWidget::branch {
                    background: transparent;
                }
                QTreeWidget::branch:has-siblings:!adjoins-item {
                    border-image: url(none.png) 0;
                }
                QTreeWidget::branch:has-siblings:adjoins-item {
                    border-image: url(none.png) 0;
                }
                QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                    border-image: url(none.png) 0;
                }
                QHeaderView::section {
                    background: rgba(4, 11, 17, 0.98);
                    color: #00A6ED;
                    padding: 4px;
                    border: 1px solid #00A6ED;
                    font-size: 12px;
                    font-weight: bold;
                }
                QHeaderView::section:hover {
                    background: rgba(0, 166, 237, 0.15);
                    color: #40C4FF;
                }
            """)

            # Add the console to the layout and set the layout for the tab
            layout.addWidget(self.console_output)
            tab.setLayout(layout)

            # Initialize logger with the properly configured console widget
            if not hasattr(self, "logger") or self.logger is None:
                try:
                    print("Initializing logger...")
                    self.logger = Logger(self.console_output, log_file=self.log_file)
                    print("Logger initialized with console widget")
                    self.logger.log_info("Console initialized")
                    print("Test log message sent successfully")
                except Exception as e:
                    print(f"Error initializing logger: {str(e)}")
                    import traceback

                    print(traceback.format_exc())
                    # Create a fallback logger that only logs to file
                    self.logger = Logger(log_file=self.log_file)

            return tab

        except Exception as e:
            print(f"Error in create_watcher_tab: {str(e)}")
            import traceback

            print(traceback.format_exc())
            # Return an empty tab if something goes wrong
            empty_tab = QWidget()
            empty_tab.setLayout(QVBoxLayout())
            return empty_tab

    def clear_console(self):
        """Clear the console output"""
        self.console_output.clear()

    def _format_event_details(self, event_data):
        """Format event data into a readable structure"""
        details = {}

        if "vname" in event_data and "kname" in event_data:
            details["Victim"] = f"💀 {event_data['vname']}"
            details["Killer"] = f"😈 {event_data['kname']}"

        if "kwep" in event_data:
            details["Weapon"] = f"🔫 {event_data['kwep']}"

        if "vship" in event_data:
            details["Ship"] = f"🚀 {event_data['vship']}"

        if "dtype" in event_data:
            details["Damage Type"] = f"💥 {event_data['dtype']}"

        return details

    def create_history_tab(self):
        print("Creating history tab...")
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Session selection
        session_layout = QHBoxLayout()
        session_layout.setSpacing(5)
        session_label = QLabel("Session:")
        session_label.setObjectName("sectionLabel")
        self.session_combo = QComboBox()
        self.session_combo.currentTextChanged.connect(self.on_session_changed)
        self.session_combo.setFixedHeight(25)

        clear_button = QPushButton("🗑️ Clear History")
        clear_button.setObjectName("actionButton")
        clear_button.setFixedHeight(25)
        clear_button.clicked.connect(self.show_clear_history_dialog)

        session_layout.addWidget(session_label)
        session_layout.addWidget(self.session_combo, 1)
        session_layout.addWidget(clear_button)
        layout.addLayout(session_layout)

        # Create horizontal splitter for side-by-side layout
        splitter = QSplitter(Qt.Horizontal)

        # Kill list group
        kill_group = QGroupBox("Events")
        kill_layout = QVBoxLayout(kill_group)
        kill_layout.setContentsMargins(5, 15, 5, 5)
        kill_layout.setSpacing(0)

        self.kill_list = QListWidget()
        self.kill_list.currentItemChanged.connect(self.on_kill_selected)
        kill_layout.addWidget(self.kill_list)

        # Kill details group
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(5, 15, 5, 5)
        details_layout.setSpacing(0)

        self.kill_details = QTreeWidget()
        self.kill_details.setHeaderLabels(["Field", "Value"])
        self.kill_details.setColumnWidth(0, 150)
        self.kill_details.itemDoubleClicked.connect(self.on_details_item_double_clicked)
        self.kill_details.setContextMenuPolicy(Qt.CustomContextMenu)
        self.kill_details.customContextMenuRequested.connect(self.show_details_context_menu)
        details_layout.addWidget(self.kill_details)

        splitter.addWidget(kill_group)
        splitter.addWidget(details_group)

        # Set initial sizes to 50-50 split
        splitter.setSizes([int(splitter.width() * 0.5)] * 2)

        layout.addWidget(splitter)
        print("History tab created")
        return tab

    def create_party_tab(self):
        print("Creating party tab...")
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Create main vertical splitter
        main_splitter = QSplitter(Qt.Vertical)

        # Party members group
        members_group = QGroupBox("Party Members")
        members_layout = QVBoxLayout(members_group)
        members_layout.setContentsMargins(5, 15, 5, 5)
        members_layout.setSpacing(5)

        # Party list and controls
        self.party_members_list = QListWidget()
        self.party_members_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.party_members_list.customContextMenuRequested.connect(
            self.show_party_member_context_menu
        )
        members_layout.addWidget(self.party_members_list)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)
        add_button = QPushButton("➕ Add Member")
        add_button.setObjectName("actionButton")
        add_button.setFixedHeight(25)
        add_button.clicked.connect(self.show_add_member_dialog)
        remove_button = QPushButton("❌ Remove Member")
        remove_button.setObjectName("actionButton")
        remove_button.setFixedHeight(25)
        remove_button.clicked.connect(self.remove_party_member)

        controls_layout.addWidget(add_button)
        controls_layout.addWidget(remove_button)
        members_layout.addLayout(controls_layout)

        # Add members group to main splitter
        main_splitter.addWidget(members_group)

        # Create horizontal splitter for events and details
        events_splitter = QSplitter(Qt.Horizontal)

        # Party events group
        events_group = QGroupBox("Party Events")
        events_layout = QVBoxLayout(events_group)
        events_layout.setContentsMargins(5, 15, 5, 5)
        events_layout.setSpacing(0)

        self.party_event_list = QListWidget()
        self.party_event_list.currentItemChanged.connect(self.on_party_event_selected)
        events_layout.addWidget(self.party_event_list)
        events_splitter.addWidget(events_group)

        # Party event details group
        details_group = QGroupBox("Event Details")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(5, 15, 5, 5)
        details_layout.setSpacing(0)

        self.party_event_details = QTreeWidget()
        self.party_event_details.setHeaderLabels(["Field", "Value"])
        self.party_event_details.setColumnWidth(0, 150)
        details_layout.addWidget(self.party_event_details)
        events_splitter.addWidget(details_group)

        # Set initial sizes for horizontal splitter (50-50)
        events_splitter.setSizes([int(events_splitter.width() * 0.5)] * 2)

        # Add events splitter to main splitter
        main_splitter.addWidget(events_splitter)

        # Set initial sizes for main splitter (40-60)
        main_splitter.setSizes(
            [int(main_splitter.height() * 0.4), int(main_splitter.height() * 0.6)]
        )

        # Add main splitter to layout
        layout.addWidget(main_splitter)

        print("Party tab created")
        return tab

    def show_party_member_context_menu(self, position):
        """Show context menu for party members"""
        try:
            item = self.party_members_list.itemAt(position)
            if not item:
                return

            player_name = item.text()
            if "NPC" in player_name:
                return

            menu = QMenu()
            view_dossier = menu.addAction("View RSI Dossier")
            view_dossier.triggered.connect(lambda: self.open_dossier(player_name))
            menu.exec_(self.party_members_list.viewport().mapToGlobal(position))

        except Exception as e:
            self.logger.log_error(f"Error showing party member context menu: {str(e)}")

    def save_session_history(self, session_id, events):
        """Save session history to a date-based file"""
        try:
            # Get current date for filename
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            history_file = os.path.join(self.history_dir, f"vw_history_{current_date}.txt")

            # Load existing events for today if file exists
            existing_events = []
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r") as f:
                        existing_events = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_events = []

            # Append new events
            all_events = existing_events + events

            # Save combined events back to file
            with open(history_file, "w") as f:
                json.dump(all_events, f, indent=4)

        except Exception as e:
            self.logger.log_error(f"Error saving session history: {str(e)}")

    def load_session_histories(self):
        """Load all session histories from date-based files"""
        try:
            self.session_history = {}
            self.session_combo.clear()

            # List all history files
            for filename in os.listdir(self.history_dir):
                if filename.startswith("vw_history_") and filename.endswith(".txt"):
                    try:
                        # Extract date from filename
                        date_str = filename[11:-4]  # Remove 'vw_history_' and '.txt'

                        # Load events from file
                        with open(os.path.join(self.history_dir, filename), "r") as f:
                            events = json.load(f)

                        # Group events by session time
                        for event in events:
                            timestamp = event.get("timestamp", "")
                            if timestamp:
                                # Use date + hour as session key
                                session_key = f"{date_str} {timestamp.split()[0]}"
                                if session_key not in self.session_history:
                                    self.session_history[session_key] = []
                                    self.session_combo.addItem(session_key)
                                self.session_history[session_key].append(event)

                    except Exception as e:
                        self.logger.log_error(f"Error loading history file {filename}: {str(e)}")

            # Sort sessions by date/time
            self.session_combo.model().sort(0, Qt.DescendingOrder)

        except Exception as e:
            self.logger.log_error(f"Error loading session histories: {str(e)}")

    def on_details_item_double_clicked(self, item, column):
        """Handle double-click events on details items"""
        try:
            if not item or column != 1:  # Only handle clicks on the value column
                return

            field = item.text(0)
            value = item.text(1)

            if field in [
                "💀 Victim",
                "😈 Killer",
            ]:  # Updated to match the actual emoji used for Killer
                if "NPC" in value:
                    self.toast_manager.show_info_toast("No dossier available for NPC")
                else:
                    # Open RSI dossier link
                    player_name = value
                    url = f"https://robertsspaceindustries.com/en/citizens/{player_name}"
                    QDesktopServices.openUrl(QUrl(url))

            elif field == "🚀 Ship":
                # Open ship performance link
                ship_name = value
                url = f"https://www.spviewer.eu/performance?ship={ship_name}"
                QDesktopServices.openUrl(QUrl(url))

        except Exception as e:
            self.logger.log_error(f"Error handling details double-click: {str(e)}")

    def show_details_context_menu(self, position):
        """Show context menu for details items"""
        try:
            item = self.kill_details.itemAt(position)
            if not item:
                return

            field = item.text(0)
            value = item.text(1)

            if field in [
                "💀 Victim",
                "😈 Killer",
            ]:  # Updated to match the actual emoji used for Killer
                menu = QMenu()

                if "NPC" in value:
                    action = menu.addAction("No dossier available")
                    action.setEnabled(False)
                else:
                    action = menu.addAction("View Dossier")
                    action.triggered.connect(lambda: self.open_dossier(value))

                menu.exec_(self.kill_details.viewport().mapToGlobal(position))

        except Exception as e:
            self.logger.log_error(f"Error showing context menu: {str(e)}")

    def open_dossier(self, player_name):
        """Open RSI dossier link for a player"""
        try:
            url = f"https://robertsspaceindustries.com/en/citizens/{player_name}"
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            self.logger.log_error(f"Error opening dossier: {str(e)}")

    def setup_tray_icon(self):
        """Set up the system tray icon and its menu"""
        # Create the tray icon menu
        tray_menu = QMenu()

        # Show action
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)

        # Hide action
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide_window)
        tray_menu.addAction(hide_action)

        # Stay on top action
        self.stay_on_top_action = QAction("Stay on top", self)
        self.stay_on_top_action.setCheckable(True)
        self.stay_on_top_action.triggered.connect(self.toggle_stay_on_top)
        tray_menu.addAction(self.stay_on_top_action)

        # Add separator
        tray_menu.addSeparator()

        # Start/Stop watcher action
        self.watcher_action = QAction("Start Watcher", self)
        self.watcher_action.triggered.connect(self.toggle_watcher)
        tray_menu.addAction(self.watcher_action)

        # Add separator
        tray_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)

        # Set the menu for tray icon
        self.tray_icon.setContextMenu(tray_menu)

        # Set default icon (black heart)
        self.update_tray_icon()

        # Connect double click
        self.tray_icon.activated.connect(self.tray_icon_activated)

        # Show the tray icon
        self.tray_icon.show()

    def create_emoji_icon(self, emoji, size=22):
        """Create an icon from an emoji character"""
        # Create a transparent image
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        # Create painter and set font
        painter = QPainter(image)
        font = QFont()
        font.setPointSize(size - 4)  # Slightly smaller than image size
        painter.setFont(font)

        # Draw the emoji centered in the image
        painter.drawText(image.rect(), Qt.AlignCenter, emoji)
        painter.end()

        # Convert to QIcon
        pixmap = QPixmap.fromImage(image)
        return QIcon(pixmap)

    def update_tray_icon(self):
        """Update the tray icon based on watcher status"""
        if self.is_watching:
            self.tray_icon.setToolTip("VerseWatcher (Watching)")
            self.tray_icon.setIcon(self.create_emoji_icon("💙"))
        else:
            self.tray_icon.setToolTip("VerseWatcher (Not Watching)")
            self.tray_icon.setIcon(self.create_emoji_icon("🖤"))

    def show_window(self):
        """Show and activate the main window"""
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_window(self):
        """Hide the main window"""
        self.hide()

    def toggle_stay_on_top(self, checked):
        """Toggle the window's stay on top state"""
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        self.show()

    def toggle_watcher(self):
        """Toggle the watcher state"""
        if self.is_watching:
            self.stop_watching()
        else:
            self.start_watching()

    def start_watching(self):
        """Start the watcher"""
        if not self.is_watching:
            self.toggle_watching()

    def stop_watching(self):
        """Stop the watcher"""
        if self.is_watching:
            self.toggle_watching()

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()


def main():
    try:
        # Create log directory in user's documents
        log_dir = os.path.join(os.path.expanduser("~"), "Documents", "PINK", "VerseWatcher", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Set up logging to file
        log_file = os.path.join(
            log_dir, f"startup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        logging.info("Starting application...")

        # Create QApplication instance
        global app
        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        # Set application icon
        try:
            # Try multiple possible icon locations
            possible_icon_paths = [
                os.path.join(os.path.dirname(__file__), "..", "vw.ico"),  # Source directory
                os.path.join(os.path.dirname(sys.executable), "vw.ico"),  # Executable directory
                "vw.ico",  # Current directory
            ]

            icon_set = False
            for icon_path in possible_icon_paths:
                if os.path.exists(icon_path):
                    app.setWindowIcon(QIcon(icon_path))
                    logging.info(f"Application icon set from: {icon_path}")
                    icon_set = True
                    break

            if not icon_set:
                logging.warning("Could not find vw.ico in any of the expected locations")
        except Exception as e:
            logging.error(f"Error setting application icon: {str(e)}")

        # Create and show the main window
        logging.info("Creating main window...")
        global window
        window = MainWindow()

        logging.info("Showing window...")
        window.show()
        window.raise_()
        window.activateWindow()

        logging.info("Starting event loop...")
        return app.exec_()

    except Exception as e:
        logging.critical(f"Fatal error in main(): {str(e)}", exc_info=True)
        import traceback

        logging.critical(traceback.format_exc())
        return 1


if __name__ == "__main__":
    try:
        # Keep global references to prevent garbage collection
        global app, window
        app = None
        window = None

        sys.exit(main())
    except Exception as e:
        logging.critical(f"Fatal error in __main__: {str(e)}", exc_info=True)
        sys.exit(1)
