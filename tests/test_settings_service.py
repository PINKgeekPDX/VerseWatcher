import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit  # noqa: E402

from i18n import TRANSLATIONS  # noqa: E402
from settings_service import apply_loaded_settings, build_settings_snapshot  # noqa: E402
from settings_tab import build_settings_tab  # noqa: E402


class SettingsServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def _localized_combo(self, option_keys, language="es"):
        combo = QComboBox()
        for key, canonical in option_keys:
            index = combo.count()
            combo.addItem(TRANSLATIONS[language][key], canonical)
            combo.setItemData(index, key, Qt.UserRole + 1)
        return combo

    def test_snapshot_uses_canonical_selector_values(self):
        position_options = [
            ("TOP_LEFT", "Top Left"),
            ("TOP_RIGHT", "Top Right"),
            ("BOTTOM_LEFT", "Bottom Left"),
            ("BOTTOM_RIGHT", "Bottom Right"),
            ("LEFT_MIDDLE", "Left Middle"),
            ("RIGHT_MIDDLE", "Right Middle"),
        ]
        size_options = [
            ("VERY_SMALL", "Very Small"),
            ("SMALL", "Small"),
            ("MEDIUM", "Medium"),
            ("LARGE", "Large"),
            ("VERY_LARGE", "Very Large"),
        ]
        window = SimpleNamespace(
            path_input=QLineEdit(),
            name_input=QLineEdit(),
            windowFlags=lambda: Qt.WindowStaysOnTopHint,
            self_events_check=QCheckBox(),
            other_events_check=QCheckBox(),
            npc_events_check=QCheckBox(),
            suicide_events_check=QCheckBox(),
            party_events_check=QCheckBox(),
            toast_position_combo=self._localized_combo(position_options),
            toast_size_combo=self._localized_combo(size_options),
            toast_duration_combo=QComboBox(),
            toast_max_stack_combo=QComboBox(),
            party_toast_position_combo=self._localized_combo(position_options),
            party_toast_size_combo=self._localized_combo(size_options),
            party_toast_duration_combo=QComboBox(),
            party_toast_max_stack_combo=QComboBox(),
            party_members=[],
            x=lambda: 0,
            y=lambda: 0,
            width=lambda: 100,
            height=lambda: 100,
        )
        for combo in (window.toast_duration_combo, window.party_toast_duration_combo):
            for seconds in (2, 3, 5, 8, 10):
                combo.addItem(f"{seconds} segundos", str(seconds))
        for combo in (window.toast_max_stack_combo, window.party_toast_max_stack_combo):
            combo.addItems([str(value) for value in range(1, 11)])

        window.toast_position_combo.setCurrentIndex(
            window.toast_position_combo.findData("Bottom Left")
        )
        window.toast_size_combo.setCurrentIndex(
            window.toast_size_combo.findData("Large")
        )
        window.toast_duration_combo.setCurrentIndex(
            window.toast_duration_combo.findData("8")
        )

        snapshot = build_settings_snapshot(window)

        self.assertEqual(snapshot["toast_config"]["position"], "Bottom Left")
        self.assertEqual(snapshot["toast_config"]["size"], "Large")
        self.assertEqual(snapshot["toast_config"]["duration"], "8")

    def test_load_migrates_translated_legacy_selector_values(self):
        position_options = [
            ("TOP_LEFT", "Top Left"),
            ("TOP_RIGHT", "Top Right"),
            ("BOTTOM_LEFT", "Bottom Left"),
            ("BOTTOM_RIGHT", "Bottom Right"),
            ("LEFT_MIDDLE", "Left Middle"),
            ("RIGHT_MIDDLE", "Right Middle"),
        ]
        size_options = [
            ("VERY_SMALL", "Very Small"),
            ("SMALL", "Small"),
            ("MEDIUM", "Medium"),
            ("LARGE", "Large"),
            ("VERY_LARGE", "Very Large"),
        ]
        window = SimpleNamespace(
            toast_position_combo=self._localized_combo(position_options, "en"),
            toast_size_combo=self._localized_combo(size_options, "en"),
            toast_duration_combo=QComboBox(),
            party_toast_position_combo=self._localized_combo(position_options, "en"),
            party_toast_size_combo=self._localized_combo(size_options, "en"),
            party_toast_duration_combo=QComboBox(),
        )
        for combo in (window.toast_duration_combo, window.party_toast_duration_combo):
            for seconds in (2, 3, 5, 8, 10):
                combo.addItem(
                    f"{seconds} {TRANSLATIONS['en']['SECONDS']}", str(seconds)
                )

        apply_loaded_settings(
            window,
            {
                "toast_config": {
                    "position": "Abajo derecha",
                    "size": "Grande",
                    "duration": "8 segundos",
                },
                "party_toast_config": {
                    "position": "Arriba izquierda",
                    "size": "Mediana",
                    "duration": "3 seconds",
                },
            },
        )

        self.assertEqual(window.toast_position_combo.currentData(), "Bottom Right")
        self.assertEqual(window.toast_size_combo.currentData(), "Large")
        self.assertEqual(window.toast_duration_combo.currentData(), "8")
        self.assertEqual(window.party_toast_position_combo.currentData(), "Top Left")
        self.assertEqual(window.party_toast_size_combo.currentData(), "Medium")
        self.assertEqual(window.party_toast_duration_combo.currentData(), "3")

    def test_settings_tab_displays_translations_with_canonical_data(self):
        window = SimpleNamespace(
            browse_game_directory=lambda: None,
            validate_toast_positions=lambda: None,
        )
        with patch.dict(os.environ, {"LANGUAGE": "es_ES"}):
            tab = build_settings_tab(window)

        self.assertEqual(window.toast_position_combo.currentText(), "Abajo derecha")
        self.assertEqual(window.toast_position_combo.currentData(), "Bottom Right")
        self.assertEqual(window.toast_size_combo.currentText(), "Mediana")
        self.assertEqual(window.toast_size_combo.currentData(), "Medium")
        self.assertEqual(window.toast_duration_combo.currentText(), "5 segundos")
        self.assertEqual(window.toast_duration_combo.currentData(), "5")
        self.assertIsNotNone(tab)


if __name__ == "__main__":
    unittest.main()
