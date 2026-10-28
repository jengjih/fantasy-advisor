"""Mac 端同步：抓 NBA 最新數據存成快照，連同陣容（data/）一起推上 GitHub，給雲端推播用。

    ~/.local/bin/uv run python sync.py

由 launchd 每天 15:30、21:30、23:30 執行（安裝檔：scripts/install_sync.sh）。
"""

import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

from fantasy_advisor import nba_data as nd
from fantasy_advisor.cloud_sync import push_data

print(f"[{datetime.now():%Y-%m-%d %H:%M}] 開始同步")
schedule, players = nd.fetch_live()
nd.save_snapshot(schedule, players)
print(f"  快照已更新：{len(players)} 位球員、{len(schedule)} 場賽程")

ok, msg = push_data()
print(f"  {'✅' if ok else '❌'} {msg}")
sys.exit(0 if ok else 1)
