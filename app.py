"""LeSunshine 作戰室（顧問網頁）。

啟動方式（在 VS Code 終端機）：
    ~/.local/bin/uv run streamlit run app.py
"""

import os
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

warnings.filterwarnings("ignore")

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))  # 雲端部署時不安裝套件，直接從 src 匯入

from fantasy_advisor import analysis as an
from fantasy_advisor import nba_data as nd
from fantasy_advisor import state as state_store
from fantasy_advisor import zh
from fantasy_advisor.leagues import LEAGUES

st.set_page_config(page_title="LeSunshine 作戰室", page_icon="🏀", layout="wide")
CLOUD = os.getenv("APP_MODE") == "cloud"  # 雲端版：唯讀、讀 Mac 上傳的數據快照

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1400px;}
.hero {background: linear-gradient(120deg,#4C1D95 0%,#7C3AED 55%,#F59E0B 130%);
       color:#fff; border-radius:18px; padding:22px 28px; margin-bottom:14px;}
.hero h1 {color:#fff; font-size:1.9rem; margin:0 0 4px 0;}
.hero p {margin:0; opacity:.9;}
.alert {border-radius:12px; padding:10px 14px; margin:6px 0; border-left:5px solid; background:#fff;}
.alert.success {border-color:#16A34A; background:#F0FDF4;}
.alert.info {border-color:#2563EB; background:#EFF6FF;}
.alert.warning {border-color:#D97706; background:#FFFBEB;}
.alert.danger {border-color:#DC2626; background:#FEF2F2;}
.tag {display:inline-block; background:#EDE9FE; color:#5B21B6; border-radius:999px;
      padding:2px 10px; margin-right:6px; font-size:.85rem;}
div[data-testid="stMetric"] {background:#fff; border-radius:14px; padding:12px 16px;
      box-shadow:0 1px 3px rgba(0,0,0,.06);}
button[data-baseweb="tab"] p {font-size:1.05rem; font-weight:600;}
</style>
""", unsafe_allow_html=True)


# ---------- 數據 ----------

@st.cache_data(ttl=3600, show_spinner="正在抓 NBA 數據（約 30 秒）…")
def load_data():
    if os.getenv("NBA_SOURCE") == "snapshot":  # 雲端連不到 NBA 官網
        schedule, players, loaded_at = nd.load_snapshot()
        return schedule, players, loaded_at[5:] + "（Mac 同步）"
    try:
        schedule, players = nd.fetch_live()
        nd.save_snapshot(schedule, players)  # 順便更新快照，給雲端推播用
        loaded_at = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%m/%d %H:%M")
    except Exception:
        schedule, players, loaded_at = nd.load_snapshot()
        loaded_at += "（快照）"
    return schedule, players, loaded_at


@st.cache_data(ttl=900, show_spinner="正在更新傷病名單…")
def load_injuries():
    return nd.fetch_injuries()


schedule, players, loaded_at = load_data()
injuries = load_injuries()
day = an.today_et()
monday, sunday = an.week_range(day)
state = state_store.load()

IMG = st.column_config.ImageColumn("", width="small")
NUM = lambda label, fmt="%.2f": st.column_config.NumberColumn(label, format=fmt)


def matchup_table(m: dict, punt: list[str]) -> tuple[list[dict], int, int]:
    """比分表格（含領先／落後、搖擺項標記）與目前幾勝幾敗。"""
    rows, w, l = an.matchup_rows(m, punt)
    status = lambda r: ("✅ 領先" if r["lead"] else "❌ 落後") if r["lead"] is not None else "➖ 平手"
    table = [{"比項": zh.cat(r["cat"]), "我": r["mine"], "對手": r["opp"],
              "狀態": status(r) + ("（搖擺）" if r["swing"] else "")} for r in rows]
    return table, w, l


def render_alerts(alerts):
    for level, msg in alerts:
        html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", msg)
        st.markdown(f'<div class="alert {level}">{html}</div>', unsafe_allow_html=True)


def render_league(label: str):
    lg = state_store.league_view(label, state)
    p = an.add_zscores(players, lg["categories"], lg["punt"], lg["teams"])
    roster_df, alerts = an.roster_report(lg, p, injuries, schedule, day)
    active = roster_df[(roster_df["名單"] == "陣容") & (roster_df["_status"] != "Out")]
    m = state[label].get("matchup")

    st.markdown(
        f'<span class="tag">🎯 {lg["strategy"]}</span>'
        f'<span class="tag">😈 宿敵：{lg["rival"]}</span>'
        f'<span class="tag">比項：{"、".join(zh.CATEGORY[c] for c in lg["categories"])}'
        f'{"（放棄 " + "、".join(zh.CATEGORY[c] for c in lg["punt"]) + "）" if lg["punt"] else ""}</span>',
        unsafe_allow_html=True)
    st.write("")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("今天出賽", f"{int(active['_plays_today'].sum())} / {lg['starters']} 人")
    c2.metric("本週剩餘出賽人次", int(active["本週剩餘"].sum()))
    if m:
        _, w, l = matchup_table(m, lg["punt"])
        c3.metric(f"第 {m['week']} 週 vs {m['opponent']}", f"{w} 勝 {l} 敗")
        c4.metric("本週 Adds", f"{m['adds_used']} / {lg['weekly_adds']}" if m["adds_used"] >= 0 else f"? / {lg['weekly_adds']}")
    else:
        c3.metric("本週對戰", "尚無資料", help="到「✏️ 陣容與對戰」填入比分就會出現")
        c4.metric("傷兵 IL", f"{len(lg['il'])} / 3")

    st.subheader("📋 今日指令")
    render_alerts(alerts)

    st.subheader("👥 我的陣容")
    st.dataframe(
        roster_df.drop(columns=["_note", "_plays_today", "_status"]),
        hide_index=True, width="stretch", row_height=56,
        column_config={"頭貼": IMG, "價值": NUM("價值", "%.2f"), "本週剩餘": NUM("本週剩餘", "%d 場")},
    )
    notes = roster_df[roster_df["_note"] != ""]
    if not notes.empty:
        with st.expander(f"🚑 傷病詳情（{len(notes)} 人）"):
            for _, r in notes.iterrows():
                st.markdown(f"**{r['球員']}**（{r['傷病']}）：{r['_note']}")

    left, right = st.columns([3, 2])
    with left:
        st.subheader("📅 本週出賽表")
        st.caption("● 還沒打　○ 已打過　最後一列是每天出賽人數，數字小的日子適合串流")
        st.dataframe(an.week_grid(lg, p, schedule, day), hide_index=True, width="stretch")
    with right:
        st.subheader("⚔️ 本週對戰")
        if m:
            rows, _, _ = matchup_table(m, lg["punt"])
            st.dataframe(rows, hide_index=True, width="stretch")
            st.caption(f"記錄於 {m['saved_at']}　{m.get('note', '')}")
        else:
            st.info("還沒有對戰資料。到「✏️ 陣容與對戰」分頁填入 Yahoo 的比分。")

    st.subheader("🎯 串流推薦")
    cats = [c for c in lg["categories"] if c not in lg["punt"]]
    f1, f2, f3 = st.columns([3, 1, 1])
    focus = f1.multiselect("想補強的比項（不選＝全部）", cats, format_func=zh.cat, key=f"focus_{label}")
    only_today = f2.toggle("只看今天有比賽", key=f"today_{label}")
    skip_top = f3.toggle("排除大概率已被持有", key=f"skip_{label}")
    my_keys = {nd.normalize(n) for n in lg["roster"] + lg["il"]}
    cands = an.stream_candidates(lg, p, injuries, schedule, day, my_keys, focus, only_today, skip_top)
    st.dataframe(
        cands, hide_index=True, width="stretch", row_height=56,
        column_config={"頭貼": IMG, "每場價值": NUM("每場價值"), "本週總價值": NUM("本週總價值"),
                       "本週剩餘": NUM("本週剩餘", "%d 場")},
    )
    st.caption("本週總價值 =（焦點比項的每場價值 − 自由市場替補水準）× 本週剩餘場次。"
               "系統不知道誰是 FA：請到 Yahoo 確認有綠色 +。")
    st.caption(f"陣容最後更新：{state[label]['updated_at']}")


def render_editor():
    """免費的手動編輯頁：陣容異動 + 本週對戰比分。"""
    flash = st.session_state.pop("flash", None)
    if flash:
        for kind, msg in flash:
            getattr(st, kind)(msg)

    label = st.radio("選擇聯盟", list(LEAGUES), horizontal=True,
                     format_func=lambda k: f"{k}・{LEAGUES[k]['name']}")
    lg = state_store.league_view(label, state)
    s = state[label]
    team_of = dict(zip(players["name"], players["team"]))
    who = lambda n: f"{n}（{zh.team(team_of[n])}）" if n in team_of else n

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("🔁 陣容異動")
        st.caption(f"目前陣容 {len(s['roster'])}/{lg['roster_cap']} 人、IL {len(s['il'])}/3。在 Yahoo 做完異動後，到這裡同步。")
        mine = set(s["roster"] + s["il"])
        with st.form(f"roster_{label}", clear_on_submit=True):
            add = st.multiselect("➕ 簽入（輸入名字搜尋）", sorted(n for n in team_of if n not in mine), format_func=who)
            drop = st.multiselect("➖ 釋出", s["roster"] + s["il"], format_func=who)
            to_il = st.multiselect("🚑 移入 IL", s["roster"], format_func=who)
            from_il = st.multiselect("↩️ 從 IL 移回陣容", s["il"], format_func=who)
            if st.form_submit_button("💾 儲存異動", type="primary", width="stretch"):
                done, warns = state_store.apply_roster_changes(label, add, drop, to_il, from_il)
                st.session_state["flash"] = ([("success", "已更新：" + "、".join(done))] if done else []) + \
                                            [("warning", w) for w in warns]
                st.rerun()

        rows = [{"頭貼": zh.headshot(players.loc[players["name"] == n, "PLAYER_ID"].iloc[0])
                 if n in team_of else None, "球員": n, "球隊": zh.team(team_of.get(n, "")),
                 "名單": "傷兵 IL" if n in s["il"] else "陣容"} for n in s["roster"] + s["il"]]
        st.dataframe(rows, hide_index=True, width="stretch", row_height=48, column_config={"頭貼": IMG})

    with right:
        st.subheader("⚔️ 本週對戰比分")
        st.caption("照 Yahoo 的 Matchup 頁面抄下來（命中率可以寫 .482 或 48.2）。")
        m = s.get("matchup") or {}
        saved = {c["category"]: c for c in m.get("categories", [])}
        with st.form(f"matchup_{label}"):
            c1, c2, c3 = st.columns([1, 2, 1])
            week = c1.number_input("第幾週", 1, 25, int(m.get("week", 1)))
            opponent = c2.text_input("對手隊名", m.get("opponent", ""))
            adds = c3.number_input("已用 Adds", 0, lg["weekly_adds"], max(0, int(m.get("adds_used", 0))))
            mine_left = an.my_games_left(lg, players, injuries, schedule, day)
            opp_left = st.number_input(
                f"對手本週剩餘出賽人次（Yahoo Matchup 頁可看到；不知道填 -1）　｜　我方剩 {mine_left}",
                -1, 100, int(m.get("opp_games_left", -1)))
            table = st.data_editor(
                [{"比項": zh.cat(c), "我": saved.get(c, {}).get("mine", ""),
                  "對手": saved.get(c, {}).get("opponent", "")} for c in lg["categories"]],
                hide_index=True, width="stretch", disabled=["比項"], key=f"editor_{label}")
            if st.form_submit_button("💾 儲存比分", type="primary", width="stretch"):
                cats = [{"category": c, "mine": str(r["我"]).strip(), "opponent": str(r["對手"]).strip()}
                        for c, r in zip(lg["categories"], table) if str(r["我"]).strip() or str(r["對手"]).strip()]
                state_store.save_matchup(label, int(week), opponent.strip(), cats, int(adds), int(opp_left))
                st.session_state["flash"] = [("success", f"已儲存第 {week} 週 vs {opponent} 的比分")]
                st.rerun()


# ---------- 版面 ----------

with st.sidebar:
    st.markdown("### 🏀 LeSunshine 作戰室")
    st.caption(f"NBA 比賽日：{day}（美東）\n\n本週：{monday:%m/%d}（一）– {sunday:%m/%d}（日）")
    st.caption(f"數據更新於 {loaded_at}（台北）")
    if st.button("🔄 重新抓最新數據", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    if CLOUD:
        st.info("☁️ 雲端唯讀版：陣容與比分請在 Mac 版網頁編輯，"
                "Mac 每天 12:30／18:30／23:30 自動同步上來。", icon="ℹ️")
    else:
        st.info("Yahoo API 審核中：陣容與比分請在「✏️ 陣容與對戰」分頁更新。"
                "推薦名單是否為 FA，請到 Yahoo 確認。", icon="ℹ️")
    st.caption("開打時間皆為台北時間。價值：0 ≈ 該聯盟可上場球員平均，越高越好。")

st.markdown(
    f'<div class="hero"><h1>🏀 LeSunshine 作戰室</h1>'
    f'<p>{datetime.now(ZoneInfo("Asia/Taipei")):%m月%d日}（台北）・NBA 比賽日 {day:%m/%d} 週{an.WEEKDAY[day.weekday()]}・'
    f'本週 {monday:%m/%d}–{sunday:%m/%d}</p></div>', unsafe_allow_html=True)

tab_labels = [f"🏆 {k}・{v['name']}" for k, v in LEAGUES.items()] + ([] if CLOUD else ["✏️ 陣容與對戰"])
tabs = st.tabs(tab_labels)
for tab, label in zip(tabs, LEAGUES):
    with tab:
        render_league(label)
if not CLOUD:
    with tabs[-1]:
        render_editor()
