"""每日推播：把兩個聯盟的「今日指令」整理成一則純文字訊息（LINE 不支援粗體）。"""

import re

from . import analysis as an
from . import state as state_store
from . import zh
from .leagues import LEAGUES
from .nba_data import normalize

STREAM_PICKS = 3


def _plain(msg: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", msg)


def build_report(schedule, players, injuries, fetched_at: str = "", day=None) -> str:
    day = day or an.today_et()
    state = state_store.load()
    lines = [f"🏀 LeSunshine 今日指令", f"NBA 比賽日 {day:%m/%d}（週{an.WEEKDAY[day.weekday()]}）・開打時間為台北時間"]
    if fetched_at:
        lines.append(f"球員數據：{fetched_at}・傷病：即時")

    for label in LEAGUES:
        lg = state_store.league_view(label, state)
        p = an.add_zscores(players, lg["categories"], lg["punt"], lg["teams"])
        roster, alerts = an.roster_report(lg, p, injuries, schedule, day)

        lines += ["", f"【{label}・{lg['name']}】"]
        playing = roster[(roster["名單"] == "陣容") & roster["_plays_today"] & (roster["_status"] != "Out")]
        for _, r in playing.iterrows():
            lines.append(f"  • {r['球員']}　{r['今天']}")
        for level, msg in alerts:
            if msg.startswith("▶️"):  # 出賽名單上面已列出，這裡只留按鈕提醒
                lines.append("▶️ 記得到 Yahoo 按 Start Active Players")
            else:
                lines.append(_plain(msg))

        m = state[label].get("matchup")
        if m:
            w = l = 0
            for c in m["categories"]:
                try:
                    a, b = float(c["mine"]), float(c["opponent"])
                    better = a < b if c["category"] == "TO" else a > b
                    w += better
                    l += (not better) and a != b
                except ValueError:
                    pass
            lines.append(f"⚔️ 第 {m['week']} 週 vs {m['opponent']}：目前 {w} 勝 {l} 敗（{m['saved_at']} 記錄）")

        adds_ok = day.weekday() >= lg.get("adds_from_weekday", 0)
        if adds_ok:
            my = {normalize(n) for n in lg["roster"] + lg["il"]}
            cands = an.stream_candidates(lg, p, injuries, schedule, day, my, [], only_today=True,
                                         skip_top=True, limit=STREAM_PICKS)
            if not cands.empty:
                lines.append("🎯 今日串流候選（請到 Yahoo 確認是 FA）：")
                for _, c in cands.iterrows():
                    lines.append(f"  • {c['球員']}（{c['球隊']}，本週 {c['本週剩餘']} 場）{c['強項']}")

    return "\n".join(lines)
