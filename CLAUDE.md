# LeSunshine Fantasy Basketball 顧問

## 使用者
- AI／程式新手，也是 fantasy basketball 新手。解釋時用白話繁體中文，一步一步帶。
- 希望盡快能用（2026-27 球季已開打）。
- 只要「建議」，由使用者自己在 Yahoo 點選操作，不要自動執行排陣或 Add/Drop。
- 金鑰一律請使用者自己貼進 `.env`，不要請他貼進對話。

## 目標
連結 Yahoo Fantasy API 和 NBA 數據，替兩個聯盟產生每日建議，最後部署成網頁，再加上 LINE 推播（LINE Notify 已停用，要用 Messaging API）。

## 聯盟（陣容和下方的球員分級已經過使用者確認，是本季資料）
### 聯盟一：誰是懂球帝（League ID 211505）
- 8 隊，H2H 11-Cat：FGM, FG%, FTM/A, FT%, 3PTM, 3PT%, PTS, REB, AST, ST, BLK, TO
- 10 先發、4 板凳、3 IL；每週 8 adds；Daily-Today；1 天 waiver；前 6 名進季後賽（Week 20–22）
- 核心：Wembanyama, Brunson, Booker, Bam, Fox, LeBron, D. White, Reaves
- 串流位：WCJ, Edey, Sarr, Buzelis；IL：Jalen Williams, Cason Wallace
- 宿敵：「尚恩·李文斯頓」。戰術：用出賽場次堆累積數據，每週用滿 6–8 次 adds

### 聯盟二：baek's Grand League（League ID 256674）
- 12 隊，9-Cat：FG%, FT%, 3PTM, PTS, REB, AST, ST, BLK, TO（punt TO）
- 10 先發、3 板凳、3 IL；每週 4 adds；2 天 waiver；前 8 名進季後賽（Week 21–23）
- 核心：Luka, AD, Embiid；主力：DeRozan, Turner, Ayton, Jabari Smith Jr., Pritchard
- 角色球員：Dosunmu, LaMelo, NAW, Kyshawn George, Mitchell Robinson；IL：Kon Knueppel
- 宿敵：「安卓·伊古達拉」。戰術：靠長人鎖住 REB 和 BLK；週一到週四不用 adds，留到週末打搖擺比項

## 每日建議 SOP
1. 陣容檢查：有比賽的球員被放在 BN、掛 O 卻占著先發位置
2. 比項分類：已鎖定、放棄（聯盟二的 TO）、搖擺（差距在 3–5 單位內）
3. 簽人：只考慮純 FA（不要 waiver 上的球員），避開掛 O 或 GTD 的球員，優先考慮 B2B 或小比賽日出賽者
4. 推薦球員時要列出：姓名、位置、對手、開打時間、能補的比項、是否為純 FA
5. 宿敵監控：週末提出防守性的建議

## 技術與進度
- Python 3.12，用 uv 管理（`~/.local/bin/uv run ...`）。已安裝：yahoo_oauth, yahoo_fantasy_api, nba_api, pandas, streamlit, python-dotenv
- [x] 階段 0：環境安裝完成
- [x] Yahoo App 已建立，金鑰放在 `.env`，OAuth 可以取得 token。但 Fantasy API 回 403：Yahoo 從 2026-07 起要求申請核准（sports.yahoo.com/developer/access）。使用者 2026-10-27 送出申請，核准後通常要建一個新 App，再把新的 Client ID 交給 Yahoo（見 yfpy issue #84）
- [x] B 版（NBA 數據版）：`app.py`（Streamlit），`src/fantasy_advisor/{nba_data,analysis,leagues}.py`
  - 數據來源：nba_api 的 ScheduleLeagueV2、LeagueDashPlayerStats（本季加上上季，用 10 場當先驗做平滑）、PlayerIndex、ESPN 傷病 JSON
  - 陣容在 `leagues.py` 手動維護（Gemini 原文的 Lonzo 是筆誤，應為 LaMelo Ball，現在在 MIN）
- [x] v2（10/27）：全中文化（`zh.py`）、球員頭貼（cdn.nba.com headshots）、介面美化（`.streamlit/config.toml` + CSS）
- [x] 陣容改存在 `data/state.json`（`state.py`）；`leagues.py` 的 initial_roster 只用來初始化
- [x] 「✏️ 陣容與對戰」編輯頁：手動同步陣容異動與本週比分（存進 state.json）
- 曾經做過網頁內建 AI 對話（Claude API），但使用者**不想額外付費**，已經移除。截圖分析改在 Claude Code 裡做（Pro 方案內含），用 `/sync` 指令。不要再提議需要付費 API 的功能
- [ ] Yahoo 核准後：接上 `yahoo_client.py`，自動抓陣容、FA、對戰比分
- [x] LINE 推播：`notify.py`（`--dry-run` 可以預覽）、`daily.py` 負責組訊息、`line_push.py` 負責發送；`.env` 要有 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID。10/27 測試推播成功
- [x] GitHub 私人 repo jengjih/fantasy-advisor（gh CLI 在 ~/.local/bin/gh）。stats.nba.com 會擋雲端主機，所以：
  - Mac 用 launchd（com.lesunshine.sync，每天 15:30、21:30、23:30；配合 16:00 和 22:00 的推播）跑 `sync.py`：抓 NBA 數據 → 存 `data/snapshot/` → 跟 `data/state.json` 一起 commit、push。安裝檔是 `scripts/install_sync.sh`
  - GitHub Actions（都用 NBA_SOURCE=snapshot；傷病從 ESPN 即時抓；LINE 金鑰存在 repo secrets）：
    - 每晚 22:00 台北（`daily-push.yml`）：`notify.py` 推今日指令。原本是早上 6:30，使用者睡覺來不及調整，10/28 改到晚上
    - 16:00 台北（`afternoon.yml`）：`--mode afternoon`，搖擺項落後或出賽人次輸對手 3 以上才推；比分超過 36 小時就不用；超過 3 天沒更新就提醒。聯盟二週一到週四原則上不推，勝敗差在 2 以內且有落後的搖擺項才破例。兩個聯盟合成一則
    - 每 30 分鐘（`injury-watch.yml`）：`--mode injury`，陣容裡（不含 IL）的球員 ESPN 預估缺陣 28 天以上或出現重傷關鍵字就推；`data/alerts.json` 記錄已通知過的，30 天內不重複推
  - 程式碼改完要自己 commit、push（sync.py 和網頁的「儲存」只會 add data/）。網頁編輯頁儲存時會自動同步（cloud_sync.push_data），也有「立即同步」按鈕
- [x] Streamlit Community Cloud 已部署：https://lesunshine-advisor.streamlit.app（唯讀模式，secrets 設 APP_MODE=cloud、NBA_SOURCE=snapshot；依賴用 requirements.txt）。Streamlit 拿不到私人 repo 的權限，所以 10/28 使用者決定把 repo 改成 public（已確認裡面沒有金鑰和個資）。repo 公開後，任何新檔案都不能放金鑰或個資
