"""
Central config. Every constant that governs pipeline behavior lives here —
nowhere else in the codebase should have a magic number for these.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Site ---
PROJECTS_URL = "https://l2e.lovable.app/projects"

# --- Selection rule (Section 6c, ARCHITECTURE_v2.md) ---
CAP = 3  # fixed, not a range

# --- Approval gate timing (see GATE_DESIGN.md) ---
REMINDER_AFTER_HOURS = 24   # send one reminder if still pending after this long
TIMEOUT_AFTER_HOURS = 72    # auto-skip (no post) if still pending after this long

# --- Discord (one bot handles both channels — see README setup steps) ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_REVIEW_CHANNEL_ID = os.getenv("DISCORD_REVIEW_CHANNEL_ID", "")
DISCORD_PUBLIC_CHANNEL_ID = os.getenv("DISCORD_PUBLIC_CHANNEL_ID", "")

# --- LLM provider for Stage 4 (AgentRouter OpenAI-compatible gateway; see lib/copywriter.py) ---
AGENTROUTER_API_KEY = os.getenv("AGENTROUTER_API_KEY", "")
AGENTROUTER_MODEL = os.getenv("AGENTROUTER_MODEL", "glm-5.3")
AGENTROUTER_BASE_URL = os.getenv("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")

# --- Copy content ---
WEEKLY_RESET_DAY = os.getenv("WEEKLY_RESET_DAY", "Friday")

# --- Paths ---
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PENDING_DIR = BASE_DIR / "pending_review"
PROCESSED_DIR = BASE_DIR / "processed"
LEDGER_PATH = BASE_DIR / "featured_log.json"
SYSTEM_PROMPT_PATH = BASE_DIR / "assets" / "system_prompt.txt"

for d in (OUTPUT_DIR, PENDING_DIR, PROCESSED_DIR):
    d.mkdir(exist_ok=True)


def missing_secrets():
    """Returns a list of required env vars that are empty. Non-fatal by
    design — callers decide whether/how loudly to warn."""
    required = {
        "DISCORD_BOT_TOKEN": DISCORD_BOT_TOKEN,
        "DISCORD_REVIEW_CHANNEL_ID": DISCORD_REVIEW_CHANNEL_ID,
        "DISCORD_PUBLIC_CHANNEL_ID": DISCORD_PUBLIC_CHANNEL_ID,
        "AGENTROUTER_API_KEY": AGENTROUTER_API_KEY,
    }
    return [k for k, v in required.items() if not v]
