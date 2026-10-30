"""季末預測：全聯盟每隊的最終戰績、進季後賽與奪冠機率。

    uv run python season.py                  # 誰是懂球帝
    uv run python season.py --league 聯盟二
    uv run python season.py --refresh        # 重新抓整季賽程（約 1 分鐘）
需要 data/league_rosters.json（各隊陣容、戰績表）；陣容固定、不算之後的串流和交易。
"""

import argparse
import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("NBA_SOURCE", "snapshot")

from fantasy_advisor import season as ss
from fantasy_advisor import zh
from fantasy_advisor.leagues import LEAGUES

parser = argparse.ArgumentParser()
parser.add_argument("--league", default="聯盟一", choices=list(LEAGUES))
parser.add_argument("--runs", type=int, default=2000)
parser.add_argument("--refresh", action="store_true")
args = parser.parse_args()

if args.refresh:
    ss.load_season_schedule(refresh=True)
r = ss.simulate_season(args.league, runs=args.runs)
lg = LEAGUES[args.league]
print(f"【{lg['name']}】模擬 {r['runs']} 次・剩 {r['regular']} 場例行賽對戰・季後賽 {r['playoff_start']:%m/%d} 起")
print(f"{'隊伍':<22}{'目前':>8}{'預測最終戰績':>16}{'勝率':>7}{'平均名次':>8}{'進季後賽':>8}{'前2':>6}{'冠軍賽':>7}{'冠軍':>6}")
for t in r["teams"]:
    now = "-".join(str(x) for x in t["now"])
    fin = f"{t['W']:.0f}-{t['L']:.0f}-{t['T']:.0f}"
    print(f"{t['team']:<22}{now:>8}{fin:>16}{t['pct']:>7.3f}{t['avg_rank']:>8.1f}{t['playoff']:>8.0%}{t['top2']:>6.0%}{t['final']:>7.0%}{t['champ']:>6.0%}")
print("\n各隊每週各比項的平均勝率（對上其他每一隊）：")
cats = lg["categories"]
print(f"{'隊伍':<22}" + "".join(f"{c:>6}" for c in cats))
for t in r["teams"]:
    print(f"{t['team']:<22}" + "".join(f"{t['cats'][c]:>6.0%}" for c in cats))
