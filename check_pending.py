#!/usr/bin/env python3
"""
Sweeps pending_review/ for anything awaiting approval too long. Meant to
run more often than the weekly trigger itself (e.g. every few hours) —
see .github/workflows/weekly_showcase.yml.

Behavior (config.py has the actual numbers):
  - Past REMINDER_AFTER_HOURS with no decision -> send one reminder ping,
    mark reminder_sent so it's only sent once.
  - Past TIMEOUT_AFTER_HOURS with no decision -> auto-skip: archive as
    timed out, no post, no ledger update.

Usage:
    python check_pending.py
"""
import json
import shutil
import datetime

import config
from lib import discord_bot, git_ops


def hours_since(iso_timestamp: str) -> float:
    created = datetime.datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    return (now - created).total_seconds() / 3600


def main():
    pending_files = sorted(config.PENDING_DIR.glob("*.json"))
    if not pending_files:
        print("[check_pending] nothing pending.")
        return

    for path in pending_files:
        pending = json.loads(path.read_text(encoding="utf-8"))
        run_id = pending["run_id"]
        age_hours = hours_since(pending["created_at"])

        if age_hours >= config.TIMEOUT_AFTER_HOURS:
            dest = config.PROCESSED_DIR / f"{run_id}_timed_out.json"
            shutil.move(str(path), str(dest))
            try:
                discord_bot.send_message(
                    config.DISCORD_REVIEW_CHANNEL_ID,
                    f"Run `{run_id}` timed out after {config.TIMEOUT_AFTER_HOURS}h "
                    f"with no response — skipped. Nothing was posted, ledger unchanged.",
                )
            except Exception as e:
                print(f"[check_pending] couldn't notify Discord: {e}")
            git_ops.commit_and_push(f"timeout run {run_id}", [str(dest)])
            print(f"[check_pending] {run_id}: timed out, archived.")
            continue

        if age_hours >= config.REMINDER_AFTER_HOURS and not pending.get("reminder_sent"):
            try:
                discord_bot.send_message(
                    config.DISCORD_REVIEW_CHANNEL_ID,
                    f"Reminder: run `{run_id}` is still waiting on a decision "
                    f"(`python approve_run.py {run_id} approve|reject`). "
                    f"Auto-skips at {config.TIMEOUT_AFTER_HOURS}h if untouched.",
                )
                pending["reminder_sent"] = True
                path.write_text(json.dumps(pending, indent=2), encoding="utf-8")
                git_ops.commit_and_push(f"reminder sent {run_id}", [str(path)])
                print(f"[check_pending] {run_id}: reminder sent.")
            except Exception as e:
                print(f"[check_pending] couldn't send reminder for {run_id}: {e}")
        else:
            print(f"[check_pending] {run_id}: still within window ({age_hours:.1f}h old).")


if __name__ == "__main__":
    main()
