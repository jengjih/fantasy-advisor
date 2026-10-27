"""LINE Messaging API：推播一則文字訊息給自己。

需要 .env（或雲端的環境變數）裡的：
    LINE_CHANNEL_ACCESS_TOKEN  — LINE Developers → Messaging API 分頁 → Channel access token（long-lived）
    LINE_USER_ID               — LINE Developers → Basic settings 分頁 → Your user ID（U 開頭）
"""

import os

import requests

PUSH_URL = "https://api.line.me/v2/bot/message/push"
MAX_CHARS = 5000  # LINE 單則文字上限


def push(text: str) -> None:
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    user_id = os.getenv("LINE_USER_ID", "").strip()
    if not token or not user_id:
        raise SystemExit("❌ 缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID，請先填進 .env")

    r = requests.post(
        PUSH_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"to": user_id, "messages": [{"type": "text", "text": text[:MAX_CHARS]}]},
        timeout=30,
    )
    if r.status_code != 200:
        raise SystemExit(f"❌ LINE 推播失敗（{r.status_code}）：{r.text}")
