import ctypes
import locale
import os

TRANSLATIONS = {
    "en": {
        "APP_TITLE": "VERSEWATCHER",
        "APP_WINDOW_TITLE": "VERSEWATCHER | A Star Citizen Tool",
        "DASHBOARD": "DASHBOARD",
        "TRACKING": "TRACKING",
        "PARTY_TRACKING": "PARTY TRACKING",
        "SETTINGS": "SETTINGS",
        "ABOUT": "ABOUT",
        "STAY_ON_TOP": "Stay on Top",
        "HIDE_TO_TRAY": "Hide to Tray",
        "SHOW_FROM_TRAY": "Show from Tray",
        "EXIT": "Exit",
        "STATUS_ACTIVE": "✔️ STATUS: ACTIVE",
        "STATUS_INACTIVE": "⛔️ STATUS: INACTIVE",
        "START": "🟢 START",
        "STOP": "🛑 STOP",
        "START_MONITORING": "Start Monitoring",
        "STOP_MONITORING": "Stop Monitoring",
        "START_STOP_TOOLTIPS": "Start/Stop monitoring Game.log events",
        "FILTER": "Filter:",
        "ALL_MESSAGES": "All Messages",
        "INFO_ONLY": "Info Only",
        "WARNINGS_ONLY": "Warnings Only",
        "ERRORS_ONLY": "Errors Only",
        "EVENTS_ONLY": "Events Only",
        "AUTO_SCROLL": "Auto-scroll",
        "CLEAR_CONSOLE": "Clear Console",
        "SAVE_LOG": "Save Log",
        "SAVE_LOG_DIALOG": "Save Console Log",
        "GENERAL_SETTINGS": "GENERAL SETTINGS",
        "EVENT_FILTERING": "EVENT FILTERING",
        "TOAST_NOTIFICATIONS": "TOAST NOTIFICATIONS",
        "PARTY_TOAST_NOTIFICATIONS": "PARTY TOAST NOTIFICATIONS",
        "GAME_INSTALL_PATH": "Game Install Path:",
        "PLAYER_NAME": "Player Name:",
        "BROWSE": "Browse",
        "SELF_EVENTS": "Self events",
        "OTHER_PLAYER_EVENTS": "Other player events",
        "NPC_EVENTS": "NPC events",
        "SUICIDE_EVENTS": "Suicide events",
        "PARTY_EVENTS": "Party events",
        "TOAST_POSITION": "Toast Position:",
        "TOAST_SIZE": "Toast Size:",
        "TOAST_DURATION": "Toast Duration:",
        "MAX_TOAST_STACK": "Max Toast Stack:",
        "TOP_LEFT": "Top Left",
        "TOP_RIGHT": "Top Right",
        "BOTTOM_LEFT": "Bottom Left",
        "BOTTOM_RIGHT": "Bottom Right",
        "LEFT_MIDDLE": "Left Middle",
        "RIGHT_MIDDLE": "Right Middle",
        "VERY_SMALL": "Very Small",
        "SMALL": "Small",
        "MEDIUM": "Medium",
        "LARGE": "Large",
        "VERY_LARGE": "Very Large",
        "SECONDS": "seconds",
        "PARTY_MEMBER_TRACKING": "👀 PARTY MEMBER TRACKING",
        "PARTY_MEMBER_DESCRIPTION": "Add party members to track their events. Events will appear in the event list below.",
        "PARTY_MEMBERS": "🧑‍🤝‍🧑 PARTY MEMBERS",
        "ENTER_PLAYER_NAME": "Enter player name",
        "ENTER_YOUR_HANDLE": "Enter your Star Citizen handle (case sensitive)",
        "ADD": "Add",
        "REMOVE": "Remove",
        "CLEAR_ALL": "Clear All",
        "PARTY_EVENTS_HEADER": "📜 PARTY EVENTS",
        "TIME": "Time",
        "MEMBER": "Member",
        "EVENT": "Event",
        "EXPORT_EVENTS": "Export Events",
        "CLEAR_EVENTS": "Clear Events",
        "PARTY_FOOTER_TEMPLATE": "Party Members: {member_count}, Events tracked: {event_count}",
        "MONITORING_ACTIVE_TEXT": "Monitoring Game.log is active. Waiting for events...",
        "MONITORING_INACTIVE_TEXT": "Monitoring inactive. Start monitoring to view real-time events.",
        "MONITORING_INACTIVE_ERROR": "Monitoring inactive: {error_message}",
        "TRAY_MONITORING_ACTIVE": "VerseWatcher - Actively Monitoring",
        "TRAY_INACTIVE": "VerseWatcher - Inactive",
        "APP_VERSION": "Alpha version 1.0.12 · Modified by Bambu666",
        "ABOUT_DESCRIPTION": "Verse Watcher is an event tracking and notification tool designed for Star Citizen, monitoring events and party activities throughout the verse in real time.",
        "ABOUT_FEATURES": "-----------------------\n## CURRENT FEATURES ##\n-----------------------\n\n> Real-time combat tracking of Game.log events\n> Detailed kill stats and engagement reports for all players, party members and org mates\n> Party member activity monitoring and notification system\n> Non-intrusive toast notifications\n> Persistent session history for all tracked events",
        "CURRENT_FEATURES_AND_PLANNED": "CURRENT FEATURES AND PLANNED",
        "GETTING_STARTED": "GETTING STARTED",
        "ABOUT_USAGE_TEXT": "1. Configure your Star Citizen installation directory in the settings tab\n\n2. Set your in-game character handle in the settings tab (case sensitive)\n\n3. Configure your toast and party notification settings\n\n4. Manually add your party members to the party list\n\n5. Press the 'Start Monitoring' button to begin tracking and notifications\n\n6. Press the 'Stop Monitoring' button to stop tracking and notifications\n\n7. Press the 'Clear Console' button to clear the console output\n\n8. Press the 'Save Log' button to save the console output to a file",
        "DEVELOPMENT_AND_CONTRIBUTORS": "DEVELOPMENT AND CONTRIBUTORS",
        "PROJECT_GITHUB_REPO": "Project GitHub Repo",
        "SUBMIT_ISSUES": "Submit Issues",
        "DOCUMENTATION": "Documentation (Coming SoonTM)",
        "ABOUT_FOOTER": "© 2025 PINKgeekPDX - Open Source Software - Wanna Fork? :D",
        "CONSOLE_HEADER": "🖥️ CONSOLE",
        "CONSOLE_DESCRIPTION": "ℹ️ Real-time events from App actions and Game.log will appear here as they occur.",
        "EXPAND_ALL": "⏫ Expand All",
        "COLLAPSE_ALL": "⏬ Collapse All",
        "EVENT_TRACKING_HEADER": "🌌 EVENT TRACKING",
        "EVENT_TRACKING_DESCRIPTION": "Tracking history of game events. Recent events appear at the top.",
        "GAME_INSTALL_DIRECTORY": "Game Installation Directory:",
        "YOUR_PLAYER_NAME": "Your Player Name:",
        "STAY_ON_TOP_LABEL": "Stay On Top:",
        "PARTY_TOAST_POSITION": "Party Toast Position:",
        "PARTY_TOAST_SIZE": "Party Toast Size:",
        "PARTY_TOAST_DURATION": "Party Toast Duration:",
        "PARTY_TOAST_MAX_STACK": "Max Party Toast Stack:",
        "SELECT_EVENT_TYPES": "Select which types of events to monitor and display:",
        "SESSION_EVENTS": "Session Events: {count} recorded",
        "ERROR_LOADING_PARTY_TAB": "Error loading party tab. Please restart the application.",
        "DEFAULT_GAME_PATH": r"C:\Program Files\Roberts Space Industries\StarCitizen",
        "VIEW_RSI_PROFILE": "RSI profile",
    },
    "es": {
        "APP_TITLE": "VERSEWATCHER",
        "APP_WINDOW_TITLE": "VERSEWATCHER | Herramienta de Star Citizen",
        "DASHBOARD": "PANEL",
        "TRACKING": "SEGUIMIENTO",
        "PARTY_TRACKING": "SEGUIMIENTO DE GRUPO",
        "SETTINGS": "CONFIGURACIÓN",
        "ABOUT": "ACERCA DE",
        "STAY_ON_TOP": "Permanecer arriba",
        "HIDE_TO_TRAY": "Ocultar a la bandeja",
        "SHOW_FROM_TRAY": "Mostrar desde la bandeja",
        "EXIT": "Salir",
        "STATUS_ACTIVE": "✔️ ESTADO: ACTIVO",
        "STATUS_INACTIVE": "⛔️ ESTADO: INACTIVO",
        "START": "🟢 INICIAR",
        "STOP": "🛑 DETENER",
        "START_MONITORING": "Iniciar monitorización",
        "STOP_MONITORING": "Detener monitorización",
        "START_STOP_TOOLTIPS": "Iniciar/detener la monitorización de eventos de Game.log",
        "FILTER": "Filtrar:",
        "ALL_MESSAGES": "Todos los mensajes",
        "INFO_ONLY": "Solo información",
        "WARNINGS_ONLY": "Solo advertencias",
        "ERRORS_ONLY": "Solo errores",
        "EVENTS_ONLY": "Solo eventos",
        "AUTO_SCROLL": "Desplazamiento automático",
        "CLEAR_CONSOLE": "Limpiar consola",
        "SAVE_LOG": "Guardar registro",
        "SAVE_LOG_DIALOG": "Guardar registro de la consola",
        "GENERAL_SETTINGS": "CONFIGURACIÓN GENERAL",
        "EVENT_FILTERING": "FILTRADO DE EVENTOS",
        "TOAST_NOTIFICATIONS": "NOTIFICACIONES EMERGENTES",
        "PARTY_TOAST_NOTIFICATIONS": "NOTIFICACIONES EMERGENTES DEL GRUPO",
        "GAME_INSTALL_PATH": "Ruta de instalación del juego:",
        "PLAYER_NAME": "Nombre del jugador:",
        "BROWSE": "Examinar",
        "SELF_EVENTS": "Eventos del propio personaje",
        "OTHER_PLAYER_EVENTS": "Eventos de otros jugadores",
        "NPC_EVENTS": "Eventos de NPC",
        "SUICIDE_EVENTS": "Eventos de suicidio",
        "PARTY_EVENTS": "Eventos del grupo",
        "TOAST_POSITION": "Posición de la notificación:",
        "TOAST_SIZE": "Tamaño de la notificación:",
        "TOAST_DURATION": "Duración de la notificación:",
        "MAX_TOAST_STACK": "Máximo de notificaciones apiladas:",
        "TOP_LEFT": "Arriba izquierda",
        "TOP_RIGHT": "Arriba derecha",
        "BOTTOM_LEFT": "Abajo izquierda",
        "BOTTOM_RIGHT": "Abajo derecha",
        "LEFT_MIDDLE": "Centro izquierda",
        "RIGHT_MIDDLE": "Centro derecha",
        "VERY_SMALL": "Muy pequeña",
        "SMALL": "Pequeña",
        "MEDIUM": "Mediana",
        "LARGE": "Grande",
        "VERY_LARGE": "Muy grande",
        "SECONDS": "segundos",
        "PARTY_MEMBER_TRACKING": "👀 SEGUIMIENTO DE MIEMBROS DEL GRUPO",
        "PARTY_MEMBER_DESCRIPTION": "Añade miembros del grupo para seguir sus eventos. Los eventos aparecerán en la lista inferior.",
        "PARTY_MEMBERS": "🧑‍🤝‍🧑 MIEMBROS DEL GRUPO",
        "ENTER_PLAYER_NAME": "Introduce el nombre del jugador",
        "ENTER_YOUR_HANDLE": "Introduce tu nombre de jugador de Star Citizen (sensible a mayúsculas)",
        "ADD": "Añadir",
        "REMOVE": "Eliminar",
        "CLEAR_ALL": "Limpiar todo",
        "PARTY_EVENTS_HEADER": "📜 EVENTOS DEL GRUPO",
        "TIME": "Hora",
        "MEMBER": "Miembro",
        "EVENT": "Evento",
        "EXPORT_EVENTS": "Exportar eventos",
        "CLEAR_EVENTS": "Limpiar eventos",
        "PARTY_FOOTER_TEMPLATE": "Miembros del grupo: {member_count}, Eventos registrados: {event_count}",
        "MONITORING_ACTIVE_TEXT": "La monitorización de Game.log está activa. Esperando eventos...",
        "MONITORING_INACTIVE_TEXT": "La monitorización está inactiva. Inicia la monitorización para ver eventos en tiempo real.",
        "MONITORING_INACTIVE_ERROR": "La monitorización está inactiva: {error_message}",
        "TRAY_MONITORING_ACTIVE": "VerseWatcher - Monitorizando activamente",
        "TRAY_INACTIVE": "VerseWatcher - Inactivo",
        "APP_VERSION": "Versión alfa 1.0.12 · Modificada por Bambu666",
        "ABOUT_DESCRIPTION": "Verse Watcher es una herramienta de seguimiento de eventos y notificaciones para Star Citizen que monitoriza eventos y actividades del grupo en tiempo real a lo largo de la verse.",
        "ABOUT_FEATURES": "-----------------------\n## CARACTERÍSTICAS ACTUALES ##\n-----------------------\n\n> Seguimiento en tiempo real de los eventos de Game.log\n> Estadísticas detalladas de muertes y enfrentamientos\n> Monitorización de la actividad del grupo y notificaciones\n> Notificaciones emergentes discretas\n> Historial persistente de sesiones y eventos",
        "CURRENT_FEATURES_AND_PLANNED": "CARACTERÍSTICAS ACTUALES Y PREVISTAS",
        "GETTING_STARTED": "PRIMEROS PASOS",
        "ABOUT_USAGE_TEXT": "1. Configura el directorio de instalación de Star Citizen en la pestaña de configuración\n\n2. Establece tu nombre de personaje en la pestaña de configuración (sensible a mayúsculas)\n\n3. Configura tus opciones de notificaciones emergentes y del grupo\n\n4. Añade manualmente a los miembros del grupo a la lista del grupo\n\n5. Pulsa el botón 'Iniciar monitorización' para empezar a seguir eventos y notificaciones\n\n6. Pulsa el botón 'Detener monitorización' para dejar de seguir eventos y notificaciones\n\n7. Pulsa el botón 'Limpiar consola' para borrar la salida de la consola\n\n8. Pulsa el botón 'Guardar registro' para guardar la salida de la consola en un archivo",
        "DEVELOPMENT_AND_CONTRIBUTORS": "DESARROLLO Y COLABORADORES",
        "PROJECT_GITHUB_REPO": "Repositorio de GitHub del proyecto",
        "SUBMIT_ISSUES": "Enviar incidencias",
        "DOCUMENTATION": "Documentación (próximamente)",
        "ABOUT_FOOTER": "© 2025 PINKgeekPDX - Software de código abierto - ¿Quieres hacer fork? :D",
        "CONSOLE_HEADER": "🖥️ CONSOLA",
        "CONSOLE_DESCRIPTION": "ℹ️ Los eventos en tiempo real de las acciones de la aplicación y de Game.log aparecerán aquí según se produzcan.",
        "EXPAND_ALL": "⏫ Expandir todo",
        "COLLAPSE_ALL": "⏬ Contraer todo",
        "EVENT_TRACKING_HEADER": "🌌 HISTORIAL DE EVENTOS",
        "EVENT_TRACKING_DESCRIPTION": "Seguimiento del historial de eventos del juego. Los eventos recientes aparecen arriba.",
        "GAME_INSTALL_DIRECTORY": "Directorio de instalación del juego:",
        "YOUR_PLAYER_NAME": "Tu nombre de jugador:",
        "STAY_ON_TOP_LABEL": "Permanecer arriba:",
        "PARTY_TOAST_POSITION": "Posición de la notificación del grupo:",
        "PARTY_TOAST_SIZE": "Tamaño de la notificación del grupo:",
        "PARTY_TOAST_DURATION": "Duración de la notificación del grupo:",
        "PARTY_TOAST_MAX_STACK": "Máximo de notificaciones del grupo:",
        "SELECT_EVENT_TYPES": "Selecciona qué tipos de eventos monitorizar y mostrar:",
        "SESSION_EVENTS": "Eventos de sesión: {count} registrados",
        "ERROR_LOADING_PARTY_TAB": "Error al cargar la pestaña del grupo. Reinicia la aplicación.",
        "DEFAULT_GAME_PATH": r"C:\Program Files\Roberts Space Industries\StarCitizen",
        "VIEW_RSI_PROFILE": "Perfil RSI",
    },
}


def _normalize_language(code):
    if not code:
        return "en"
    code = code.lower().replace("_", "-")
    if code.startswith("es"):
        return "es"
    return "en"


def get_system_language():
    env_lang = None
    for env_name in ("LANGUAGE", "LC_ALL", "LANG"):
        value = os.environ.get(env_name)
        if value:
            env_lang = value
            break
    if env_lang:
        return _normalize_language(env_lang.split(":")[0].split(".")[0])

    locale_name = locale.getdefaultlocale()[0]
    if locale_name:
        return _normalize_language(locale_name)

    try:
        if hasattr(ctypes, "windll"):
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lang_id:
                lang = hex(lang_id & 0xFF)
                if lang.startswith("0x"):
                    lang = lang[2:]
                if lang.lower() == "0a":
                    return "es"
    except Exception:
        pass

    return "en"


def T(key, **kwargs):
    lang = get_system_language()
    mapping = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = mapping.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
