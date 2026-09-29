"""Save watcher tests: STS2 save dir -> advisor partial state."""
import json
import unittest
from pathlib import Path

from savewatch import find_live_save, parse_run_save

TMP = Path(__file__).parent / "tmp_savewatch"


class TestSaveWatch(unittest.TestCase):
    def test_parse_live_save(self):
        raw = {
            "character": "CHARACTER.IRONCLAD",
            "floor": 12,
            "act": 1,
            "current_hp": 58,
            "max_hp": 80,
            "gold": 150,
            "deck": [
                {"id": "CARD.INFLAME"},
                {"id": "CARD.STRIKE_IRONCLAD"},
                {"id": "CARD.STRIKE_IRONCLAD"},
            ],
        }
        s = parse_run_save(raw)
        self.assertEqual(s["deck"], ["Inflame", "Strike", "Strike"])
        self.assertEqual(s["hp"], 58)
        self.assertEqual(s["gold"], 150)
        self.assertEqual(s["act"], 1)

    def test_current_run_shape(self):
        raw = {
            "current_act_index": 0,
            "acts": [{"rooms": {"boss_id": "ENCOUNTER.VANTOM_BOSS"}}],
            "visited_map_coords": [{"col": 3, "row": 4}],
            "players": [{
                "character_id": "CHARACTER.SILENT",
                "current_hp": 60,
                "max_hp": 70,
                "gold": 99,
                "deck": [{"id": "CARD.STRIKE_SILENT"}, {"id": "CARD.NEUTRALIZE"}],
            }],
        }
        s = parse_run_save(raw)
        self.assertEqual(s["boss"], "Vantom")
        self.assertEqual(s["act"], 1)
        self.assertEqual(s["floor"], 5)
        self.assertIn("Strike", s["deck"])

    def test_find_live_save_picks_newest_run_file(self):
        TMP.mkdir(exist_ok=True)
        (TMP / "prefs.save").write_text("{}")
        a = TMP / "aaa.run"
        b = TMP / "bbb.run"
        a.write_text("{}")
        b.write_text("{}")
        import os
        import time
        now = time.time()
        os.utime(a, (now - 100, now - 100))
        os.utime(b, (now, now))
        self.assertEqual(find_live_save(TMP), b)


if __name__ == "__main__":
    unittest.main()
