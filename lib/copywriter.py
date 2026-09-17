"""
Stage 4 — generate copy. This is intentionally a plain
generate(prompt) -> text function underneath — _call_agentrouter() speaks
to the AgentRouter OpenAI-compatible gateway (default model glm-5.3).
Nothing upstream or downstream cares which provider answers, only that
generate_drafts() returns {"whatsapp": str, "discord": str}.
"""
import json
from openai import OpenAI
import config


def _build_user_message(selection: list[dict], run_mode: str) -> str:
    payload = {
        "run_mode": run_mode,
        "weekly_reset_day": config.WEEKLY_RESET_DAY,
        "projects": [
            {
                "title": p["project"]["title"],
                "builder_handle": p["project"]["builder_handle"],
                "description": p["project"]["description"],
                "demo_url": p["project"].get("demo_url"),
                "captured_detail": p.get("text", "")[:400],
            }
            for p in selection
        ],
    }
    return json.dumps(payload, indent=2)


def _call_agentrouter(system_prompt: str, user_message: str) -> str:
    """Call the AgentRouter OpenAI-compatible chat-completions endpoint."""
    if not config.AGENTROUTER_API_KEY:
        raise RuntimeError("AGENTROUTER_API_KEY is not set — see .env.example")

    client = OpenAI(
        api_key=config.AGENTROUTER_API_KEY,
        base_url=config.AGENTROUTER_BASE_URL,
    )
    resp = client.chat.completions.create(
        model=config.AGENTROUTER_MODEL,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        timeout=60,
    )
    return resp.choices[0].message.content


def generate_drafts(feature_set: list[dict], run_mode: str) -> dict:
    """feature_set: list of {"project": <Project record>, "text": <captured
    detail>, "usable": bool, ...} as produced by capture.capture_project(),
    paired back with its project record. Returns {"whatsapp": str, "discord": str}.
    """
    system_prompt = config.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    user_message = _build_user_message(feature_set, run_mode)

    raw = _call_agentrouter(system_prompt, user_message)

    try:
        drafts = json.loads(raw)
    except json.JSONDecodeError:
        # Model didn't return clean JSON — surface the raw text rather than
        # silently failing, so Stage 5's human reviewer can still see it.
        drafts = {"whatsapp": raw, "discord": raw}

    return drafts
