"""每日 LINE 推播。

    ~/.local/bin/uv run python notify.py            # 產生並推播到 LINE
    ~/.local/bin/uv run python notify.py --dry-run  # 只印出內容，不推播
"""

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from dotenv import load_dotenv

from fantasy_advisor import daily, line_push
from fantasy_advisor.nba_data import load_all

load_dotenv(Path(__file__).parent / ".env")

report = daily.build_report(*load_all())
if "--dry-run" in sys.argv:
    print(report)
else:
    line_push.push(report)
    print("✅ 已推播到 LINE")
