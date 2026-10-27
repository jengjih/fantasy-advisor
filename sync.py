"""Mac 端同步：抓 NBA 最新數據存成快照，連同陣容（data/）一起推上 GitHub，給雲端推播用。

    ~/.local/bin/uv run python sync.py

由 launchd 每天定時執行（見 CLAUDE.md）。
"""

import subprocess
import sys
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

from fantasy_advisor import nba_data as nd

ROOT = Path(__file__).parent


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


print(f"[{datetime.now():%Y-%m-%d %H:%M}] 開始同步")
schedule, players = nd.fetch_live()
nd.save_snapshot(schedule, players)
print(f"  快照已更新：{len(players)} 位球員、{len(schedule)} 場賽程")

git("add", "data/")
if git("diff", "--cached", "--quiet").returncode == 0:
    print("  沒有變動，不需上傳")
    sys.exit(0)

git("commit", "-m", f"自動同步 NBA 數據與陣容 {datetime.now():%m/%d %H:%M}")
pull = git("pull", "--rebase", "--autostash")
push = git("push")
if push.returncode != 0:
    sys.exit(f"  ❌ 上傳失敗：{pull.stderr}{push.stderr}")
print("  ✅ 已上傳到 GitHub")
