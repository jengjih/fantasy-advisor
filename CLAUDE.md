# LeSunshine Fantasy Basketball 顧問

## 使用者
- AI／程式新手，也是 fantasy basketball 新手。解釋時用白話繁體中文，一步一步帶。
- 希望盡快能用（2026-27 球季已開打）。
- 只要「建議」，由使用者自己在 Yahoo 點選操作，不要自動執行排陣或 Add/Drop。
- 金鑰一律請使用者自己貼進 `.env`，不要請他貼進對話。
- 稱呼聯盟時直接用名稱「誰是懂球帝」「baek's Grand League」，不要說聯盟一、聯盟二（程式裡的 key 仍是聯盟一／聯盟二）。
- 除了 Pro 訂閱，不使用任何要額外付費的服務。
- 要使用者在終端機操作時，寫完整步驟：先點終端機、按 Cmd+K 清空、在 % 後面貼上、等提示出現再貼下一個值。
- 時間一律用台北時間跟使用者溝通；NBA／Yahoo 的「比賽日」以美東時間為準（台北早上的比賽＝美東前一天）。

## 手機（雲端 Claude Code）工作流程
使用者主要用手機 Claude App 的 Code 分頁開雲端對話，傳 Yahoo 截圖討論陣容。雲端對話不記得之前的事，所以：
1. **每次對話開頭先讀 `data/advisor_notes.md`**（本週計劃、已做的換人、交易決定），再讀 `data/state.json`。
2. 收到截圖照 `.claude/commands/同步.md`（使用者打 `/同步`）的步驟更新資料。
3. **直接在 main 分支 commit 並 push**（先 `git checkout main && git pull`），不要開新分支或 PR；網頁和推播都讀 main。執行 `uv run python sync.py` 會自動 commit、push data/。
4. 對話結尾更新 `data/advisor_notes.md`，寫下新的決定和接下來的計劃。
5. repo 是公開的：筆記和程式裡不能放金鑰、Email 或任何個資。
6. **每次回覆的最後一步，用 PushNotification 工具推一則手機通知**（一行、200 字內，先講結論，例如「懂球帝：週五放 Edey 簽 G. Allen，回來看細節」）。一定要等回覆文字全部寫完才推，不要在開頭或中途推：太早推的時候使用者可能還在看畫面，通知會被略過，等他切去別的 App 就收不到了。

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

## 待辦（10/29 使用者同意的順序）
1. [x] 手機雲端版 + 資料改由 GitHub Actions 從 ESPN 抓（Mac 不用開）
2. [x] 剩餘出賽改用賽程計算（Yahoo 的數字只算目前先發，會低估）
3. [x] 本週比數預測（我方陣容＋對手陣容截圖，逐比項預測結算）
4. [x] Adds 規劃器（每天先發空位、換誰淨多幾場、哪天換）
5. [ ] 推播改成「行動卡」：具體 Drop/Add 與理由；沒事不推；週日 Adds 最後提醒；先發球員 Q/GTD 提醒
6. [ ] 交易評估（傳交易截圖 → 各比項變化）
7. [ ] 簽人推薦排除小樣本（出賽太少或上場時間短）、W、O、Q

## 本週推演（`plan.py` → `projection.py`，10/30 完成）
- 每天先發：當天有比賽、沒缺陣的人依「每場價值」排序填滿先發位；GTD 以 75% 機率計
- 結算預測：Matchup 截圖的比分＋截圖後剩下的賽程（雙方陣容）；命中率用「命中數 ÷ 命中率」反推已出手數。需要 state.json 的 `opponent_roster`（本週）
- Adds 規劃：貪婪法，每步挑「哪天、放誰、簽誰」讓本週預期價值增加最多；`untouchable`＋`core`（leagues.py）不釋出；長期價值比新簽的人高 2.5 以上也不釋出（但長期排名落在全聯盟持有球員後 20% 的串流位隨時可換）；候選人優先用截圖的 FA 名單
- 勝率模擬（`simulate()`，10/30 加入）：蒙地卡羅 5000 次，出手／籃板等用卜瓦松、命中用二項分布，GTD 依機率上場；plan.py 會列出「不換人」和「照 Adds 規劃換人」兩種情況的本週勝率與搖擺項機率
- 網頁每個聯盟頁的「📊 本週推演」、下午推播的雙方剩餘出賽都用這套

