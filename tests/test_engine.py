"""Rule-based engine RED test 1: synergy should flip a pick."""
import unittest

from engine import score_options, score_shop, score_event


class TestPoisonSynergy(unittest.TestCase):
    def test_poison_synergy_flips_pick(self):
        deck = ["Noxious Fumes", "Bouncing Flask", "Strike", "Strike", "Defend", "Defend"]
        options = ["Envenom", "Shrug It Off", "Mangle"]
        result = score_options(deck, options, act=2, boss=None)
        self.assertEqual(result["best"], "Envenom")


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


class TestRelics(unittest.TestCase):
    def test_best_relic_wins(self):
        from engine import score_relics
        result = score_relics(["Anchor", "Bag of Marbles"])
        self.assertEqual(result["best"], "Anchor")


class TestPotions(unittest.TestCase):
    def test_full_slots_swap_weakest(self):
        from engine import score_potion_offer
        result = score_potion_offer(
            held=["Weak Potion", "Weak Potion"],
            offered="Blood Potion",
            hp=20, max_hp=70, slots=2,
        )
        self.assertEqual(result["action"], "SWAP")
        self.assertIn("Weak Potion", result["drop"])

    def test_skip_weak_offer(self):
        from engine import score_potion_offer
        result = score_potion_offer(held=[], offered="Weak Potion", hp=60, max_hp=70, slots=3)
        self.assertEqual(result["action"], "SKIP")


class TestEvent(unittest.TestCase):
    def test_low_hp_prefers_heal_over_relic(self):
        deck = ["Strike", "Strike", "Defend", "Defend", "Bash"]
        result = score_event(deck, hp=15, max_hp=70, gold=100, act=1, boss="Time Eater", event_id="fountain")
        self.assertEqual(result["best"], "치유 (HP 12 회복)")


if __name__ == "__main__":
    unittest.main()
