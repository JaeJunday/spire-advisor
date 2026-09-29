"""Rule-based engine RED test 1: synergy should flip a pick."""
import unittest

from engine import score_options, score_shop


class TestScoreOptions(unittest.TestCase):
    def test_strength_synergy_flips_pick(self):
        # Deck is strength-oriented: Limit Break, Reaper, Pummel
        deck = ["Limit Break", "Reaper", "Pummel", "Strike", "Strike", "Defend", "Defend"]
        options = ["Demon Form", "Power Through", "Disarm"]
        result = score_options(deck, options, act=2, boss="Donu & Deca")
        # Demon Form shares High-Strength synergy with 3 deck cards, must win
        self.assertEqual(result["best"], "Demon Form")
        self.assertGreater(
            result["scores"]["Demon Form"], result["scores"]["Disarm"]
        )


class TestShop(unittest.TestCase):
    def test_removal_beats_weak_buy_when_broke(self):
        deck = ["Strike", "Strike", "Strike", "Defend", "Defend", "Bash"]
        result = score_shop(
            deck,
            gold=120,
            cards=[{"name": "Disarm", "price": 110}],
            relics=[],
            removal_cost=75,
            boss="Donu & Deca",
        )
        # 렌더링이 아니라 동작 검증: 살 수 있는 BEST가 있어야 하고, 삭제가 후보에 있어야 함
        self.assertIn("REMOVE", result["ranked"])
        self.assertIsNotNone(result["best_affordable"])


if __name__ == "__main__":
    unittest.main()
