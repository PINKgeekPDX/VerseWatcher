import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app_config import AppConfig  # noqa: E402
from settings_service import load_app_settings  # noqa: E402


class AppConfigTests(unittest.TestCase):
    def test_missing_json_file_returns_default(self):
        with tempfile.TemporaryDirectory() as app_dir:
            config = AppConfig(app_dir)
            self.assertEqual(
                config.load_json(str(Path(app_dir) / "missing.json"), {}),
                {},
            )

    def test_invalid_json_is_not_treated_as_missing(self):
        with tempfile.TemporaryDirectory() as app_dir:
            config = AppConfig(app_dir)
            Path(config.settings_file).write_text("{invalid", encoding="utf-8")

            with self.assertRaises(json.JSONDecodeError):
                config.load_settings()

    def test_settings_service_logs_corrupt_file_path(self):
        with tempfile.TemporaryDirectory() as app_dir:
            config = AppConfig(app_dir)
            Path(config.settings_file).write_text("{invalid", encoding="utf-8")
            errors = []
            logger = SimpleNamespace(
                log_info=lambda message: None,
                log_error=errors.append,
            )
            window = SimpleNamespace(config=config, logger=logger)

            self.assertFalse(load_app_settings(window))
            self.assertTrue(any(config.settings_file in error for error in errors))
            self.assertTrue(any("Expecting property name" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
