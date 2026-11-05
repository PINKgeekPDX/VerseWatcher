import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from watch_controller import start_monitoring, validate_monitoring_inputs


class DummyLogger:
    def log_error(self, *args, **kwargs):
        pass

    def log_info(self, *args, **kwargs):
        pass


class DummyInput:
    def __init__(self, value=""):
        self._value = value

    def text(self):
        return self._value


class DummyWindow:
    def __init__(self, game_path="", player_name=""):
        self.path_input = DummyInput(game_path)
        self.name_input = DummyInput(player_name)
        self.logger = DummyLogger()
        self.watcher = None
        self.is_watching = False
        self.tray_icon = None
        self.start_button = None
        self.status_label = None
        self.console_footer = None
        self.monitoring_tray_action = None
        self.icon_green = None
        self.icon_red = None
        self.icon_yellow = None


class WatchControllerTests(unittest.TestCase):
    def test_validate_monitoring_inputs_requires_game_path(self):
        window = DummyWindow(game_path="", player_name="Player")

        result = validate_monitoring_inputs(window)

        self.assertEqual(result[0], None)
        self.assertEqual(result[1], None)
        self.assertEqual(result[2], None)
        self.assertIn("Game installation directory not specified", result[3])

    def test_validate_monitoring_inputs_requires_player_name(self):
        window = DummyWindow(game_path="C:/Games/StarCitizen", player_name="")

        result = validate_monitoring_inputs(window)

        self.assertEqual(result[0], None)
        self.assertEqual(result[1], None)
        self.assertEqual(result[2], None)
        self.assertIn("Player name not specified", result[3])

    def test_validate_monitoring_inputs_detects_missing_game_log(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            window = DummyWindow(game_path=temp_dir, player_name="Player")

            result = validate_monitoring_inputs(window)

            self.assertEqual(result[0], temp_dir)
            self.assertEqual(result[1], "Player")
            self.assertTrue(result[2].endswith(os.path.join("Game.log")))
            self.assertIn("Game.log not found at:", result[3])

    def test_start_monitoring_fails_without_inputs(self):
        window = DummyWindow(game_path="", player_name="")

        self.assertFalse(start_monitoring(window))
        self.assertFalse(window.is_watching)


if __name__ == "__main__":
    unittest.main()
