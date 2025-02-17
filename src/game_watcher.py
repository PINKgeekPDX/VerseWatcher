import os
import re
from PyQt5.QtCore import QTimer
from datetime import datetime


class GameLogWatcher:
    def __init__(self, game_path, player_name, logger, toast_manager, main_window):
        try:
            self.game_path = game_path
            self.log_file = os.path.join(game_path, "Game.log")
            self.player_name = player_name
            self.logger = logger
            self.toast_manager = toast_manager
            self.main_window = main_window  # Store reference to main window
            self.observer = None
            self.event_handler = None
            self.last_position = 0
            self.kill_counts = {}  # Track kills for killstreak notifications
            self.timer = QTimer()
            self.timer.timeout.connect(self.check_file)

            # Death event pattern - using the known working pattern
            self.death_pattern = re.compile(
                r"^(?P<timestamp>\S+)\s+\[Notice\]\s+<Actor Death> CActor::Kill:\s+"
                r"\'(?P<vname>[^\']+)\'\s+\[\d+\]\s+in zone\s+\'(?P<vship>[^\']+)\'\s+"
                r"killed by\s+\'(?P<kname>[^\']+)\'\s+\[\d+\]\s+using\s+\'(?P<kwep>[^\']+)\'\s+"
                r"\[[^\]]*\]\s+with damage type\s+\'(?P<dtype>[^\']+)\'\s+from direction x:\s*"
                r"(?P<dirvecx>[^,]+),\s*y:\s*(?P<dirvecy>[^,]+),\s*z:\s*(?P<dirvecz>[^\s]+)"
                r"\s+\[Team_ActorTech\]\[Actor\]$"
            )

            self.logger.debug(f"GameLogWatcher initialized with game_path: {game_path}")
            self.logger.debug(f"Looking for log file at: {self.log_file}")

            # Load last position from file
            self.last_position_file = os.path.join(game_path, "last_position.txt")
            if os.path.exists(self.last_position_file):
                try:
                    with open(self.last_position_file, "r") as f:
                        self.last_position = int(f.read())
                    self.logger.info(
                        f"Loaded last position from file: {self.last_position}"
                    )
                except Exception as e:
                    self.logger.error(f"Error loading last position: {str(e)}")
                    self.last_position = 0
            else:
                self.last_position = 0

        except Exception as e:
            self.logger.error(f"Error initializing GameLogWatcher: {str(e)}")
            import traceback

            self.logger.error(traceback.format_exc())
            raise

    def check_file(self):
        """Check for new lines in the log file and process all new events"""
        try:
            if not os.path.exists(self.log_file):
                return

            current_size = os.path.getsize(self.log_file)

            # Only process if there's new content
            if current_size > self.last_position:
                with open(self.log_file, "rb") as f:
                    f.seek(self.last_position)
                    new_data = f.read()
                    self.last_position = f.tell()

                    try:
                        # Decode and split new data into lines
                        new_lines = new_data.decode("utf-8").splitlines()
                        # Process each new line immediately
                        for line in new_lines:
                            if line.strip():  # Skip empty lines
                                self.process_line(line)
                    except UnicodeDecodeError as e:
                        self.logger.error(f"Decode error: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in check_file: {str(e)}")
            import traceback

            self.logger.error(traceback.format_exc())

    def start(self):
        """Start watching the game log file"""
        try:
            # Verify log file exists
            if not os.path.exists(self.log_file):
                self.logger.error(f"Log file not found: {self.log_file}")
                self.toast_manager.show_error_toast(
                    f"❌ Game.log not found at: {self.log_file} ⚠️"
                )
                return False

            # Set initial position to end of file - we ONLY want new events
            self.last_position = os.path.getsize(self.log_file)
            self.logger.info(
                f"Starting to watch ONLY new events from position {self.last_position}"
            )

            # Start polling timer - check frequently for real-time response
            self.timer.start(
                50
            )  # Check every 50ms for more responsive real-time monitoring

            # Show startup success toast
            self.toast_manager.show_info_toast(
                "🎮 Started watching for new game events ✨"
            )

            return True

        except Exception as e:
            error_msg = f"Failed to start watching: {str(e)}"
            self.logger.error(error_msg)
            self.toast_manager.show_error_toast(f"⚠️ {error_msg} ❌")
            import traceback

            self.logger.error(traceback.format_exc())
            return False

    def stop(self):
        """Stop watching the game log file"""
        try:
            self.timer.stop()
        except Exception as e:
            self.logger.error(f"Error stopping watcher: {str(e)}")
            import traceback

            self.logger.error(traceback.format_exc())

    def process_line(self, line):
        """Process a single line from the log file"""
        try:
            # Death event
            death_match = self.death_pattern.match(line)
            if death_match:
                event_details = death_match.groupdict()
                vname = event_details["vname"]
                kname = event_details["kname"]
                kwep = event_details["kwep"]
                vship = event_details["vship"]
                dtype = event_details["dtype"]

                # Format direction vector
                try:
                    x = float(event_details["dirvecx"])
                    y = float(event_details["dirvecy"])
                    z = float(event_details["dirvecz"])
                    direction = f"x:{x:.1f}, y:{y:.1f}, z:{z:.1f}"
                except (ValueError, TypeError):
                    direction = f"x:{event_details['dirvecx']}, y:{event_details['dirvecy']}, z:{event_details['dirvecz']}"

                # Add timestamp to event details
                event_details["timestamp"] = datetime.now().strftime("%H:%M:%S")
                event_details["direction"] = direction

                # Create toast message
                toast_message = {
                    "title": "",
                    "details": f"🔫 Weapon: {kwep}\n🚀 Ship: {vship}\n💥 Damage: {dtype}",
                }

                # Determine event type for logging and toast
                if vname == kname:
                    self.logger.info(f"{vname} committed suicide using {kwep}")
                    toast_message["title"] = f"💀 {vname} committed suicide 🔫"
                    self.toast_manager.show_death_toast(toast_message, "suicide")
                elif "NPC" in vname or "NPC" in kname:
                    if "NPC" in vname:
                        self.logger.info(f"NPC killed by {kname} using {kwep}")
                        toast_message["title"] = f"🤖 NPC eliminated by {kname} ⚔️"
                    else:
                        self.logger.info(f"{vname} killed by NPC using {kwep}")
                        toast_message["title"] = f"🤖 {vname} eliminated by NPC ⚔️"
                    self.toast_manager.show_death_toast(toast_message, "npc")
                elif vname == self.player_name:
                    self.logger.info(f"You were killed by {kname} using {kwep}")
                    toast_message["title"] = f"☠️ You were eliminated by {kname} ⚰️"
                    self.toast_manager.show_death_toast(toast_message, "death")
                elif kname == self.player_name:
                    self.logger.info(f"You killed {vname} using {kwep}")
                    toast_message["title"] = f"🎯 You eliminated {vname} ✨"
                    self.toast_manager.show_death_toast(toast_message, "kill")

                    # Track killstreak
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
                    self.logger.info(f"{vname} was killed by {kname} using {kwep}")
                    toast_message["title"] = f"⚔️ {vname} eliminated by {kname} 🎯"
                    self.toast_manager.show_death_toast(toast_message, "info")

                # Add to main window history
                self.main_window.add_kill_event(event_details)

        except Exception as e:
            self.logger.error(f"Error processing line: {str(e)}")
            import traceback

            self.logger.error(traceback.format_exc())
