"""本週推演：用賽程算每天誰上場、預測結算比數、規劃 Adds。

Yahoo Matchup 頁的「Games Played 已打/總數」只算目前排在先發的人，會低估剩餘場次，
所以這裡一律從 NBA 賽程推算：每天有比賽、沒缺陣的人裡，挑價值最高的填滿先發位。
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from . import analysis as an
from . import zh
from .nba_data import normalize

DTD_PLAY_PROB = 0.75      # 每日觀察（GTD）的人，大約七成五會上場
FOCUS_WEIGHT = 2.0        # 規劃 Adds 時，想追的比項加倍計分
MIN_ADD_GAIN = 3.0        # 一次 Add 至少要多這麼多價值（約 1/4 場串流）才值得用
LONG_TERM_WEIGHT = 0.5    # 長期價值差 1 分 ≈ 本週價值 0.5 分
DROP_MARGIN = 2.5         # 長期價值（z 分數）比新簽的人高出這麼多的，不為了這週多幾場就釋出
POOL_SIZE = 40            # 規劃時只從價值前 40 名的候選人裡挑，加快速度
TOTALS = ["FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "PTS", "REB", "AST", "STL", "BLK", "TOV"]


@dataclass
class Member:
    name: str
    team: str
    stats: pd.Series          # 場均
    value: float              # 每場對比項的貢獻（相對於空位）
    status: str = ""
    return_date: date | None = None
    start: date = date.min    # 在陣容的期間 [start, end)
    end: date = date.max
    keep: bool = False        # 核心／主力，不考慮釋出
    season_z: float = 0.0     # 長期價值（各比項 z 分數總和）

    def play_prob(self, d: date) -> float:
        if not (self.start <= d < self.end):
            return 0.0
        if self.status == "Out":
            return 1.0 if self.return_date and d >= self.return_date else 0.0
        return DTD_PLAY_PROB if self.status == "Day-To-Day" else 1.0


# ---------- 準備 ----------

def score(players: pd.DataFrame, lg: dict) -> tuple[pd.DataFrame, dict[str, float]]:
    """z 分數，以及「完全沒數據的人」在各比項的 z（＝空位的價值），用來算每場相對於空位的貢獻。"""
    zero = {c: 0.0 for c in players.columns if players[c].dtype.kind == "f"}
    dummy = pd.DataFrame([{**zero, "PLAYER_ID": "__empty__", "name": "", "key": "__empty__"}])
    scored = an.add_zscores(pd.concat([players, dummy], ignore_index=True), lg["categories"], lg["punt"], lg["teams"])
    empty = scored[scored["key"] == "__empty__"].iloc[0]
    return scored[scored["key"] != "__empty__"].reset_index(drop=True), {c: empty[f"z_{c}"] for c in lg["categories"]}


def game_value(row: pd.Series, lg: dict, empty: dict[str, float], focus: list[str] = ()) -> float:
    return sum((FOCUS_WEIGHT if c in focus else 1.0) * (row[f"z_{c}"] - empty[c])
               for c in lg["categories"] if c not in lg["punt"])


def resolve(names: list[str], scored: pd.DataFrame, injuries: pd.DataFrame, lg: dict,
            empty: dict[str, float], focus: list[str] = ()) -> tuple[list[Member], list[str]]:
    """名單 → Member；找不到的名字另外回傳。"""
    inj = injuries.set_index("key")
    members, missing = [], []
    for name in names:
        p = an.find_player(scored, name)
        if p is None:
            missing.append(name)
            continue
        status = inj["injury_status"].get(p["key"], "") if not inj.empty else ""
        ret = str(inj["return_date"].get(p["key"], "") or "")[:10] if not inj.empty else ""
        members.append(Member(
            name=name, team=p["team"], stats=p[TOTALS], value=game_value(p, lg, empty, focus),
            status=status or "", return_date=date.fromisoformat(ret) if ret else None,
            keep=name in lg.get("untouchable", []) + lg.get("core", []), season_z=float(p["z_total"]),
        ))
    return members, missing


def days_between(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def teams_playing(schedule: pd.DataFrame) -> dict[date, set[str]]:
    out: dict[date, set[str]] = {}
    for _, g in schedule.iterrows():
        out.setdefault(g["date"], set()).update((g["home"], g["away"]))
    return out


# ---------- 每天的先發 ----------

def lineup(members: list[Member], playing: set[str], d: date, starters: int) -> list[tuple[Member, float]]:
    """當天有比賽的人依價值排序，填滿先發位：[(球員, 上場機率)]。"""
    cands = sorted(((m, m.play_prob(d)) for m in members if m.team in playing),
                   key=lambda x: -x[0].value)
    return [(m, prob) for m, prob in cands if prob > 0][:starters]


def day_table(members: list[Member], playing_by_day: dict, days: list[date], starters: int) -> list[dict]:
    rows = []
    for d in days:
        playing = playing_by_day.get(d, set())
        on = [m for m in members if m.team in playing and m.play_prob(d) > 0]
        started = lineup(members, playing, d, starters)
        rows.append({"day": d, "playing": len(on), "open": max(0, starters - len(on)),
                     "started": [m.name for m, _ in started],
                     "bench": [m.name for m in on if m.name not in {s.name for s, _ in started}],
                     "games": sum(p for _, p in started)})
    return rows


def expected(members: list[Member], playing_by_day: dict, days: list[date], starters: int) -> tuple[float, float, pd.Series]:
    """（預期出賽人次, 預期價值, 預期各項數據總和）。"""
    games, value, totals = 0.0, 0.0, pd.Series(0.0, index=TOTALS)
    for d in days:
        for m, prob in lineup(members, playing_by_day.get(d, set()), d, starters):
            games += prob
            value += prob * m.value
            totals += prob * m.stats.astype(float)
    return games, value, totals


# ---------- 結算比數預測 ----------

def remaining_start(m: dict) -> date:
    """比分截圖之後還沒打的第一個美東比賽日（截圖時比賽已經開打，就從隔天算）。"""
    saved = datetime.fromisoformat(m["saved_ts"]).astimezone(ZoneInfo("America/New_York"))
    return saved.date() + timedelta(days=1 if saved.hour >= 19 else 0)


def _current(m: dict) -> dict[str, float]:
    out = {}
    for c in m["categories"]:
        try:
            v = float(str(c["mine"]).replace("%", "")), float(str(c["opponent"]).replace("%", ""))
        except ValueError:
            continue
        if c["category"] in an.PCT_CATS:
            v = tuple(x / 100 if x > 1 else x for x in v)
        out[c["category"]] = v
    return out


def _final(cat: str, side: int, cur: dict, past: pd.Series, proj: pd.Series) -> float | None:
    """單一比項的預期結算值。命中率：已打的出手數用「命中數 ÷ 命中率」反推，沒有命中數就用賽程估。"""
    if cat in an.PCT_CATS:
        made, att = an.PCT_CATS[cat]
        if cat not in cur:
            return None
        pct = cur[cat][side]
        made_cat = {"FGM": "FGM", "FG3M": "3PTM"}.get(made)
        if made_cat in cur and pct > 0:
            past_att = cur[made_cat][side] / pct
        else:
            past_att = past[att]
        total_att = past_att + proj[att]
        return (pct * past_att + proj[made]) / total_att if total_att else pct
    stat = an.COUNTING_CATS[cat]
    return cur[cat][side] + proj[stat] if cat in cur else None


def predict(lg: dict, m: dict, mine: list[Member], opp: list[Member], schedule: pd.DataFrame) -> dict:
    """依截圖比分＋雙方陣容剩下的賽程，預測本週結算。"""
    monday, sunday = an.week_range(date.fromisoformat(m["week_monday"]))
    start = max(remaining_start(m), monday)
    playing = teams_playing(schedule)
    past_days, left_days = days_between(monday, start - timedelta(days=1)), days_between(start, sunday)
    cur = _current(m)

    sides = []
    for members in (mine, opp):
        _, _, past = expected(members, playing, past_days, lg["starters"])
        games, _, proj = expected(members, playing, left_days, lg["starters"])
        sides.append((games, past, proj))

    cats = []
    for c in lg["categories"]:
        vals = [_final(c, i, cur, sides[i][1], sides[i][2]) for i in (0, 1)]
        if None in vals:
            continue
        fmt = (lambda x: f"{x:.3f}".lstrip("0")) if c in an.PCT_CATS else (lambda x: f"{x:.0f}")
        cats.append({"category": c, "mine": fmt(vals[0]), "opponent": fmt(vals[1])})
    rows, w, l = an.matchup_rows({"categories": cats}, lg["punt"])
    return {"rows": rows, "w": w, "l": l, "t": len(rows) - w - l, "from": start,
            "my_games": sides[0][0], "opp_games": sides[1][0]}


# ---------- Adds 規劃 ----------

def candidate_pool(lg: dict, scored: pd.DataFrame, injuries: pd.DataFrame, empty: dict, focus: list[str],
                   exclude: set[str], fa_keys: set[str] | None) -> list[Member]:
    inj = injuries.set_index("key")["injury_status"] if not injuries.empty else pd.Series(dtype=str)
    df = scored[~scored["key"].isin(exclude) & (scored["MIN"] >= an.MIN_STREAM_MINUTES)].copy()
    df = df[df["key"].map(inj).fillna("") != "Out"]
    if fa_keys is not None:
        df = df[df["key"].isin(fa_keys)]
    else:  # 排名太前面的幾乎一定被別人持有
        df = df[df["rank"] > lg["teams"] * an.ROSTER_SIZE]
    df["v"] = df.apply(lambda r: game_value(r, lg, empty, focus), axis=1)
    names = df.nlargest(POOL_SIZE, "v")["name"].tolist()
    return resolve(names, scored, injuries, lg, empty, focus)[0]


def plan_adds(lg: dict, members: list[Member], pool: list[Member], schedule: pd.DataFrame,
              day: date, adds_left: int, add_days: list[date]) -> list[dict]:
    """貪婪法：每一步挑「哪天、放掉誰、簽誰」讓本週先發的預期價值增加最多，直到 adds 用完或不再划算。"""
    _, sunday = an.week_range(day)
    days = days_between(day, sunday)
    playing = teams_playing(schedule)
    roster = list(members)
    pool = [p for p in pool if any(p.team in playing.get(d, ()) for d in add_days)]
    steps = []
    for _ in range(adds_left):
        base_games, base_value, _ = expected(roster, playing, days, lg["starters"])
        best = None
        for d in add_days:
            for drop in roster:
                if drop.keep or drop.end <= d or drop.start >= d:
                    continue
                cut = Member(**{**drop.__dict__, "end": d})
                others = [x for x in roster if x is not drop] + [cut]
                for cand in pool:
                    if drop.season_z > cand.season_z + DROP_MARGIN and drop.start == date.min:
                        continue
                    new = Member(**{**cand.__dict__, "start": d})
                    games, value, _ = expected(others + [new], playing, days, lg["starters"])
                    gain = value - base_value
                    # 本週多的價值為主；同分時留下長期價值高的人
                    rank = gain - LONG_TERM_WEIGHT * (drop.season_z - cand.season_z)
                    if gain >= MIN_ADD_GAIN and (best is None or rank > best[0]):
                        best = (rank, gain, games - base_games, d, drop, cut, cand, new)
        if best is None:
            break
        _, gain, dgames, d, drop, cut, cand, new = best
        roster = [x for x in roster if x is not drop] + [cut, new]
        pool = [p for p in pool if p is not cand]
        steps.append({"day": d, "drop": drop.name, "add": cand.name, "team": cand.team,
                      "games": dgames, "gain": gain,
                      "add_days": [x for x in days if x >= d and cand.team in playing.get(x, ())]})
    return steps


# ---------- 文字報告（雲端對話、推播共用） ----------

def wd(d: date) -> str:
    return f"週{an.WEEKDAY[d.weekday()]}"


def league_report(label: str, lg: dict, state: dict, players: pd.DataFrame, injuries: pd.DataFrame,
                  schedule: pd.DataFrame, day: date, allow_weekday: bool = False) -> str:
    monday, sunday = an.week_range(day)
    m = state[label].get("matchup")
    m = m if m and m.get("week_monday") == str(monday) and m.get("saved_ts") else None
    opp_info = state[label].get("opponent_roster")
    opp_info = opp_info if opp_info and opp_info.get("week_monday") == str(monday) else None

    focus = []
    if m:
        rows, _, _ = an.matchup_rows(m, lg["punt"])
        focus = [r["cat"] for r in rows if r["swing"] and r["cat"] != "TO"]
    scored, empty = score(players, lg)
    mine, missing = resolve(lg["roster"], scored, injuries, lg, empty, focus)
    out = [f"【{lg['name']}】" + (f"vs {m['opponent']}" if m else "")]
    if missing:
        out.append("❓ 找不到這些球員的 NBA 數據：" + "、".join(missing))

    playing = teams_playing(schedule)
    out.append(f"📅 剩下每天的出賽（先發 {lg['starters']} 格，依賽程計算）：")
    for r in day_table(mine, playing, days_between(day, sunday), lg["starters"]):
        line = f"  {wd(r['day'])} {r['day']:%m/%d}：{r['playing']} 人有賽"
        if r["open"]:
            line += f"，空 {r['open']} 格"
        if r["bench"]:
            line += f"，坐板凳 {'、'.join(r['bench'])}"
        out.append(line)
    games, _, _ = expected(mine, playing, days_between(day, sunday), lg["starters"])
    out.append(f"  本週剩餘出賽人次（預期）：{games:.1f}")

    if m and opp_info:
        opp, opp_missing = resolve(opp_info["roster"], scored, injuries, lg, empty)
        p = predict(lg, m, mine, opp, schedule)
        tie = f" {p['t']} 平" if p["t"] else ""
        out.append(f"📊 預測結算：{p['w']} 勝 {p['l']} 敗{tie}"
                   f"（{m['saved_at']} 的比分＋{wd(p['from'])}起的賽程；剩餘人次 我 {p['my_games']:.1f} vs 對手 {p['opp_games']:.1f}）")
        for r in p["rows"]:
            mark = "✅" if r["lead"] else ("❌" if r["lead"] is False else "➖")
            punt = "（放棄）" if r["cat"] in lg["punt"] else ""
            out.append(f"  {mark} {zh.cat(r['cat'])} {r['mine']} vs {r['opp']}" + ("　⚖️ 接近" if r["swing"] else "") + punt)
        if opp_missing:
            out.append("  （對手這些人找不到數據，沒算進去：" + "、".join(opp_missing) + "）")
        out.append("  ※ 沒算到對手之後的換人，只是參考")
    elif m:
        out.append("📊 預測結算：需要對手陣容截圖（Matchup 頁點對手隊名）")
    else:
        out.append("📊 預測結算：需要本週的 Matchup 比分截圖")

    adds_left = lg["weekly_adds"] - max(m["adds_used"], 0) if m else lg["weekly_adds"]
    if adds_left <= 0:
        out.append("🔁 本週 Adds 已用完")
        return "\n".join(out)
    from_wd = 0 if allow_weekday else lg.get("adds_from_weekday", 0)
    add_days = [d for d in days_between(day, sunday) if d.weekday() >= from_wd]
    fa = state[label].get("free_agents")
    fa_keys = {normalize(n) for n in fa["names"]} if fa else None
    exclude = {normalize(n) for n in lg["roster"] + lg["il"] + (opp_info["roster"] if opp_info else [])}
    pool = candidate_pool(lg, scored, injuries, empty, focus, exclude, fa_keys)
    steps = plan_adds(lg, mine, pool, schedule, day, adds_left, add_days) if add_days else []
    src = f"從 {fa['saved_ts'][5:10].replace('-', '/')} 截圖的 FA 名單挑" if fa else "沒有 FA 截圖，請到 Yahoo 確認是 FA"
    target = "、".join(zh.CATEGORY[c] for c in focus) if focus else "全部比項"
    out.append(f"🔁 Adds 規劃（剩 {adds_left} 次；加重{target}；{src}）：")
    if not add_days:
        out.append(f"  照紀律{wd(monday + timedelta(days=from_wd))}前不用 adds（比分很接近時可以加 --allow-weekday 試算）")
    elif not steps:
        out.append("  目前名單裡沒有划算的換法（換了也不會多上場），先保留")
    for i, s in enumerate(steps, 1):
        when = "今天" if s["day"] == day else f"{wd(s['day'])}（{s['day']:%m/%d}）"
        out.append(f"  {i}. {when}：放 {s['drop']} → 簽 {s['add']}（{zh.team(s['team'])}，"
                   f"出賽 {'、'.join(wd(d) for d in s['add_days'])}；淨多 {s['games']:+.1f} 場）")
    if steps and len(steps) < adds_left:
        out.append(f"  剩下 {adds_left - len(steps)} 次先留著（目前沒有更划算的換法）")
    return "\n".join(out)
