import os
import re
from datetime import datetime

from PyQt5.QtCore import QTimer


class GameLogWatcher:
    def __init__(self, game_path, player_name, logger, toast_manager, main_window):
        try:
            self.game_path = game_path
            self.log_file = os.path.join(game_path, "Game.log")
            self.player_name = player_name
            self.logger = logger
            self.toast_manager = toast_manager
            self.main_window = main_window  # Store reference to the main window
            
            # Get config information from main_window
            if hasattr(main_window, 'self_events_check'):
                self.show_self_events = main_window.self_events_check.isChecked()
            else:
                self.show_self_events = True
                
            if hasattr(main_window, 'other_events_check'):
                self.show_other_events = main_window.other_events_check.isChecked()
            else:
                self.show_other_events = True
                
            if hasattr(main_window, 'npc_events_check'):
                self.show_npc_events = main_window.npc_events_check.isChecked()
            else:
                self.show_npc_events = True
                
            if hasattr(main_window, 'suicide_events_check'):
                self.show_suicide_events = main_window.suicide_events_check.isChecked()
            else:
                self.show_suicide_events = True
                
            if hasattr(main_window, 'party_events_check'):
                self.show_party_events = main_window.party_events_check.isChecked()
            else:
                self.show_party_events = True
                
            if hasattr(main_window, 'party_members'):
                self.party_members = main_window.party_members
            else:
                self.party_members = []
            
            self.observer = None
            self.event_handler = None
            self.last_position = 0
            self.is_running = False  # Add a flag to track if watcher is running
            self.kill_counts = {}  # Track kills for killstreak notifications

            # Create timer in the main thread (parented to main_window)
            # Using a weak reference pattern to avoid circular references
            self.timer = QTimer(main_window)
            self.timer.setInterval(500)  # 500ms interval for checking new events (reduced frequency)
            self.timer.timeout.connect(self.check_file)

            # Death event pattern – using the known working pattern.
            # Note: the direction vector groups (dirvecx, dirvecy, dirvecz) are captured
            # but will be removed.
            self.death_pattern = re.compile(
                r"^(?P<timestamp>\S+)\s+\[Notice\]\s+<Actor Death> CActor::Kill:\s+"
                r"\'(?P<vname>[^\']+)\'\s+\[\d+\]\s+in zone\s+\'(?P<vship>[^\']+)\'\s+"
                r"killed by\s+\'(?P<kname>[^\']+)\'\s+\[\d+\]\s+using\s+\'(?P<kwep>[^\']+)\'\s+"
                r"\[[^\]]*\]\s+with damage type\s+\'(?P<dtype>[^\']+)\'\s+from direction x:\s*"
                r"(?P<dirvecx>[^,]+),\s*y:\s*(?P<dirvecy>[^,]+),\s*z:\s*(?P<dirvecz>[^\s]+)"
                r"\s+\[Team_ActorTech\]\[Actor\]$"
            )

            self.logger.log_debug(f"GameLogWatcher initialized with game_path: {game_path}")
            self.logger.log_debug(f"Looking for log file at: {self.log_file}")

            # Set up the last position file path
            self.last_position_file = os.path.join(game_path, "last_position.txt")
            
            # Load last position from file if available
            self._load_last_position()

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error initializing GameLogWatcher: {str(e)}")
                import traceback
                self.logger.log_error(traceback.format_exc())
            raise

    def _load_last_position(self):
        """Safely load the last position from file"""
        if os.path.exists(self.last_position_file):
            try:
                with open(self.last_position_file, "r") as f:
                    self.last_position = int(f.read().strip() or "0")
                self.logger.log_info(f"Loaded last position from file: {self.last_position}")
            except Exception as e:
                self.logger.log_error(f"Error loading last position: {str(e)}")
                self.last_position = 0
        else:
            self.last_position = 0

    def check_file(self):
        """Check for new events in the log file and process them."""
        # First check if we're supposed to be running
        if not self.is_running:
            return
            
        try:
            # Check if file exists before attempting to open
            if not os.path.exists(self.log_file):
                self.logger.log_warning(f"Log file not found: {self.log_file}")
                return

            # Track how many lines we process in this check to avoid excessive CPU usage
            lines_processed = 0
            max_lines_per_check = 1000  # Limit lines processed per check to prevent freezing

            # Get current file size
            try:
                file_size = os.path.getsize(self.log_file)
            except OSError as e:
                self.logger.log_error(f"Error getting file size: {str(e)}")
                return

            # If file has been truncated, reset position
            if file_size < self.last_position:
                self.logger.log_info(f"Log file truncated, resetting position from {self.last_position} to 0")
                self.last_position = 0

            # Retry counter for file access issues
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries and self.is_running:
                try:
                    with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
                        # Seek to the last read position
                        f.seek(self.last_position)
                        
                        # Process each new line
                        for line in f:
                            # Check if we've been stopped mid-processing
                            if not self.is_running:
                                return
                                
                            self.process_line(line.strip())
                            lines_processed += 1
                            
                            # Avoid processing too many lines at once to prevent UI freezing
                            if lines_processed >= max_lines_per_check:
                                self.logger.log_warning(f"Reached maximum lines per check ({max_lines_per_check}), will continue in next cycle")
                                break
                                
                        # Update the last position
                        self.last_position = f.tell()
                        
                    # If we made it here, the read was successful
                    break
                    
                except PermissionError:
                    # File might be locked by the game, retry
                    retry_count += 1
                    if retry_count < max_retries:
                        self.logger.log_warning(f"Permission error when reading log file, retrying ({retry_count}/{max_retries})...")
                        # Small delay before retry
                        QTimer.singleShot(50, lambda: None)
                    else:
                        self.logger.log_error(f"Failed to read log file after {max_retries} attempts")
                except Exception as e:
                    self.logger.log_error(f"Error reading log file: {str(e)}")
                    break

            # Only save position if we're still running
            if self.is_running:
                self._save_last_position()

        except Exception as e:
            self.logger.log_error(f"Error in check_file: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())
    
    def _save_last_position(self):
        """Safely save the last position to file"""
        try:
            # Create a temp file and then rename for atomic write
            temp_file = self.last_position_file + ".tmp"
            with open(temp_file, "w") as f:
                f.write(str(self.last_position))
            
            # Replace the old file with the new one (atomic operation)
            if os.path.exists(self.last_position_file):
                os.replace(temp_file, self.last_position_file)
            else:
                os.rename(temp_file, self.last_position_file)
                
        except Exception as e:
            self.logger.log_error(f"Error saving last position: {str(e)}")

    def start(self):
        """Start watching the game log file for new events."""
        try:
            # Don't start if already running
            if self.is_running:
                self.logger.log_warning("Watcher already running, ignoring start request")
                return True
                
            # Verify that game log exists
            if not os.path.exists(self.log_file):
                error_msg = f"Game.log not found at: {self.log_file}"
                self.logger.log_error(error_msg)
                if hasattr(self, 'toast_manager') and self.toast_manager:
                    self.toast_manager.show_error_toast(f"❌ {error_msg}")
                return False

            try:
                # Set the initial file position to the end so that only new events are processed
                with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(0, 2)  # Seek to the end of the file
                    self.last_position = f.tell()
                self.logger.log_info(
                    f"Starting to watch new events from position {self.last_position}"
                )

                # Set running flag
                self.is_running = True
                
                # Start timer with safety check
                try:
                    if hasattr(self, 'timer') and self.timer and not self.timer.isActive():
                        self.timer.start()
                        self.logger.log_info("File watching timer started successfully")
                except Exception as e:
                    self.logger.log_error(f"Error starting timer: {str(e)}")
                    self.is_running = False
                    return False

                # Show a startup success toast
                if hasattr(self, 'toast_manager') and self.toast_manager:
                    self.toast_manager.show_info_toast("🎮 Started watching for new game events ✨")
                return True

            except (IOError, OSError) as e:
                error_msg = f"Error accessing game log: {str(e)}"
                self.logger.log_error(error_msg)
                if hasattr(self, 'toast_manager') and self.toast_manager:
                    self.toast_manager.show_error_toast(f"⚠️ {error_msg}")
                self.is_running = False
                return False

        except Exception as e:
            error_msg = f"Failed to start watching: {str(e)}"
            self.logger.log_error(error_msg)
            import traceback
            self.logger.log_error(traceback.format_exc())
            
            # Show error toast if available
            if hasattr(self, 'toast_manager') and self.toast_manager:
                self.toast_manager.show_error_toast(f"⚠️ {error_msg}")
            
            # Make sure we're marked as not running
            self.is_running = False
            return False

    def stop(self):
        """Stop watching the game log file and save the last read position."""
        try:
            # First mark as not running to stop processing in check_file
            self.is_running = False
            
            # Disconnect the timer signal first
            try:
                if hasattr(self, 'timer') and self.timer:
                    # Only try to disconnect if the timer is active
                    if self.timer.isActive():
                        self.timer.stop()
                        # Don't try to manually disconnect the timeout signal
                        # Just stopping the timer is sufficient
                        self.logger.log_info("File watching timer stopped successfully")
            except Exception as e:
                self.logger.log_error(f"Error stopping timer: {str(e)}")

            # Save the last position
            self._save_last_position()
            
        except Exception as e:
            self.logger.log_error(f"Error stopping watcher: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())

    def process_line(self, line):
        """Process a single line from the log file and trigger events accordingly."""
        try:
            # Remove the general debug logging of every line
            # self.logger.log_debug(f"Processing log line: {line[:100]}..." if len(line) > 100 else f"Processing log line: {line}")
            
            # Attempt to match a death event via regex
            death_match = self.death_pattern.match(line)
            if death_match:
                # Only log lines that match an event pattern
                self.logger.log_debug(f"Event match found: {line[:100]}..." if len(line) > 100 else f"Event match found: {line}")
                
                event_details = death_match.groupdict()
                vname = event_details.get("vname")
                kname = event_details.get("kname")
                kwep = event_details.get("kwep")
                vship = event_details.get("vship")
                dtype = event_details.get("dtype")

                # Do NOT include any direction information.
                # Remove the raw direction vector keys if they are present.
                for vec_key in ["dirvecx", "dirvecy", "dirvecz"]:
                    event_details.pop(vec_key, None)

                # Add only a timestamp to the event details
                event_details["timestamp"] = datetime.now().strftime("%H:%M:%S")

                # Determine if the names are designated as NPC:
                # Any name containing "NPC" or starting with "PU_" is treated as an NPC.
                vname_is_npc = ("NPC" in vname) or vname.startswith("PU_")
                kname_is_npc = ("NPC" in kname) or kname.startswith("PU_")

                # Process different event types
                if vname == kname:
                    # Suicide event
                    self.logger.log_kill(vname, kname, kwep, vship, dtype)
                    self.logger.log_event(f"{vname} committed suicide using {kwep}", event_details)
                    title = f"💀 {vname} committed suicide 🔫"
                    details = f"🔫 Weapon: {kwep}\n🚀 Ship: {vship}\n💥 Damage: {dtype}"
                    self.toast_manager.show_death_toast({"title": title, "details": details}, "suicide")
                    
                elif vname_is_npc or kname_is_npc:
                    # NPC event
                    if vname_is_npc:
                        self.logger.log_kill(vname, kname, kwep, vship, dtype)
                        self.logger.log_event(f"NPC {vname} killed by {kname} using {kwep}", event_details)
                        title = f"🤖 NPC killed by {kname} ⚔️"
                    else:
                        self.logger.log_kill(vname, kname, kwep, vship, dtype)
                        self.logger.log_event(f"{vname} killed by NPC {kname} using {kwep}", event_details)
                        title = f"🤖 {vname} killed by NPC ⚔️"
                    
                    details = f"🔫 Weapon: {kwep}\n🚀 Ship: {vship}\n💥 Damage: {dtype}"
                    self.toast_manager.show_death_toast({"title": title, "details": details}, "npc")
                    
                elif vname == self.player_name:
                    # Player death
                    self.logger.log_kill(vname, kname, kwep, vship, dtype)
                    self.logger.log_event(f"You were killed by {kname} using {kwep}", event_details)
                    title = f"☠️ You were killed by {kname} ⚰️"
                    details = f"🔫 Weapon: {kwep}\n🚀 Ship: {vship}\n💥 Damage: {dtype}"
                    self.toast_manager.show_death_toast({"title": title, "details": details}, "death")
                    
                elif kname == self.player_name:
                    # Player kill
                    self.logger.log_kill(vname, kname, kwep, vship, dtype)
                    self.logger.log_event(f"You killed {vname} using {kwep}", event_details)
                    title = f"🎯 You killed {vname} ✨"
                    details = f"🔫 Weapon: {kwep}\n🚀 Ship: {vship}\n💥 Damage: {dtype}"
                    self.toast_manager.show_death_toast({"title": title, "details": details}, "kill")

                    # Track killstreak notifications
                    self.kill_counts[self.player_name] = (
                        self.kill_counts.get(self.player_name, 0) + 1
                    )
                    streak = self.kill_counts[self.player_name]
                    if streak > 1:
                        self.toast_manager.show_killstreak_toast(
                            {
                                "title": f"🔥 KILLSTREAK: {streak} 🏆",
                                "details": "Keep it up! 🌟",
                            }
                        )
                else:
                    # Other player kills
                    self.logger.log_kill(vname, kname, kwep, vship, dtype)
                    self.logger.log_event(
                        f"{vname} was killed by {kname} using {kwep}", event_details
                    )
                    title = f"⚔️ {vname} killed by {kname} 🎯"
                    details = f"🔫 Weapon: {kwep}\n🚀 Ship: {vship}\n💥 Damage: {dtype}"
                    self.toast_manager.show_death_toast({"title": title, "details": details}, "info")

                # Notify the main window about the event to update UI
                if hasattr(self.main_window, 'add_kill_event'):
                    self.main_window.add_kill_event(event_details)

        except Exception as e:
            self.logger.log_error(f"Error processing log line: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())
