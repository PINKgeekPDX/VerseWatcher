import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from event_history import EventHistory
from event_parser import is_npc_name, parse_death_event


SAMPLE_LOG_LINE = (
    "2024-01-01T12:00:00 [Notice] <Actor Death> CActor::Kill: 'Victim' [5] in zone 'Lorville' "
    "killed by 'Attacker' [9] using 'M3A' [Weapon_1] with damage type 'Energy' from direction x: 1.2, y: 3.4, z: 5.6 [Team_ActorTech][Actor]"
)


class EventParserTests(unittest.TestCase):
    def test_parse_death_event_success(self):
        event = parse_death_event(SAMPLE_LOG_LINE)

        self.assertIsNotNone(event)
        self.assertEqual(event["vname"], "Victim")
        self.assertEqual(event["kname"], "Attacker")
        self.assertEqual(event["vship"], "Lorville")
        self.assertEqual(event["kwep"], "M3A")
        self.assertEqual(event["dtype"], "Energy")
        self.assertNotIn("dirvecx", event)
        self.assertNotIn("dirvecy", event)
        self.assertNotIn("dirvecz", event)
        self.assertIn("timestamp", event)

    def test_parse_death_event_invalid_line(self):
        self.assertIsNone(parse_death_event("this is not a valid log line"))
        self.assertIsNone(parse_death_event(""))

    def test_is_npc_name(self):
        self.assertTrue(is_npc_name("NPC_Test"))
        self.assertTrue(is_npc_name("PU_Trader"))
        self.assertFalse(is_npc_name("PlayerOne"))

    def test_event_history_record_and_clear(self):
        history = EventHistory(".")
        history.record({
            "timestamp": "12:00:00",
            "vname": "Victim",
            "kname": "Attacker",
            "kwep": "M3A",
            "vship": "Lorville",
            "dtype": "Energy",
        })

        self.assertEqual(len(history.session_history["kills"]), 1)
        self.assertEqual(history.session_history["kills"][0]["victim"], "Victim")

        history.clear()
        self.assertEqual(history.session_history, {"kills": []})


if __name__ == "__main__":
    unittest.main()
