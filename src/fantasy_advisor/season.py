"""季末預測：全聯盟每一隊剩下的例行賽＋季後賽，用真實賽程逐週模擬。

H2H 比項制的戰績是「比項」的勝敗和（一週 11 項 → 例如 7-3-1），排名依勝率 (W + T/2) / 總數。
- 球員能力：本季數據＋上季數據當作已經打了 ROS_PRIOR 場（季初樣本少，避免被幾場爆發或低潮帶走）
- 每天先發上限、傷兵依 ESPN 預估回歸日才上場（projection.lineup）
- 陣容固定：不算之後的串流、交易
- 賽程（每週誰對誰）不知道時，每次模擬隨機排一個循環賽程
"""

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from . import analysis as an
from . import projection as pj
from .leagues import LEAGUES
from .nba_data import PREV_SEASON, SEASON, SNAPSHOT_DIR, fetch_player_stats, fetch_schedule

ROS_PRIOR = 20            # 上季數據的權重（當作已打幾場）
ROSTERS_FILE = Path(__file__).resolve().parents[2] / "data" / "league_rosters.json"
SEASON_SCHEDULE = SNAPSHOT_DIR / "season_schedule.json"
SEASON_END = {"聯盟一": date(2027, 4, 4), "聯盟二": date(2027, 4, 11)}
PLAYOFF_WEEKS = {"聯盟一": 3, "聯盟二": 3}
PLAYOFF_TEAMS = {"聯盟一": 6, "聯盟二": 8}
REG_MATCHUPS = {"聯盟一": 17, "聯盟二": 18}  # 第 3 週起還剩幾場例行賽對戰


def load_season_schedule(refresh: bool = False) -> pd.DataFrame:
    """整季賽程（從下週一起）：抓一次要 1 分鐘多，存在 data/snapshot/season_schedule.json。"""
    if SEASON_SCHEDULE.exists() and not refresh:
        df = pd.read_json(SEASON_SCHEDULE, orient="records", dtype={"game_id": str})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    today = an.today_et()
    start = today - timedelta(days=today.weekday())
    df = fetch_schedule(start, (date(2027, 4, 15) - start).days)
    out = df.assign(date=df["date"].astype(str), tip_taipei=df["tip_taipei"].map(lambda t: t.isoformat()))
    out.to_json(SEASON_SCHEDULE, orient="records", force_ascii=False, indent=0)
    return df


def ros_players() -> pd.DataFrame:
    cur, info_cur = fetch_player_stats(SEASON)
    prev, info_prev = fetch_player_stats(PREV_SEASON)
    index = pd.concat([info_cur, info_prev]).drop_duplicates("PLAYER_ID").reset_index(drop=True)
    keep, an.PRIOR_GAMES = an.PRIOR_GAMES, ROS_PRIOR
    try:
        return an.build_players(cur, prev, index)
    finally:
        an.PRIOR_GAMES = keep


def matchup_periods(schedule: pd.DataFrame, first_monday: date, end: date, n_reg: int, n_po: int) -> tuple[list, list]:
    """把日曆週切成對戰期：季後賽是最後 n_po 週；例行賽日曆週比 n_reg 多出來的，
    就把比賽最少的那幾週（All-Star 週之類）併進下一週。"""
    weeks = []
    mon = first_monday
    while mon + timedelta(days=6) <= end:
        weeks.append([mon + timedelta(days=i) for i in range(7)])
        mon += timedelta(days=7)
    playoff, regular = weeks[-n_po:], weeks[:-n_po]
    counts = schedule.groupby("date").size()
    while len(regular) > n_reg:
        i = min(range(len(regular) - 1), key=lambda k: sum(counts.get(d, 0) for d in regular[k]))
        regular[i] = regular[i] + regular.pop(i + 1)
    return regular, playoff


