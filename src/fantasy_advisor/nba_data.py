"""抓 NBA 公開數據：賽程（NBA 官方）、球員數據（NBA 官方）、傷病（ESPN 公開資料）。"""

import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from nba_api.stats.endpoints import leaguedashplayerstats, playerindex, scheduleleaguev2

SEASON = "2026-27"
PREV_SEASON = "2025-26"
TIMEOUT = 60
# NBA 官網會擋雲端主機：Mac 抓好的數據存成快照，雲端（GitHub Actions）讀快照
SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


def normalize(name: str) -> str:
    """名字比對用：去掉重音符號、標點與大小寫（Dončić → doncic）。"""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(ch for ch in s.lower() if ch.isalnum())


def fetch_schedule() -> pd.DataFrame:
    """本季例行賽賽程：每場一列，含美東日期與台北開打時間。"""
    df = scheduleleaguev2.ScheduleLeagueV2(season=SEASON, timeout=TIMEOUT).get_data_frames()[0]
    df = df[df["gameId"].str.startswith("002")]  # 002 = 例行賽（含盃賽）
    out = pd.DataFrame({
        "game_id": df["gameId"],
        "date": pd.to_datetime(df["gameDateEst"].str[:10]).dt.date,
        "tip_taipei": pd.to_datetime(df["gameDateTimeUTC"], utc=True).dt.tz_convert("Asia/Taipei"),
        "home": df["homeTeam_teamTricode"],
        "away": df["awayTeam_teamTricode"],
        "status": df["gameStatusText"],
    })
    return out.reset_index(drop=True)


def fetch_player_stats(season: str) -> pd.DataFrame:
    return leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, per_mode_detailed="Totals", timeout=TIMEOUT
    ).get_data_frames()[0]


def fetch_live() -> tuple[pd.DataFrame, pd.DataFrame]:
    """直接從 NBA 官網抓（賽程, 球員場均）；只在 Mac 上可用。"""
    from . import analysis as an  # 避免循環匯入

    schedule = fetch_schedule()
    index = playerindex.PlayerIndex(season=SEASON, timeout=TIMEOUT).get_data_frames()[0]
    players = an.build_players(fetch_player_stats(SEASON), fetch_player_stats(PREV_SEASON), index)
    return schedule, players


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
    """（賽程, 球員場均, 傷病, 數據時間）。NBA_SOURCE=snapshot 時只讀快照（雲端用）；
    否則抓即時數據並順便更新快照，失敗時退回快照。傷病一律抓即時（ESPN 不擋雲端）。"""
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
    """ESPN 傷病名單：status 為 Out / Day-To-Day 等；return_date 是 ESPN 預估的回歸日。"""
    r = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries", timeout=30)
    r.raise_for_status()
    rows = []
    for team in r.json().get("injuries", []):
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
    cols = ["key", "name", "injury_status", "injury_note", "injury_long", "return_date", "injury_type"]
    return pd.DataFrame(rows, columns=cols).drop_duplicates("key")
