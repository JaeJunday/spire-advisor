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
    top = max(scores.values()) if scores else 0
    # 스킵 판단: 다 약하면 스킵. 덱이 컨셉 상한을 넘고 시너지도 없으면 스킵.
    skip, why = False, ""
    if top < 40:
        skip, why = True, f"최고 {top}점. 다 약해서 스킵이 나아요."
    else:
        concept = deck_concept(list(deck))
        eff, (_, hi) = concept["effective_size"], concept["target"]
        no_synergy = all(_synergy_hits(c, deck_set, classes) == 0 for c in options)
        if eff > hi and no_synergy:
            skip, why = True, f"유효 {eff}장(상한 {hi}). 시너지 없이 비대해져요."
    return {"best": best, "scores": scores, "reasons": reasons, "patch": PATCH, "boss": boss, "skip": skip, "skip_reason": why}


EXHAUST_CLASS = "exhaust"
BASIC_REMOVAL = {"Strike": 10, "Defend": 8}
CURSE_REMOVAL = {"Ascender's Bane": 15, "Slimed": 12, "Dazed": 10, "Wound": 10, "Burn": 8, "Decay": 8, "Void": 6, "Doubt": 6, "Shame": 6, "Regret": 6}


def _deck_data():
    tier = _load("tier")
    synergy = _load("synergy")
    return tier, synergy


def effective_size(deck):
    """유효 덱 크기. 탈진으로 빠질 분량을 빼고 봐요. 두꺼워도 좋은 덱을 가려내요."""
    tier, synergy = _deck_data()
    classes = synergy.get("classes", {})
    exhaust = set(classes.get(EXHAUST_CLASS, []))
    thinners = sum(1 for d in deck if d in exhaust)
    return len(deck) - min(thinners, 4)


def deck_concept(deck):
    """덱 컨셉 + 적정 범위. 사이클은 얇게, 탈진/파워는 두껍게 봐요."""
    _, synergy = _deck_data()
    classes = synergy.get("classes", {})
    deck_set = set(deck)
    eff = effective_size(deck)
    hits = {name: len(set(m) & deck_set) for name, m in classes.items()}
    if hits.get("high_strength", 0) >= 3:
        concept, target = "힘 스케일링", (20, 30)
    elif hits.get("exhaust", 0) >= 3:
        concept, target = "탈진 순환", (28, 40)
    elif hits.get("aoe", 0) >= 2:
        concept, target = "광역 컨트롤", (22, 32)
    else:
        concept, target = "일반 균형", (20, 30)
    missing = []
    if eff < target[0]:
        missing.append(f"카드 {target[0] - eff}장 더 집어도 돼요")
    elif eff > target[1]:
        missing.append("이젠 스킵/삭제 우선이에요")
    return {"concept": concept, "effective_size": eff, "raw_size": len(deck), "target": target, "missing": missing}


def removal_top3(deck):
    """버릴 카드 TOP 3. 기본기/저주/컨셉 밖 카드를 먼저 골라요."""
    tier, synergy = _deck_data()
    base = tier.get("base", {})
    classes = synergy.get("classes", {})
    deck_set = set(deck)
    scored = []
    for card in deck:
        v = 0
        v += BASIC_REMOVAL.get(card, 0)
        v += CURSE_REMOVAL.get(card, 0)
        b = float(base.get(card, 30))
        if b < 20:
            v += 6
        # 컨셉 밖 카드면 삭제 우선
        hits = _synergy_hits(card, deck_set - {card}, classes)
        if hits == 0 and card not in BASIC_REMOVAL and card not in CURSE_REMOVAL:
            v += 2
        # 3장째 중복이면 정리 대상
        if deck.count(card) >= 3:
            v += 4
        scored.append((v, card))
    scored.sort(reverse=True)
    return [c for _, c in scored[:3]]


def _price_penalty(price, gold):
    return 20 * (price / max(gold, 1))


def score_shop(deck, gold, cards, relics, removal_cost, boss=None, act=1):
    """상점 추천. 사는 것 vs 자르는 것 vs 저장(세이브)을 점수 대결해요."""
    tier, synergy = _deck_data()
    bosses = _load("bosses")
    shop = _load("shop")
    base = tier.get("base", {})
    tags = tier.get("tags", {})
    classes = synergy.get("classes", {})
    mult = synergy.get("mult", 1.5)
    relic_base = shop.get("relics", {})
    deck_set = set(deck)

    cands = {}
    for c in cards or []:
        name, price = c["name"], c["price"]
        b = float(base.get(name, 30))
        k = _synergy_hits(name, deck_set, classes)
        coef = _boss_coef(name, tags, boss, bosses)
        score = b * (mult ** k) * coef
        value = round(score - _price_penalty(price, gold), 1)
        cands[f"BUY {name}"] = {"value": value, "cost": price, "reason": f"점수 {round(score,1)} - 가격부담 {round(_price_penalty(price, gold),1)}"}
    for r in relics or []:
        name, price = r["name"], r["price"]
        score = float(relic_base.get(name, 40))
        value = round(score - _price_penalty(price, gold), 1)
        cands[f"BUY {name}"] = {"value": value, "cost": price, "reason": f"유물 BASE {score} - 가격부담 {round(_price_penalty(price, gold),1)}"}

    # 삭제 가치: 최악 카드 제거 이득
    worst = removal_top3(deck)[:1]
    gain = float(shop.get("removal_base", 45))
    if worst:
        w = worst[0]
        gain += BASIC_REMOVAL.get(w, 0) + CURSE_REMOVAL.get(w, 0)
    eff = effective_size(deck)
    if eff <= 20:
        gain += 8
    if len([d for d in deck if d in set(classes.get(EXHAUST_CLASS, []))]) >= 3:
        gain -= 8
    cands["REMOVE"] = {"value": round(gain - _price_penalty(removal_cost, gold), 1), "cost": removal_cost, "reason": f"제거 이득 {round(gain,1)} ({' ,'.join(worst) if worst else '없음'}) - 가격부담 {round(_price_penalty(removal_cost, gold),1)}"}
    cands["SAVE"] = {"value": 5.0, "cost": 0, "reason": "아무것도 안 사기. 다음 상점을 봐요."}

    ranked = sorted(cands, key=lambda a: cands[a]["value"], reverse=True)
    affordable = [a for a in ranked if cands[a]["cost"] <= gold]
    best = affordable[0] if affordable else "SAVE"
    return {"ranked": ranked, "values": {a: cands[a]["value"] for a in cands}, "reasons": {a: cands[a]["reason"] for a in cands}, "best_affordable": best, "patch": PATCH}


