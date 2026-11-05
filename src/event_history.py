from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTreeWidget


class EventHistory:
    """Encapsulates event persistence and export logic for the app."""

    def __init__(self, app_dir: str, logger: Optional[Any] = None):
        self.app_dir = app_dir
        self.logger = logger
        self.session_history: Dict[str, List[Dict[str, Any]]] = {"kills": []}

    def clear(self):
        self.session_history = {"kills": []}

    def record(self, event_details: Dict[str, Any]) -> Dict[str, Any]:
        if not event_details:
            return {}

        record = {
            "timestamp": event_details.get("timestamp", datetime.now().strftime("%H:%M:%S")),
            "victim": event_details.get("vname", "Unknown"),
            "killer": event_details.get("kname", "Unknown"),
            "weapon": event_details.get("kwep", "Unknown"),
            "ship": event_details.get("vship", "Unknown"),
            "damage_type": event_details.get("dtype", "Unknown"),
            "datetime": datetime.now().isoformat(),
        }
        self.session_history.setdefault("kills", []).append(record)
        return record

    def export_tree(self, events_tree: Any, file_path: str):
        if not events_tree or events_tree.topLevelItemCount() == 0:
            return False

        with open(file_path, "w", encoding="utf-8") as handle:
            handle.write("VERSEWATCHER - EVENT EXPORT\n")
            handle.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            handle.write("=" * 50 + "\n\n")

            def write_item(item, level=0):
                indent = "  " * level
                if item.text(0):
                    handle.write(f"{indent}[{item.text(0)}] {item.text(1)}\n")
                else:
                    handle.write(f"{indent}• {item.text(1)}\n")

                for index in range(item.childCount()):
                    write_item(item.child(index), level + 1)

            for index in range(events_tree.topLevelItemCount()):
                write_item(events_tree.topLevelItem(index))
                handle.write("\n")

        return True

    def export_path(self, directory: str, default_filename: str) -> str:
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, default_filename)
