"""推播訊息產生器（純文字，LINE 不支援粗體）。

- build_report：每晚 22:00 的今日指令
- build_afternoon：16:00 的條件式搶人推播（沒有需要就回傳 None，不推）
- find_major_injuries / injury_message：重大傷病（預估缺陣 4 週以上）即時通知
"""

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

from . import analysis as an
from . import state as state_store
from . import zh
from .leagues import LEAGUES
from .nba_data import normalize

STREAM_PICKS = 3
FRESH_HOURS = 36          # 比分在這個時間內更新過，才拿來判斷搶人
STALE_REMIND_DAYS = 3     # 超過這麼多天沒更新比分，提醒使用者
FA_FRESH_HOURS = 48       # 截圖確認過的 FA 名單有效時間
GAMES_GAP_ALERT = 3       # 對手剩餘出賽人次多我 3 以上就提醒
MAJOR_INJURY_DAYS = 28
MAJOR_KEYWORDS = re.compile(
    r"surgery|torn|tear\b|fractur|acl\b|achilles|season-ending|rest of the season|indefinitely|"
    r"\b(?:four|five|six|seven|eight|[4-9]|1[0-9])\s*(?:-|to)?\s*(?:\w+\s+)?weeks|\bmonths?\b", re.I)


def _plain(msg: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", msg)


def _scored(players, lg):
    return an.add_zscores(players, lg["categories"], lg["punt"], lg["teams"])


def _fresh_fa_keys(state: dict, label: str) -> set[str] | None:
    """使用者 48 小時內截圖確認過的 FA 名單；沒有就回傳 None（改用「排除排名前段」的估計）。"""
    fa = state[label].get("free_agents")
    if not fa or (datetime.now(ZoneInfo("Asia/Taipei")) - datetime.fromisoformat(fa["saved_ts"])).total_seconds() > FA_FRESH_HOURS * 3600:
        return None
    return {normalize(n) for n in fa["names"]}


def _stream_lines(lg, players, injuries, schedule, day, focus, only_today,
                  fa_keys=None, count_days=None) -> list[str]:
    my = {normalize(n) for n in lg["roster"] + lg["il"]}
    cands = an.stream_candidates(lg, _scored(players, lg), injuries, schedule, day, my, focus,
                                 only_today=only_today, skip_top=True, limit=STREAM_PICKS,
                                 only_keys=fa_keys, count_days=count_days)
    games = "空位日可上" if count_days is not None else "本週"
    return [f"  • {c['球員']}（{c['位置']}，{c['球隊']}，{c['今天']}，{games} {c['本週剩餘']} 場）{c['強項']}"
            for _, c in cands.iterrows() if c["本週剩餘"] > 0]


# ---------- 每晚 22:00：今日指令 ----------

def build_report(schedule, players, injuries, fetched_at: str = "", day=None) -> str:
    day = day or an.today_et()
    state = state_store.load()
    lines = ["🏀 LeSunshine 今日指令",
             f"NBA 比賽日 {day:%m/%d}（週{an.WEEKDAY[day.weekday()]}）・開打時間為台北時間"]
    if fetched_at:
        lines.append(f"球員數據：{fetched_at}・傷病：即時")

    for label in LEAGUES:
        lg = state_store.league_view(label, state)
        roster, alerts = an.roster_report(lg, _scored(players, lg), injuries, schedule, day)

        lines += ["", f"【{lg['name']}】"]
        playing = roster[(roster["名單"] == "陣容") & roster["_plays_today"] & (roster["_status"] != "Out")]
        for _, r in playing.iterrows():
            gtd = "　⚠️每日觀察，賽前可能變動" if r["_status"] == "Day-To-Day" else ""
            lines.append(f"  • {r['球員']}　{r['今天']}{gtd}")
        for _, msg in alerts:
            if msg.startswith("▶️"):  # 出賽名單上面已列出，這裡只留按鈕提醒
                lines.append("▶️ 記得到 Yahoo 按 Start Active Players")
            elif not msg.startswith("⚠️"):  # GTD 已經標在名單上
                lines.append(_plain(msg))

        m = state[label].get("matchup")
        if m:
            _, w, l = an.matchup_rows(m, lg["punt"])
            lines.append(f"⚔️ 第 {m['week']} 週 vs {m['opponent']}：目前 {w} 勝 {l} 敗（{m['saved_at']} 記錄）")

        if day.weekday() >= lg.get("adds_from_weekday", 0):
            fa_keys = _fresh_fa_keys(state, label)
            picks = _stream_lines(lg, players, injuries, schedule, day, [], only_today=True, fa_keys=fa_keys)
            if picks:
                note = "（從你截圖的 FA 名單挑）" if fa_keys else "（請到 Yahoo 確認是 FA）"
                lines += [f"🎯 今日串流候選{note}："] + picks

    return "\n".join(lines)


# ---------- 16:00：條件式搶人推播 ----------

def _matchup_age_hours(m: dict) -> float:
    tz = ZoneInfo("Asia/Taipei")
    if m.get("saved_ts"):
        saved = datetime.fromisoformat(m["saved_ts"])
    else:  # 舊格式只有「月-日 時:分」
        saved = datetime.strptime(f"{datetime.now(tz).year}-{m['saved_at']}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    return (datetime.now(tz) - saved).total_seconds() / 3600


def build_afternoon(schedule, players, injuries, day=None) -> str | None:
    """美東剛進入新的一天：搖擺項落後、或出賽人次輸對手時才推；都沒有就回傳 None（不推）。"""
    day = day or an.today_et()
    monday, _ = an.week_range(day)
    state = state_store.load()
    sections, reminders = [], []

    for label in LEAGUES:
        lg = state_store.league_view(label, state)
        m = state[label].get("matchup")
        age = _matchup_age_hours(m) if m else None
        if age is None or age > STALE_REMIND_DAYS * 24:
            how = "從未記錄" if age is None else f"已 {int(age // 24)} 天沒更新"
            reminders.append(f"⏰ {lg['name']} 的對戰比分{how}，請在 Mac 網頁或傳截圖更新，搶人分析才準。")
        if not m or age > FRESH_HOURS or m.get("week_monday") != str(monday):
            continue

        rows, w, l = an.matchup_rows(m, lg["punt"])
        losing = [r for r in rows if r["swing"] and r["lead"] is False]
        shaky = [r for r in rows if r["swing"] and r["lead"] is True]
        chase = [r for r in losing if r["cat"] != "TO"]  # 只差失誤 TO 不值得為它搶人
        mine_left = m.get("my_games_left", -1)
        if mine_left < 0:
            mine_left = an.my_games_left(lg, players, injuries, schedule, day)
        opp_left = m.get("opp_games_left", -1)
        gap = opp_left - mine_left if opp_left >= 0 else 0
        adds_left = lg["weekly_adds"] - max(m["adds_used"], 0)
        if adds_left <= 0 or not (chase or gap >= GAMES_GAP_ALERT):
            continue

        exception = False
        if day.weekday() < lg.get("adds_from_weekday", 0):  # 聯盟二週一到週四原則上不用 adds
            # 破例條件：把「落後但追得回」的比項追回來，就能扭轉整場勝負
            if not (chase and w + len(losing) > l - len(losing)):
                continue
            exception = True

        out = [f"【{lg['name']}】vs {m['opponent']}：{w} 勝 {l} 敗",
               f"Adds 剩 {adds_left} 次" + ("　📌 週間破例：比分迫近，建議出手" if exception else "")]
        fmt = lambda rs: "、".join(f"{zh.cat(r['cat'])} {r['mine']} vs {r['opp']}" for r in rs)
        if losing:
            out.append("🔻 落後但追得回：" + fmt(losing))
        if shaky:
            out.append("🔸 領先但不穩：" + fmt(shaky))
        if opp_left >= 0:
            out.append(f"🏃 本週剩餘出賽：我 {mine_left} vs 對手 {opp_left}"
                       + ("　⚠️ 場次落後" if gap >= GAMES_GAP_ALERT else ""))

        slots = an.open_slots_by_day(lg, players, injuries, schedule, day)
        open_days = [d for d, n in slots.items() if n > 0]
        if open_days:
            out.append("📅 有空先發位的日子：" + "、".join(f"週{an.WEEKDAY[d.weekday()]}（空 {slots[d]}）" for d in open_days))
        else:
            out.append("📅 本週剩下每天先發都已排滿：新簽的人要換掉陣容裡價值最低、場次少的球員才有用")
        focus = [r["cat"] for r in chase]
        fa_keys = _fresh_fa_keys(state, label)
        picks = _stream_lines(lg, players, injuries, schedule, day, focus, only_today=False,
                              fa_keys=fa_keys, count_days=open_days or None)
        if picks:
            target = "、".join(zh.CATEGORY[c] for c in focus) if focus else "出賽人次"
            src = "從你截圖的 FA 名單挑" if fa_keys else "請確認是 FA"
            out += [f"🎯 建議搶人（補{target}，{src}）："] + picks
        sections.append("\n".join(out))

    if not sections and not reminders:
        return None
    head = f"⚡ LeSunshine 搶人時間（美東 {day:%m/%d} 週{an.WEEKDAY[day.weekday()]}）"
    return "\n\n".join([head] + sections + reminders)


# ---------- 重大傷病即時通知 ----------

def is_major(row: pd.Series, today: date) -> bool:
    if row["injury_status"] != "Out":
        return False
    try:
        if (date.fromisoformat(str(row["return_date"])[:10]) - today).days >= MAJOR_INJURY_DAYS:
            return True
    except ValueError:
        pass
    return bool(MAJOR_KEYWORDS.search(f"{row['injury_note']} {row['injury_long']}"))


def find_major_injuries(injuries: pd.DataFrame, alerted: dict) -> list[tuple[str, str, pd.Series]]:
    """[(聯盟, 球員, 傷病資料)]：陣容裡（不含 IL）新出現的重大傷病；30 天內通知過的跳過。"""
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    state = state_store.load()
    inj = injuries.set_index("key")
    hits = []
    for label in LEAGUES:
        for name in state[label]["roster"]:
            key = normalize(name)
            if key not in inj.index or not is_major(inj.loc[key], today):
                continue
            last = alerted.get(f"{label}|{key}")
            if last and (today - date.fromisoformat(last)).days < 30:
                continue
            hits.append((label, name, inj.loc[key]))
    return hits


def injury_message(hits, schedule, players, injuries) -> str:
    day = an.today_et()
    state = state_store.load()
    lines = ["🚨 重大傷病通知"]
    for label, name, row in hits:
        lg = state_store.league_view(label, state)
        il_free = 3 - len(lg["il"])
        ret = f"，ESPN 預估 {str(row['return_date'])[:10]} 回歸" if row["return_date"] else ""
        lines += ["", f"【{lg['name']}】{name}：{zh.injury(row['injury_status'])}{ret}",
                  f"ESPN：{row['injury_note']}",
                  "👉 建議：" + (f"移入 IL（還有 {il_free} 格），再簽人補位" if il_free > 0 else "IL 已滿，考慮 Drop 換人")]
        picks = _stream_lines(lg, players, injuries, schedule, day, [], only_today=False)
        if picks:
            lines += ["🎯 替補候選（請到 Yahoo 確認是 FA）："] + picks
    return "\n".join(lines)
