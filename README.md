# LeSunshine Fantasy 顧問

Yahoo Fantasy Basketball 個人顧問：NBA 賽程、傷病、球員價值分析、串流推薦，以及每日 LINE 推播。

- 網頁：`~/.local/bin/uv run streamlit run app.py`
- 推播預覽：`~/.local/bin/uv run python notify.py --dry-run`
- 每日推播：GitHub Actions（`.github/workflows/daily-push.yml`），台北時間 06:30
- 陣容與比分：`data/state.json`（在網頁的「✏️ 陣容與對戰」分頁編輯）

金鑰放在 `.env`（不會上傳）。開發筆記見 `CLAUDE.md`。
