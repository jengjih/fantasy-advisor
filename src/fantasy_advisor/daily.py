"""LINE 推播訊息（純文字，LINE 不支援粗體）。

- build_card_push：作戰卡推播（台北 16:00、22:00）。只有「現在就能做、還沒推過」的動作或重要提醒才推，
  沒事回傳 None（不推）；內容是摘要＋App 連結，細節在 App 裡
- find_major_injuries / injury_message：重大傷病（預估缺陣 4 週以上）即時通知
"""

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from . import state as state_store
from . import zh
from .leagues import LEAGUES
from .nba_data import normalize

APP_URL = "https://jengjih.github.io/fantasy-advisor/"
SHORT_NAME = {"聯盟一": "懂球帝", "聯盟二": "baek's"}
PUSHED_KEEP_DAYS = 14     # 推過的紀錄保留天數
MAJOR_INJURY_DAYS = 28
MAJOR_KEYWORDS = re.compile(
    r"surgery|torn|tear\b|fractur|acl\b|achilles|season-ending|rest of the season|indefinitely|"
    r"\b(?:four|five|six|seven|eight|[4-9]|1[0-9])\s*(?:-|to)?\s*(?:\w+\s+)?weeks|\bmonths?\b", re.I)


def _short_time(label: str | None) -> str:
    """「11/2（一）09:30 前」→「11/2 09:30」。"""
    if not label:
        return ""
    return re.sub(r"（.）", " ", label).replace(" 前", "").replace("  ", " ").strip()


# ---------- 作戰卡推播 ----------

def build_card_push(data: dict, pushed: dict, now: datetime) -> tuple[str | None, list[str]]:
    """回傳（訊息或 None, 這次推的項目 id）。pushed：{id: 推播日期}，推過的不再推。"""
    todo, notes, ids = [], [], []
    for a in data["actions"]:
        if a["type"] == "check" or a["id"] in pushed:
            continue
        earliest = datetime.fromisoformat(a["earliest"]) if a["earliest"] else None
        deadline = datetime.fromisoformat(a["deadline"]) if a["deadline"] else None
        if (earliest and earliest > now) or (deadline and deadline <= now):
            continue  # 還不能做（等下一次推播）或已經來不及
        todo.append(a)
        ids.append(a["id"])

    day = date.fromisoformat(data["nba_day"])
    monday = day - timedelta(days=day.weekday())
    for al in data["alerts"]:
        key = f"alert|{monday}|{al['league']}|{al['text']}"   # 同一則提醒一週只推一次
        if al["level"] in ("danger", "warning") and key not in pushed:
            notes.append(al)
            ids.append(key)

    if not todo and not notes:
        return None, []

    lines = [f"🏀 LeSunshine 作戰卡｜{now.month}/{now.day} {now:%H:%M}"]
    if todo:
        lines.append(f"現在要做 {len(todo)} 件：")
        for i, a in enumerate(todo, 1):
            when = f"{_short_time(a['deadline_label'])} 前" if a["deadline_label"] else ""
            impact = f"｜{a['impact']['label'].replace('本週勝率 ', '勝率 ')}" if a.get("impact") else ""
            lines.append(f"{'①②③④⑤⑥⑦⑧⑨⑩'[i - 1] if i <= 10 else i} {SHORT_NAME.get(a['league'], a['league_name'])}｜{a['title']}")
            lines.append(f"   {when}{impact}")
    for al in notes:
        icon = "🚨" if al["level"] == "danger" else "⚠️"
        lines.append(f"{icon} {SHORT_NAME.get(al['league'], al['league_name'])}：{al['text']}")

    week = []
    for lg in data["leagues"]:
        f = lg.get("forecast")
        if f and f.get("win_prob") is not None:
            tie = f"-{f['t']}" if f["t"] else ""
            week.append(f"{SHORT_NAME.get(lg['key'], lg['name'])} 預測 {f['w']}-{f['l']}{tie}（{f['win_prob']:.0%}）")
    if week:
        lines.append("本週：" + "｜".join(week))
    lines.append(f"👉 作戰卡 {APP_URL}")
    return "\n".join(lines), ids


def prune_pushed(pushed: dict, today: date) -> dict:
    return {k: v for k, v in pushed.items() if (today - date.fromisoformat(v)).days <= PUSHED_KEEP_DAYS}


# ---------- 重大傷病即時通知 ----------

def is_major(row: pd.Series, today: date) -> bool:
    if row["injury_status"] != "Out":
        return False
    try:
        if (date.fromisoformat(str(row["return_date"])[:10]) - today).days >= MAJOR_INJURY_DAYS:
            return True
    except ValueError:
        pass
    return bool(MAJOR_KEYWORDS.search(f"{row['injury_note']} {row['injury_long']}"))


def find_major_injuries(injuries: pd.DataFrame, alerted: dict) -> list[tuple[str, str, pd.Series]]:
    """[(聯盟, 球員, 傷病資料)]：陣容裡（不含 IL）新出現的重大傷病；30 天內通知過的跳過。"""
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    state = state_store.load()
    inj = injuries.set_index("key")
    hits = []
    for label in LEAGUES:
        for name in state[label]["roster"]:
            key = normalize(name)
            if key not in inj.index or not is_major(inj.loc[key], today):
                continue
            last = alerted.get(f"{label}|{key}")
            if last and (today - date.fromisoformat(last)).days < 30:
                continue
            hits.append((label, name, inj.loc[key]))
    return hits


def injury_message(hits) -> str:
    state = state_store.load()
    lines = ["🚨 重大傷病通知"]
    for label, name, row in hits:
        lg = state_store.league_view(label, state)
        il_free = 3 - len(lg["il"])
        ret = f"，ESPN 預估 {str(row['return_date'])[:10]} 回歸" if row["return_date"] else ""
        lines += ["", f"【{lg['name']}】{name}：{zh.injury(row['injury_status'])}{ret}",
                  f"ESPN：{row['injury_note']}",
                  "👉 建議：" + (f"移入 IL（還有 {il_free} 格），再簽人補位" if il_free > 0 else "IL 已滿，考慮 Drop 換人")]
    lines += ["", "要簽誰補位：傳一張 FA 截圖到手機對話，作戰卡會算好給你", f"👉 作戰卡 {APP_URL}"]
    return "\n".join(lines)
