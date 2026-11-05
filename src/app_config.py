import json
import os
from typing import Any, Dict, Optional


class AppConfig:
    """Centralizes app path and settings persistence."""

    def __init__(self, app_dir: Optional[str] = None):
        self.app_dir = app_dir or os.path.join(os.path.expanduser("~"), "Documents", "PINK", "VerseWatcher")
        self.settings_file = os.path.join(self.app_dir, "settings.json")
        self.history_dir = os.path.join(self.app_dir, "history")
        self.logs_dir = os.path.join(self.app_dir, "logs")
        self.ensure_dirs()

    def ensure_dirs(self):
        os.makedirs(self.app_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def load_json(self, path: str, default: Any = None) -> Any:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_json(self, path: str, payload: Any):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=4)

    def load_settings(self) -> Dict[str, Any]:
        return self.load_json(self.settings_file, {}) or {}

    def save_settings(self, data: Dict[str, Any]):
        self.save_json(self.settings_file, data)
