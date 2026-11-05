from urllib.parse import quote


def citizen_profile_url(player_name):
    """Return an RSI citizen URL for a handle without whitespace."""
    if not isinstance(player_name, str) or not player_name or any(
        character.isspace() for character in player_name
    ):
        return None

    return f"https://robertsspaceindustries.com/en/citizens/{quote(player_name, safe='')}"
