from __future__ import annotations

import os

from PyQt5.QtCore import Qt

from i18n import TRANSLATIONS


def _combo_value(combo, default):
    """Return a selector's stable value, falling back for legacy widgets."""
    if combo is None:
        return default
    value = combo.currentData()
    return value if value is not None else (combo.currentText() or default)


def _set_combo_value(combo, value):
    """Select an option using canonical values or labels persisted by older versions."""
    value = str(value)
    index = combo.findData(value)
    if index < 0:
        index = combo.findText(value, Qt.MatchFixedString)

    if index < 0:
        try:
            seconds = str(int(value.split()[0]))
        except (ValueError, IndexError):
            seconds = None
        if seconds is not None:
            index = combo.findData(seconds)

    if index < 0:
        for item_index in range(combo.count()):
            translation_key = combo.itemData(item_index, Qt.UserRole + 1)
            if translation_key and any(
                translations.get(translation_key) == value
                for translations in TRANSLATIONS.values()
            ):
                index = item_index
                break

    if index >= 0:
        combo.setCurrentIndex(index)


def build_settings_snapshot(window):
    """Collect the current window state into a serializable settings payload."""
    return {
        "game_path": window.path_input.text() if hasattr(window, 'path_input') and window.path_input is not None else "",
        "player_name": window.name_input.text() if hasattr(window, 'name_input') and window.name_input is not None else "",
        "stay_on_top": bool(window.windowFlags() & Qt.WindowStaysOnTopHint),
        "event_filters": {
            "self_events": window.self_events_check.isChecked() if hasattr(window, 'self_events_check') and window.self_events_check is not None else True,
            "other_events": window.other_events_check.isChecked() if hasattr(window, 'other_events_check') and window.other_events_check is not None else True,
            "npc_events": window.npc_events_check.isChecked() if hasattr(window, 'npc_events_check') and window.npc_events_check is not None else True,
            "suicide_events": window.suicide_events_check.isChecked() if hasattr(window, 'suicide_events_check') and window.suicide_events_check is not None else True,
            "party_events": window.party_events_check.isChecked() if hasattr(window, 'party_events_check') and window.party_events_check is not None else True,
        },
        "toast_config": {
            "position": _combo_value(getattr(window, 'toast_position_combo', None), "Bottom Right"),
            "size": _combo_value(getattr(window, 'toast_size_combo', None), "Medium"),
            "duration": _combo_value(getattr(window, 'toast_duration_combo', None), "5"),
            "max_stack": window.toast_max_stack_combo.currentText() if hasattr(window, 'toast_max_stack_combo') and window.toast_max_stack_combo is not None else "5",
        },
        "party_toast_config": {
            "position": _combo_value(
                getattr(window, 'party_toast_position_combo', None), "Top Right"
            ),
            "size": _combo_value(getattr(window, 'party_toast_size_combo', None), "Medium"),
            "duration": _combo_value(getattr(window, 'party_toast_duration_combo', None), "5"),
            "max_stack": window.party_toast_max_stack_combo.currentText() if hasattr(window, 'party_toast_max_stack_combo') and window.party_toast_max_stack_combo is not None else "5",
        },
        "party_members": getattr(window, 'party_members', []),
        "window_geometry": {
            "x": window.x(),
            "y": window.y(),
            "width": window.width(),
            "height": window.height(),
        },
    }


