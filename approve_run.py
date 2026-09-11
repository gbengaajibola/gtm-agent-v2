#!/usr/bin/env python3
"""
Run by a human after reading the draft (in Discord, or straight from the
pending_review/<run_id>.json file). This is the entire approval gate —
there is no bot polling for reactions; this script IS the "approve".

Usage:
    python approve_run.py 2026-W37 approve
    python approve_run.py 2026-W37 reject
"""
import sys
import json
import shutil

import config
from lib import ledger, discord_bot, git_ops


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ("approve", "reject"):
        print("Usage: python approve_run.py <run_id> approve|reject")
        sys.exit(1)

    run_id, decision = sys.argv[1], sys.argv[2]
    pending_path = config.PENDING_DIR / f"{run_id}.json"

    if not pending_path.exists():
        print(f"No pending review found for run_id '{run_id}'. "
              f"Check {config.PENDING_DIR} for the actual filename.")
        sys.exit(1)

    pending = json.loads(pending_path.read_text(encoding="utf-8"))

    if decision == "reject":
        dest = config.PROCESSED_DIR / f"{run_id}_rejected.json"
        shutil.move(str(pending_path), str(dest))
        git_ops.commit_and_push(f"reject run {run_id}", [str(dest)])
        print(f"Run {run_id} rejected. Nothing was posted. Ledger unchanged.")
        return

    # --- approve: Stage 6 ---
    drafts = pending["drafts"]
    selection = pending["selection"]
    run_mode = pending["run_mode"]

    try:
        discord_bot.send_message(config.DISCORD_PUBLIC_CHANNEL_ID, drafts["discord"])
        print("Posted to the public Discord channel.")
    except Exception as e:
        print(f"WARNING: failed to post to public Discord channel: {e}")
        print("The draft is still saved below — you can post it manually.")

    whatsapp_path = config.PROCESSED_DIR / f"{run_id}_whatsapp_draft.txt"
    whatsapp_path.write_text(drafts["whatsapp"], encoding="utf-8")
    print(f"\nWhatsApp has no public send API — copy/paste this manually "
          f"(also saved to {whatsapp_path}):\n")
    print("-" * 40)
    print(drafts["whatsapp"])
    print("-" * 40)

    # --- Stage 7: update ledger ---
    the_ledger = ledger.load_ledger()
    the_ledger = ledger.append_entries(the_ledger, selection, run_mode, run_id)
    ledger.save_ledger(the_ledger)

    dest = config.PROCESSED_DIR / f"{run_id}_approved.json"
    shutil.move(str(pending_path), str(dest))

    git_ops.commit_and_push(
        f"approve run {run_id} ({run_mode})",
        [str(config.LEDGER_PATH), str(dest), str(whatsapp_path)],
    )
    print(f"\nRun {run_id} approved and ledger updated. Done.")


if __name__ == "__main__":
    main()
