"""可變動的球隊狀態（陣容、IL、本週對戰），存在 data/state.json。

網頁的 AI 顧問透過這裡讀寫；檔案不存在時，用 leagues.py 的初始陣容建立。
"""

import json
from datetime import datetime
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


def save_matchup(label: str, week: int, opponent: str, categories: list[dict], adds_used: int) -> None:
    state = load()
    state[label]["matchup"] = {"week": week, "opponent": opponent, "categories": categories,
                               "adds_used": adds_used, "note": "", "saved_at": _now()[5:]}
    touch(state, label)
    save(state)
