#!/usr/bin/env python3
import os
import json
import random
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QComboBox, QFormLayout, 
                            QGroupBox, QTextEdit, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

class GameLogTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game.log Kill Event Generator")
        self.setMinimumSize(600, 700)
        
        # Set default paths
        self.app_dir = os.path.join(
            os.path.expanduser("~"),
            "Documents",
            "PINK",
            "VerseWatcher"
        )
        self.settings_file = os.path.join(self.app_dir, "settings.json")
        self.game_log_path = None
        
        # Load settings if available
        self.load_settings()
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        # Info section
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready to generate kill events for testing.")
        self.status_label.setStyleSheet("color: #00A6ED; font-weight: bold;")
        
        self.log_path_label = QLabel(f"Game.log Path: {self.game_log_path or 'Not found'}")
        self.log_path_label.setWordWrap(True)
        
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.log_path_label)
        
        # Path selection button
        path_button = QPushButton("Select Game Log Path Manually")
        path_button.clicked.connect(self.select_game_log_path)
        info_layout.addWidget(path_button)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Event configuration
        event_group = QGroupBox("Kill Event Configuration")
        form_layout = QFormLayout()
        
        # Victim name
        self.victim_input = QLineEdit("SOMEVIC")
        form_layout.addRow("Victim Name:", self.victim_input)
        
        # Killer name
        self.killer_input = QLineEdit("SOMEKILL")
        form_layout.addRow("Killer Name:", self.killer_input)
        
        # Ship name
        self.ship_input = QLineEdit("MISC_Razor_PU_AI_CRIM")
        form_layout.addRow("Ship Name:", self.ship_input)
        
        # Weapon name
        self.weapon_input = QLineEdit("MRCK_S04_ANVL_Hornet_F7CM_Mk2_Turret")
        form_layout.addRow("Weapon Name:", self.weapon_input)
        
        # Damage type
        self.damage_combo = QComboBox()
        damage_types = ["VehicleDestruction", "Ballistic", "Laser", "Explosion", "Impact", "Missile"]
        self.damage_combo.addItems(damage_types)
        form_layout.addRow("Damage Type:", self.damage_combo)
        
        # Random IDs
        random_id_check_layout = QHBoxLayout()
        self.random_ids_button = QPushButton("Generate Random IDs")
        self.random_ids_button.clicked.connect(self.generate_random_ids)
        random_id_check_layout.addWidget(self.random_ids_button)
        random_id_check_layout.addStretch()
        
        form_layout.addRow("", random_id_check_layout)
        
        # Victim ID
        self.victim_id_input = QLineEdit(str(random.randint(1000000000000, 9999999999999)))
        form_layout.addRow("Victim ID:", self.victim_id_input)
        
        # Killer ID
        self.killer_id_input = QLineEdit(str(random.randint(1000000000000, 9999999999999)))
        form_layout.addRow("Killer ID:", self.killer_id_input)
        
        # Ship ID
        self.ship_id_input = QLineEdit(str(random.randint(1000000000000, 9999999999999)))
        form_layout.addRow("Ship ID:", self.ship_id_input)
        
        # Weapon ID
        self.weapon_id_input = QLineEdit(str(random.randint(1000000000000, 9999999999999)))
        form_layout.addRow("Weapon ID:", self.weapon_id_input)
        
        event_group.setLayout(form_layout)
        main_layout.addWidget(event_group)
        
        # Preview section
        preview_group = QGroupBox("Event Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 9))
        preview_layout.addWidget(self.preview_text)
        
        # Update preview button
        preview_button = QPushButton("Update Preview")
        preview_button.clicked.connect(self.update_preview)
        preview_layout.addWidget(preview_button)
        
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        # Generate event button
        self.generate_button = QPushButton("GENERATE KILL EVENT")
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #0077AA; 
                color: white; 
                font-weight: bold; 
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00A6ED;
            }
        """)
        self.generate_button.setMinimumHeight(50)
        self.generate_button.clicked.connect(self.generate_kill_event)
        
        buttons_layout.addWidget(self.generate_button)
        main_layout.addLayout(buttons_layout)
        
        # Update the preview initially
        self.update_preview()
        
        # Apply dark theme
        self.apply_dark_theme()
        
    def apply_dark_theme(self):
        """Apply a dark theme to the application"""
        app = QApplication.instance()
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(0, 0, 0))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(0, 166, 237))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        
        app.setPalette(palette)
        
        # Set stylesheet for specific widgets
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #00A6ED;
                border-radius: 5px;
                margin-top: 15px;
                font-weight: bold;
                color: #00A6ED;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #E0E0E0;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #333333;
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: #E0E0E0;
                padding: 5px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #40C4FF;
            }
            QPushButton {
                background-color: #0D1F2D;
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: #E0E0E0;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1A3F5D;
                border: 1px solid #40C4FF;
            }
        """)
    
    def load_settings(self):
        """Load settings from the VerseWatcher settings.json file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Get game path from settings
                game_path = settings.get("game_path", "")
                if game_path:
                    potential_log_path = os.path.join(game_path, "Game.log")
                    if os.path.exists(game_path) and os.access(game_path, os.W_OK):
                        self.game_log_path = potential_log_path
                        return True
            
            # If we couldn't get the path from settings, try some common locations
            common_paths = [
                "C:\\Program Files\\Roberts Space Industries\\StarCitizen\\LIVE",
                "D:\\Program Files\\Roberts Space Industries\\StarCitizen\\LIVE"
            ]
            
            for path in common_paths:
                potential_log_path = os.path.join(path, "Game.log")
                if os.path.exists(path) and os.access(path, os.W_OK):
                    self.game_log_path = potential_log_path
                    return True
                    
            return False
        except Exception as e:
            self.status_label.setText(f"Error loading settings: {str(e)}")
            self.status_label.setStyleSheet("color: #FF5252; font-weight: bold;")
            return False
    
    def select_game_log_path(self):
        """Allow user to manually select the Game.log path"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Star Citizen Installation Directory",
            os.path.expanduser("~")
        )
        
        if directory:
            self.game_log_path = os.path.join(directory, "Game.log")
            self.log_path_label.setText(f"Game.log Path: {self.game_log_path}")
            self.status_label.setText("Game log path updated.")
            self.status_label.setStyleSheet("color: #00A6ED; font-weight: bold;")
    
    def generate_random_ids(self):
        """Generate random IDs for all fields"""
        self.victim_id_input.setText(str(random.randint(1000000000000, 9999999999999)))
        self.killer_id_input.setText(str(random.randint(1000000000000, 9999999999999)))
        self.ship_id_input.setText(str(random.randint(1000000000000, 9999999999999)))
        self.weapon_id_input.setText(str(random.randint(1000000000000, 9999999999999)))
        self.update_preview()
    
    def update_preview(self):
        """Update the preview text with the current event configuration"""
        try:
            # Get current timestamp in ISO format with Z suffix (UTC)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
            
            # Get values from input fields
            victim = self.victim_input.text()
            killer = self.killer_input.text()
            ship = self.ship_input.text()
            weapon = self.weapon_input.text()
            damage_type = self.damage_combo.currentText()
            
            # Get IDs 
            victim_id = self.victim_id_input.text()
            killer_id = self.killer_id_input.text()
            ship_id = self.ship_id_input.text()
            weapon_id = self.weapon_id_input.text()
            
            # Format the line
            kill_line = f"<{timestamp}> [Notice] <Actor Death> CActor::Kill: '{victim}' [{victim_id}] in zone '{ship}_{ship_id}' killed by '{killer}' [{killer_id}] using '{weapon}_{weapon_id}' [Class unknown] with damage type '{damage_type}' from direction x: 0.000000, y: 0.000000, z: 0.000000 [Team_ActorTech][Actor]"
            
            # Update the preview
            self.preview_text.setText(kill_line)
            
        except Exception as e:
            self.preview_text.setText(f"Error generating preview: {str(e)}")
    
    def generate_kill_event(self):
        """Generate and add a kill event to the Game.log file"""
        if not self.game_log_path:
            QMessageBox.warning(self, "Path Not Found", "Game.log path not found. Please select the path manually.")
            return
            
        try:
            # Update preview first to get the latest event text
            self.update_preview()
            kill_line = self.preview_text.toPlainText()
            
            # Check if the directory exists and is writable
            log_dir = os.path.dirname(self.game_log_path)
            if not os.path.exists(log_dir):
                QMessageBox.critical(self, "Directory Not Found", f"The directory {log_dir} does not exist.")
                return
                
            if not os.access(log_dir, os.W_OK):
                QMessageBox.critical(self, "Permission Denied", f"No write permission for {log_dir}.")
                return
            
            # Create the log file if it doesn't exist
            if not os.path.exists(self.game_log_path):
                with open(self.game_log_path, 'w') as f:
                    f.write("# Star Citizen Game.log created by test tool\n")
            
            # Append the kill line to the log file
            with open(self.game_log_path, 'a') as f:
                f.write(kill_line + "\n")
            
            # Update status
            self.status_label.setText(f"Kill event added to Game.log at {datetime.datetime.now().strftime('%H:%M:%S')}")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # Generate new random IDs for next event
            self.generate_random_ids()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add kill event: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #FF5252; font-weight: bold;")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better dark theme support
    window = GameLogTester()
    window.show()
    sys.exit(app.exec_()) 