def apply_loaded_settings(window, settings):
    """Populate UI widgets from a loaded settings payload."""
    if hasattr(window, 'path_input') and "game_path" in settings:
        window.path_input.setText(settings["game_path"])

    if hasattr(window, 'name_input') and "player_name" in settings:
        window.name_input.setText(settings["player_name"])
        window.player_name = settings["player_name"]

    filters = settings.get("event_filters", {})
    if hasattr(window, 'self_events_check') and "self_events" in filters:
        window.self_events_check.setChecked(filters["self_events"])
    if hasattr(window, 'other_events_check') and "other_events" in filters:
        window.other_events_check.setChecked(filters["other_events"])
    if hasattr(window, 'npc_events_check') and "npc_events" in filters:
        window.npc_events_check.setChecked(filters["npc_events"])
    if hasattr(window, 'suicide_events_check') and "suicide_events" in filters:
        window.suicide_events_check.setChecked(filters["suicide_events"])
    if hasattr(window, 'party_events_check') and "party_events" in filters:
        window.party_events_check.setChecked(filters["party_events"])

    toast_config = settings.get("toast_config", {})
    if hasattr(window, 'toast_position_combo') and "position" in toast_config:
        _set_combo_value(window.toast_position_combo, toast_config["position"])
    if hasattr(window, 'toast_size_combo') and "size" in toast_config:
        _set_combo_value(window.toast_size_combo, toast_config["size"])
    if hasattr(window, 'toast_duration_combo') and "duration" in toast_config:
        _set_combo_value(window.toast_duration_combo, toast_config["duration"])
    if hasattr(window, 'toast_max_stack_combo') and "max_stack" in toast_config:
        window.toast_max_stack_combo.setCurrentText(str(toast_config["max_stack"]))

    party_toast_config = settings.get("party_toast_config", {})
    if hasattr(window, 'party_toast_position_combo') and "position" in party_toast_config:
        _set_combo_value(window.party_toast_position_combo, party_toast_config["position"])
    if hasattr(window, 'party_toast_size_combo') and "size" in party_toast_config:
        _set_combo_value(window.party_toast_size_combo, party_toast_config["size"])
    if hasattr(window, 'party_toast_duration_combo') and "duration" in party_toast_config:
        _set_combo_value(window.party_toast_duration_combo, party_toast_config["duration"])
    if hasattr(window, 'party_toast_max_stack_combo') and "max_stack" in party_toast_config:
        window.party_toast_max_stack_combo.setCurrentText(str(party_toast_config["max_stack"]))

    if hasattr(window, 'validate_toast_positions'):
        window.validate_toast_positions()

    if "party_members" in settings:
        members = settings["party_members"]
        if members and isinstance(members[0], str):
            window.party_members = [{'name': name, 'muted': False} for name in members]
            if getattr(window, 'logger', None):
                window.logger.log_info("Migrated party members from old format to new format")
        else:
            window.party_members = members
        if hasattr(window, 'update_party_members_list'):
            window.update_party_members_list()

    if "stay_on_top" in settings:
        current_flags = window.windowFlags()
        if bool(settings["stay_on_top"]):
            window.setWindowFlags(current_flags | Qt.WindowStaysOnTopHint)
        else:
            window.setWindowFlags(current_flags & ~Qt.WindowStaysOnTopHint)
        window.show()


def save_app_settings(window):
    """Persist the current UI state using the app configuration abstraction."""
    try:
        window.config.ensure_dirs()
        settings = build_settings_snapshot(window)
        window.config.save_settings(settings)

        if hasattr(window, 'toast_manager') and window.toast_manager:
            try:
                duration_text = settings["toast_config"]["duration"]
                duration_seconds = int(duration_text.split()[0])
                duration_ms = duration_seconds * 1000
                window.toast_manager.update_config(
                    position=settings["toast_config"]["position"],
                    size=settings["toast_config"]["size"],
                    duration=duration_ms,
                    max_stack=int(settings["toast_config"]["max_stack"]),
                )

                party_duration_text = settings["party_toast_config"]["duration"]
                party_duration_seconds = int(party_duration_text.split()[0])
                party_duration_ms = party_duration_seconds * 1000
                window.toast_manager.update_party_config(
                    position=settings["party_toast_config"]["position"],
                    size=settings["party_toast_config"]["size"],
                    duration=party_duration_ms,
                    max_stack=int(settings["party_toast_config"]["max_stack"]),
                )
            except Exception as exc:
                if window.logger:
                    window.logger.log_error(f"Error updating toast manager config: {str(exc)}")

        if hasattr(window, 'name_input') and window.name_input and window.name_input.text():
            window.player_name = window.name_input.text()

        if window.logger:
            window.logger.log_info("Settings saved successfully")
        return True
    except Exception as exc:
        if getattr(window, 'logger', None):
            window.logger.log_error(f"Error saving settings: {str(exc)}")
        import traceback
        window.logger.log_error(traceback.format_exc())
        return False


def load_app_settings(window):
    """Load persisted settings into the current UI window."""
    settings_path = window.config.settings_file
    if not os.path.exists(settings_path):
        if getattr(window, 'logger', None):
            window.logger.log_info("No settings file found, using defaults")
        return False

    try:
        settings = window.config.load_settings()
        if not settings:
            if getattr(window, 'logger', None):
                window.logger.log_info("Settings file is empty, using defaults")
            return False

        apply_loaded_settings(window, settings)
        return True
    except Exception as exc:
        if getattr(window, 'logger', None):
            window.logger.log_error(
                f"Error loading settings from {settings_path}: {exc}"
            )
        return False
