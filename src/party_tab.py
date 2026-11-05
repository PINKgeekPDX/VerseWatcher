from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from i18n import T


def build_party_tab(window):
    try:
        party_tab = QWidget()
        layout = QVBoxLayout(party_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_label = QLabel(T("PARTY_MEMBER_TRACKING"))
        header_label.setStyleSheet("""
            color: #00A6ED;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 3px;
            margin-bottom: 10px;
        """)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        description = QLabel(T("PARTY_MEMBER_DESCRIPTION"))
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #90CAF9;
            font-size: 13px;
            margin-bottom: 15px;
            background: rgba(0, 60, 90, 0.3);
            border-radius: 4px;
            padding: 8px;
            border-left: 2px solid #00A6ED;
        """)
        layout.addWidget(description)

        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #00A6ED;
                height: 2px;
            }
            QSplitter::handle:hover {
                background-color: #40C4FF;
            }
        """)

        party_section = QWidget()
        party_layout = QVBoxLayout(party_section)
        party_layout.setContentsMargins(0, 0, 0, 0)

        party_header = QLabel(T("PARTY_MEMBERS"))
        party_header.setStyleSheet("""
            color: #00A6ED;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 2px;
            padding-bottom: 5px;
            border-bottom: 1px solid #00A6ED;
        """)
        party_layout.addWidget(party_header)

        main_list_layout = QHBoxLayout()

        window.party_members_list = QListWidget()
        window.party_members_list.setObjectName("partyMembersList")
        window.party_members_list.setStyleSheet("""
            #partyMembersList {
                background-color: rgba(0, 15, 25, 0.95);
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                padding: 5px;
                selection-background-color: rgba(0, 166, 237, 0.4);
            }
            #partyMembersList::item {
                border-bottom: 1px solid rgba(0, 166, 237, 0.1);
                padding: 6px 8px;
            }
            #partyMembersList::item:hover {
                background: rgba(0, 166, 237, 0.1);
            }
            #partyMembersList::item:selected {
                background: rgba(0, 166, 237, 0.2);
                border-left: 2px solid #00A6ED;
            }
        """)
        window.party_members_list.setContextMenuPolicy(Qt.CustomContextMenu)
        window.party_members_list.customContextMenuRequested.connect(window.show_party_context_menu)
        main_list_layout.addWidget(window.party_members_list, 4)

        controls_layout = QVBoxLayout()

        window.party_member_input = QLineEdit()
        window.party_member_input.setPlaceholderText(T("ENTER_PLAYER_NAME"))
        window.party_member_input.setStyleSheet("""
            background-color: rgba(0, 15, 25, 0.95);
            border: 1px solid #00A6ED;
            border-radius: 3px;
            color: #E0E0E0;
            padding: 8px;
            font-size: 13px;
        """)
        controls_layout.addWidget(window.party_member_input)

        add_button = QPushButton(f"➕ {T('ADD')}")
        add_button.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #003D5C,
                stop:1 #0077AA
            );
            border: 1px solid #00A6ED;
            border-radius: 3px;
            color: white;
            padding: 2px 4px;
            font-size: 13px;
            font-weight: bold;
        """)
        add_button.clicked.connect(window.add_party_member)
        controls_layout.addWidget(add_button)

        remove_button = QPushButton(f"🗑️ {T('REMOVE')}")
        remove_button.setObjectName("removeButton")
        remove_button.setStyleSheet("""
            QPushButton#removeButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #C62828,
                    stop:1 #D32F2F
                );
                border: 1px solid #F44336;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        remove_button.clicked.connect(window.remove_party_member)
        controls_layout.addWidget(remove_button)

        clear_button = QPushButton(f"💥 {T('CLEAR_ALL')}")
        clear_button.setObjectName("clearPartyButton")
        clear_button.setStyleSheet("""
            QPushButton#clearPartyButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7B1FA2,
                    stop:1 #9C27B0
                );
                border: 1px solid #AB47BC;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        clear_button.clicked.connect(window.clear_party_members)
        controls_layout.addWidget(clear_button)
        controls_layout.addStretch()

        main_list_layout.addLayout(controls_layout, 1)
        party_layout.addLayout(main_list_layout)

        events_section = QWidget()
        events_layout = QVBoxLayout(events_section)
        events_header = QLabel(T("PARTY_EVENTS_HEADER"))
        events_header.setStyleSheet("""
            color: #00A6ED;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 2px;
            padding-bottom: 5px;
            border-bottom: 1px solid #00A6ED;
        """)
        events_layout.addWidget(events_header)

        window.party_events_tree = QTreeWidget()
        window.party_events_tree.setObjectName("partyEventsTree")
        window.party_events_tree.setColumnCount(3)
        window.party_events_tree.setHeaderLabels([T("TIME"), T("MEMBER"), T("EVENT")])
        window.party_events_tree.setAlternatingRowColors(True)
        window.party_events_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        window.party_events_tree.setStyleSheet("""
            #partyEventsTree {
                background-color: rgba(0, 15, 25, 0.95);
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: #E0E0E0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                padding: 5px;
                selection-background-color: rgba(0, 166, 237, 0.4);
            }
            #partyEventsTree::item {
                border-bottom: 1px solid rgba(0, 166, 237, 0.1);
                padding: 4px 8px;
            }
            #partyEventsTree QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                color: white;
                padding: 5px;
                border: 1px solid #00A6ED;
                font-weight: bold;
            }
        """)
        window.party_events_tree.setUniformRowHeights(True)
        window.party_events_tree.header().resizeSection(0, 140)
        window.party_events_tree.header().resizeSection(1, 160)
        window.party_events_tree.header().resizeSection(2, 300)
        events_layout.addWidget(window.party_events_tree)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        export_events_button = QPushButton(f"📤 {T('EXPORT_EVENTS')}")
        export_events_button.setObjectName("exportPartyEventsButton")
        export_events_button.setStyleSheet("""
            QPushButton#exportPartyEventsButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565C0,
                    stop:1 #1976D2
                );
                border: 1px solid #2196F3;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        export_events_button.clicked.connect(window.export_party_events)

        clear_events_button = QPushButton(f"🗑️ {T('CLEAR_EVENTS')}")
        clear_events_button.setObjectName("clearEventsButton")
        clear_events_button.setStyleSheet("""
            QPushButton#clearEventsButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #003D5C,
                    stop:1 #0077AA
                );
                border: 1px solid #00A6ED;
                border-radius: 3px;
                color: white;
                padding: 2px 4px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        clear_events_button.clicked.connect(window.clear_party_events)

        buttons_layout.addWidget(export_events_button)
        buttons_layout.addWidget(clear_events_button)
        events_layout.addLayout(buttons_layout)

        splitter.addWidget(party_section)
        splitter.addWidget(events_section)
        splitter.setSizes([200, 300])
        layout.addWidget(splitter, 1)

        window.party_footer = QLabel(T("PARTY_FOOTER_TEMPLATE", member_count=0, event_count=0))
        window.party_footer.setObjectName("partyFooter")
        window.party_footer.setStyleSheet("""
            #partyFooter {
                color: #90CAF9;
                font-size: 12px;
                font-style: italic;
                padding: 5px;
                text-align: center;
                border-top: 1px solid rgba(0, 166, 237, 0.3);
                margin-top: 5px;
            }
        """)
        layout.addWidget(window.party_footer)

        if not hasattr(window, 'party_members'):
            window.party_members = []
        window.update_party_members_list()
        window.setup_party_events_tree_context_menu()
        return party_tab
    except Exception as exc:
        if hasattr(window, 'logger') and window.logger:
            window.logger.log_error(f"Error creating party tab: {exc}")
            import traceback
            window.logger.log_error(traceback.format_exc())
        fallback = QWidget()
        fallback_layout = QVBoxLayout(fallback)
        label = QLabel(T("ERROR_LOADING_PARTY_TAB"))
        label.setStyleSheet("color: red; font-weight: bold;")
        fallback_layout.addWidget(label)
        return fallback
