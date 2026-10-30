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
1. **每次對話開頭先讀 `data/advisor_notes.md`**（本週計劃、已做的換人、交易決定），再讀 `data/state.json`。使用者的需求類型、終極目標（兩個聯盟都贏宿敵）與各類請求的處理方式見 `docs/使用者需求與工作流程.md`。
2. 收到截圖照 `.claude/commands/同步.md`（使用者打 `/同步`）的步驟更新資料。
3. **直接在 main 分支 commit 並 push**（先 `git checkout main && git pull`），不要開新分支或 PR；作戰卡 App 和推播都讀 main。執行 `uv run python sync.py` 會自動 commit、push data/。
4. 對話結尾更新 `data/advisor_notes.md`，寫下新的決定和接下來的計劃。
5. repo 是公開的：筆記和程式裡不能放金鑰、Email 或任何個資。
6. **每次回覆的最後一步，用 PushNotification 工具推一則手機通知**（一行、200 字內，先講結論，例如「懂球帝：週五放 Edey 簽 G. Allen，回來看細節」）。一定要等回覆文字全部寫完才推，不要在開頭或中途推：太早推的時候使用者可能還在看畫面，通知會被略過，等他切去別的 App 就收不到了。

## 目標
連結 Yahoo Fantasy API 和 NBA 數據，替兩個聯盟產生每日建議，最後做成手機作戰卡 App，再加上 LINE 推播（LINE Notify 已停用，要用 Messaging API）。

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
5. [x] 推播改成「行動卡」（10/31：App＋LINE 作戰卡推播）：具體 Drop/Add 與理由；沒事不推；週日 Adds 最後提醒；先發球員 Q/GTD 提醒
6. [ ] 交易評估（傳交易截圖 → 各比項變化）
7. [x] 簽人推薦排除小樣本（出賽太少或上場時間短）、W、O、Q（作戰卡的 Adds 候選）

## 本週推演（`plan.py` → `projection.py`，10/30 完成）
- 每天先發：當天有比賽、沒缺陣的人依「每場價值」排序填滿先發位；GTD 以 75% 機率計
- 結算預測：Matchup 截圖的比分＋截圖後剩下的賽程（雙方陣容）；命中率用「命中數 ÷ 命中率」反推已出手數。需要 state.json 的 `opponent_roster`（本週）
- Adds 規劃：貪婪法，每步挑「哪天、放誰、簽誰」讓本週預期價值增加最多；`untouchable`＋`core`（leagues.py）不釋出；長期價值比新簽的人高 2.5 以上也不釋出（但長期排名落在全聯盟持有球員後 20% 的串流位隨時可換）；候選人優先用截圖的 FA 名單
- 勝率模擬（`simulate()`，10/30 加入）：蒙地卡羅 5000 次，出手／籃板等用卜瓦松、命中用二項分布，GTD 依機率上場；plan.py 會列出「不換人」和「照 Adds 規劃換人」兩種情況的本週勝率與搖擺項機率
- 作戰卡 App 的資料（app_data.py）也建立在這套上

## 季末預測（`season.py` → `season.py` 模組，10/30 完成）
- `data/league_rosters.json`：全聯盟各隊陣容（含 IL）、戰績表（比項 W-L-T）、本週目前比分；使用者傳截圖後手動更新
- 球員能力：本季＋上季（當作已打 20 場）；整季賽程存在 `data/snapshot/season_schedule.json`（`--refresh` 重抓）
- 逐週模擬每隊數據總和（每日先發上限、傷兵回歸日），例行賽兩兩比項對決；每週誰對誰不知道時隨機排循環賽；季後賽依 Yahoo 設定（誰是懂球帝 6 隊、3/15 起 3 週、前 2 名輪空、重新排種子）
- 限制：陣容固定，不算串流、交易
- `rival.py`：在季末模擬上加「虛擬串流位」和交易，算最終名次贏過宿敵的機率（`--stream 6`、`--give/--get/--partner`）

## 作戰卡 App（v2.0，10/31）
- 網址 https://jengjih.github.io/fantasy-advisor/（GitHub Pages，`pages.yml` 發布；主畫面 App；舊的 Streamlit 網頁 10/31 已移除）
- 前端 `web/`（純 HTML/CSS/JS，`?data=`、`?tab=`、`?theme=`、`?now=`、`?nosw=1` 方便截圖測試）；資料 `build_app.py` → `src/fantasy_advisor/app_data.py` → `data/app/today.json`（格式 `docs/app-data-contract.md`，不進 git，發布時產生）
- 比分：Yahoo 截圖＋截圖之後的 ESPN 每場數據（`live_score.py`，陣容每天的變化靠 state 的 `roster_log`）；沒截圖就全部 ESPN 估算
- 對話決定的換人與保留名單：`state.save_plan(label, planned_adds, keep)`，App 照著列；宿敵資料 `data/rivals.json`
- 改了前端要截圖自我檢查（淺色／深色、375／390 寬），確認沒有破圖、跑版才推

