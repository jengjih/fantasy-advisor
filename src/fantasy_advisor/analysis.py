"""分析引擎：球員價值（z 分數）、本週賽程、陣容警示、串流推薦。"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from . import zh
from .nba_data import normalize

PRIOR_GAMES = 6    # 季初樣本少：用上季數據當作「已經打了 6 場」來平滑
ROSTER_SIZE = 13   # 估算各隊持有人數，用來界定「計算 z 分數的球員池」
REPLACEMENT_DEPTH = 40   # 被持有球員之後再往下數 40 名 ≈ 自由市場隨手撿得到的水準
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
    """合併本季與上季，算出平滑後的場均數據。index 為 PlayerIndex（現役名單、球隊、位置）。"""
    players = pd.DataFrame({
        "PLAYER_ID": index["PERSON_ID"],
        "name": index["PLAYER_FIRST_NAME"] + " " + index["PLAYER_LAST_NAME"],
        "team": index["TEAM_ABBREVIATION"],
        "pos": index["POSITION"],
    })
    cur = cur.set_index("PLAYER_ID")
    prev = prev.set_index("PLAYER_ID")

    gp_cur = cur["GP"].reindex(players["PLAYER_ID"]).fillna(0).to_numpy()
    gp_prev = prev["GP"].reindex(players["PLAYER_ID"]).fillna(0).to_numpy()
    prior_w = np.where(gp_prev >= 10, PRIOR_GAMES, 0)
    denom = gp_cur + prior_w

    for stat in COUNT_STATS:
        tot_cur = cur[stat].reindex(players["PLAYER_ID"]).fillna(0).to_numpy()
        pg_prev = (prev[stat] / prev["GP"]).reindex(players["PLAYER_ID"]).fillna(0).to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            players[stat] = np.where(denom > 0, (tot_cur + pg_prev * prior_w) / denom, np.nan)

    players["GP"] = gp_cur.astype(int)
    players["key"] = players["name"].map(normalize)
    players["headshot"] = players["PLAYER_ID"].map(zh.headshot)
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


def games_on(schedule: pd.DataFrame, day: date) -> dict[str, dict]:
    """某天每支有比賽的球隊 → 對手、主客、台北開打時間。"""
    out = {}
    for _, g in schedule[schedule["date"] == day].iterrows():
        tip = g["tip_taipei"].strftime("%m/%d %H:%M")
        out[g["home"]] = {"opp": g["away"], "text": f"主 vs {zh.team(g['away'])}", "tip": tip}
        out[g["away"]] = {"opp": g["home"], "text": f"客 @ {zh.team(g['home'])}", "tip": tip}
    return out


def game_label(g: dict | None) -> str:
    return f"{g['text']}（{g['tip']}）" if g else "—"


def b2b_teams(schedule: pd.DataFrame, day: date) -> set[str]:
    """今天有比賽，且昨天或明天也有比賽的球隊（背靠背）。"""
    playing = lambda d: set(games_on(schedule, d))
    today = playing(day)
    return today & (playing(day - timedelta(days=1)) | playing(day + timedelta(days=1)))


def week_grid(league: dict, players: pd.DataFrame, schedule: pd.DataFrame, day: date) -> pd.DataFrame:
    """本週（週一到週日）每位球員哪幾天有比賽：●＝還沒打，○＝已打過。"""
    monday, _ = week_range(day)
    days = [monday + timedelta(days=i) for i in range(7)]
    playing = {d: set(games_on(schedule, d)) for d in days}
    labels = [f"週{WEEKDAY[d.weekday()]} {d.month}/{d.day}" for d in days]

    rows = []
    for name in league["roster"]:
        p = find_player(players, name)
        if p is None:
            continue
        row = {"球員": name}
        for d, label in zip(days, labels):
            row[label] = ("●" if d >= day else "○") if p["team"] in playing[d] else ""
        rows.append(row)
    grid = pd.DataFrame(rows)
    totals = {"球員": "▶ 當天出賽人數"}
    for d, label in zip(days, labels):
        totals[label] = str((grid[label] == "●").sum()) if d >= day else ""
    return pd.concat([grid, pd.DataFrame([totals])], ignore_index=True)


# ---------- 報告 ----------

def roster_report(league: dict, players: pd.DataFrame, injuries: pd.DataFrame,
                  schedule: pd.DataFrame, day: date) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """回傳（陣容表, [(等級, 訊息)]）；等級為 danger / warning / info / success。"""
    _, sunday = week_range(day)
    left = team_games(schedule, day, sunday)
    today = games_on(schedule, day)
    inj = injuries.set_index("key")

    rows, alerts, missing = [], [], []
    for name in league["roster"] + league["il"]:
        p = find_player(players, name)
        if p is None:
            missing.append(name)
            continue
        status = inj["injury_status"].get(p["key"], "")
        g = today.get(p["team"])
        rows.append({
            "頭貼": p["headshot"],
            "球員": name,
            "位置": zh.pos(p["pos"]),
            "球隊": zh.team(p["team"]),
            "名單": "傷兵 IL" if name in league["il"] else "陣容",
            "今天": game_label(g),
            "本週剩餘": int(left.get(p["team"], 0)),
            "傷病": zh.injury(status),
            "價值": round(p["z_total"], 2),
            "_status": status,
            "_note": inj["injury_note"].get(p["key"], ""),
            "_plays_today": bool(g),
        })
    df = pd.DataFrame(rows)
    il_free = 3 - len(league["il"])

    for name in missing:
        alerts.append(("warning", f"❓ **{name}** 不在本季任何 NBA 球隊名單上，可能是空占陣容位置，請到 Yahoo 確認。"))

    for _, r in df.iterrows():
        if r["名單"] == "陣容" and r["_status"] == "Out":
            tip = "移入 IL，空出位置簽 FA" if il_free > 0 else "IL 已滿，考慮 Drop 或等待"
            alerts.append(("danger", f"🚑 **{r['球員']}** 缺陣（Out）：{tip}。"))
        elif r["名單"] == "陣容" and r["_status"] == "Day-To-Day" and r["_plays_today"]:
            alerts.append(("warning", f"⚠️ **{r['球員']}** 每日觀察（GTD），開打前再確認能不能上：{r['今天']}"))
        elif r["名單"] != "陣容" and r["_status"] != "Out":
            alerts.append(("info", f"🔄 **{r['球員']}** 在 IL 但已不是缺陣（{r['傷病'] or '無傷病紀錄'}），可能可以移回陣容。"))

    active = df[(df["名單"] == "陣容") & (df["_status"] != "Out")]
    playing = active[active["_plays_today"]]
    n = len(playing)
    if n:
        who = "、".join(playing["球員"])
        alerts.insert(0, ("success", f"▶️ 今天有比賽（{n} 人）：{who}。到 Yahoo 按 **Start Active Players**，確認他們都不在板凳 BN。"))
    if n > league["starters"]:
        bench = playing.nsmallest(n - league["starters"], "價值")["球員"].tolist()
        alerts.append(("warning", f"🪑 今天有 {n} 人出賽，但只有 {league['starters']} 個先發位：建議坐板凳 → {', '.join(bench)}（價值最低者）。"))
    elif n < league["starters"]:
        open_slots = league["starters"] - n
        if day.weekday() < league.get("adds_from_weekday", 0):
            alerts.append(("info", f"🔒 今天只有 {n} 人出賽、{open_slots} 個先發位空著；週一到週四照紀律**先不用 adds**，留到週末打搖擺項。"))
        else:
            alerts.append(("info", f"📈 今天只有 {n} 人出賽、{open_slots} 個先發位空著：可以串流補人次。"))

    cap = league.get("roster_cap")
    if cap and len(league["roster"]) < cap:
        alerts.append(("danger", f"🆓 陣容只有 {len(league['roster'])}/{cap} 人：有 {cap - len(league['roster'])} 個空位，直接簽 FA 不用 Drop！"))

    return df, alerts


def stream_candidates(league: dict, players: pd.DataFrame, injuries: pd.DataFrame,
                      schedule: pd.DataFrame, day: date, my_keys: set[str],
                      focus: list[str], only_today: bool, skip_top: bool, limit: int = 25) -> pd.DataFrame:
    """串流推薦：排除自己陣容、缺陣球員；依「焦點比項價值 × 本週剩餘場次」排序。"""
    _, sunday = week_range(day)
    left = team_games(schedule, day, sunday)
    today = games_on(schedule, day)
    b2b = b2b_teams(schedule, day)
    inj = injuries.set_index("key")["injury_status"]

    df = players[~players["key"].isin(my_keys)].copy()
    df["status"] = df["key"].map(inj).fillna("")
    df = df[(df["status"] != "Out") & (df["MIN"] >= MIN_STREAM_MINUTES)]
    if skip_top:  # 排名太前面的幾乎一定被別人持有
        df = df[df["rank"] > league["teams"] * ROSTER_SIZE]

    df["left"] = df["team"].map(left).fillna(0).astype(int)
    df["today"] = df["team"].map(lambda t: game_label(today.get(t)))
    if only_today:
        df = df[df["today"] != "—"]

    cats = [c for c in (focus or league["categories"]) if c not in league["punt"]]
    df["focus"] = df[[f"z_{c}" for c in cats]].sum(axis=1)
    # 替補水準：大約是「市場上隨手撿得到」的球員；比他好多少 × 場次 = 這週能多賺的價值
    all_focus = players[[f"z_{c}" for c in cats]].sum(axis=1)
    replacement = all_focus.nlargest(league["teams"] * ROSTER_SIZE + REPLACEMENT_DEPTH).iloc[-1]
    df["week_value"] = (df["focus"] - replacement).clip(lower=0) * df["left"]
    df["strengths"] = df.apply(lambda r: "、".join(
        zh.CATEGORY[c] for c in sorted(cats, key=lambda c: -r[f"z_{c}"])[:3] if r[f"z_{c}"] > 0.3), axis=1)

    df = df.sort_values("week_value", ascending=False).head(limit)
    return pd.DataFrame({
        "頭貼": df["headshot"],
        "球員": df["name"],
        "位置": df["pos"].map(zh.pos),
        "球隊": df["team"].map(zh.team),
        "今天": df["today"],
        "背靠背": df["team"].isin(b2b).map({True: "✓", False: ""}),
        "本週剩餘": df["left"],
        "強項": df["strengths"],
        "每場價值": df["focus"].round(2),
        "本週總價值": df["week_value"].round(2),
        "排名": df["rank"],
        "傷病": df["status"].map(zh.injury),
    })


def player_lines(players: pd.DataFrame, names: list[str]) -> list[dict]:
    """給 AI 顧問查詢用：球員場均數據與各比項 z 分數。"""
    out = []
    for name in names:
        p = find_player(players, name)
        if p is None:
            out.append({"query": name, "found": False})
            continue
        line = {"query": name, "found": True, "name": p["name"], "team": zh.team(p["team"]),
                "pos": zh.pos(p["pos"]), "games_this_season": int(p["GP"]), "rank": int(p.get("rank", 0)),
                "per_game": {s: round(float(p[s]), 1) for s in COUNT_STATS}}
        line["z"] = {c[2:]: round(float(p[c]), 2) for c in p.index if c.startswith("z_")}
        out.append(line)
    return out
