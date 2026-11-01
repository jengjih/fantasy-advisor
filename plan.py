"""本週推演：每天出賽人數、預測結算比數、Adds 規劃。

    uv run python plan.py                    # 兩個聯盟
    uv run python plan.py --league 聯盟二     # 只看一個聯盟
    uv run python plan.py --allow-weekday    # baek's Grand League 週一到週四也試算 adds
    uv run python plan.py --next-week        # 下週一到週日整週規劃（週日晚上先排好下週的 adds）
    uv run python plan.py --assume "聯盟一:-Neemias Queta" "聯盟一:+LeBron James"   # 假設還沒做的陣容異動（+ 加入、- 移除）
預設讀 data/snapshot（GitHub 每天更新三次）；傷病即時從 ESPN 抓。
"""

import argparse
import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("NBA_SOURCE", "snapshot")

from fantasy_advisor import analysis as an
from fantasy_advisor import projection as pj
from fantasy_advisor import state as state_store
from fantasy_advisor.leagues import LEAGUES
from fantasy_advisor.nba_data import load_all

parser = argparse.ArgumentParser()
parser.add_argument("--league", choices=list(LEAGUES))
parser.add_argument("--allow-weekday", action="store_true")
parser.add_argument("--next-week", action="store_true")
parser.add_argument("--assume", nargs="*", default=[], help="還沒做的陣容異動，例如 聯盟一:-Neemias Queta")
args = parser.parse_args()

schedule, players, injuries, fetched_at = load_all()
day = an.today_et()
if args.next_week:
    from datetime import timedelta
    day = an.week_range(day)[0] + timedelta(days=7)
state = state_store.load()
print(f"NBA 比賽日 {day:%m/%d}（{pj.wd(day)}）・球員數據 {fetched_at}・傷病 {'即時' if not injuries.empty else '抓不到'}\n")
for label in ([args.league] if args.league else LEAGUES):
    lg = state_store.league_view(label, state)
    for a in args.assume:
        lab, change = a.split(":", 1)
        if lab == label:
            name = change[1:].strip()
            lg["roster"] = [n for n in lg["roster"] if n != name] + ([name] if change[0] == "+" else [])
            lg["il"] = [n for n in lg["il"] if n != name]
    print(pj.league_report(label, lg, state, players, injuries, schedule, day, args.allow_weekday))
    print()
