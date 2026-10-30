"""本週對戰即時比分估算：抓 ESPN 每場 box score，照每天的先發陣容加總，換算成 Yahoo 比項。

Yahoo 只計算當天排在先發格的球員；這裡不知道實際排陣，所以假設「有出賽的人都先發，
超過先發格數時，價值最低（或上場時間最短）的人坐板凳」。結果是估計值，和 Yahoo 會有小誤差。
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from .analysis import COUNTING_CATS, PCT_CATS, find_player
from .nba_data import ESPN, SNAPSHOT_DIR, _get_json, _team, normalize

BOX_CACHE = SNAPSHOT_DIR / "boxscores.json"
CACHE_KEEP_DAYS = 14  # 快取只留最近兩週的比賽，檔案才不會越長越大
BOX_STATS = ["MIN", "FGM", "FGA", "FG3M", "FG3A", "FTM", "FTA", "PTS", "REB", "AST", "STL", "BLK", "TOV"]
TOTAL_STATS = BOX_STATS[1:]
BOX_COLS = ["date", "game_id", "team", "player_id", "name", "key", *BOX_STATS, "did_play", "final"]
# ESPN box score 欄位 key → 我們的欄位（命中-出手寫成 "7-15"）
SPLIT_KEYS = {"fieldGoalsMade-fieldGoalsAttempted": ("FGM", "FGA"),
              "threePointFieldGoalsMade-threePointFieldGoalsAttempted": ("FG3M", "FG3A"),
              "freeThrowsMade-freeThrowsAttempted": ("FTM", "FTA")}
PLAIN_KEYS = {"minutes": "MIN", "points": "PTS", "rebounds": "REB", "assists": "AST",
              "steals": "STL", "blocks": "BLK", "turnovers": "TOV"}


def _num(v) -> float:
    """ESPN 的數字是字串，DNP 時可能是 "--" 或空白；分鐘偶爾是 "34:12"。"""
    s = str(v or "").strip()
    if ":" in s:
        m, _, sec = s.partition(":")
        return _num(m) + _num(sec) / 60
    try:
        return float(s)
    except ValueError:
        return 0.0


def _split(v) -> tuple[float, float]:
    made, _, att = str(v or "").partition("-")
    return _num(made), _num(att)


def _parse_summary(data: dict, game_id: str, day: date) -> tuple[list[dict], bool]:
    """一場比賽的 summary → （每位球員一列, 是否已結束）。"""
    status = ((data.get("header", {}).get("competitions") or [{}])[0].get("status") or {}).get("type", {})
    final = bool(status.get("completed")) or status.get("state") == "post"
    rows = []
    for team in (data.get("boxscore") or {}).get("players", []):
        abbr = _team((team.get("team") or {}).get("abbreviation", ""))
        for block in team.get("statistics", []):
            keys = block.get("keys") or []
            for a in block.get("athletes", []):
                ath = a.get("athlete") or {}
                stats = a.get("stats") or []
                row = {"date": day, "game_id": game_id, "team": abbr, "player_id": str(ath.get("id", "")),
                       "name": ath.get("displayName", ""), **{c: 0.0 for c in BOX_STATS}}
                row["key"] = normalize(row["name"])
                if stats and not a.get("didNotPlay") and len(stats) == len(keys):
                    for k, v in zip(keys, stats):
                        if k in SPLIT_KEYS:
                            row.update(zip(SPLIT_KEYS[k], _split(v)))
                        elif k in PLAIN_KEYS:
                            row[PLAIN_KEYS[k]] = _num(v)
                row["did_play"] = row["MIN"] > 0
                row["final"] = final
                rows.append(row)
    return rows, final


def fetch_boxscores(schedule: pd.DataFrame, start: date, end: date, cache_path: Path = BOX_CACHE) -> pd.DataFrame:
    """[start, end]（美東日期）已開打比賽的球員 box score，每人每場一列。
    已結束的比賽存進 cache_path，之後不再重抓；進行中的比賽每次都重抓。"""
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    keep_from = str(start - timedelta(days=CACHE_KEEP_DAYS))
    old = [gid for gid, game in cache.items() if not game or game[0]["date"] < keep_from]
    for gid in old:
        del cache[gid]
    now = datetime.now(ZoneInfo("Asia/Taipei"))
    games = schedule[(schedule["date"] >= start) & (schedule["date"] <= end)]
    rows, dirty = [], bool(old)
    for _, g in games.iterrows():
        gid = str(g["game_id"])
        if gid in cache:
            rows += cache[gid]
            continue
        tip = pd.Timestamp(g["tip_taipei"])
        tip = tip.tz_localize("Asia/Taipei") if tip.tzinfo is None else tip
        if tip > now or str(g.get("status", "")).startswith(("Postponed", "Canceled")):
            continue  # 還沒開打（賽程快照的 status 可能過時，用開打時間判斷）
        try:
            game_rows, final = _parse_summary(_get_json(f"{ESPN}/summary", {"event": gid}), gid, g["date"])
        except Exception as e:
            print(f"⚠️ 抓不到 box score {gid}（{type(e).__name__}）")
            continue
        rows += game_rows
        if final and game_rows:  # 只存有上場的人（沒上場的對加總沒影響）
            cache[gid] = [{**r, "date": str(r["date"])} for r in game_rows if r["did_play"]] or game_rows[:1]
            dirty = True
    if dirty:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False))
    box = pd.DataFrame(rows, columns=BOX_COLS)
    box["date"] = pd.to_datetime(box["date"]).dt.date
    return box


def _match_ids(names: list[str], box: pd.DataFrame, players: pd.DataFrame) -> tuple[dict[str, str], list[str]]:
    """名字 → ESPN player_id。先用球員快照（find_player），找不到再用 box score 本身的名字。"""
    ids, unmatched = {}, []
    box_players = box.drop_duplicates("player_id")[["player_id", "name", "key"]]
    for n in names:
        p = find_player(players, n)
        if p is None:
            p = find_player(box_players, n)
            pid = None if p is None else str(p["player_id"])
        else:
            pid = str(p["PLAYER_ID"])
        if pid is None:
            unmatched.append(n)
        else:
            ids[n] = pid
    return ids, unmatched


def side_totals(box: pd.DataFrame, roster_by_day: dict[date, list[str]], starters: int,
                values: dict[str, float] | None = None, players: pd.DataFrame | None = None) -> dict:
    """一隊的本週累計。roster_by_day：美東日期 → 當天在陣容上的球員（不含 IL）。
    當天出賽人數超過 starters 時，values 最低（沒給 values 就是上場時間最短）的人當作坐板凳。"""
    if players is None:
        players = pd.read_json(SNAPSHOT_DIR / "players.json", orient="records", dtype={"PLAYER_ID": str})
    players = players.assign(PLAYER_ID=players["PLAYER_ID"].astype(str))
    all_names = sorted({n for names in roster_by_day.values() for n in names})
    ids, unmatched = _match_ids(all_names, box, players)
    played = box[box["did_play"]]
    totals = {c: 0.0 for c in TOTAL_STATS}
    games = 0
    for day, names in roster_by_day.items():
        by_id = {ids[n]: n for n in names if n in ids}
        today = played[(played["date"] == day) & played["player_id"].isin(by_id)]
        if len(today) > starters:
            if values:
                rank = today["player_id"].map(lambda pid: values.get(by_id[pid], 0.0))
                today = today.loc[rank.sort_values(ascending=False).index[:starters]]
            else:
                today = today.nlargest(starters, "MIN")
        for c in TOTAL_STATS:
            totals[c] += float(today[c].sum())
        games += len(today)
    return {**{c: int(round(v)) for c, v in totals.items()}, "games": games, "unmatched": unmatched}


def _fmt_pct(made: float, att: float) -> str:
    if not att:
        return "-"
    s = f"{made / att:.3f}"
    return s[1:] if s.startswith("0") else s


def _cat_value(totals: dict, cat: str) -> str:
    if cat in PCT_CATS:
        made, att = PCT_CATS[cat]
        return _fmt_pct(totals[made], totals[att])
    return str(int(totals[COUNTING_CATS[cat]]))


def matchup_categories(lg: dict, mine_totals: dict, opp_totals: dict) -> list[dict]:
    """轉成 state.json matchup.categories 的格式（計數取整數，命中率寫成 .481）。"""
    return [{"category": c, "mine": _cat_value(mine_totals, c), "opponent": _cat_value(opp_totals, c)}
            for c in lg["categories"]]
