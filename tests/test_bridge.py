"""Bridge state parsing tests: mod/save JSON -> advisor fields."""
import unittest

from bridge import parse_state


class TestParseState(unittest.TestCase):
    def test_reward_screen_sync(self):
        raw = {
            "patch": "v0.111.0",
            "act": 2,
            "act_boss": "DonuDeca",
            "current_hp": 45,
            "max_hp": 75,
            "gold": 200,
            "deck": ["Limit Break", "Reaper", "Strike"],
            "screen": "reward",
            "reward_options": ["Demon Form", "Power Through", "Disarm"],
        }
        s = parse_state(raw)
        self.assertEqual(s["boss"], "Donu & Deca")
        self.assertEqual(s["deck"], ["Limit Break", "Reaper", "Strike"])
        self.assertEqual(s["reward_options"], ["Demon Form", "Power Through", "Disarm"])
        self.assertEqual(s["screen"], "reward")

    def test_combat_screen_no_options(self):
        raw = {"act": 1, "act_boss": "TimeEater", "current_hp": 60, "max_hp": 70, "deck": ["Strike"]}
        s = parse_state(raw)
        self.assertEqual(s["boss"], "Time Eater")
        self.assertEqual(s["reward_options"], [])


if __name__ == "__main__":
    unittest.main()
