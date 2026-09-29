"""Rule-based recommender prototype (v0.111.0 beta anchor, offline, <100ms)."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PATCH = "v0.111.0"


def _load(name):
    with open(DATA_DIR / f"{PATCH}-{name}.json", encoding="utf-8") as f:
        return json.load(f)


def _synergy_hits(card, deck_set, classes):
    hits = 0
    for members in classes.values():
        if card in members:
            hits += sum(1 for d in deck_set if d in members and d != card)
    return hits


def _boss_coef(card, tags, boss, bosses):
    cfg = (bosses.get("bosses", {}) or {}).get(boss, {})
    if not cfg:
        return 1.0
    coef = 1.0
    ctags = set(tags.get(card, []))
    if "spam" in ctags and "spam_penalty" in cfg:
        coef *= cfg["spam_penalty"]
    if "high_value" in ctags and "high_value_bonus" in cfg:
        coef *= cfg["high_value_bonus"]
    if "single_hit" in ctags and "high_value_bonus" in cfg:
        coef *= cfg["high_value_bonus"]
    if "aoe" in ctags and "aoe_bonus" in cfg:
        coef *= cfg["aoe_bonus"]
    if "weak" in ctags and "weak_bonus" in cfg:
        coef *= cfg["weak_bonus"]
    if "block" in ctags and "block_bonus" in cfg:
        coef *= cfg["block_bonus"]
    return coef


def score_options(deck, options, act=1, boss=None):
    tier = _load("tier")
    synergy = _load("synergy")
    bosses = _load("bosses")
    base = tier.get("base", {})
    tags = tier.get("tags", {})
    classes = synergy.get("classes", {})
    mult = synergy.get("mult", 1.5)
    deck_set = set(deck)

    scores = {}
    reasons = {}
    for card in options:
        b = float(base.get(card, 30))
        k = _synergy_hits(card, deck_set, classes)
        s = b * (mult ** k)
        c = _boss_coef(card, tags, boss, bosses)
        final = round(s * c, 1)
        scores[card] = final
        bits = [f"BASE {b}"]
        if k:
            bits.append(f"시너지 x{mult}^{k}")
        if c != 1.0:
            bits.append(f"보스계수 x{c}")
        reasons[card] = " ".join(bits)

    best = max(scores, key=scores.get) if scores else None
    return {"best": best, "scores": scores, "reasons": reasons, "patch": PATCH, "boss": boss}