## 每日建議 SOP
1. 陣容檢查：有比賽的球員被放在 BN、掛 O 卻占著先發位置
2. 比項分類：已鎖定、放棄（聯盟二的 TO）、搖擺（差距在 3–5 單位內）
3. 簽人：只考慮純 FA（不要 waiver 上的球員），避開掛 O 或 GTD 的球員，優先考慮 B2B 或小比賽日出賽者
4. 推薦球員時要列出：姓名、位置、對手、開打時間、能補的比項、是否為純 FA
5. 宿敵監控：週末提出防守性的建議

## 技術與進度
- Python 3.12，用 uv 管理（`uv run ...`；Mac 上是 `~/.local/bin/uv run ...`）。已安裝：yahoo_oauth, yahoo_fantasy_api, nba_api, pandas, pillow（圖示）, python-dotenv
- [x] 階段 0：環境安裝完成
- [x] Yahoo App 已建立，金鑰放在 `.env`，OAuth 可以取得 token。但 Fantasy API 回 403：Yahoo 從 2026-07 起要求申請核准（sports.yahoo.com/developer/access）。使用者 2026-10-27 送出申請，核准後通常要建一個新 App，再把新的 Client ID 交給 Yahoo（見 yfpy issue #84）
- [x] NBA 數據：`src/fantasy_advisor/{nba_data,analysis,leagues}.py`
  - 數據來源（10/29 起全部改用 ESPN，雲端主機也連得到）：scoreboard（賽程，抓本週一起 21 天）、statistics/byathlete（本季與上季總和，上季當 6 場先驗做平滑）、injuries（傷病）。原本的 nba_api 會被 stats.nba.com 擋雲端主機，已不用
  - 陣容在 `leagues.py` 手動維護（Gemini 原文的 Lonzo 是筆誤，應為 LaMelo Ball，現在在 MIN）
- [x] 全中文化（`zh.py`）
- [x] 陣容改存在 `data/state.json`（`state.py`）；`leagues.py` 的 initial_roster 只用來初始化
- 曾經在舊網頁做過內建 AI 對話（Claude API），但使用者**不想額外付費**，已經移除。截圖分析改在 Claude Code 裡做（Pro 方案內含），用 `/同步` 指令。不要再提議需要付費 API 的功能
- [ ] Yahoo 核准後：接上 `yahoo_client.py`，自動抓陣容、FA、對戰比分
- [x] LINE 推播：`notify.py`（`--dry-run` 可以預覽）、`daily.py` 負責組訊息、`line_push.py` 負責發送；`.env` 要有 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID。10/27 測試推播成功
- [x] GitHub repo jengjih/fantasy-advisor（公開；gh CLI 在 ~/.local/bin/gh）：
  - `data-sync.yml`：每天台北 15:30、21:30、23:30 跑 `sync.py`，從 ESPN 抓數據存成 `data/snapshot/` 再 commit。Mac 不用開（原本的 launchd 同步已在 10/29 移除）
  - GitHub Actions 的推播都用 NBA_SOURCE=snapshot 讀快照；傷病從 ESPN 即時抓；LINE 金鑰存在 repo secrets：
    - 台北 16:00、22:00（`card-push.yml`）：`notify.py` 作戰卡推播（`daily.build_card_push`）。只推「現在就能做（earliest 已過、deadline 未到）、還沒推過」的動作，以及 danger／warning 提醒（同一則一週一次）；「確認」型動作不推；沒事就不推。推過的記在 `data/pushed.json`（保留 14 天）。訊息是摘要＋App 連結
    - 每 30 分鐘（`injury-watch.yml`）：`--mode injury`，陣容裡（不含 IL）的球員 ESPN 預估缺陣 28 天以上或出現重傷關鍵字就推；`data/alerts.json` 記錄已通知過的，30 天內不重複推
  - 程式碼改完要自己 commit、push（sync.py 只會 add data/）
- repo 在 10/28 改成 public（當時為了 Streamlit；10/31 Streamlit 已移除，改用 GitHub Pages 也需要公開）。任何新檔案都不能放金鑰或個資