## 每日建議 SOP
1. 陣容檢查：有比賽的球員被放在 BN、掛 O 卻占著先發位置
2. 比項分類：已鎖定、放棄（聯盟二的 TO）、搖擺（差距在 3–5 單位內）
3. 簽人：只考慮純 FA（不要 waiver 上的球員），避開掛 O 或 GTD 的球員，優先考慮 B2B 或小比賽日出賽者
4. 推薦球員時要列出：姓名、位置、對手、開打時間、能補的比項、是否為純 FA
5. 宿敵監控：週末提出防守性的建議

## 技術與進度
- Python 3.12，用 uv 管理（`uv run ...`；Mac 上是 `~/.local/bin/uv run ...`）。已安裝：yahoo_oauth, yahoo_fantasy_api, nba_api, pandas, streamlit, python-dotenv
- [x] 階段 0：環境安裝完成
- [x] Yahoo App 已建立，金鑰放在 `.env`，OAuth 可以取得 token。但 Fantasy API 回 403：Yahoo 從 2026-07 起要求申請核准（sports.yahoo.com/developer/access）。使用者 2026-10-27 送出申請，核准後通常要建一個新 App，再把新的 Client ID 交給 Yahoo（見 yfpy issue #84）
- [x] B 版（NBA 數據版）：`app.py`（Streamlit），`src/fantasy_advisor/{nba_data,analysis,leagues}.py`
  - 數據來源（10/29 起全部改用 ESPN，雲端主機也連得到）：scoreboard（賽程，抓本週一起 21 天）、statistics/byathlete（本季與上季總和，上季當 6 場先驗做平滑）、injuries（傷病）。原本的 nba_api 會被 stats.nba.com 擋雲端主機，已不用
  - 陣容在 `leagues.py` 手動維護（Gemini 原文的 Lonzo 是筆誤，應為 LaMelo Ball，現在在 MIN）
- [x] v2（10/27）：全中文化（`zh.py`）、球員頭貼（cdn.nba.com headshots）、介面美化（`.streamlit/config.toml` + CSS）
- [x] 陣容改存在 `data/state.json`（`state.py`）；`leagues.py` 的 initial_roster 只用來初始化
- [x] 「✏️ 陣容與對戰」編輯頁：手動同步陣容異動與本週比分（存進 state.json）
- 曾經做過網頁內建 AI 對話（Claude API），但使用者**不想額外付費**，已經移除。截圖分析改在 Claude Code 裡做（Pro 方案內含），用 `/同步` 指令。不要再提議需要付費 API 的功能
- [ ] Yahoo 核准後：接上 `yahoo_client.py`，自動抓陣容、FA、對戰比分
- [x] LINE 推播：`notify.py`（`--dry-run` 可以預覽）、`daily.py` 負責組訊息、`line_push.py` 負責發送；`.env` 要有 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID。10/27 測試推播成功
- [x] GitHub repo jengjih/fantasy-advisor（公開；gh CLI 在 ~/.local/bin/gh）：
  - `data-sync.yml`：每天台北 15:30、21:30、23:30 跑 `sync.py`，從 ESPN 抓數據存成 `data/snapshot/` 再 commit。Mac 不用開（原本的 launchd 同步已在 10/29 移除）
  - GitHub Actions 的推播都用 NBA_SOURCE=snapshot 讀快照；傷病從 ESPN 即時抓；LINE 金鑰存在 repo secrets：
    - 每晚 22:00 台北（`daily-push.yml`）：`notify.py` 推今日指令
    - 16:00 台北（`afternoon.yml`）：`--mode afternoon`，搖擺項落後或出賽人次輸對手 3 以上才推；比分超過 36 小時就不用；超過 3 天沒更新就提醒。baek's Grand League 週一到週四原則上不推；如果把落後的搖擺項追回來就能扭轉勝負，才破例。兩個聯盟合成一則
    - 每 30 分鐘（`injury-watch.yml`）：`--mode injury`，陣容裡（不含 IL）的球員 ESPN 預估缺陣 28 天以上或出現重傷關鍵字就推；`data/alerts.json` 記錄已通知過的，30 天內不重複推
  - 程式碼改完要自己 commit、push（sync.py 和網頁的「儲存」只會 add data/）。網頁編輯頁儲存時會自動同步（cloud_sync.push_data），也有「立即同步」按鈕
- [x] Streamlit Community Cloud 已部署：https://lesunshine-advisor.streamlit.app（唯讀模式，secrets 設 APP_MODE=cloud、NBA_SOURCE=snapshot；依賴用 requirements.txt）。Streamlit 拿不到私人 repo 的權限，所以 10/28 使用者決定把 repo 改成 public（已確認裡面沒有金鑰和個資）。repo 公開後，任何新檔案都不能放金鑰或個資
