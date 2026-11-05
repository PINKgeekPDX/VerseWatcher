from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from i18n import T


def build_settings_tab(window):
    """Create the settings tab and wire it to the window state."""
    tab = QWidget()
    tab_layout = QVBoxLayout(tab)
    tab_layout.setContentsMargins(0, 0, 0, 0)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QScrollArea.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    tab_layout.addWidget(scroll_area)

    content = QWidget()
    scroll_area.setWidget(content)

    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(15, 15, 15, 15)
    content_layout.setSpacing(16)

    header_label = QLabel(T("SETTINGS"))
    header_label.setStyleSheet("""
        color: #00A6ED;
        font-size: 20px;
        font-weight: bold;
        letter-spacing: 3px;
        margin-bottom: 5px;
    """)
    content_layout.addWidget(header_label)

    general_group = QGroupBox(T("GENERAL_SETTINGS"))
    general_group.setObjectName("settingsGroup")
    general_group.setStyleSheet("""
        QGroupBox#settingsGroup {
            border: 1px solid #00A6ED;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
            font-weight: bold;
            color: #00A6ED;
        }
        QGroupBox#settingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    general_layout = QFormLayout(general_group)
    general_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
    general_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
    general_layout.setContentsMargins(15, 25, 15, 15)
    general_layout.setSpacing(15)

    game_path_label = QLabel(T("GAME_INSTALL_PATH"))
    game_path_label.setStyleSheet("font-weight: bold;")
    window.path_input = QLineEdit()
    window.path_input.setPlaceholderText(T("DEFAULT_GAME_PATH"))
    window.path_input.setStyleSheet("padding: 6px; min-width: 260px;")

    browse_button = QPushButton(T("BROWSE"))
    browse_button.clicked.connect(window.browse_game_directory)
    path_row = QHBoxLayout()
    path_row.addWidget(window.path_input)
    path_row.addWidget(browse_button)
    general_layout.addRow(game_path_label, path_row)

    player_name_label = QLabel(T("PLAYER_NAME"))
    player_name_label.setStyleSheet("font-weight: bold;")
    window.name_input = QLineEdit()
    window.name_input.setPlaceholderText(T("ENTER_YOUR_HANDLE"))
    window.name_input.setStyleSheet("padding: 6px; min-width: 260px;")
    general_layout.addRow(player_name_label, window.name_input)
    content_layout.addWidget(general_group)

    event_group = QGroupBox(T("EVENT_FILTERING"))
    event_group.setObjectName("settingsGroup")
    event_group.setStyleSheet("""
        QGroupBox#settingsGroup {
            border: 1px solid #00A6ED;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
            font-weight: bold;
            color: #00A6ED;
        }
        QGroupBox#settingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    event_layout = QVBoxLayout(event_group)
    event_layout.setContentsMargins(15, 25, 15, 15)
    event_layout.setSpacing(10)

    event_labels = [
        (T("SELF_EVENTS"), "self_events_check"),
        (T("OTHER_PLAYER_EVENTS"), "other_events_check"),
        (T("NPC_EVENTS"), "npc_events_check"),
        (T("SUICIDE_EVENTS"), "suicide_events_check"),
        (T("PARTY_EVENTS"), "party_events_check"),
    ]

    for label_text, attr_name in event_labels:
        checkbox = QCheckBox(label_text)
        checkbox.setChecked(True)
        setattr(window, attr_name, checkbox)
        event_layout.addWidget(checkbox)

    content_layout.addWidget(event_group)

    toast_group = QGroupBox(T("TOAST_NOTIFICATIONS"))
    toast_group.setObjectName("settingsGroup")
    toast_group.setStyleSheet("""
        QGroupBox#settingsGroup {
            border: 1px solid #00A6ED;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
            font-weight: bold;
            color: #00A6ED;
        }
        QGroupBox#settingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    toast_layout = QFormLayout(toast_group)
    toast_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
    toast_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
    toast_layout.setContentsMargins(15, 25, 15, 15)
    toast_layout.setSpacing(15)

    window.toast_position_combo = QComboBox()
    window.toast_position_combo.addItems([T("TOP_LEFT"), T("TOP_RIGHT"), T("BOTTOM_LEFT"), T("BOTTOM_RIGHT"), T("LEFT_MIDDLE"), T("RIGHT_MIDDLE")])
    window.toast_position_combo.setCurrentText(T("BOTTOM_RIGHT"))
    window.toast_position_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    window.toast_size_combo = QComboBox()
    window.toast_size_combo.addItems([T("VERY_SMALL"), T("SMALL"), T("MEDIUM"), T("LARGE"), T("VERY_LARGE")])
    window.toast_size_combo.setCurrentText(T("MEDIUM"))
    window.toast_size_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    window.toast_duration_combo = QComboBox()
    window.toast_duration_combo.addItems([f"2 {T('SECONDS')}", f"3 {T('SECONDS')}", f"5 {T('SECONDS')}", f"8 {T('SECONDS')}", f"10 {T('SECONDS')}"])
    window.toast_duration_combo.setCurrentText(f"5 {T('SECONDS')}")
    window.toast_duration_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    window.toast_max_stack_combo = QComboBox()
    window.toast_max_stack_combo.addItems([str(i) for i in range(1, 11)])
    window.toast_max_stack_combo.setCurrentText("5")
    window.toast_max_stack_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    toast_layout.addRow(QLabel(T("TOAST_POSITION")), window.toast_position_combo)
    toast_layout.addRow(QLabel(T("TOAST_SIZE")), window.toast_size_combo)
    toast_layout.addRow(QLabel(T("TOAST_DURATION")), window.toast_duration_combo)
    toast_layout.addRow(QLabel(T("MAX_TOAST_STACK")), window.toast_max_stack_combo)
    content_layout.addWidget(toast_group)

    party_toast_group = QGroupBox(T("PARTY_TOAST_NOTIFICATIONS"))
    party_toast_group.setObjectName("settingsGroup")
    party_toast_group.setStyleSheet("""
        QGroupBox#settingsGroup {
            border: 1px solid #00A6ED;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
            font-weight: bold;
            color: #00A6ED;
        }
        QGroupBox#settingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
    """)
    party_toast_layout = QFormLayout(party_toast_group)
    party_toast_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
    party_toast_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
    party_toast_layout.setContentsMargins(15, 25, 15, 15)
    party_toast_layout.setSpacing(15)

    window.party_toast_position_combo = QComboBox()
    window.party_toast_position_combo.addItems([T("TOP_LEFT"), T("TOP_RIGHT"), T("BOTTOM_LEFT"), T("BOTTOM_RIGHT"), T("LEFT_MIDDLE"), T("RIGHT_MIDDLE")])
    window.party_toast_position_combo.setCurrentText(T("TOP_RIGHT"))
    window.party_toast_position_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    window.party_toast_size_combo = QComboBox()
    window.party_toast_size_combo.addItems([T("VERY_SMALL"), T("SMALL"), T("MEDIUM"), T("LARGE"), T("VERY_LARGE")])
    window.party_toast_size_combo.setCurrentText(T("MEDIUM"))
    window.party_toast_size_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    window.party_toast_duration_combo = QComboBox()
    window.party_toast_duration_combo.addItems([f"2 {T('SECONDS')}", f"3 {T('SECONDS')}", f"5 {T('SECONDS')}", f"8 {T('SECONDS')}", f"10 {T('SECONDS')}"])
    window.party_toast_duration_combo.setCurrentText(f"5 {T('SECONDS')}")
    window.party_toast_duration_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    window.party_toast_max_stack_combo = QComboBox()
    window.party_toast_max_stack_combo.addItems([str(i) for i in range(1, 11)])
    window.party_toast_max_stack_combo.setCurrentText("5")
    window.party_toast_max_stack_combo.setStyleSheet("padding: 6px; min-width: 150px;")

    party_toast_layout.addRow(QLabel(T("PARTY_TOAST_POSITION")), window.party_toast_position_combo)
    party_toast_layout.addRow(QLabel(T("PARTY_TOAST_SIZE")), window.party_toast_size_combo)
    party_toast_layout.addRow(QLabel(T("PARTY_TOAST_DURATION")), window.party_toast_duration_combo)
    party_toast_layout.addRow(QLabel(T("PARTY_TOAST_MAX_STACK")), window.party_toast_max_stack_combo)
    content_layout.addWidget(party_toast_group)

    window.toast_position_combo.currentIndexChanged.connect(window.validate_toast_positions)
    window.party_toast_position_combo.currentIndexChanged.connect(window.validate_toast_positions)

    content_layout.addStretch()
    return tab