def period_totals(members: list, days: list[date], playing: dict, lg: dict, rng, runs: int) -> dict:
    t = {k: np.zeros(runs) for k in pj.TOTALS}
    for d in days:
        for p, prob in pj.lineup(members, playing.get(d, set()), d, lg["starters"]):
            s = p.stats.astype(float)
            on = rng.random(runs) < prob
            fga = rng.poisson(s["FGA"], runs)
            fgm = rng.binomial(fga, min(s["FGM"] / s["FGA"], 1.0) if s["FGA"] > 0 else 0.0)
            f3a = rng.poisson(s["FG3A"], runs)
            f3m = np.minimum(rng.binomial(f3a, min(s["FG3M"] / s["FG3A"], 1.0) if s["FG3A"] > 0 else 0.0), fgm)
            fta = rng.poisson(s["FTA"], runs)
            ftm = rng.binomial(fta, min(s["FTM"] / s["FTA"], 1.0) if s["FTA"] > 0 else 0.0)
            game = {"FGM": fgm, "FGA": fga, "FG3M": f3m, "FG3A": f3a, "FTM": ftm, "FTA": fta, "PTS": 2 * fgm + f3m + ftm}
            game.update({k: rng.poisson(s[k], runs) for k in ["REB", "AST", "STL", "BLK", "TOV"]})
            for k, v in game.items():
                t[k] += v * on
    out = {}
    for c in lg["categories"]:
        if c in an.PCT_CATS:
            made, att = an.PCT_CATS[c]
            out[c] = t[made] / np.maximum(t[att], 1)
        else:
            out[c] = t[an.COUNTING_CATS[c]]
    return out


