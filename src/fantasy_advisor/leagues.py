"""兩個聯盟的設定與陣容。

initial_roster / initial_il 只用來建立 data/state.json；之後陣容以 state.json 為準（網頁 AI 顧問會更新它）。
球員名字請用 NBA 官方拼法（例如 Alex Sarr，不是 Alexandre Sarr）。
"""

LEAGUES = {
    "聯盟一": {
        "name": "誰是懂球帝",
        "league_id": 211505,
        "teams": 8,
        "starters": 10,
        "roster_cap": 14,  # 不含 IL
        "weekly_adds": 8,
        "rival": "尚恩·李文斯頓",
        # FTM/A 在 Yahoo 只是顯示用、不計分，所以 11 個計分比項是這些
        "categories": ["FGM", "FG%", "FT%", "3PTM", "3PT%", "PTS", "REB", "AST", "ST", "BLK", "TO"],
        "punt": [],
        "strategy": "場次暴力：每週用滿 6–8 次 Adds，靠出賽人次堆累積數據。",
        "initial_roster": [
            "Victor Wembanyama", "Jalen Brunson", "Devin Booker", "Bam Adebayo",
            "De'Aaron Fox", "LeBron James", "Derrick White", "Austin Reaves",
            "Wendell Carter Jr.", "Zach Edey", "Alex Sarr", "Matas Buzelis",
            "Dylan Harper", "Toumani Camara",  # 10/27 簽入
        ],
        "initial_il": ["Jalen Williams", "Cason Wallace"],
        "untouchable": [
            "Victor Wembanyama", "Jalen Brunson", "Devin Booker", "Bam Adebayo",
            "De'Aaron Fox", "LeBron James", "Derrick White", "Austin Reaves",
        ],
    },
    "聯盟二": {
        "name": "baek's Grand League",
        "league_id": 256674,
        "teams": 12,
        "starters": 10,
        "roster_cap": 13,  # 不含 IL
        "weekly_adds": 4,
        "rival": "安卓·伊古達拉",
        "categories": ["FG%", "FT%", "3PTM", "PTS", "REB", "AST", "ST", "BLK", "TO"],
        "punt": ["TO"],
        "strategy": "Punt TO + 防守碉堡：長人鎖 REB/BLK；Adds 週一到週四不動，留到週末打搖擺項。",
        "adds_from_weekday": 4,  # 0=週一…4=週五：這天之前不建議用 adds
        "initial_roster": [
            "Luka Dončić", "Anthony Davis", "Joel Embiid", "DeMar DeRozan",
            "Myles Turner", "Deandre Ayton", "Jabari Smith Jr.", "Payton Pritchard",
            "Ayo Dosunmu", "LaMelo Ball", "Nickeil Alexander-Walker", "Kyshawn George",
            "Mitchell Robinson",
        ],
        "initial_il": ["Kon Knueppel"],
        "untouchable": ["Luka Dončić", "Anthony Davis", "Joel Embiid"],
    },
}
