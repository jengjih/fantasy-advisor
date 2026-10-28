---
description: 依使用者貼上的 Yahoo 截圖，同步 data/state.json 的陣容與對戰比分
---

使用者貼了 Yahoo Fantasy 截圖（My Team、Matchup 或 FA 名單）。請：

1. 判斷是哪個聯盟：8 隊／每週 8 adds＝聯盟一（誰是懂球帝）；12 隊／每週 4 adds＝聯盟二（baek's Grand League）。看不出來就問。
2. 讀 `data/state.json`，跟截圖比對：
   - My Team：同步 roster 與 il（球員名字用 NBA 官方拼法，例如 Nickeil Alexander-Walker，不是 N. Alexander-Walker）。
   - Matchup：用 `fantasy_advisor.state.save_matchup()` 記錄週次、對手、各比項（字串照抄）、已用 adds，以及對手本週剩餘出賽人次（opp_games_left，看不到就填 -1）。
   - FA 名單：不改檔案，直接依該聯盟戰術推薦人選。
3. 修改請用 `fantasy_advisor.state` 裡的函式（apply_roster_changes、save_matchup），用 `~/.local/bin/uv run python` 執行。
4. 改完後執行 `~/.local/bin/uv run python sync.py`，把資料推上雲端（16:00 和 22:00 的推播要用）。
5. 用白話中文回報：改了什麼、今天該做什麼（排陣、簽人），以及哪些比項是搖擺項。

$ARGUMENTS
