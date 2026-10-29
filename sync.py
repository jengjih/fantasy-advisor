"""同步：從 ESPN 抓最新賽程與球員數據存成快照，連同陣容（data/）一起推上 GitHub。

    uv run python sync.py

由 GitHub Actions（.github/workflows/data-sync.yml）每天 15:30、21:30、23:30 自動執行，Mac 不用開。
在手機（雲端 Claude Code）更新完陣容後也執行這支；如果那邊連不到 ESPN，就只上傳陣容。
"""

import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

from fantasy_advisor import nba_data as nd
from fantasy_advisor.cloud_sync import push_data

print(f"[{datetime.now():%Y-%m-%d %H:%M}] 開始同步")
try:
    schedule, players = nd.fetch_live()
    nd.save_snapshot(schedule, players)
    print(f"  快照已更新：{len(players)} 位球員、{len(schedule)} 場賽程")
except Exception as e:  # 連不到 ESPN 時仍要把陣容推上去
    print(f"  ⚠️ 抓不到 ESPN 數據（{type(e).__name__}），這次只上傳陣容")

ok, msg = push_data()
print(f"  {'✅' if ok else '❌'} {msg}")
sys.exit(0 if ok else 1)
