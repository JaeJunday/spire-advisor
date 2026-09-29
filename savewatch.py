"""STS2 save watcher: live run save -> advisor partial state.

실행 중 런 세이브를 찾아 덱/층/피/골드를 뽑아요.
보상 선택지는 세이브에 없어서 C# 모드가 있어야 해요.
"""
import json
from pathlib import Path

from bridge import parse_state

DATA_DIR = Path(__file__).parent / "data"

IGNORE = {"prefs.save", "prefs.save.backup", "progress.save", "progress.save.backup",
          "settings.save", "settings.save.backup", "profile.save", "profile.save.backup"}


def _idmap():
    with open(DATA_DIR / "card-idmap.json", encoding="utf-8") as f:
        return json.load(f)["cards"]


def id_to_name(cid):
    """CARD.INFLAME -> Inflame. 모르는 ID는 그대로 둬요."""
    key = (cid or "").removeprefix("CARD.")
    info = _idmap().get(key)
    return info["name"] if info else cid


def find_live_save(saves_dir):
    """current_run.save 우선, 없으면 가장 최근 런 파일. 없으면 None."""
    d = Path(saves_dir)
    if not d.is_dir():
        return None
    first = d / "current_run.save"
    if first.is_file():
        return first
    cands = []
    for p in d.iterdir():
        if not p.is_file() or p.suffix not in (".run", ".save"):
            continue
        if p.name in IGNORE or p.parent.name == "history":
            continue
        cands.append(p)
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


def _player(raw):
    if isinstance(raw.get("players"), list) and raw["players"]:
        return raw["players"][0]
    return raw


def _boss_from_run(raw):
    """acts[current].rooms.boss_id -> 표시 이름. 모르는 보스는 원본 정리해서 그대로."""
    try:
        acts = raw.get("acts") or []
        idx = int(raw.get("current_act_index", 0))
        rooms = (acts[idx] or {}).get("rooms", {})
        bid = rooms.get("boss_id") or ""
    except (IndexError, TypeError, ValueError):
        return None
    core = bid.removeprefix("ENCOUNTER.").removesuffix("_BOSS")
    known = {"VANTOM": "Vantom", "THE_INSATIABLE": "The Insatiable", "AEONGLASS": "Aeonglass",
             "TIME_EATER": "Time Eater", "DONU_DECA": "Donu & Deca"}
    if core in known:
        return known[core]
    return core.replace("_", " ").title() if core else None


def _floor_from_run(raw):
    visited = raw.get("visited_map_coords") or []
    rows = [c.get("row", 0) for c in visited if isinstance(c, dict)]
    idx = int(raw.get("current_act_index", 0))
    if rows:
        return idx * 100 + max(rows) + 1
    return raw.get("floor")


def parse_run_save(raw):
    """런 세이브 JSON -> 어드바이저 상태. 없는 값은 빈값."""
    p = _player(raw or {})
    deck = []
    for c in p.get("deck") or p.get("master_deck") or []:
        cid = c.get("id") if isinstance(c, dict) else c
        name = id_to_name(cid)
        if name:
            deck.append(name)
    idx = raw.get("current_act_index", p.get("current_act_index"))
    act = int(idx) + 1 if idx is not None else int(raw.get("act", p.get("act", 1)))
    base = {
        "act": act,
        "act_boss": _boss_from_run(raw) or raw.get("act_boss"),
        "current_hp": raw.get("current_hp", p.get("current_hp", 0)),
        "max_hp": raw.get("max_hp", p.get("max_hp", 1)),
        "gold": raw.get("gold", p.get("gold", 0)),
        "deck": deck,
        "screen": "map",
        "character": p.get("character_id", p.get("character", raw.get("character"))),
        "floor": _floor_from_run(raw),
    }
    s = parse_state(base)
    s["live"] = bool(deck)
    s["source"] = "save"
    return s


def read_live_state(saves_dir):
    """saves_dir에서 라이브 상태를 읽어요. 실패하면 live False."""
    try:
        target = find_live_save(saves_dir)
        if not target:
            return {"live": False, "reason": "진행 중 런이 없어요. 게임을 켜고 런을 시작하세요."}
        with open(target, encoding="utf-8") as f:
            s = parse_run_save(json.load(f))
        s["mtime"] = target.stat().st_mtime
        return s
    except (OSError, ValueError) as e:
        return {"live": False, "reason": f"세이브를 읽지 못했어요: {e}"}


DEFAULT_SAVES = str(Path.home() / "Library/Application Support/SlayTheSpire2/steam/76561199763968547/profile1/saves")
