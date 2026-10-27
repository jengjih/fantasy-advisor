"""連線測試：登入 Yahoo，印出兩個聯盟的球隊與你的陣容。

執行方式（在 VS Code 終端機）：
    ~/.local/bin/uv run python check_connection.py
"""

from fantasy_advisor.yahoo_client import get_leagues, get_session

sc = get_session()
print("\n✅ Yahoo 登入成功！\n")

for label, lg in get_leagues(sc).items():
    settings = lg.settings()
    print("=" * 50)
    print(f"🏀 {label}：{settings['name']}（目前第 {lg.current_week()} 週）")
    print("=" * 50)

    my_key = lg.team_key()
    for team in lg.teams().values():
        mark = "  ← 你" if team["team_key"] == my_key else ""
        print(f"  - {team['name']}{mark}")

    print("\n  你的陣容：")
    for p in lg.to_team(my_key).roster():
        status = f" [{p['status']}]" if p.get("status") else ""
        print(f"    {p['selected_position']:>4}  {p['name']}{status}")
    print()
