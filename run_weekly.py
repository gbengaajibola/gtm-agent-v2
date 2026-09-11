#!/usr/bin/env python3
"""
Weekly trigger (Stage 0) -> Stages 1-4 -> opens the approval gate (Stage 5)
and stops. Nothing gets posted publicly or written to the ledger from this
script — that only happens after a human runs approve_run.py.

Usage:
    python run_weekly.py
"""
import sys
import json
import datetime
import glob

import config
from lib import extractor, ledger, capture, copywriter, discord_bot, git_ops


def latest_previous_roster(current_week_tag: str) -> list[dict]:
    snapshots = sorted(glob.glob(str(config.OUTPUT_DIR / "roster_*.json")))
    snapshots = [s for s in snapshots if current_week_tag not in s]
    if not snapshots:
        return []
    with open(snapshots[-1], encoding="utf-8") as f:
        return json.load(f)


def main():
    missing = config.missing_secrets()
    if missing:
        print(f"[run_weekly] WARNING: missing env vars: {', '.join(missing)}")
        print("[run_weekly] continuing anyway where possible — see .env.example")

    week_tag = ledger.iso_week_tag()
    print(f"[run_weekly] Starting run {week_tag}")

    # --- Stage 1 ---
    print("[run_weekly] Stage 1: extracting roster...")
    roster = extractor.extract_roster()
    roster_path = config.OUTPUT_DIR / f"roster_{week_tag}.json"
    roster_path.write_text(json.dumps(roster, indent=2), encoding="utf-8")
    print(f"[run_weekly] Extracted {len(roster)} projects -> {roster_path}")

    # --- Stage 1b/1c ---
    the_ledger = ledger.load_ledger()
    never, most_improved_candidates, retired = ledger.classify(roster, the_ledger)
    previous_roster = latest_previous_roster(week_tag)
    selection, run_mode = ledger.select(never, most_improved_candidates, previous_roster)

    git_ops.commit_and_push(
        f"roster snapshot {week_tag} ({run_mode})", [str(roster_path)]
    )

    if run_mode == "none":
        print("[run_weekly] Nothing eligible (all projects already used twice). "
              "END — no post this week.")
        return

    titles = ", ".join(p["title"] for p in selection)
    print(f"[run_weekly] Selected {len(selection)} project(s) as '{run_mode}': {titles}")

    # --- Stage 2 ---
    print("[run_weekly] Stage 2: visiting each project's live link...")
    feature_set = []
    for p in selection:
        captured = capture.capture_project(p)
        feature_set.append({"project": p, **captured})

    # --- Stage 3 is just this list itself; nothing extra to build ---

    # --- Stage 4 ---
    print("[run_weekly] Stage 4: generating copy...")
    try:
        drafts = copywriter.generate_drafts(feature_set, run_mode)
    except Exception as e:
        print(f"[run_weekly] Stage 4 failed: {e}")
        print("[run_weekly] Aborting before the gate — nothing was posted.")
        sys.exit(1)

    # --- Stage 5: open the gate, then stop ---
    pending = {
        "run_id": week_tag,
        "run_mode": run_mode,
        "selection": selection,
        "drafts": drafts,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "reminder_sent": False,
    }
    pending_path = config.PENDING_DIR / f"{week_tag}.json"
    pending_path.write_text(json.dumps(pending, indent=2), encoding="utf-8")

    review_message = (
        f"**New draft ready for review — run `{week_tag}`** (mode: {run_mode})\n\n"
        f"--- WhatsApp draft ---\n{drafts.get('whatsapp', '')}\n\n"
        f"--- Discord draft ---\n{drafts.get('discord', '')}\n\n"
        f"To approve: `python approve_run.py {week_tag} approve`\n"
        f"To reject: `python approve_run.py {week_tag} reject`"
    )

    try:
        discord_bot.send_message(config.DISCORD_REVIEW_CHANNEL_ID, review_message)
        print("[run_weekly] Posted draft to the private review channel.")
    except Exception as e:
        print(f"[run_weekly] Could not post to Discord review channel: {e}")
        print(f"[run_weekly] Draft is still saved at {pending_path} — review it there.")

    git_ops.commit_and_push(f"pending review {week_tag}", [str(pending_path)])
    print(f"[run_weekly] Gate open. Waiting on: python approve_run.py {week_tag} approve|reject")


if __name__ == "__main__":
    main()
