# LeSunshine Fantasy 顧問

Yahoo Fantasy Basketball 個人顧問：NBA 賽程、傷病、球員價值、本週推演與勝率模擬、Adds 規劃，做成手機作戰卡 App，再加上 LINE 推播。

- 作戰卡 App：https://jengjih.github.io/fantasy-advisor/（`web/`；資料由 `build_app.py` 產生，`pages.yml` 發布）
- 本週推演：`uv run python plan.py`；季末預測：`season.py`；贏宿敵機率：`rival.py`
- 推播預覽：`uv run python notify.py --dry-run`（台北 16:00、22:00 由 `card-push.yml` 推，有事才推）
- 陣容與比分：`data/state.json`（傳 Yahoo 截圖給 Claude Code，用 `/同步` 更新）

金鑰放在 `.env`（不會上傳）。開發筆記見 `CLAUDE.md`。
