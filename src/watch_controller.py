import os

from ui_state import apply_watch_ui_state


def validate_monitoring_inputs(window):
    """Validate the required inputs for a watch session and return normalized values."""
    try:
        game_path = window.path_input.text() if hasattr(window, 'path_input') and window.path_input else ""
        player_name = window.name_input.text() if hasattr(window, 'name_input') and window.name_input else ""

        if not game_path:
            return None, None, None, "Game installation directory not specified"

        if not player_name:
            return None, None, None, "Player name not specified"

        game_log_path = os.path.join(game_path, "Game.log")
        if not os.path.exists(game_log_path):
            return game_path, player_name, game_log_path, f"Game.log not found at: {game_log_path}"

        return game_path, player_name, game_log_path, None
    except Exception as exc:  # pragma: no cover - defensive guard
        return None, None, None, str(exc)


def start_monitoring(window):
    """Create/start the watcher using a dedicated controller to keep UI logic thin."""
    try:
        game_path, player_name, game_log_path, error = validate_monitoring_inputs(window)
        if error:
            logger = getattr(window, 'logger', None)
            if logger:
                logger.log_error(error)
            apply_watch_ui_state(window, False, error_message=error)
            return False

        window.is_watching = True
        apply_watch_ui_state(window, True)

        if window.watcher is None:
            from game_watcher import GameLogWatcher

            window.watcher = GameLogWatcher(
                game_path=game_path,
                player_name=player_name,
                logger=window.logger,
                toast_manager=getattr(window, 'toast_manager', None),
                main_window=window,
            )

        success = window.watcher.start()
        if not success:
            window.is_watching = False
            apply_watch_ui_state(window, False, error_message="Failed to start monitoring")
            return False

        logger = getattr(window, 'logger', None)
        if logger:
            logger.log_info(f"Started monitoring game log at: {game_log_path}")
        return True
    except Exception as exc:  # pragma: no cover - defensive guard
        window.is_watching = False
        apply_watch_ui_state(window, False, error_message=str(exc))
        logger = getattr(window, 'logger', None)
        if logger:
            logger.log_error(f"Error toggling watch state: {str(exc)}")
        return False


def stop_monitoring(window):
    """Stop the watcher and put the UI back in the inactive state."""
    try:
        if window.watcher:
            try:
                window.watcher.stop()
            except Exception as exc:  # pragma: no cover - defensive guard
                logger = getattr(window, 'logger', None)
                if logger:
                    logger.log_error(f"Error stopping watcher: {str(exc)}")

        window.is_watching = False
        apply_watch_ui_state(window, False)
        return True
    except Exception as exc:  # pragma: no cover - defensive guard
        window.is_watching = False
        apply_watch_ui_state(window, False, error_message=str(exc))
        logger = getattr(window, 'logger', None)
        if logger:
            logger.log_error(f"Error stopping watch state: {str(exc)}")
        return False
