from i18n import T


def apply_watch_ui_state(window, is_active, *, error_message=None):
    """Apply a consistent watch-state UI update across the main window."""
    window.is_watching = is_active

    status_label = getattr(window, "status_label", None)
    if status_label is not None:
        if is_active:
            status_label.setText(T("STATUS_ACTIVE"))
            status_label.setStyleSheet(
                "background-color: rgba(8, 41, 66, 0.7); color: #4CAF50; font-size: 12px; font-weight: bold; margin-right: 15px; padding: 4px 8px; border-radius: 3px;"
            )
        else:
            status_label.setText(T("STATUS_INACTIVE"))
            status_label.setStyleSheet(
                "background-color: rgba(8, 41, 66, 0.7); color: #F44336; font-size: 12px; font-weight: bold; margin-right: 15px; padding: 4px 8px; border-radius: 3px;"
            )

    start_button = getattr(window, "start_button", None)
    if start_button is not None:
        if is_active:
            start_button.setText(T("STOP"))
            start_button.setStyleSheet("""
                QPushButton#startButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00695C,
                        stop:1 #00897B
                    );
                    border: 1px solid #4CAF50;
                    border-radius: 3px;
                    color: white;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton#startButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00897B,
                        stop:1 #26A69A
                    );
                    border: 1px solid #81C784;
                }
            """)
        else:
            start_button.setText(T("START"))
            start_button.setStyleSheet("""
                QPushButton#startButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #C62828,
                        stop:1 #D32F2F
                    );
                    border: 1px solid #F44336;
                    border-radius: 3px;
                    color: white;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton#startButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #D32F2F,
                        stop:1 #E53935
                    );
                    border: 1px solid #EF5350;
                }
            """)

    console_footer = getattr(window, "console_footer", None)
    if console_footer is not None:
        if is_active:
            console_footer.setText(T("MONITORING_ACTIVE_TEXT"))
            console_footer.setStyleSheet("font-size: 12px; font-weight: bold; padding: 2px 2px; color: #828C36;")
        else:
            console_footer.setText(
                T("MONITORING_INACTIVE_TEXT") if not error_message else T("MONITORING_INACTIVE_ERROR", error_message=error_message)
            )
            console_footer.setStyleSheet(
                "font-size: 12px; font-weight: bold; padding: 2px 2px; color: #A8394B; margin-top: 10px; border-top: 1px solid rgba(0, 166, 237, 0.3); text-align: center;"
            )

    tray_icon = getattr(window, "tray_icon", None)
    if tray_icon is not None and getattr(window, "icon_green", None) is not None and getattr(window, "icon_red", None) is not None and getattr(window, "icon_yellow", None) is not None:
        if is_active:
            tray_icon.setIcon(window.icon_green)
            tray_icon.setToolTip(T("TRAY_MONITORING_ACTIVE"))
            monitoring_tray_action = getattr(window, "monitoring_tray_action", None)
            if monitoring_tray_action is not None:
                monitoring_tray_action.setText(T("STOP_MONITORING"))
        elif error_message:
            tray_icon.setIcon(window.icon_red)
            tray_icon.setToolTip(f"VerseWatcher - Error: {error_message}")
            monitoring_tray_action = getattr(window, "monitoring_tray_action", None)
            if monitoring_tray_action is not None:
                monitoring_tray_action.setText(T("START_MONITORING"))
        else:
            tray_icon.setIcon(window.icon_yellow)
            tray_icon.setToolTip(T("TRAY_INACTIVE"))
            monitoring_tray_action = getattr(window, "monitoring_tray_action", None)
            if monitoring_tray_action is not None:
                monitoring_tray_action.setText(T("START_MONITORING"))
