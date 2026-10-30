"""產生作戰卡 App 的資料 data/app/today.json（GitHub Actions 每次同步後執行）。

    uv run python build_app.py            # 讀 data/snapshot，傷病即時從 ESPN 抓
"""

import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("NBA_SOURCE", "snapshot")

from fantasy_advisor import app_data
from fantasy_advisor.nba_data import load_all

schedule, players, injuries, _ = load_all()
data = app_data.build(players, injuries, schedule)
path = app_data.write(data)
print(f"✅ {path.relative_to(app_data.ROOT)}：{len(data['actions'])} 個動作、{len(data['alerts'])} 則提醒")
