"""抓 NBA 公開數據：賽程（NBA 官方）、球員數據（NBA 官方）、傷病（ESPN 公開資料）。"""

import unicodedata

import pandas as pd
import requests
from nba_api.stats.endpoints import leaguedashplayerstats, playerindex, scheduleleaguev2

SEASON = "2026-27"
PREV_SEASON = "2025-26"
TIMEOUT = 60


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


def fetch_positions() -> pd.DataFrame:
    df = playerindex.PlayerIndex(season=SEASON, timeout=TIMEOUT).get_data_frames()[0]
    return df[["PERSON_ID", "POSITION"]].rename(columns={"PERSON_ID": "PLAYER_ID"})


def load_all():
    """一次抓齊分析需要的數據：（賽程, 球員場均, 傷病）。"""
    from . import analysis as an  # 避免循環匯入

    schedule = fetch_schedule()
    index = playerindex.PlayerIndex(season=SEASON, timeout=TIMEOUT).get_data_frames()[0]
    players = an.build_players(fetch_player_stats(SEASON), fetch_player_stats(PREV_SEASON), index)
    return schedule, players, fetch_injuries()


def fetch_injuries() -> pd.DataFrame:
    """ESPN 傷病名單：status 為 Out / Day-To-Day 等。"""
    r = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries", timeout=30)
    r.raise_for_status()
    rows = []
    for team in r.json().get("injuries", []):
        for inj in team["injuries"]:
            rows.append({
                "key": normalize(inj["athlete"]["displayName"]),
                "injury_status": inj["status"],
                "injury_note": inj.get("shortComment", ""),
            })
    return pd.DataFrame(rows, columns=["key", "injury_status", "injury_note"]).drop_duplicates("key")
