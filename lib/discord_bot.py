"""
Send-only Discord bot wrapper. One bot token posts to both the private
review channel and the public channel — no gateway connection, no
reaction/message polling, since approve/reject is handled by
approve_run.py instead (see GATE_DESIGN.md).

Setup (one-time, see README.md for the full walkthrough):
  1. discord.com/developers/applications -> New Application -> Bot tab ->
     Reset Token, copy it into DISCORD_BOT_TOKEN.
  2. OAuth2 -> URL Generator -> scope "bot" -> permission "Send Messages" ->
     open the generated URL, invite it to your server.
  3. Enable Developer Mode in Discord (User Settings -> Advanced), then
     right-click each target channel -> Copy Channel ID, for both the
     private review channel and the public channel.
"""
import requests
import config

API_BASE = "https://discord.com/api/v10"


def send_message(channel_id: str, content: str) -> dict:
    if not config.DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set — see .env.example")
    if not channel_id:
        raise RuntimeError("A Discord channel ID is required but was empty")

    # Discord caps a single message at 2000 characters — split defensively
    # rather than letting the API call fail outright.
    chunks = [content[i:i + 1900] for i in range(0, len(content), 1900)] or [""]

    last_resp = None
    for chunk in chunks:
        last_resp = requests.post(
            f"{API_BASE}/channels/{channel_id}/messages",
            headers={
                "Authorization": f"Bot {config.DISCORD_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"content": chunk},
            timeout=15,
        )
        last_resp.raise_for_status()
    return last_resp.json()
