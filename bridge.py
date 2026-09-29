"""Live bridge: game state file -> advisor UI.

C# 모드가 쓰는 상태 파일 형식 (v1, JSON):
{
  "patch": "v0.111.0",
  "act": 2,
  "act_boss": "DonuDeca",        # 보스 ID. 이름 변형 허용 (아래 BOSS_ALIASES 참고)
  "current_hp": 45, "max_hp": 75,
  "gold": 200,
  "deck": ["Limit Break", "Reaper", "Strike"],
  "screen": "reward",            # map | combat | reward | shop | event | rest
  "reward_options": ["Demon Form", "Power Through", "Disarm"],
  "shop_cards": [{"name": "Disarm", "price": 110}],
  "shop_relics": [{"name": "Anchor", "price": 150}],
  "removal_cost": 75,
  "event_id": "fountain"
}

실행: python3 bridge.py [--port 8931] [--state ./game-state.json]
UI: http://localhost:8931/ui.html -> 🎮 자동추적 ON
"""
import argparse
import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BOSS_ALIASES = {
    "timeeater": "Time Eater",
    "donudeca": "Donu & Deca",
    "donuanddeca": "Donu & Deca",
    "doormaker": "Doormaker + Door",
    "doormakerdoor": "Doormaker + Door",
    "thequeen": "The Queen",
    "queen": "The Queen",
    "testsubjectc10": "Test Subject C10",
    "c10": "Test Subject C10",
}

SCREENS = {"map", "combat", "reward", "shop", "event", "rest"}


def _norm_boss(raw):
    if not raw:
        return None
    key = "".join(c for c in str(raw).lower() if c.isalpha())
    if raw in ("Time Eater", "Donu & Deca", "Doormaker + Door", "The Queen", "Test Subject C10"):
        return raw
    return BOSS_ALIASES.get(key)


def parse_state(raw):
    """모드/세이브 JSON을 어드바이저 필드로 바꿔요. 없는 키는 빈값으로 둬요."""
    raw = raw or {}
    boss = _norm_boss(raw.get("act_boss", raw.get("boss")))
    screen = raw.get("screen", "map")
    if screen not in SCREENS:
        screen = "map"

    def cards(lst):
        out = []
        for c in lst or []:
            out.append(c if isinstance(c, str) else c.get("name", ""))
        return [c for c in out if c]

    def priced(lst):
        out = []
        for c in lst or []:
            if isinstance(c, dict) and "name" in c:
                out.append({"name": c["name"], "price": int(c.get("price", 0))})
            elif isinstance(c, str):
                out.append({"name": c, "price": 0})
        return out

    return {
        "live": True,
        "patch": raw.get("patch", "v0.111.0"),
        "act": int(raw.get("act", 1)),
        "boss": boss,
        "hp": int(raw.get("current_hp", raw.get("hp", 0))),
        "max_hp": int(raw.get("max_hp", raw.get("maxHp", 1))),
        "gold": int(raw.get("gold", 0)),
        "deck": cards(raw.get("deck")),
        "screen": screen,
        "reward_options": cards(raw.get("reward_options")),
        "shop_cards": priced(raw.get("shop_cards")),
        "shop_relics": priced(raw.get("shop_relics")),
        "removal_cost": int(raw.get("removal_cost", 75)),
        "event_id": raw.get("event_id"),
    }


class BridgeHandler(SimpleHTTPRequestHandler):
    state_file = "game-state.json"

    def _json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/state":
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    raw = json.load(f)
                self._json(parse_state(raw) | {"mtime": os.path.getmtime(self.state_file)})
            except FileNotFoundError:
                self._json({"live": False, "reason": "게임 상태 파일이 없어요. 게임을 켜고 모드를 확인하세요."})
            except (json.JSONDecodeError, OSError) as e:
                self._json({"live": False, "reason": f"상태 파일을 읽지 못했어요: {e}"})
            return
        super().do_GET()


def main():
    ap = argparse.ArgumentParser(description="Spire Advisor live bridge")
    ap.add_argument("--port", type=int, default=8931)
    ap.add_argument("--state", default="game-state.json")
    args = ap.parse_args()
    BridgeHandler.state_file = args.state
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), BridgeHandler)
    print(f"bridge on http://127.0.0.1:{args.port}/ui.html (state: {args.state})")
    srv.serve_forever()


if __name__ == "__main__":
    main()
