"""把 data/（陣容、比分、數據快照）commit 並推上 GitHub，給雲端推播用。只在 Mac 上執行。"""

import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def push_data(reason: str = "自動同步 NBA 數據與陣容") -> tuple[bool, str]:
    """回傳（成功與否, 說明）。沒有變動時也算成功。"""
    _git("add", "data/")
    if _git("diff", "--cached", "--quiet").returncode == 0:
        pull = _git("pull", "--rebase", "--autostash")  # 順便拿回雲端的傷病通知紀錄
        return pull.returncode == 0, "沒有新的變動，雲端已是最新"
    _git("commit", "-m", f"{reason} {datetime.now():%m/%d %H:%M}")
    pull = _git("pull", "--rebase", "--autostash")
    push = _git("push")
    if push.returncode != 0:
        return False, f"上傳失敗：{pull.stderr}{push.stderr}".strip()
    return True, "已上傳到 GitHub"
