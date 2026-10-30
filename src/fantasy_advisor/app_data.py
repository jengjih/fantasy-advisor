"""作戰卡 App 的資料（data/app/today.json）：今天要做的事、本週戰況、陣容、宿敵。

格式見 docs/app-data-contract.md。把手機對話裡學到的判斷寫成規則，讓 App 打開就知道今天怎麼排：
- Daily-Today：要釋出的人當天還有比賽，等他打完再換；簽進來的人要在他開打前簽好
- 不釋出 untouchable／core／state 的 keep（例如潛力新秀）
- 簽人不推：O、Q、每日觀察、本季出賽太少、會拉低搖擺命中率的人
- 每個動作附台北時間的截止時間與「照做 vs 不做」的本週勝率
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from . import analysis as an
from . import projection as pj
from . import zh
from .leagues import LEAGUES
from .nba_data import normalize

ROOT = Path(__file__).resolve().parents[2]
OUT_FILE = ROOT / "data" / "app" / "today.json"
RIVALS_FILE = ROOT / "data" / "rivals.json"
TPE, ET = ZoneInfo("Asia/Taipei"), ZoneInfo("America/New_York")

GAME_HOURS = 2.5           # 一場比賽約 2.5 小時（估「打完」的時間）
FA_STALE_HOURS = 48
MIN_GP = 3                 # 本季出賽少於 3 場的不推（小樣本）
PCT_GUARD = -0.5           # 搖擺的命中率比項 z 低於這個的人不推（例：命中率 .316 的 Wagler）
SIM_RUNS = 3000
SWING_LOW, SWING_HIGH = 0.25, 0.75


# ---------- 小工具 ----------

def _wd(d: date) -> str:
    return f"週{an.WEEKDAY[d.weekday()]}"


def _tpe_label(t: datetime) -> str:
    t = t.astimezone(TPE)
    return f"{t.month}/{t.day}（{'一二三四五六日'[t.weekday()]}）{t:%H:%M}"


def _tips(schedule: pd.DataFrame) -> dict[tuple[date, str], datetime]:
    """(美東日期, 球隊) → 台北開打時間。"""
    out = {}
    for _, g in schedule.iterrows():
        tip = g["tip_taipei"].to_pydatetime()
        out[(g["date"], g["home"])] = out[(g["date"], g["away"])] = tip
    return out


def _player_info(scored: pd.DataFrame, name: str) -> dict:
    p = an.find_player(scored, name)
    if p is None:
        return {"name": name, "team": None, "team_zh": None, "pos": None, "headshot": None}
    return {"name": name, "team": p["team"], "team_zh": zh.team(p["team"]), "pos": zh.pos(p["pos"]),
            "headshot": p["headshot"] or None}


def _num(x, nd=1):
    return None if x is None or pd.isna(x) else round(float(x), nd)


# ---------- 陣容歷史（ESPN 自動比分用） ----------

def roster_by_day(lg_state: dict, monday: date, last: date) -> dict[date, list[str]]:
    """用 roster_log 倒推本週每天陣容裡有誰（不含 IL）。"""
    log = sorted(lg_state.get("roster_log", []), key=lambda e: e["date"])
    out = {}
    for d in pj.days_between(monday, last):
        roster = set(lg_state["roster"])
        for e in reversed(log):          # 把 d 之後才生效的異動倒回去
            if date.fromisoformat(e["date"]) > d:
                roster -= set(e["add"])
                roster |= set(e["drop"])
        out[d] = sorted(roster)
    return out


def _yahoo_plus(cur: dict, side: int, before: dict, after: dict) -> dict:
    """Yahoo 截圖的數字（準）＋截圖之後的 ESPN 數據。命中率只有百分比，出手數用同期 ESPN 的出手數估。"""
    t = {k: after[k] for k in after if k in TOTAL_KEYS}
    for cat, stat in an.COUNTING_CATS.items():
        if cat in cur:
            t[stat] = cur[cat][side] + after[stat]
    for cat, (made, att) in an.PCT_CATS.items():
        if cat not in cur:
            continue
        made_cat = {"FGM": "FGM", "FG3M": "3PTM"}.get(made)
        pct = cur[cat][side]
        if made_cat in cur and pct > 0:
            base_att, base_made = cur[made_cat][side] / pct, cur[made_cat][side]
        else:
            base_att = before[att]
            base_made = pct * base_att
        t[att], t[made] = base_att + after[att], base_made + after[made]
    return t


TOTAL_KEYS = pj.TOTALS


def live_matchup(label: str, lg: dict, st: dict, m: dict | None, opp_names: list[str],
                 values: dict[str, float], schedule: pd.DataFrame, day: date) -> tuple[dict | None, str, str]:
    """本週目前比分（到昨天為止）。回傳（和 state.json 的 matchup 同格式的 dict, 來源, 說明）。
    - Yahoo 截圖已涵蓋到昨天：直接用截圖（最準）
    - 截圖比較舊：截圖＋截圖之後的 ESPN 數據
    - 沒有截圖：全部用 ESPN 估算（不知道雙方板凳和對手週間換人，會有誤差）"""
    monday, _ = an.week_range(day)
    last = day - timedelta(days=1)                 # 已經打完的最後一天
    yahoo_ok = bool(m and m.get("week_monday") == str(monday) and m.get("saved_ts"))
    shot = lambda: f"Yahoo 截圖・{datetime.fromisoformat(m['saved_ts']).astimezone(TPE):%m/%d %H:%M}".replace("/0", "/").lstrip("0")
    if yahoo_ok and pj.remaining_start(m) > last:
        return m, "yahoo", shot()
    if last < monday:
        return (m if yahoo_ok else None), "yahoo", shot() if yahoo_ok else ""
    try:
        from . import live_score as ls
        box = ls.fetch_boxscores(schedule, monday, last)
        mine_days = roster_by_day(st[label], monday, last)
        opp_days = {d: opp_names for d in mine_days}

        def totals(days_map, lo, hi):
            sub = {d: v for d, v in days_map.items() if lo <= d <= hi}
            return ls.side_totals(box, sub, lg["starters"], values)

        if yahoo_ok:
            ys = pj.remaining_start(m)
            cur = pj._current(m)
            sides = [_yahoo_plus(cur, i, totals(dm, monday, ys - timedelta(days=1)), totals(dm, ys, last))
                     for i, dm in enumerate((mine_days, opp_days))]
            src, label_txt = "yahoo+espn", f"{shot()}＋ESPN 打到{_wd(last)}"
        else:
            sides = [totals(dm, monday, last) for dm in (mine_days, opp_days)]
            src, label_txt = "espn", f"ESPN 估算・打到{_wd(last)}"
        cats = ls.matchup_categories(lg, *sides)
    except Exception as e:  # ESPN 連不到：退回截圖
        print(f"⚠️ ESPN 自動比分失敗（{type(e).__name__}: {e}），改用截圖比分")
        return (m if yahoo_ok else None), "yahoo", shot() if yahoo_ok else ""
    # 假裝是「last 隔天美東中午」存的，predict/simulate 就會從 last+1 開始推算
    saved = datetime.combine(last + timedelta(days=1), datetime.min.time(), ET).replace(hour=12)
    return {"week": (m or {}).get("week"), "opponent": (m or {}).get("opponent"),
            "categories": cats, "adds_used": (m or {}).get("adds_used", -1),
            "saved_ts": saved.isoformat(), "saved_at": saved.astimezone(TPE).strftime("%m-%d %H:%M"),
            "week_monday": str(monday)}, src, label_txt


# ---------- 每個聯盟 ----------

def _planned_steps(lg_state, mine, scored, injuries, lg, empty, focus, schedule, day) -> dict:
    """state 的 planned_adds → plan_adds 同格式的 steps。已經換好、過期、或名字對不上的跳過。"""
    playing = pj.teams_playing(schedule)
    _, sunday = an.week_range(day)
    names = {x.name for x in mine}
    steps, members, roster = [], [], list(mine)
    for p in lg_state.get("planned_adds", []):
        d = max(date.fromisoformat(p["day"]), day)
        if d > sunday or p["drop"] not in names or p["add"] in names:
            continue
        new, _ = pj.resolve([p["add"]], scored, injuries, lg, empty, focus)
        if not new:
            continue
        members.append(new[0])
        step = {"day": d, "drop": p["drop"], "add": p["add"], "team": new[0].team, "planned": True,
                "add_days": [x for x in pj.days_between(d, sunday) if new[0].team in playing.get(x, ())]}
        days = pj.days_between(day, sunday)
        before = pj.expected(roster, playing, days, lg["starters"])[0]
        roster = pj.apply_steps(roster, members, [step])
        step["games"] = pj.expected(roster, playing, days, lg["starters"])[0] - before
        steps.append(step)
    return {"steps": steps, "members": members}


def _candidate_pool(lg, scored, injuries, empty, focus, exclude, fa_keys) -> list[pj.Member]:
    """Adds 候選：只要健康、本季有一定出場，且不會拉低搖擺中的命中率。"""
    inj = injuries.set_index("key")["injury_status"] if not injuries.empty else pd.Series(dtype=str)
    df = scored[~scored["key"].isin(exclude) & (scored["MIN"] >= an.MIN_STREAM_MINUTES) & (scored["GP"] >= MIN_GP)]
    df = df[df["key"].map(inj).fillna("") == ""]           # O、Q、每日觀察都不推
    for c in focus:
        if c in an.PCT_CATS:
            df = df[df[f"z_{c}"] >= PCT_GUARD]
    if fa_keys is not None:
        df = df[df["key"].isin(fa_keys)]
    else:
        df = df[df["rank"] > lg["teams"] * an.ROSTER_SIZE]
    df = df.assign(v=df.apply(lambda r: pj.game_value(r, lg, empty, focus), axis=1))
    return pj.resolve(df.nlargest(pj.POOL_SIZE, "v")["name"].tolist(), scored, injuries, lg, empty, focus)[0]


def build_league(label: str, st: dict, players: pd.DataFrame, injuries: pd.DataFrame,
                 schedule: pd.DataFrame, day: date, now: datetime) -> tuple[dict, list[dict], list[dict]]:
    """回傳（leagues[] 的一項, actions, alerts）。"""
    lg_state = st[label]
    lg = {**LEAGUES[label], "roster": lg_state["roster"], "il": lg_state["il"],
          "core": LEAGUES[label].get("core", []) + lg_state.get("keep", [])}
    monday, sunday = an.week_range(day)
    tips = _tips(schedule)
    playing = pj.teams_playing(schedule)
    name = lg["name"]
    actions, alerts = [], []
    alert = lambda level, text: alerts.append({"level": level, "league": label, "league_name": name, "text": text})

    m = lg_state.get("matchup")
    m = m if m and m.get("week_monday") == str(monday) else None
    opp_info = lg_state.get("opponent_roster")
    opp_info = opp_info if opp_info and opp_info.get("week_monday") == str(monday) else None
    opp_name = (opp_info or m or {}).get("opponent")

    scored, empty = pj.score(players, lg)
    base_mine, missing = pj.resolve(lg["roster"], scored, injuries, lg, empty)
    values = {x.name: x.value for x in base_mine}
    for n in missing:
        alert("warning", f"找不到 {n} 的 NBA 數據，可能拼錯或已經不在聯盟")

    # 目前比分（ESPN 估算或截圖）
    cur, source, source_label = None, "yahoo", ""
    opp = []
    if opp_info:
        opp, _ = pj.resolve(opp_info["roster"], scored, injuries, lg, empty)
        values.update({x.name: x.value for x in opp})
        cur, source, source_label = live_matchup(label, lg, st, m, opp_info["roster"], values, schedule, day)
    elif m:
        cur, source_label = m, "Yahoo 截圖"
        alert("warning", "還沒有本週對手陣容：傳一張對手陣容截圖，才能預測比數和勝率")
    else:
        alert("warning", "還沒有本週比分和對手陣容：傳 Matchup 和對手陣容截圖")

    # 要追的比項：有模擬就看「贏的機率在 20–80% 之間」的，否則看比分差距
    focus = []
    if cur and opp:
        sim0 = pj.simulate(lg, cur, base_mine, opp, schedule, runs=SIM_RUNS)
        focus = [c for c, p in sim0["cats"].items() if 0.2 <= p <= 0.8 and c not in lg["punt"] and c != "TO"]
    elif cur:
        rows, _, _ = an.matchup_rows(cur, lg["punt"])
        focus = [r["cat"] for r in rows if r["swing"] and r["cat"] != "TO"]
    mine, _ = pj.resolve(lg["roster"], scored, injuries, lg, empty, focus)

    # ---- 排先發（今天） ----
    today_on = [x for x in mine if x.team in playing.get(day, set()) and x.play_prob(day) > 0]
    if today_on:
        started = pj.lineup(mine, playing.get(day, set()), day, lg["starters"])
        sit = [x for x in today_on if x.name not in {s.name for s, _ in started}]
        first_tip = min(tips[(day, x.team)] for x in today_on)
        # 只列需要注意的人（坐板凳、每日觀察）；全部人都上先發就不用一一列出
        players_out = [{**_player_info(scored, x.name), "role": "bench"} for x in sit]
        players_out += [{**_player_info(scored, x.name), "role": "start"} for x, _ in started if x.status == "Day-To-Day"]
        gtd = [x.name for x in today_on if x.status == "Day-To-Day"]
        detail = "到 My Team 按 Start Active Players，確認有比賽的人都不在板凳（BN）。"
        if sit:
            detail += f"人太多：{'、'.join(x.name for x in sit)} 坐板凳（價值最低）。"
        if gtd:
            detail += f"{'、'.join(gtd)} 每日觀察，開打前再看一次。"
        busy = bool(sit or gtd)
        title = (f"排好{_wd(day)}先發（{len(today_on)} 人有比賽）" if busy else
                 f"確認{_wd(day)}先發（{len(today_on)} 人有比賽，" + ("剛好排滿）" if len(today_on) == lg["starters"] else "全部上先發）"))
        actions.append({
            "id": f"{day}|{label}|lineup", "league": label, "league_name": name, "type": "lineup" if busy else "check",
            "priority": "high" if busy else "normal", "title": title,
            "detail": detail, "deadline": first_tip.isoformat(), "deadline_label": _tpe_label(first_tip) + " 前",
            "earliest": None, "earliest_label": None, "impact": None, "players": players_out})

    # ---- Adds 規劃 ----
    adds_used = max((m or {}).get("adds_used", 0), 0)
    adds_left = lg["weekly_adds"] - adds_used
    sim_m = cur if (cur and opp) else None
    win_now = pj.simulate(lg, sim_m, mine, opp, schedule, runs=SIM_RUNS)["win"] if sim_m else None
    steps, pool = [], []
    if adds_left > 0:
        from_wd = lg.get("adds_from_weekday", 0)
        if from_wd and day.weekday() < from_wd and win_now is not None and win_now < 0.6:
            from_wd = 0   # 週間破例：比分很接近
            alert("info", f"本週勝率只有 {win_now:.0%}，週間也可以考慮用 adds")
        add_days = [d for d in pj.days_between(day, sunday) if d.weekday() >= from_wd]
        fa = lg_state.get("free_agents")
        fa_keys = {normalize(n) for n in fa["names"]} if fa else None
        fa_age = (now - datetime.fromisoformat(fa["saved_ts"])).total_seconds() / 3600 if fa else None
        exclude = {normalize(n) for n in lg["roster"] + lg["il"] + (opp_info["roster"] if opp_info else [])}
        pool = _candidate_pool(lg, scored, injuries, empty, focus, exclude, fa_keys)
        # 對話裡已經決定的換人優先（state 的 planned_adds），剩下的次數才交給規劃器
        planned = _planned_steps(lg_state, mine, scored, injuries, lg, empty, focus, schedule, day)
        pool += [x for x in planned["members"] if x.name not in {p.name for p in pool}]
        steps = planned["steps"][:adds_left]
        if add_days and adds_left > len(steps):
            base = pj.apply_steps(mine, pool, steps)
            more = pj.plan_adds(lg, base, [p for p in pool if p.name not in {s["add"] for s in steps}],
                                schedule, day, adds_left - len(steps), add_days)
            for s in more:
                s["planned"] = False
            steps += more
        fa_note = ("名單來自 FA 截圖" + (f"（{fa_age / 24:.0f} 天前，換之前再確認還在）" if fa_age > FA_STALE_HOURS else "")
                   if fa else "沒有 FA 截圖，請確認是 FA（綠色 +）")
        for i, s in enumerate(steps):
            d = s["day"]
            drop_m = next(x for x in pj.apply_steps(mine, pool, steps[:i]) if x.name == s["drop"])
            cand_m = next(x for x in pool if x.name == s["add"])
            # 最早：要釋出的人前一場打完；最晚：新簽的人第一場開打前
            prev = [x for x in pj.days_between(monday, d - timedelta(days=1)) if (x, drop_m.team) in tips]
            earliest = tips[(prev[-1], drop_m.team)] + timedelta(hours=GAME_HOURS) if prev else None
            if earliest and earliest <= now:
                earliest = None
            first = s["add_days"][0] if s["add_days"] else d
            deadline = tips.get((first, cand_m.team))
            before = pj.simulate(lg, sim_m, pj.apply_steps(mine, pool, steps[:i]), opp, schedule, runs=SIM_RUNS)["win"] if sim_m else None
            after = pj.simulate(lg, sim_m, pj.apply_steps(mine, pool, steps[:i + 1]), opp, schedule, runs=SIM_RUNS)["win"] if sim_m else None
            p = scored[scored["key"] == normalize(cand_m.name)].iloc[0]
            cats = [c for c in lg["categories"] if c not in lg["punt"]]
            strong = "、".join(("少失誤" if c == "TO" else zh.CATEGORY[c]) for c in sorted(cats, key=lambda c: -p[f"z_{c}"])[:3] if p[f"z_{c}"] > 0.3)
            game_days = "、".join(_wd(x) for x in s["add_days"])
            decided = "已討論決定。" if s.get("planned") else "系統建議。"
            actions.append({
                "id": f"{monday}|{label}|add|{s['drop']}|{s['add']}", "league": label, "league_name": name,
                "type": "add", "priority": "high" if d == day else "normal",
                "title": f"放 {s['drop']} → 簽 {s['add']}",
                "detail": (f"{s['add']}（{zh.team(cand_m.team)}）{game_days}有比賽" if game_days else f"{s['add']}（{zh.team(cand_m.team)}）")
                          + f"，多打 {s['games']:.0f} 場" + (f"；強項：{strong}" if strong else "") + f"。{decided}"
                          + ("" if s.get("planned") else f"{fa_note}。"),
                "deadline": deadline.isoformat() if deadline else None,
                "deadline_label": (_tpe_label(deadline) + " 前") if deadline else f"{_wd(d)}開打前",
                "earliest": earliest.isoformat() if earliest else None,
                "earliest_label": (f"{s['drop']} 打完後・約 {_tpe_label(earliest)}") if earliest else None,
                "impact": ({"before": round(before, 3), "after": round(after, 3),
                            "label": f"本週勝率 {before:.0%} → {after:.0%}"} if before is not None else None),
                "players": [{**_player_info(scored, s["drop"]), "role": "drop"},
                            {**_player_info(scored, s["add"]), "role": "add"}]})
        if not steps and add_days and adds_left:
            alert("info", f"Adds 還剩 {adds_left} 次，目前 FA 名單裡沒有划算的換法" + ("" if fa else "（傳一張 FA 截圖再算一次）"))
        if day.weekday() == 6 and adds_left and not steps:
            alert("warning", f"今天是本週最後一天，Adds 還剩 {adds_left} 次沒用")

    # ---- 傷病 ----
    for x in mine:
        if x.status == "Out":
            ret = f"，ESPN 預估 {x.return_date:%m/%d} 回來" if x.return_date else ""
            il_free = 3 - len(lg["il"])
            alert("danger", f"{x.name} 缺陣{ret}" + ("：可以移進 IL 空出位置" if il_free > 0 else ""))
        elif x.status == "Day-To-Day":
            alert("warning", f"{x.name} 每日觀察，開打前確認")
    inj = injuries.set_index("key") if not injuries.empty else None
    for n in lg["il"]:
        if inj is not None and normalize(n) not in inj.index:
            alert("info", f"{n} 已經不在傷病名單，可能可以移出 IL（要先釋出一人）")
    for x in opp:
        if x.status in ("Out", "Day-To-Day") and x.season_z > 0:
            alert("info", f"對手 {x.name} {zh.injury(x.status)}")

    # ---- 本週戰況 ----
    league = {"key": label, "name": name, "team_name": "LeSunshine",
              "week": (m or {}).get("week"), "week_label": f"{monday:%m/%d}–{sunday:%m/%d}".replace("/0", "/").lstrip("0"),
              "opponent": opp_name, "score": None, "forecast": None,
              "adds": {"used": adds_used, "total": lg["weekly_adds"]},
              "games_left": None, "categories": [], "days": [], "roster": []}
    if league["week"]:
        league["week_label"] = f"第 {league['week']} 週（{league['week_label']}）"
    if cur:
        rows, w, l = an.matchup_rows(cur, lg["punt"])
        league["score"] = {"w": w, "l": l, "t": len(rows) - w - l, "source": source, "source_label": source_label}
        final = {}
        if opp:
            plan_mine = pj.apply_steps(mine, pool, steps) if steps else mine
            pred = pj.predict(lg, cur, plan_mine, opp, schedule)
            sim = pj.simulate(lg, cur, plan_mine, opp, schedule, runs=SIM_RUNS)
            final = {r["cat"]: r for r in pred["rows"]}
            fw = sum(p > 0.5 for p in sim["cats"].values())
            fl = sum(p < 0.5 for p in sim["cats"].values())
            league["forecast"] = {"w": fw, "l": fl, "t": len(sim["cats"]) - fw - fl,
                                  "win_prob": round(sim["win"], 3),
                                  "win_prob_no_action": round(win_now, 3) if win_now is not None else None}
            now_pred = pj.predict(lg, cur, mine, opp, schedule)
            league["games_left"] = {"mine": round(now_pred["my_games"]), "opp": round(now_pred["opp_games"])}
        for r in rows:
            c = r["cat"]
            prob = (sim["cats"].get(c) if opp else None)
            status = ("punt" if c in lg["punt"] else
                      "lead" if prob is not None and prob >= SWING_HIGH else
                      "behind" if prob is not None and prob <= SWING_LOW else
                      "swing" if prob is not None else
                      ("lead" if r["lead"] else "behind" if r["lead"] is False else "swing"))
            league["categories"].append({
                "cat": c, "label": zh.CATEGORY[c], "mine": r["mine"], "opp": r["opp"],
                "mine_final": final[c]["mine"] if c in final else None,
                "opp_final": final[c]["opp"] if c in final else None,
                "win_prob": round(prob, 3) if prob is not None else None, "status": status})

    # 已經打完的日子用當天的陣容（roster_log 倒推），之後的日子用現在的陣容
    past = roster_by_day(lg_state, monday, day - timedelta(days=1)) if day > monday else {}
    table = []
    for d, names in past.items():
        table += pj.day_table(pj.resolve(names, scored, injuries, lg, empty)[0], playing, [d], lg["starters"])
    table += pj.day_table(mine, playing, pj.days_between(day, sunday), lg["starters"])
    for r in table:
        league["days"].append({"date": str(r["day"]), "label": f"{_wd(r['day'])} {r['day'].month}/{r['day'].day}",
                               "playing": r["playing"], "slots": lg["starters"], "open": r["open"],
                               "starters": r["started"], "bench": r["bench"]})

    left = an.team_games(schedule, day, sunday)
    inj_status = injuries.set_index("key")["injury_status"] if not injuries.empty else pd.Series(dtype=str)
    for slot, names in (("active", lg["roster"]), ("il", lg["il"])):
        for n in names:
            p = an.find_player(scored, n)
            info = _player_info(scored, n)
            status = inj_status.get(normalize(n), "") if p is not None else ""
            league["roster"].append({**info, "slot": slot, "injury": status or None,
                                     "injury_label": zh.injury(status) or None,
                                     "games_left": int(left.get(p["team"], 0)) if p is not None and slot == "active" else None,
                                     "value": _num(p["z_total"]) if p is not None else None,
                                     "rank": int(p["rank"]) if p is not None else None})
    league["roster"].sort(key=lambda r: (r["slot"] != "active", r["rank"] if r["rank"] is not None else 9999))
    return league, actions, alerts


# ---------- 全部 ----------

def build(players: pd.DataFrame, injuries: pd.DataFrame, schedule: pd.DataFrame,
          day: date | None = None, now: datetime | None = None) -> dict:
    from . import state as state_store
    now = now or datetime.now(TPE)
    day = day or an.today_et()
    st = state_store.load()
    leagues, actions, alerts = [], [], []
    for label in LEAGUES:
        lg, act, al = build_league(label, st, players, injuries, schedule, day, now)
        leagues.append(lg)
        actions += act
        alerts += al
    far = "9999"
    actions.sort(key=lambda a: (a["deadline"] or far, a["priority"] != "high"))

    rivals = []
    if RIVALS_FILE.exists():
        r = json.loads(RIVALS_FILE.read_text(encoding="utf-8"))
        for x in r["rivals"]:
            rivals.append({"league": x["league"], "league_name": LEAGUES[x["league"]]["name"], "rival": x["rival"],
                           "beat_prob": x["beat_prob"], "beat_label": f"季末贏他的機率約 {x['beat_prob']:.0%}",
                           "updated_label": x["updated"], "notes": x["notes"]})

    first_tip = schedule.loc[schedule["date"] == day, "tip_taipei"]
    when = f"台北 {first_tip.min():%-m/%-d} 早上開打" if not first_tip.empty else "沒有比賽"
    return {"version": 1, "generated_at": now.isoformat(timespec="minutes"),
            "generated_label": f"{now.month}/{now.day} {now:%H:%M} 更新",
            "nba_day": str(day), "nba_day_label": f"{_wd(day)} {day.month}/{day.day}（{when}）",
            "actions": actions, "alerts": alerts, "leagues": leagues, "rivals": rivals}


def write(data: dict) -> Path:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return OUT_FILE
