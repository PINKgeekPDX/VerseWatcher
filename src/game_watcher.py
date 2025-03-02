import os
import re
import time
from datetime import datetime
from collections import deque

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
            self.is_running = False  # Flag to track if watcher is running
            self.kill_counts = {}  # Track kills for killstreak notifications
            
            # Enhanced tracking mechanism with buffer
            self.file_size = 0  # Current known file size
            self.buffer_size = 500  # Increased buffer size to catch more duplicates
            self.line_buffer = deque(maxlen=self.buffer_size)  # Circular buffer of recently processed lines
            self.last_read_time = 0  # Time of last successful read
            self.last_line_fragment = ""  # Store any partial line from previous read
            self.consecutive_errors = 0  # Track consecutive read errors

            # Create timer in the main thread (parented to main_window)
            self.timer = QTimer(main_window)
            self.timer.setInterval(250)  # Faster interval to catch more events
            self.timer.timeout.connect(self.check_file)

            # Death event pattern – using the known working pattern
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

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error initializing GameLogWatcher: {str(e)}")
                import traceback
                self.logger.log_error(traceback.format_exc())
            raise

    def check_file(self):
        """Check for new events in the log file and process them."""
        # Check if we're supposed to be running
        if not self.is_running:
            return
            
        # Rate limiting to avoid excessive file reads
        current_time = time.time()
        if current_time - self.last_read_time < 0.1:  # Reduced to catch events faster
            return
            
        try:
            # Reset consecutive errors counter on successful execution
            self.consecutive_errors = 0
            
            # Check if file exists
            if not os.path.exists(self.log_file):
                self.logger.log_warning(f"Log file not found: {self.log_file}")
                return

            # Get current file size
            try:
                current_size = os.path.getsize(self.log_file)
            except OSError as e:
                self.logger.log_error(f"Error getting file size: {str(e)}")
                return
                
            # If file hasn't changed, nothing to do
            if current_size == self.file_size and self.file_size > 0:
                return
                
            # If file has been truncated (smaller than before), reset tracking
            if current_size < self.file_size:
                self.logger.log_info(f"Log file has been truncated or rotated, restarting from end")
                self.file_size = current_size
                self.line_buffer.clear()
                self.last_line_fragment = ""
                return
            
            # Safety check - don't try to read too much new data at once
            # If file grew by more than 5MB since last check, read in chunks
            max_read_size = 5 * 1024 * 1024  # 5MB
            bytes_to_read = current_size - self.file_size
            if bytes_to_read > max_read_size and self.file_size > 0:
                self.logger.log_warning(f"File grew too much ({bytes_to_read / 1024:.1f}KB), reading in chunks")
                # We'll read in max_read_size chunks
                bytes_to_read = max_read_size
            
            # Update last read time
            self.last_read_time = current_time
            
            # We have new content to process
            try:
                with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                    # If this is the first time, jump to the end
                    if self.file_size == 0:
                        f.seek(0, 2)  # Seek to end of file
                        self.file_size = current_size
                        self.logger.log_info(f"First time processing log, starting from end of file (size: {current_size})")
                        return
                    
                    # Seek to where we left off
                    f.seek(self.file_size)
                    
                    # Read new content
                    new_content = f.read(bytes_to_read)
                    
                    # Handle line fragments from previous read
                    if self.last_line_fragment:
                        new_content = self.last_line_fragment + new_content
                        self.last_line_fragment = ""
                    
                    # Check if the content ends with a complete line
                    if new_content and not new_content.endswith('\n'):
                        # Find the last newline
                        last_newline = new_content.rfind('\n')
                        if last_newline >= 0:
                            # Store the fragment for next read
                            self.last_line_fragment = new_content[last_newline + 1:]
                            # Process only complete lines
                            new_content = new_content[:last_newline + 1]
                        else:
                            # No newline found, store everything as fragment
                            self.last_line_fragment = new_content
                            new_content = ""
                    
                    # Split content into lines
                    new_lines = new_content.splitlines()
                    
                    # Count lines for logging
                    line_count = len(new_lines)
                    if line_count > 0:
                        self.logger.log_debug(f"Processing {line_count} new lines from log file")
                    
                    # Process new lines and add to buffer
                    for line in new_lines:
                        line = line.strip()
                        # Skip empty lines
                        if not line:
                            continue
                        
                        # Skip if this exact line is in our recent buffer (duplicate prevention)
                        if line in self.line_buffer:
                            continue
                            
                        # Add to buffer
                        self.line_buffer.append(line)
                        
                        # Process the line
                        self.process_line(line)
                    
                    # Update file size after successfully processing
                    self.file_size += bytes_to_read
                    
                    # If we read a chunk and there's more to read, trigger another check soon
                    if bytes_to_read == max_read_size and current_size > self.file_size:
                        QTimer.singleShot(100, self.check_file)
                    
            except Exception as e:
                self.consecutive_errors += 1
                self.logger.log_error(f"Error reading log file (attempt {self.consecutive_errors}): {str(e)}")
                
                # If there have been too many consecutive errors, reset tracking
                if self.consecutive_errors > 5:
                    self.logger.log_warning("Too many consecutive errors, resetting file tracking")
                    self.file_size = 0
                    self.line_buffer.clear()
                    self.last_line_fragment = ""
                    self.consecutive_errors = 0
                
                import traceback
                self.logger.log_error(traceback.format_exc())
                
        except Exception as e:
            self.logger.log_error(f"Error in check_file: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())

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

            # Reset tracking variables
            self.file_size = 0  # Start from the end
            self.line_buffer.clear()
            self.last_read_time = 0
            self.last_line_fragment = ""
            self.consecutive_errors = 0
            
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
        """Stop watching the game log file."""
        try:
            # First mark as not running to stop processing in check_file
            self.is_running = False
            
            # Stop the timer if active
            try:
                if hasattr(self, 'timer') and self.timer:
                    # Only try to stop if the timer is active
                    if self.timer.isActive():
                        self.timer.stop()
                        self.logger.log_info("File watching timer stopped successfully")
            except Exception as e:
                self.logger.log_error(f"Error stopping timer: {str(e)}")
            
        except Exception as e:
            self.logger.log_error(f"Error stopping watcher: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())

    def process_line(self, line):
        """Process a single line from the log file and trigger events accordingly."""
        try:
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
