# 作戰卡 App 資料格式（today.json）

產生者：`build_app.py`（GitHub Actions 每次同步後執行），輸出 `data/app/today.json`。
使用者：`web/` 的靜態 App（GitHub Pages），用 `fetch("data/today.json")` 讀取。
範例：`web/data/today.json`（開發用假資料，結構與正式版相同）。

所有時間都是**台北時間**的 ISO 字串（`+08:00`）；`*_label` 是已經排好版的中文，前端直接顯示，不要自己再算。
機率是 0–1 的小數。數字欄位可能是 `null`（資料不足），前端要顯示「—」而不是 `null`／`NaN`。

```jsonc
{
  "version": 1,
  "generated_at": "2026-10-31T14:21+08:00",
  "generated_label": "10/31 14:21 更新",
  "nba_day": "2026-10-31",                 // 美東比賽日
  "nba_day_label": "週六 10/31（台北 11/1 早上開打）",

  // 今天要做的事，已依截止時間排序。done 由前端用 localStorage 記（key = id）
  "actions": [{
    "id": "2026-10-31|聯盟一|lineup",     // 穩定且唯一
    "league": "聯盟一", "league_name": "誰是懂球帝",
    "type": "lineup",                      // lineup 排先發 | add 簽人 | il 傷兵名單 | trade 交易 | check 確認事項
    "priority": "high",                    // high | normal
    "title": "把 Harper、Camara 移上先發",
    "detail": "週六 8 人有比賽、只有 6 人在先發。到 My Team 按 Start Active Players 或手動移動。",
    "deadline": "2026-11-01T07:00+08:00", "deadline_label": "11/1（日）07:00 前",
    "earliest": null, "earliest_label": null,   // 例如「Edey 打完後（約 12:30）」
    "impact": {"before": 0.93, "after": 0.97, "label": "本週勝率 93% → 97%"},  // 可為 null
    "players": [                            // 可為空陣列
      {"name": "Dylan Harper", "team": "SAS", "team_zh": "馬刺", "pos": "後衛",
       "headshot": "https://…png", "role": "start"}   // role: start | bench | add | drop | il_in | il_out
    ]
  }],

  // 不需要動手但要知道的事
  "alerts": [{"level": "warning", "league": "聯盟二", "league_name": "baek's Grand League",
              "text": "對手 Ja Morant 每日觀察（腿後肌），可能缺陣"}],   // level: danger | warning | info | success

  "leagues": [{
    "key": "聯盟一", "name": "誰是懂球帝", "team_name": "LeSunshine",
    "week": 2, "week_label": "第 2 週（10/26–11/1）",
    "opponent": "永吉路懂球帝",
    "score": {"w": 6, "l": 4, "t": 1,
              "source": "espn",            // yahoo = 截圖 | yahoo+espn = 截圖＋之後的 ESPN 數據 | espn = 全部 ESPN 估算
              "source_label": "ESPN 估算・10/31 14:21"},
    "forecast": {"w": 9, "l": 2, "t": 0, "win_prob": 0.97, "win_prob_no_action": 0.93},
    "adds": {"used": 6, "total": 8},
    "games_left": {"mine": 12.5, "opp": 10.0},
    "categories": [{
      "cat": "FGM", "label": "命中數",
      "mine": "139", "opp": "139",          // 目前（字串，照原格式）
      "mine_final": "201", "opp_final": "188",   // 預測結算
      "win_prob": 0.72,
      "status": "swing"                     // lead 穩贏 | swing 搖擺 | behind 落後 | punt 放棄
    }],
    "days": [{"date": "2026-10-31", "label": "週六 10/31", "playing": 8, "slots": 10, "open": 2,
              "starters": ["Victor Wembanyama", "…"], "bench": []}],
    "roster": [{"name": "Victor Wembanyama", "team": "SAS", "team_zh": "馬刺", "pos": "中鋒",
                "headshot": "https://…png", "slot": "active",     // active | il
                "injury": null, "injury_label": null,             // 例如 "Day-To-Day" / "每日觀察"
                "games_left": 2, "value": 9.8, "rank": 2}]
  }],

  // 宿敵追蹤（終極目標：兩個聯盟季末都贏宿敵）
  "rivals": [{"league": "聯盟一", "league_name": "誰是懂球帝", "rival": "尚恩·李文斯頓",
              "beat_prob": 0.84, "beat_label": "季末贏他的機率約 84%",
              "updated_label": "10/30 模擬", "notes": ["他本週只用 1 次 add", "弱點：FT%、3PTM、3PT%、TO"]}]
}
```

聯盟數量固定是 2，但前端不要寫死名稱，一律讀 `league_name`。
