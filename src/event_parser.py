import re
from datetime import datetime

DEATH_PATTERN = re.compile(
    r"^(?P<timestamp>\S+)\s+\[Notice\]\s+<Actor Death> CActor::Kill:\s+"
    r"'(?P<vname>[^']+)'\s+\[\d+\]\s+in zone\s+'(?P<vship>[^']+)'\s+"
    r"killed by\s+'(?P<kname>[^']+)'\s+\[\d+\]\s+using\s+'(?P<kwep>[^']+)'\s+"
    r"\[[^\]]*\]\s+with damage type\s+'(?P<dtype>[^']+)'\s+from direction x:\s*"
    r"(?P<dirvecx>[^,]+),\s*y:\s*(?P<dirvecy>[^,]+),\s*z:\s*(?P<dirvecz>[^\s]+)"
    r"\s+\[Team_ActorTech\]\[Actor\]$"
)


def is_npc_name(name):
    """Return True when a name matches the game's NPC naming conventions."""
    if not name:
        return False
    return "NPC" in name or name.startswith("PU_")


def parse_death_event(line):
    """Parse a Star Citizen death line into a normalized event dictionary."""
    if not line or not line.strip():
        return None

    match = DEATH_PATTERN.match(line.strip())
    if match is None:
        return None

    event = match.groupdict()
    for vec_key in ("dirvecx", "dirvecy", "dirvecz"):
        event.pop(vec_key, None)

    event["timestamp"] = datetime.now().strftime("%H:%M:%S")
    return event
