"""分析基礎：球員價值（z 分數）、球員查找、週次與賽程、比分整理。"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .nba_data import normalize

PRIOR_GAMES = 6    # 季初樣本少：用上季數據當作「已經打了 6 場」來平滑
ROSTER_SIZE = 13   # 估算各隊持有人數，用來界定「計算 z 分數的球員池」
MIN_STREAM_MINUTES = 18  # 場均上場時間太少的不推薦

COUNT_STATS = ["MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "PTS", "REB", "AST", "STL", "BLK", "TOV"]
COUNTING_CATS = {"FGM": "FGM", "3PTM": "FG3M", "PTS": "PTS", "REB": "REB", "AST": "AST",
                 "ST": "STL", "BLK": "BLK", "TO": "TOV"}
PCT_CATS = {"FG%": ("FGM", "FGA"), "FT%": ("FTM", "FTA"), "3PT%": ("FG3M", "FG3A")}
WEEKDAY = "一二三四五六日"


def today_et() -> date:
    """NBA 與 Yahoo 的「比賽日」以美東時間為準。"""
    return datetime.now(ZoneInfo("America/New_York")).date()


# ---------- 球員數據 ----------

def build_players(cur: pd.DataFrame, prev: pd.DataFrame, index: pd.DataFrame) -> pd.DataFrame:
    """合併本季與上季，算出平滑後的場均數據。
    cur / prev：以 PLAYER_ID 為索引，含 GP 與各項總和；index：PLAYER_ID、name、team、pos、headshot。"""
    players = index[["PLAYER_ID", "name", "team", "pos", "headshot"]].copy()
    ids = players["PLAYER_ID"]

    gp_cur = cur["GP"].reindex(ids).fillna(0).to_numpy()
    gp_prev = prev["GP"].reindex(ids).fillna(0).to_numpy()
    prior_w = np.where(gp_prev >= 10, PRIOR_GAMES, 0)
    denom = gp_cur + prior_w

    for stat in COUNT_STATS:
        tot_cur = cur[stat].reindex(ids).fillna(0).to_numpy()
        pg_prev = (prev[stat] / prev["GP"]).reindex(ids).fillna(0).to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            players[stat] = np.where(denom > 0, (tot_cur + pg_prev * prior_w) / denom, np.nan)

    players["GP"] = gp_cur.astype(int)
    players["key"] = players["name"].map(normalize)
    return players.dropna(subset=["MIN"]).reset_index(drop=True)


def add_zscores(players: pd.DataFrame, categories: list[str], punt: list[str], teams: int) -> pd.DataFrame:
    """依聯盟比項算每位球員的 z 分數（每場貢獻相對於「可上場球員池」平均值）。"""
    df = players.copy()
    pool = df.nlargest(teams * ROSTER_SIZE, "MIN")

    z_cols = []
    for c in categories:
        col = f"z_{c}"
        if c in PCT_CATS:
            made, att = PCT_CATS[c]
            avg = pool[made].sum() / pool[att].sum()
            # 命中率影響 = (個人命中率 − 平均) × 出手數；出手多的人影響更大
            impact = lambda d: (d[made] - avg * d[att])
            mu, sd = impact(pool).mean(), impact(pool).std()
            df[col] = (impact(df) - mu) / sd
        else:
            stat = COUNTING_CATS[c]
            mu, sd = pool[stat].mean(), pool[stat].std()
            df[col] = (df[stat] - mu) / sd
            if c == "TO":
                df[col] = -df[col]
        if c not in punt:
            z_cols.append(col)

    df["z_total"] = df[z_cols].sum(axis=1)
    df["rank"] = df["z_total"].rank(ascending=False, method="min").astype(int)
    return df


def find_player(players: pd.DataFrame, name: str) -> pd.Series | None:
    """用名字找球員：先完全比對，再試姓氏唯一比對（處理 Yahoo 縮寫如 N. Alexander-Walker）。"""
    key = normalize(name)
    hit = players[players["key"] == key]
    if not hit.empty:
        return hit.iloc[0]
    last = normalize(name.split()[-1]) if name.split() else ""
    cands = players[players["name"].map(lambda n: normalize(n.split()[-1]) == last)]
    return cands.iloc[0] if len(cands) == 1 else None


# ---------- 賽程 ----------

def week_range(day: date) -> tuple[date, date]:
    """Yahoo fantasy 週：週一到週日。"""
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def team_games(schedule: pd.DataFrame, start: date, end: date) -> pd.Series:
    """每隊在 [start, end] 期間的場次數。"""
    s = schedule[(schedule["date"] >= start) & (schedule["date"] <= end)]
    return pd.concat([s["home"], s["away"]]).value_counts()


# ---------- 對戰比分 ----------

# 計數比項的「搖擺」門檻：差距在 max(絕對值, 比例) 以內就算還能翻
SWING_ABS = {"FGM": 8, "3PTM": 4, "PTS": 25, "REB": 10, "AST": 8, "ST": 3, "BLK": 3, "TO": 4}
SWING_PCT_OF_LARGER = 0.08
SWING_RATE = 0.015  # 命中率比項：差 1.5 個百分點以內


def _num(v: str) -> float | None:
    try:
        return float(str(v).replace("%", "").strip())
    except ValueError:
        return None


def matchup_rows(m: dict, punt: list[str]) -> tuple[list[dict], int, int]:
    """把記錄的比分整理成逐項狀態，並算出幾勝幾敗（失誤 TO 越少越好）。"""
    rows, w, l = [], 0, 0
    for c in m.get("categories", []):
        cat, mine, opp = c["category"], _num(c["mine"]), _num(c["opponent"])
        row = {"cat": cat, "mine": c["mine"], "opp": c["opponent"], "lead": None, "swing": False}
        if mine is not None and opp is not None:
            if cat in PCT_CATS:  # 統一成小數：48.2 → .482
                mine, opp = (x / 100 if x > 1 else x for x in (mine, opp))
                close = abs(mine - opp) <= SWING_RATE
            else:
                close = abs(mine - opp) <= max(SWING_ABS.get(cat, 0), SWING_PCT_OF_LARGER * max(mine, opp))
            if mine != opp:
                row["lead"] = (mine < opp) if cat == "TO" else (mine > opp)
                w += row["lead"]
                l += not row["lead"]
            row["swing"] = close and cat not in punt
        rows.append(row)
    return rows, w, l

