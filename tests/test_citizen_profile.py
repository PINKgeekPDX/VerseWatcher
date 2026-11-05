import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from citizen_profile import citizen_profile_url


class CitizenProfileTests(unittest.TestCase):
    def test_builds_profile_url_for_handle_without_spaces(self):
        self.assertEqual(
            citizen_profile_url("PlayerOne"),
            "https://robertsspaceindustries.com/en/citizens/PlayerOne",
        )

    def test_encodes_path_characters(self):
        self.assertEqual(
            citizen_profile_url("Player/One"),
            "https://robertsspaceindustries.com/en/citizens/Player%2FOne",
        )

    def test_does_not_build_profile_url_for_names_with_whitespace(self):
        self.assertIsNone(citizen_profile_url("Player One"))
        self.assertIsNone(citizen_profile_url("Player\tOne"))
        self.assertIsNone(citizen_profile_url(""))
        self.assertIsNone(citizen_profile_url(None))


if __name__ == "__main__":
    unittest.main()
