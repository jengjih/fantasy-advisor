"""可變動的球隊狀態（陣容、IL、本週對戰），存在 data/state.json。

網頁的 AI 顧問透過這裡讀寫；檔案不存在時，用 leagues.py 的初始陣容建立。
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .leagues import LEAGUES

STATE_FILE = Path(__file__).resolve().parents[2] / "data" / "state.json"


def _now() -> str:
    return datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")


def load() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    state = {
        label: {"roster": list(lg["initial_roster"]), "il": list(lg["initial_il"]),
                "matchup": None, "updated_at": _now()}
        for label, lg in LEAGUES.items()
    }
    save(state)
    return state


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def league_view(label: str, state: dict | None = None) -> dict:
    """聯盟設定 + 目前陣容，合成分析用的 dict。"""
    state = state or load()
    return {**LEAGUES[label], "roster": state[label]["roster"], "il": state[label]["il"]}


def touch(state: dict, label: str) -> None:
    state[label]["updated_at"] = _now()


def apply_roster_changes(label: str, add: list[str], drop: list[str],
                         to_il: list[str], from_il: list[str]) -> tuple[list[str], list[str]]:
    """套用陣容異動並存檔；回傳（完成的動作, 警告）。名字需與名單上的寫法一致。"""
    state = load()
    s = state[label]
    done, warnings = [], []
    for name in drop:
        if name in s["roster"] or name in s["il"]:
            (s["roster"] if name in s["roster"] else s["il"]).remove(name)
            done.append(f"釋出 {name}")
    for name in to_il:
        if name in s["roster"]:
            s["roster"].remove(name); s["il"].append(name); done.append(f"{name} 移入 IL")
    for name in from_il:
        if name in s["il"]:
            s["il"].remove(name); s["roster"].append(name); done.append(f"{name} 移回陣容")
    for name in add:
        if name in s["roster"] or name in s["il"]:
            warnings.append(f"{name} 已經在陣容裡")
        else:
            s["roster"].append(name); done.append(f"簽入 {name}")

    if len(s["il"]) > 3:
        warnings.append(f"IL 有 {len(s['il'])} 人，超過 3 格上限")
    cap = LEAGUES[label]["roster_cap"]
    if len(s["roster"]) > cap:
        warnings.append(f"陣容 {len(s['roster'])} 人，超過上限 {cap} 人，是不是漏了釋出？")
    if done:
        touch(state, label)
        save(state)
    return done, warnings


def save_matchup(label: str, week: int, opponent: str, categories: list[dict], adds_used: int,
                 opp_games_left: int = -1) -> None:
    """opp_games_left：對手本週剩餘出賽人次（Yahoo Matchup 頁可看到），-1＝不知道。"""
    now = datetime.now(ZoneInfo("Asia/Taipei"))
    et_today = datetime.now(ZoneInfo("America/New_York")).date()
    state = load()
    state[label]["matchup"] = {
        "week": week, "opponent": opponent, "categories": categories,
        "adds_used": adds_used, "opp_games_left": opp_games_left, "note": "",
        "saved_at": now.strftime("%m-%d %H:%M"), "saved_ts": now.isoformat(timespec="minutes"),
        "week_monday": str(et_today - timedelta(days=et_today.weekday())),
    }
    touch(state, label)
    save(state)
