import os
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import QTimer
from datetime import datetime

class GameLogWatcher:
    def __init__(self, game_path, player_name, logger, toast_manager, main_window):
        try:
            self.game_path = game_path
            self.log_file = os.path.join(game_path, 'Game.log')
            self.player_name = player_name
            self.logger = logger
            self.toast_manager = toast_manager
            self.main_window = main_window  # Store reference to the main window
            self.observer = None
            self.event_handler = None
            self.last_position = 0
            self.kill_counts = {}  # Track kills for killstreak notifications

            # Create timer in the main thread (parented to main_window)
            self.timer = QTimer(main_window)
            self.timer.setInterval(100)  # 100ms interval for checking new events
            self.timer.timeout.connect(self.check_file)

            # Death event pattern – using the known working pattern.
            # Note: the direction vector groups (dirvecx, dirvecy, dirvecz) are captured but will be removed.
            self.death_pattern = re.compile(
                r'^(?P<timestamp>\S+)\s+\[Notice\]\s+<Actor Death> CActor::Kill:\s+'
                r'\'(?P<vname>[^\']+)\'\s+\[\d+\]\s+in zone\s+\'(?P<vship>[^\']+)\'\s+'
                r'killed by\s+\'(?P<kname>[^\']+)\'\s+\[\d+\]\s+using\s+\'(?P<kwep>[^\']+)\'\s+'
                r'\[[^\]]*\]\s+with damage type\s+\'(?P<dtype>[^\']+)\'\s+from direction x:\s*'
                r'(?P<dirvecx>[^,]+),\s*y:\s*(?P<dirvecy>[^,]+),\s*z:\s*(?P<dirvecz>[^\s]+)'
                r'\s+\[Team_ActorTech\]\[Actor\]$'
            )

            self.logger.log_debug(f"GameLogWatcher initialized with game_path: {game_path}")
            self.logger.log_debug(f"Looking for log file at: {self.log_file}")

            # Load last position from file if available
            self.last_position_file = os.path.join(game_path, 'last_position.txt')
            if os.path.exists(self.last_position_file):
                try:
                    with open(self.last_position_file, 'r') as f:
                        self.last_position = int(f.read())
                    self.logger.log_info(f"Loaded last position from file: {self.last_position}")
                except Exception as e:
                    self.logger.log_error(f"Error loading last position: {str(e)}")
                    self.last_position = 0
            else:
                self.last_position = 0

        except Exception as e:
            self.logger.log_error(f"Error initializing GameLogWatcher: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())
            raise

    def check_file(self):
        """Check for new lines in the log file and process new events."""
        try:
            if not os.path.exists(self.log_file):
                self.logger.log_warning(f"Game log file not found: {self.log_file}")
                return

            try:
                current_size = os.path.getsize(self.log_file)
                # Only process if there is new content in the file
                if current_size > self.last_position:
                    with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                        # Seek to the last read position
                        f.seek(self.last_position)
                        new_lines = f.readlines()
                        self.last_position = f.tell()
                        # Process each new non-empty line
                        for line in new_lines:
                            if line.strip():
                                try:
                                    self.process_line(line)
                                except Exception as e:
                                    self.logger.log_error(f"Error processing line: {str(e)}")
                                    continue
            except (IOError, OSError) as e:
                self.logger.log_error(f"Error accessing game log file: {str(e)}")
                return

        except KeyboardInterrupt:
            # Handle KeyboardInterrupt gracefully during file checking.
            self.logger.log_info("File checking interrupted via KeyboardInterrupt.")
            return
        except Exception as e:
            self.logger.log_error(f"Error in check_file: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())

    def start(self):
        """Start watching the game log file for new events."""
        try:
            # Verify that game log exists
            if not os.path.exists(self.log_file):
                error_msg = f"Game.log not found at: {self.log_file}"
                self.logger.log_error(error_msg)
                self.toast_manager.show_error_toast(f"❌ {error_msg}")
                return False

            try:
                # Set the initial file position to the end so that only new events are processed
                with open(self.log_file, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(0, 2)  # Seek to the end of the file
                    self.last_position = f.tell()
                self.logger.log_info(f"Starting to watch new events from position {self.last_position}")

                try:
                    if not self.timer.isActive():
                        self.timer.start()
                        self.logger.log_info("File watching timer started successfully")
                except Exception as e:
                    self.logger.log_error(f"Error starting timer: {str(e)}")
                    return False

                # Show a startup success toast
                self.toast_manager.show_info_toast("🎮 Started watching for new game events ✨")
                return True

            except (IOError, OSError) as e:
                error_msg = f"Error accessing game log: {str(e)}"
                self.logger.log_error(error_msg)
                self.toast_manager.show_error_toast(f"⚠️ {error_msg}")
                return False

        except Exception as e:
            error_msg = f"Failed to start watching: {str(e)}"
            self.logger.log_error(error_msg)
            import traceback
            self.logger.log_error(traceback.format_exc())
            self.toast_manager.show_error_toast(f"⚠️ {error_msg}")
            return False

    def stop(self):
        """Stop watching the game log file and save the last read position."""
        try:
            try:
                if self.timer and self.timer.isActive():
                    self.timer.stop()
                    self.logger.log_info("File watching timer stopped successfully")
            except Exception as e:
                self.logger.log_error(f"Error stopping timer: {str(e)}")

            try:
                with open(self.last_position_file, 'w') as f:
                    f.write(str(self.last_position))
            except Exception as e:
                self.logger.log_error(f"Error saving last position: {str(e)}")
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
                event_details = death_match.groupdict()
                vname = event_details.get('vname')
                kname = event_details.get('kname')
                kwep = event_details.get('kwep')
                vship = event_details.get('vship')
                dtype = event_details.get('dtype')

                # Do NOT include any direction information.
                # Remove the raw direction vector keys if they are present.
                for vec_key in ['dirvecx', 'dirvecy', 'dirvecz']:
                    event_details.pop(vec_key, None)

                # Add only a timestamp to the event details
                event_details['timestamp'] = datetime.now().strftime('%H:%M:%S')

                # Prepare the toast message with relevant event details
                toast_message = {
                    'title': '',
                    'details': f"🔫 Weapon: {kwep}\n🚀 Ship: {vship}\n💥 Damage: {dtype}"
                }

                # Determine if the names are designated as NPC:
                # Any name containing "NPC" or starting with "PU_" is treated as an NPC.
                vname_is_npc = ('NPC' in vname) or vname.startswith("PU_")
                kname_is_npc = ('NPC' in kname) or kname.startswith("PU_")

                if vname == kname:
                    self.logger.log_event(f"{vname} committed suicide using {kwep}", event_details)
                    toast_message['title'] = f"💀 {vname} committed suicide 🔫"
                    self.toast_manager.show_death_toast(toast_message, 'suicide')
                elif vname_is_npc or kname_is_npc:
                    if vname_is_npc:
                        self.logger.log_event(f"NPC killed by {kname} using {kwep}", event_details)
                        toast_message['title'] = f"🤖 NPC eliminated by {kname} ⚔️"
                    else:
                        self.logger.log_event(f"{vname} killed by NPC using {kwep}", event_details)
                        toast_message['title'] = f"🤖 {vname} eliminated by NPC ⚔️"
                    self.toast_manager.show_death_toast(toast_message, 'npc')
                elif vname == self.player_name:
                    self.logger.log_event(f"You were killed by {kname} using {kwep}", event_details)
                    toast_message['title'] = f"☠️ You were eliminated by {kname} ⚰️"
                    self.toast_manager.show_death_toast(toast_message, 'death')
                elif kname == self.player_name:
                    self.logger.log_event(f"You killed {vname} using {kwep}", event_details)
                    toast_message['title'] = f"🎯 You eliminated {vname} ✨"
                    self.toast_manager.show_death_toast(toast_message, 'kill')

                    # Track killstreak notifications
                    self.kill_counts[self.player_name] = self.kill_counts.get(self.player_name, 0) + 1
                    streak = self.kill_counts[self.player_name]
                    if streak > 1:
                        self.toast_manager.show_killstreak_toast({
                            'title': f"🔥 KILLSTREAK: {streak} 🏆",
                            'details': "Keep it up! 🌟"
                        })
                else:
                    self.logger.log_event(f"{vname} was killed by {kname} using {kwep}", event_details)
                    toast_message['title'] = f"⚔️ {vname} eliminated by {kname} 🎯"
                    self.toast_manager.show_death_toast(toast_message, 'info')

                # Append the event details to the main window’s kill history
                self.main_window.add_kill_event(event_details)

        except Exception as e:
            self.logger.log_error(f"Error processing line: {str(e)}")
            import traceback
            self.logger.log_error(traceback.format_exc())