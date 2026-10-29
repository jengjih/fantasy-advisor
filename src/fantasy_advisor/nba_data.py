"""抓 NBA 公開數據（全部來自 ESPN，雲端主機也連得到）：賽程、球員數據、傷病。"""

import json
import os
import time
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

SEASON = 2027        # ESPN 用球季結束的年份：2026-27 球季 = 2027
PREV_SEASON = 2026
TIMEOUT = 30
SCHEDULE_DAYS = 21   # 抓本週一起 3 週的賽程（本週＋下週，週日晚上也夠用）
SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_STATS = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/statistics/byathlete"
# ESPN 少數球隊縮寫跟 NBA 官方不同
TEAM_FIX = {"GS": "GSW", "NO": "NOP", "NY": "NYK", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"}
# 我們的欄位 ← ESPN 的總和欄位
STAT_FIELDS = {"GP": "gamesPlayed", "MIN": "minutes", "FGM": "fieldGoalsMade", "FGA": "fieldGoalsAttempted",
               "FG3M": "threePointFieldGoalsMade", "FG3A": "threePointFieldGoalsAttempted",
               "FTM": "freeThrowsMade", "FTA": "freeThrowsAttempted", "PTS": "points", "REB": "rebounds",
               "AST": "assists", "STL": "steals", "BLK": "blocks", "TOV": "turnovers"}


def normalize(name: str) -> str:
    """名字比對用：去掉重音符號、標點與大小寫（Dončić → doncic）。"""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _team(abbr: str) -> str:
    return TEAM_FIX.get(abbr, abbr)


def _get_json(url: str, params: dict) -> dict:
    """ESPN 偶爾會回空白內容（快取問題），換個參數重試幾次就好。"""
    for attempt in range(4):
        r = requests.get(url, params={**params, "_": attempt}, timeout=TIMEOUT)
        r.raise_for_status()
        if r.content:
            return r.json()
        time.sleep(1)
    raise RuntimeError(f"ESPN 沒有回傳資料：{url} {params}")


def fetch_schedule(start: date | None = None, days: int = SCHEDULE_DAYS) -> pd.DataFrame:
    """賽程：每場一列，含美東日期與台北開打時間。預設從美東本週一起抓 days 天。"""
    if start is None:
        today = datetime.now(ZoneInfo("America/New_York")).date()
        start = today - timedelta(days=today.weekday())
    rows = []
    for i in range(days):
        day = start + timedelta(days=i)
        for e in _get_json(f"{ESPN}/scoreboard", {"dates": f"{day:%Y%m%d}", "limit": 100}).get("events", []):
            if e["season"]["type"] != 2:  # 只要例行賽
                continue
            teams = {t["homeAway"]: _team(t["team"]["abbreviation"]) for t in e["competitions"][0]["competitors"]}
            tip = pd.Timestamp(e["date"]).tz_convert("Asia/Taipei")
            rows.append({"game_id": e["id"], "date": day, "tip_taipei": tip,
                         "home": teams["home"], "away": teams["away"],
                         "status": e["status"]["type"]["shortDetail"]})
    return pd.DataFrame(rows, columns=["game_id", "date", "tip_taipei", "home", "away", "status"])


def fetch_player_stats(season: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """（各項總和，以 PLAYER_ID 為索引；球員基本資料）。"""
    params = {"region": "us", "lang": "en", "contentorigin": "espn", "isqualified": "false",
              "limit": 1000, "page": 1, "season": season, "seasontype": 2}
    data = _get_json(ESPN_STATS, params)
    names = {c["name"]: c["names"] for c in data["categories"]}
    stats, info = [], []
    for a in data["athletes"]:
        values = {}
        for c in a["categories"]:
            values.update(zip(names[c["name"]], c["values"]))
        pid = a["athlete"]["id"]
        stats.append({"PLAYER_ID": pid, **{k: values.get(v, 0) for k, v in STAT_FIELDS.items()}})
        info.append({"PLAYER_ID": pid, "name": a["athlete"]["displayName"],
                     "team": _team(a["athlete"].get("teamShortName", "")),
                     "pos": (a["athlete"].get("position") or {}).get("abbreviation", ""),
                     "headshot": (a["athlete"].get("headshot") or {}).get("href", "")})
    return pd.DataFrame(stats).set_index("PLAYER_ID"), pd.DataFrame(info)


def fetch_live() -> tuple[pd.DataFrame, pd.DataFrame]:
    """從 ESPN 抓（賽程, 球員場均）。本季沒出賽的球員用上季資料補上基本資料。"""
    from . import analysis as an  # 避免循環匯入

    cur, info_cur = fetch_player_stats(SEASON)
    prev, info_prev = fetch_player_stats(PREV_SEASON)
    index = pd.concat([info_cur, info_prev]).drop_duplicates("PLAYER_ID").reset_index(drop=True)
    return fetch_schedule(), an.build_players(cur, prev, index)


def save_snapshot(schedule: pd.DataFrame, players: pd.DataFrame) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    sched = schedule.assign(date=schedule["date"].astype(str), tip_taipei=schedule["tip_taipei"].map(lambda t: t.isoformat()))
    sched.to_json(SNAPSHOT_DIR / "schedule.json", orient="records", force_ascii=False, indent=0)
    players.to_json(SNAPSHOT_DIR / "players.json", orient="records", force_ascii=False, indent=0)
    meta = {"fetched_at": datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")}
    (SNAPSHOT_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False))


def load_snapshot() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    sched = pd.read_json(SNAPSHOT_DIR / "schedule.json", orient="records", dtype={"game_id": str})
    sched["date"] = pd.to_datetime(sched["date"]).dt.date
    sched["tip_taipei"] = pd.to_datetime(sched["tip_taipei"], utc=True).dt.tz_convert("Asia/Taipei")
    players = pd.read_json(SNAPSHOT_DIR / "players.json", orient="records")
    fetched_at = json.loads((SNAPSHOT_DIR / "meta.json").read_text())["fetched_at"]
    return sched, players, fetched_at


def load_all():
    """（賽程, 球員場均, 傷病, 數據時間）。NBA_SOURCE=snapshot 時只讀快照（推播用，速度快）；
    否則抓即時數據並順便更新快照，失敗時退回快照。傷病一律抓即時。"""
    if os.getenv("NBA_SOURCE") == "snapshot":
        schedule, players, fetched_at = load_snapshot()
    else:
        try:
            schedule, players = fetch_live()
            save_snapshot(schedule, players)
            fetched_at = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")
        except Exception:
            schedule, players, fetched_at = load_snapshot()
    return schedule, players, fetch_injuries(), fetched_at


def fetch_injuries() -> pd.DataFrame:
    """ESPN 傷病名單：status 為 Out / Day-To-Day 等；return_date 是 ESPN 預估的回歸日。
    連不到 ESPN（例如雲端對話的網路限制）時回傳空表，分析照常進行，只是少了傷病資訊。"""
    cols = ["key", "name", "injury_status", "injury_note", "injury_long", "return_date", "injury_type"]
    try:
        data = _get_json(f"{ESPN}/injuries", {})
    except Exception as e:
        print(f"⚠️ 抓不到 ESPN 傷病資料（{type(e).__name__}），這次分析沒有傷病資訊")
        return pd.DataFrame(columns=cols)
    rows = []
    for team in data.get("injuries", []):
        for inj in team["injuries"]:
            rows.append({
                "key": normalize(inj["athlete"]["displayName"]),
                "name": inj["athlete"]["displayName"],
                "injury_status": inj["status"],
                "injury_note": inj.get("shortComment", ""),
                "injury_long": inj.get("longComment", ""),
                "return_date": (inj.get("details") or {}).get("returnDate", ""),
                "injury_type": " ".join(str(v) for v in [(inj.get("details") or {}).get("type"),
                                                        (inj.get("details") or {}).get("detail")] if v),
            })
    return pd.DataFrame(rows, columns=cols).drop_duplicates("key")
