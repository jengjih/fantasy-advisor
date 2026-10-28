"""LINE 推播。

    ~/.local/bin/uv run python notify.py                    # 每晚 22:00 今日指令
    ~/.local/bin/uv run python notify.py --mode afternoon   # 16:00 搶人（沒有需要就不推）
    ~/.local/bin/uv run python notify.py --mode injury      # 重大傷病檢查（有新傷病才推）
    加上 --dry-run：只印出內容，不推播、不記錄
"""

import argparse
import json
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

warnings.filterwarnings("ignore")

from dotenv import load_dotenv

from fantasy_advisor import daily, line_push
from fantasy_advisor.nba_data import load_all

ROOT = Path(__file__).parent
ALERTS_FILE = ROOT / "data" / "alerts.json"  # 已通知過的重大傷病，避免重複推播
load_dotenv(ROOT / ".env")

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["evening", "afternoon", "injury"], default="evening")
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

schedule, players, injuries, fetched_at = load_all()

if args.mode == "evening":
    message = daily.build_report(schedule, players, injuries, fetched_at)
elif args.mode == "afternoon":
    message = daily.build_afternoon(schedule, players, injuries)
else:
    alerted = json.loads(ALERTS_FILE.read_text()) if ALERTS_FILE.exists() else {}
    hits = daily.find_major_injuries(injuries, alerted)
    message = daily.injury_message(hits, schedule, players, injuries) if hits else None
    if hits and not args.dry_run:
        today = datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()
        alerted.update({f"{label}|{row.name}": today for label, _, row in hits})
        ALERTS_FILE.write_text(json.dumps(alerted, ensure_ascii=False, indent=2))

if message is None:
    print("（沒有需要推播的內容）")
elif args.dry_run:
    print(message)
else:
    line_push.push(message)
    print("✅ 已推播到 LINE")
