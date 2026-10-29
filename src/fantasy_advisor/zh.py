"""中文對照：比項、位置、球隊、傷病狀態。"""

CATEGORY = {
    "FGM": "命中數", "FG%": "命中率", "FT%": "罰球%", "3PTM": "三分命中", "3PT%": "三分%",
    "PTS": "得分", "REB": "籃板", "AST": "助攻", "ST": "抄截", "BLK": "阻攻", "TO": "失誤",
}

TEAM = {
    "ATL": "老鷹", "BOS": "塞爾提克", "BKN": "籃網", "CHA": "黃蜂", "CHI": "公牛",
    "CLE": "騎士", "DAL": "獨行俠", "DEN": "金塊", "DET": "活塞", "GSW": "勇士",
    "HOU": "火箭", "IND": "溜馬", "LAC": "快艇", "LAL": "湖人", "MEM": "灰熊",
    "MIA": "熱火", "MIL": "公鹿", "MIN": "灰狼", "NOP": "鵜鶘", "NYK": "尼克",
    "OKC": "雷霆", "ORL": "魔術", "PHI": "七六人", "PHX": "太陽", "POR": "拓荒者",
    "SAC": "國王", "SAS": "馬刺", "TOR": "暴龍", "UTA": "爵士", "WAS": "巫師",
}

_POS = {"G": "後衛", "F": "前鋒", "C": "中鋒"}

INJURY = {"Out": "缺陣", "Day-To-Day": "每日觀察", "Questionable": "出賽成疑", "Probable": "大概率出賽",
          "Doubtful": "可能缺陣", "Suspension": "禁賽"}


def cat(c: str) -> str:
    """「得分 PTS」這種中英對照。"""
    return f"{CATEGORY.get(c, c)} {c}"


def team(abbr: str) -> str:
    return TEAM.get(abbr, abbr)


def pos(p: str) -> str:
    return "/".join(_POS.get(x, x) for x in str(p).split("-")) if p else ""


def injury(status: str) -> str:
    return INJURY.get(status, status) if status else ""

