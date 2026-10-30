"""驗證 live_score：用 ESPN box score 重算 10/30 17:15（台北）的 Yahoo 比分截圖，逐比項對照。

    ~/.local/bin/uv run python scripts/check_live_score.py
截圖涵蓋美東 10/26（一）～10/29（四）。我方陣容異動日期是大概的，所以也試「提早／延後一天生效」，
另外比較「超過先發格數時坐板凳」和「全部算進去」。
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from fantasy_advisor import live_score as ls  # noqa: E402
from fantasy_advisor.analysis import add_zscores  # noqa: E402
from fantasy_advisor.leagues import LEAGUES  # noqa: E402
from fantasy_advisor.nba_data import fetch_schedule  # noqa: E402

START, END = date(2026, 10, 26), date(2026, 10, 29)
DAYS = [START + timedelta(days=i) for i in range((END - START).days + 1)]
MY_TEAMS = {
    "聯盟一": {
        "start": ["Victor Wembanyama", "Jalen Brunson", "Devin Booker", "Bam Adebayo", "De'Aaron Fox",
                  "LeBron James", "Derrick White", "Austin Reaves", "Wendell Carter Jr.", "Zach Edey",
                  "Alex Sarr", "Matas Buzelis", "Dylan Harper", "Toumani Camara"],
        "moves": [(date(2026, 10, 28), "Matas Buzelis", "Moussa Diabaté"),
                  (date(2026, 10, 29), "Alex Sarr", "Jaylen Wells")],
    },
    "聯盟二": {
        "start": ["Luka Dončić", "Anthony Davis", "Joel Embiid", "DeMar DeRozan", "Myles Turner",
                  "Deandre Ayton", "Jabari Smith Jr.", "Payton Pritchard", "Ayo Dosunmu", "LaMelo Ball",
                  "Nickeil Alexander-Walker", "Kyshawn George", "Mitchell Robinson"],
        "moves": [(date(2026, 10, 28), "Mitchell Robinson", "Saddiq Bey"),
                  (date(2026, 10, 29), "Deandre Ayton", "Scotty Pippen Jr.")],
    },
}


def my_roster_by_day(team: dict, shift: int) -> dict:
    """shift=0：D 日起生效；-1：提早一天；+1：延後一天。"""
    out = {}
    for d in DAYS:
        roster = list(team["start"])
        for eff, drop, add in team["moves"]:
            if d >= eff + timedelta(days=shift):
                roster = [add if n == drop else n for n in roster]
        out[d] = roster
    return out


def errors(est: list[dict], yahoo: list[dict], side: str) -> list[float]:
    out = []
    for e, y in zip(est, yahoo):
        a, b = e[side], y[side]
        if a.startswith(".") or b.startswith("."):
            out.append(abs(float(a) - float(b)) * 100)  # 命中率差幾個百分點
        else:
            out.append(abs(float(a) - float(b)))
    return out


def main():
    state = json.loads((ROOT / "data/state.json").read_text())
    players = pd.read_json(ROOT / "data/snapshot/players.json", orient="records", dtype={"PLAYER_ID": str})
    schedule = fetch_schedule(START, 4)
    box = ls.fetch_boxscores(schedule, START, END)
    print(f"box score：{box['game_id'].nunique()} 場、{int(box['did_play'].sum())} 人次出賽\n")

    for key, lg in LEAGUES.items():
        yahoo = state[key]["matchup"]["categories"]
        z = add_zscores(players, lg["categories"], lg["punt"], lg["teams"])
        values = dict(zip(z["name"], z["z_total"]))
        opp_names = state[key]["opponent_roster"]["roster"]
        # values 用 players 快照的名字當 key，陣容名字先轉成快照名字
        name_map = {}
        for n in set(opp_names) | set(MY_TEAMS[key]["start"]) | {m[2] for m in MY_TEAMS[key]["moves"]}:
            p = ls.find_player(players, n)
            name_map[n] = values.get(p["name"], 0.0) if p is not None else 0.0
        opp = ls.side_totals(box, {d: opp_names for d in DAYS}, lg["starters"], name_map, players)
        opp_all = ls.side_totals(box, {d: opp_names for d in DAYS}, 99, None, players)

        print(f"=== {lg['name']}（對手 {state[key]['matchup']['opponent']}）===")
        shown = None
        for shift in (-1, 0, 1):
            for label, starters in (("坐板凳", lg["starters"]), ("全算", 99)):
                mine = ls.side_totals(box, my_roster_by_day(MY_TEAMS[key], shift), starters, name_map, players)
                est = ls.matchup_categories(lg, mine, opp if starters != 99 else opp_all)
                err = sum(errors(est, yahoo, "mine"))
                print(f"  異動 {shift:+d} 天、{label}：我方誤差總和 {err:.1f}（{mine['games']} 人次）")
                if shift == 0 and starters != 99:
                    shown = (est, mine)  # 正式用法：照給定日期、超過先發格數就坐板凳
        est, mine = shown
        print("\n  正式算法（異動照給定日期、超過先發格數價值最低的坐板凳）：")
        print(f"  {'比項':<6}{'我方估':>8}{'Yahoo':>8}{'對手估':>8}{'Yahoo':>8}")
        for e, y in zip(est, yahoo):
            print(f"  {e['category']:<6}{e['mine']:>8}{y['mine']:>8}{e['opponent']:>8}{y['opponent']:>8}")
        print(f"  出賽人次：我方 {mine['games']}、對手 {opp['games']}（全算 {opp_all['games']}）")
        print(f"  FGA/FG3A/FTA：我方 {mine['FGA']}/{mine['FG3A']}/{mine['FTA']}、對手 {opp['FGA']}/{opp['FG3A']}/{opp['FTA']}")
        unmatched = sorted(set(mine["unmatched"]) | set(opp["unmatched"]))
        print(f"  對不到的名字：{unmatched or '無'}\n")


if __name__ == "__main__":
    main()