def compare(a: dict, b: dict, lg: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    """（a 贏的比項數, a 輸的比項數, 各比項 a 贏的布林陣列）。"""
    w = l = 0
    per = {}
    for c in lg["categories"]:
        x, y = (-a[c], -b[c]) if c == "TO" else (a[c], b[c])
        per[c] = x > y
        w = w + (x > y)
        l = l + (x < y)
    return w, l, per


def round_robin(teams: list[str], n: int, rng) -> list[list[tuple[str, str]]]:
    """隨機排 n 週的循環賽（circle method），每週每隊一場。"""
    t = list(teams)
    rng.shuffle(t)
    if len(t) % 2:
        t.append(None)
    rounds = []
    for _ in range(len(t) - 1):
        rounds.append([(t[i], t[-1 - i]) for i in range(len(t) // 2) if None not in (t[i], t[-1 - i])])
        t = [t[0]] + [t[-1]] + t[1:-1]
    order = list(rng.permutation(len(rounds)))
    return [rounds[order[k % len(rounds)]] for k in range(n)]


def simulate_season(label: str, runs: int = 2000, seed: int = 0, log=print, tweak=None) -> dict:
    """tweak(rosters, scored, injuries, lg, empty)：模擬前改陣容（試算交易、串流）。
    回傳的 place[隊] 是每次模擬的最終名次（季後賽打得越遠越前面，同一輪出局依例行賽名次）。"""
    lg = LEAGUES[label]
    data = json.loads(ROSTERS_FILE.read_text())[label]
    schedule = load_season_schedule()
    players = ros_players()
    from .nba_data import fetch_injuries
    injuries = fetch_injuries()
    scored, empty = pj.score(players, lg)
    rosters = {}
    for team, names in data["rosters"].items():
        members, missing = pj.resolve(names, scored, injuries, lg, empty)
        if missing:
            log(f"  （{team} 找不到數據：{'、'.join(missing)}）")
        rosters[team] = members
    if tweak:
        tweak(rosters, scored, injuries, lg, empty)
    teams = list(rosters)
    playing = pj.teams_playing(schedule)
    first = min(schedule["date"])
    first -= timedelta(days=first.weekday())
    regular, playoff = matchup_periods(schedule, first, SEASON_END[label], REG_MATCHUPS[label], PLAYOFF_WEEKS[label])
    rng = np.random.default_rng(seed)

    rng = rng
    W = {t: np.full(runs, float(data["standings"][t][0])) for t in teams}
    L = {t: np.full(runs, float(data["standings"][t][1])) for t in teams}
    T = {t: np.full(runs, float(data["standings"][t][2])) for t in teams}
    for a, b, (w, l, tie) in data.get("week2_now", []):  # 本週還沒打完：用目前比分當結果的近似
        W[a] += w; L[a] += l; T[a] += tie
        W[b] += l; L[b] += w; T[b] += tie

    # 每個對戰期：先算每隊的數據總和，再把所有兩隊組合都比一次，最後依賽程挑出實際的對戰
    n = len(lg["categories"])
    cat_rate = {t: {c: 0.0 for c in lg["categories"]} for t in teams}
    schedules = [round_robin(teams, len(regular), rng) for _ in range(runs)]
    for p, days in enumerate(regular):
        tot = {t: period_totals(rosters[t], days, playing, lg, rng, runs) for t in teams}
        res = {}
        for a in teams:
            for b in teams:
                if a < b:
                    w, l, per = compare(tot[a], tot[b], lg)
                    res[a, b] = (w, l)
                    for c in lg["categories"]:
                        cat_rate[a][c] += per[c].mean()
                        cat_rate[b][c] += 1 - per[c].mean()
        for r in range(runs):
            for a, b in schedules[r][p]:
                a, b = sorted((a, b))
                w, l = res[a, b][0][r], res[a, b][1][r]
                W[a][r] += w; L[a][r] += l; T[a][r] += n - w - l
                W[b][r] += l; L[b][r] += w; T[b][r] += n - w - l
    games_per_period = len(regular) * (len(teams) - 1)

    pct = {t: (W[t] + T[t] / 2) / (W[t] + L[t] + T[t]) for t in teams}
    stack = np.stack([pct[t] + rng.random(runs) * 1e-9 for t in teams])  # 同勝率用亂數拆
    rank = (-stack).argsort(axis=0).argsort(axis=0) + 1  # rank[隊, 第幾次模擬]

    # 季後賽：前 N 名；隊數不是 2 的次方時，前段種子第一輪輪空（6 隊＝前 2 名），每輪重新排種子
    po = []
    for days in playoff:
        tot = {t: period_totals(rosters[t], days, playing, lg, rng, runs) for t in teams}
        po.append({(a, b): compare(tot[a], tot[b], lg)[:2] for a in teams for b in teams if a != b})
    n_po = PLAYOFF_TEAMS[label]
    champ = {t: 0 for t in teams}
    final = {t: 0 for t in teams}
    reached = {t: np.zeros(runs) for t in teams}  # 季後賽打到第幾輪（沒進＝0）
    for r in range(runs):
        seeds = sorted(teams, key=lambda t: rank[teams.index(t), r])[:n_po]
        alive = list(seeds)
        for p in range(len(playoff)):
            for t in alive:
                reached[t][r] = p + 1
            if len(alive) == 2:
                for t in alive:
                    final[t] += 1
            size = 1 << (len(alive) - 1).bit_length()
            byes, play = alive[: size - len(alive)], alive[size - len(alive):]
            nxt = list(byes)
            for i in range(len(play) // 2):
                a, b = play[i], play[-1 - i]
                w, l = po[p][a, b][0][r], po[p][a, b][1][r]
                nxt.append(a if w >= l else b)  # 平手：種子高的晉級
            alive = sorted(nxt, key=seeds.index)
            if len(alive) == 1:
                break
        champ[alive[0]] += 1
        reached[alive[0]][r] = len(playoff) + 1

    out = []
    for i, t in enumerate(teams):
        out.append({
            "team": t,
            "now": data["standings"][t],
            "W": W[t].mean(), "L": L[t].mean(), "T": T[t].mean(), "pct": pct[t].mean(),
            "avg_rank": rank[i].mean(), "playoff": (rank[i] <= n_po).mean(),
            "top2": (rank[i] <= 2).mean(), "final": final[t] / runs, "champ": champ[t] / runs,
            "cats": {c: v / games_per_period for c, v in cat_rate[t].items()},
        })
    out.sort(key=lambda x: x["avg_rank"])
    key = np.stack([reached[t] * 100 - rank[i] for i, t in enumerate(teams)])
    place = {t: p for t, p in zip(teams, (-key).argsort(axis=0).argsort(axis=0) + 1)}
    return {"teams": out, "rank": {t: rank[i] for i, t in enumerate(teams)}, "place": place, "regular": len(regular), "playoff_start": playoff[0][0], "runs": runs}
