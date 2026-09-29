"""Spire Advisor CLI. 예: python3 cli.py reward --deck "Limit Break,Reaper,Pummel" --options "Demon Form,Power Through,Disarm" --boss "Donu & Deca\""""
import argparse
import json

from engine import deck_concept, removal_top3, score_event, score_options, score_shop


def _split(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _price_list(s):
    out = []
    for item in _split(s):
        name, _, price = item.partition(":")
        out.append({"name": name.strip(), "price": int(price or 0)})
    return out


def main():
    p = argparse.ArgumentParser(description="Slay the Spire 2 보상/상점/이벤트 추천 (v0.111.0)")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("reward", help="카드 보상 3택 추천")
    r.add_argument("--deck", required=True, help='"카드A,카드B,..."')
    r.add_argument("--options", required=True, help='"선택지1,선택지2,선택지3"')
    r.add_argument("--act", type=int, default=1)
    r.add_argument("--boss", default=None)

    s = sub.add_parser("shop", help="상점: 사기 vs 자르기 vs 저장")
    s.add_argument("--deck", required=True)
    s.add_argument("--gold", type=int, required=True)
    s.add_argument("--cards", default="", help='"카드A:가격,카드B:가격"')
    s.add_argument("--relics", default="", help='"유물A:가격"')
    s.add_argument("--removal-cost", type=int, default=75)
    s.add_argument("--boss", default=None)
    s.add_argument("--act", type=int, default=1)

    e = sub.add_parser("event", help="물음표 이벤트 선택지 추천")
    e.add_argument("--deck", required=True)
    e.add_argument("--hp", type=int, required=True)
    e.add_argument("--max-hp", type=int, required=True)
    e.add_argument("--gold", type=int, default=0)
    e.add_argument("--act", type=int, default=1)
    e.add_argument("--boss", default=None)
    e.add_argument("--event", required=True, help="fountain | golden_idol")

    c = sub.add_parser("concept", help="내 덱 컨셉 + 버릴 카드 TOP3")
    c.add_argument("--deck", required=True)

    a = p.parse_args()
    deck = _split(a.deck)
    if a.cmd == "reward":
        print(json.dumps(score_options(deck, _split(a.options), a.act, a.boss), ensure_ascii=False, indent=2))
    elif a.cmd == "shop":
        print(json.dumps(score_shop(deck, a.gold, _price_list(a.cards), _price_list(a.relics), a.removal_cost, a.boss, a.act), ensure_ascii=False, indent=2))
    elif a.cmd == "event":
        print(json.dumps(score_event(deck, a.hp, a.max_hp, a.gold, a.act, a.boss, a.event), ensure_ascii=False, indent=2))
    elif a.cmd == "concept":
        print(json.dumps({"concept": deck_concept(deck), "remove_top3": removal_top3(deck)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