def score_event(deck, hp, max_hp, gold, act, boss, event_id):
    """물음표 이벤트 추천. HP/골드/덱 상태로 선택지 점수를 매겨요."""
    events = _load("events")
    shop = _load("shop")
    relic_base = shop.get("relics", {})
    ev = (events.get("events", {}) or {}).get(event_id, {})
    options = ev.get("options", {})
    deck_set = set(deck)
    mitigated = bool(deck_set & {"Evolve", "Medical Kit"})
    missing = max(max_hp - hp, 0)
    frac = hp / max(max_hp, 1)

    values, reasons = {}, {}
    for name, fx in options.items():
        v, bits = 50.0, []
        if fx.get("heal"):
            g = missing * 0.3
            v += g
            bits.append(f"치유 +{round(g,1)}")
        if fx.get("hp_cost"):
            c = fx["hp_cost"]
            p = c * 2.0 if frac < 0.4 else c * 0.8
            v -= p
            bits.append(f"HP비용 -{round(p,1)}")
        if fx.get("gold_gain"):
            g = min(fx["gold_gain"] / 10.0, 15)
            v += g
            bits.append(f"골드 +{round(g,1)}")
        if fx.get("relic"):
            g = float(relic_base.get(fx["relic"], 40)) * 0.5
            v += g
            bits.append(f"유물 +{round(g,1)}")
        if fx.get("curse"):
            p = 8 if mitigated else 20
            v -= p
            bits.append(f"저주 -{p}")
        if fx.get("remove"):
            v += 12
            bits.append("삭제 +12")
        if fx.get("upgrade"):
            v += 10
            bits.append("강화 +10")
        if fx.get("card_reward"):
            v += 8
            bits.append("카드선택 +8")
        values[name] = round(v, 1)
        reasons[name] = " ".join(bits) if bits else "그냥 가기"
    ranked = sorted(values, key=values.get, reverse=True)
    return {"best": ranked[0] if ranked else None, "ranked": ranked, "values": values, "reasons": reasons, "patch": PATCH, "event": ev.get("name", event_id)}


def _shop_data():
    tier = _load("tier")
    shop = _load("shop")
    potions = _load("potions")
    return tier, shop, potions


def score_relics(options, boss=None):
    """유물 선택지 점수. 카드/포션과 별개 트랙이에요."""
    _, shop, _ = _shop_data()
    relic_base = shop.get("relics", {})
    scores = {r: round(float(relic_base.get(r, 45)), 1) for r in (options or [])}
    best = max(scores, key=scores.get) if scores else None
    return {"best": best, "scores": scores, "patch": PATCH}


def _potion_value(name, hp, max_hp, potions):
    base = float(potions.get("base", {}).get(name, 40))
    missing = max(max_hp - hp, 0)
    bonus = 0.0
    if name in potions.get("heals", []) and max_hp > 0:
        bonus = (missing / max_hp) * 25
    return round(base + bonus, 1)


def score_potion_offer(held, offered, hp, max_hp, slots=3):
    """포션 제안. 자리 있으면 먹기, 꽉 찼으면 제일 약한 거랑 교체할지, 별로면 스킵."""
    _, _, potions = _shop_data()
    threshold = float(potions.get("take_threshold", 45))
    ov = _potion_value(offered, hp, max_hp, potions)
    held = list(held or [])
    if len(held) < slots:
        if ov >= threshold:
            return {"action": "TAKE", "take": offered, "value": ov, "reason": f"{ov}점. 빈 슬롯에 챙겨요.", "patch": PATCH}
        return {"action": "SKIP", "value": ov, "reason": f"{ov}점. 별로라 안 먹어요.", "patch": PATCH}
    scored = sorted(((_potion_value(h, hp, max_hp, potions), h) for h in held))
    worst_v, worst = scored[0]
    if ov - worst_v >= 10:
        return {"action": "SWAP", "take": offered, "drop": worst, "value": ov,
                "reason": f"{offered} {ov}점 > {worst} {worst_v}점. 버리고 채워요.", "patch": PATCH}
    return {"action": "SKIP", "value": ov, "reason": f"가진 게 더 나아요({worst} {worst_v}점).", "patch": PATCH}
