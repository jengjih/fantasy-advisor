"""宿敵對決：試算「多串流幾場」「做某筆交易」之後，季末最終名次贏過宿敵的機率。

    uv run python rival.py                                   # 兩個聯盟：不串流 vs 每週多串 N 場
    uv run python rival.py --league 聯盟一 --stream 6
    uv run python rival.py --league 聯盟一 --stream 6 --give "Jalen Brunson" --get "Jalen Johnson" --partner 永吉路懂球帝
陣容與戰績讀 data/league_rosters.json；串流用 state.json 的 FA 名單前 12 名平均當作「補空先發格的虛擬球員」。
"""

import argparse
import json
import os
import warnings
from dataclasses import dataclass

warnings.filterwarnings("ignore")
os.environ.setdefault("NBA_SOURCE", "snapshot")

import pandas as pd

from fantasy_advisor import analysis as an
from fantasy_advisor import projection as pj
from fantasy_advisor import season as ss
from fantasy_advisor.leagues import LEAGUES

ME = "LeSunshine"
STATE = json.load(open("data/state.json"))

_teams_playing = pj.teams_playing


def _teams_playing_with_stream(schedule):
    out = _teams_playing(schedule)
    return {d: teams | {"ALL"} for d, teams in out.items()}


pj.teams_playing = _teams_playing_with_stream


@dataclass
class Streamer(pj.Member):
    prob: float = 0.0

    def play_prob(self, d):
        return self.prob


def stream(label: str, games_per_week: float):
    """每天有空先發格時，以 games_per_week/7 的機率補一場「FA 前段班平均」的表現（只有我方）。"""
    def tweak(rosters, scored, injuries, lg, empty):
        if games_per_week <= 0:
            return
        fa = [an.find_player(scored, n) for n in STATE[label]["free_agents"]["names"]]
        fa = sorted((p for p in fa if p is not None and p["MIN"] >= 20), key=lambda p: -pj.game_value(p, lg, empty))[:12]
        stats = pd.concat([p[pj.TOTALS] for p in fa], axis=1).mean(axis=1)
        rosters[ME].append(Streamer(name="串流", team="ALL", stats=stats, value=-100, prob=games_per_week / 7))
    return tweak


def trade(give: list[str], get: list[str], partner: str):
    def tweak(rosters, scored, injuries, lg, empty):
        rosters[ME] = [m for m in rosters[ME] if m.name not in give] + pj.resolve(get, scored, injuries, lg, empty)[0]
        rosters[partner] = [m for m in rosters[partner] if m.name not in get] + pj.resolve(give, scored, injuries, lg, empty)[0]
    return tweak


def run(label: str, tweaks: list, tag: str, runs: int) -> None:
    def tweak(*a):
        for t in tweaks:
            t(*a)
    rival = LEAGUES[label]["rival"]
    r = ss.simulate_season(label, runs=runs, seed=3, log=lambda *a: None, tweak=tweak)
    t = {x["team"]: x for x in r["teams"]}
    beat_reg = (r["rank"][ME] < r["rank"][rival]).mean()
    beat_final = (r["place"][ME] < r["place"][rival]).mean()
    print(f"[{LEAGUES[label]['name']}] {tag}：我 勝率 {t[ME]['pct']:.3f}、平均第 {t[ME]['avg_rank']:.1f} 名、"
          f"季後賽 {t[ME]['playoff']:.0%}、冠軍 {t[ME]['champ']:.0%}｜例行賽贏過 {rival} {beat_reg:.0%}｜最終名次贏過 {beat_final:.0%}",
          flush=True)


parser = argparse.ArgumentParser()
parser.add_argument("--league", choices=list(LEAGUES))
parser.add_argument("--stream", type=float, help="每週多串幾場（不給就比較 0 和預設值）")
parser.add_argument("--give", nargs="*", default=[])
parser.add_argument("--get", nargs="*", default=[])
parser.add_argument("--partner")
parser.add_argument("--runs", type=int, default=1500)
args = parser.parse_args()

DEFAULT_STREAM = {"聯盟一": 6, "聯盟二": 3}  # 每週 adds 8 次／4 次大約能多打的場數
for label in [args.league] if args.league else LEAGUES:
    if args.give:
        n = args.stream if args.stream is not None else DEFAULT_STREAM[label]
        run(label, [stream(label, n)], f"每週多串 {n:g} 場、不交易", args.runs)
        run(label, [stream(label, n), trade(args.give, args.get, args.partner)],
            f"每週多串 {n:g} 場＋{'、'.join(args.give)} → {'、'.join(args.get)}", args.runs)
    else:
        for n in ([args.stream] if args.stream is not None else [0, DEFAULT_STREAM[label]]):
            run(label, [stream(label, n)], f"每週多串 {n:g} 場", args.runs)
