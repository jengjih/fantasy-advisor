"""LINE 推播。

    uv run python notify.py                  # 作戰卡推播（台北 16:00、22:00）：有現在就能做的事才推
    uv run python notify.py --mode injury    # 重大傷病檢查（有新傷病才推）
    加上 --dry-run：只印出內容，不推播、不記錄
"""

import argparse
import json
import os
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

warnings.filterwarnings("ignore")
os.environ.setdefault("NBA_SOURCE", "snapshot")

from dotenv import load_dotenv

from fantasy_advisor import app_data, daily, line_push
from fantasy_advisor.nba_data import load_all

ROOT = Path(__file__).parent
ALERTS_FILE = ROOT / "data" / "alerts.json"  # 已通知過的重大傷病，避免重複推播
PUSHED_FILE = ROOT / "data" / "pushed.json"  # 作戰卡推過的動作／提醒，避免重複推播
load_dotenv(ROOT / ".env")

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["card", "injury"], default="card")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

schedule, players, injuries, _ = load_all()
now = datetime.now(ZoneInfo("Asia/Taipei"))

if args.mode == "card":
    pushed = json.loads(PUSHED_FILE.read_text()) if PUSHED_FILE.exists() else {}
    message, ids = daily.build_card_push(app_data.build(players, injuries, schedule), pushed, now)
    if ids and not args.dry_run:
        pushed.update({i: now.date().isoformat() for i in ids})
        PUSHED_FILE.write_text(json.dumps(daily.prune_pushed(pushed, now.date()), ensure_ascii=False, indent=1))
else:
    alerted = json.loads(ALERTS_FILE.read_text()) if ALERTS_FILE.exists() else {}
    hits = daily.find_major_injuries(injuries, alerted)
    message = daily.injury_message(hits) if hits else None
    if hits and not args.dry_run:
        alerted.update({f"{label}|{row.name}": now.date().isoformat() for label, _, row in hits})
        ALERTS_FILE.write_text(json.dumps(alerted, ensure_ascii=False, indent=2))

if message is None:
    print("（沒有需要推播的內容）")
elif args.dry_run:
    print(message)
else:
    line_push.push(message)
    print("✅ 已推播到 LINE")
