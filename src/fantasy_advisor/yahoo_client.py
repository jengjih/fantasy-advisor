"""連線 Yahoo Fantasy：負責登入授權，以及取得兩個聯盟的物件。"""

import json
import os
from pathlib import Path

import yahoo_fantasy_api as yfa
from dotenv import load_dotenv
from yahoo_oauth import OAuth2

PROJECT_DIR = Path(__file__).resolve().parents[2]
OAUTH_FILE = PROJECT_DIR / "oauth.json"
REDIRECT_URI = "https://localhost:8000"

load_dotenv(PROJECT_DIR / ".env")


def get_session() -> OAuth2:
    """回傳已登入的 Yahoo session；第一次執行會開瀏覽器請你授權。"""
    if not OAUTH_FILE.exists():
        client_id = os.getenv("YAHOO_CLIENT_ID", "").strip()
        client_secret = os.getenv("YAHOO_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise SystemExit("❌ .env 裡的 YAHOO_CLIENT_ID / YAHOO_CLIENT_SECRET 還是空的，請先填好並存檔。")
        OAUTH_FILE.write_text(json.dumps({
            "consumer_key": client_id,
            "consumer_secret": client_secret,
            "callback_uri": REDIRECT_URI,
        }))
        OAUTH_FILE.chmod(0o600)

    sc = OAuth2(None, None, from_file=str(OAUTH_FILE))
    if not sc.token_is_valid():
        sc.refresh_access_token()
    return sc


def get_leagues(sc: OAuth2) -> dict[str, yfa.League]:
    """依 .env 的聯盟 ID，回傳 {"聯盟一": League, "聯盟二": League}。"""
    game = yfa.Game(sc, "nba")
    my_keys = game.league_ids()  # 例如 ["466.l.211505", ...]，含歷年聯盟
    current_prefix = f"{game.game_id()}.l."

    leagues = {}
    for label, env_name in [("聯盟一", "LEAGUE1_ID"), ("聯盟二", "LEAGUE2_ID")]:
        league_key = current_prefix + os.environ[env_name]
        if league_key not in my_keys:
            raise SystemExit(f"❌ 找不到{label}（{league_key}）。你本季的聯盟有：{[k for k in my_keys if k.startswith(current_prefix)]}")
        leagues[label] = game.to_league(league_key)
    return leagues
