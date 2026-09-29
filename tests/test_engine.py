"""Rule-based engine RED test 1: synergy should flip a pick."""
import unittest

from engine import score_options, score_shop, score_event


class TestSkip(unittest.TestCase):
    def test_all_weak_options_suggests_skip(self):
        deck = ["Demon Form", "Inflame", "Setup Strike", "Fight Me!", "Bludgeon", "Barricade", "Impervious"]
        result = score_options(deck, ["Strike", "Defend", "Shiv"], act=2, boss="Time Eater")
        self.assertTrue(result["skip"])


class TestScoreOptions(unittest.TestCase):
    def test_strength_synergy_flips_pick(self):
        # Deck is strength-oriented: Inflame, Setup Strike, Fight Me!
        deck = ["Inflame", "Setup Strike", "Fight Me!", "Strike", "Strike", "Defend", "Defend"]
        options = ["Demon Form", "Shrug It Off", "Mangle"]
        result = score_options(deck, options, act=2, boss="Donu & Deca")
        # Demon Form shares High-Strength synergy with 3 deck cards, must win
        self.assertEqual(result["best"], "Demon Form")
        self.assertGreater(
            result["scores"]["Demon Form"], result["scores"]["Mangle"]
        )


class TestShop(unittest.TestCase):
    def test_removal_beats_weak_buy_when_broke(self):
        deck = ["Strike", "Strike", "Strike", "Defend", "Defend", "Bash"]
        result = score_shop(
            deck,
            gold=120,
            cards=[{"name": "Mangle", "price": 110}],
            relics=[],
            removal_cost=75,
            boss="Donu & Deca",
        )
        # 렌더링이 아니라 동작 검증: 살 수 있는 BEST가 있어야 하고, 삭제가 후보에 있어야 함
        self.assertIn("REMOVE", result["ranked"])
        self.assertIsNotNone(result["best_affordable"])


class TestEvent(unittest.TestCase):
    def test_low_hp_prefers_heal_over_relic(self):
        deck = ["Strike", "Strike", "Defend", "Defend", "Bash"]
        result = score_event(deck, hp=15, max_hp=70, gold=100, act=1, boss="Time Eater", event_id="fountain")
        self.assertEqual(result["best"], "치유 (HP 12 회복)")


if __name__ == "__main__":
    unittest.main()
