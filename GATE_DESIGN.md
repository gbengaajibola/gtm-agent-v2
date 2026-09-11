# Approval Gate — Final Design

This supersedes the "private Discord channel, react ✅/❌" description in
`ARCHITECTURE_v2.md` Section 6e — that was the working assumption before
this was finalized. Kept as its own file so it's easy to find the one
place that documents exactly how approval actually works.

## Why not reactions

A Discord webhook can only send messages — it has no way to see reactions,
replies, or anything else happening in a channel. Detecting a reaction
requires a real Discord bot that polls the API for it, which is real
infrastructure (an Application + bot token + invite + permissions) just to
answer a yes/no question.

## What v2 actually does

- **One Discord bot** (not a webhook) sends messages to both the private
  review channel and the public channel. A single bot token can post to any
  channel it's been invited to, which is simpler than managing a separate
  webhook URL per channel.
- **Approval itself is a local script, not anything read from Discord.**
  `run_weekly.py` posts the draft to the review channel for visibility and
  writes `pending_review/<run_id>.json`, then stops. A human reads the
  draft (in Discord or straight from the file) and runs:
  ```
  python approve_run.py <run_id> approve
  python approve_run.py <run_id> reject
  ```
  Approving runs Stage 6 (post to Discord, print/save the WhatsApp draft for
  manual pasting) and Stage 7 (ledger update). Rejecting just archives the
  pending file — nothing is posted, the ledger is untouched.
- **No polling loop runs inside a single script execution.** Instead,
  `check_pending.py` is a separate script meant to run on its own more
  frequent schedule (every 6 hours in the provided GitHub Actions workflow)
  that sweeps `pending_review/` for anything that's been sitting too long.

## Timing

- **Reminder:** if a pending run is still undecided after
  `REMINDER_AFTER_HOURS` (default 24h, in `config.py`), one reminder message
  is sent to the review channel. Only ever sent once per run.
- **Timeout:** if still undecided after `TIMEOUT_AFTER_HOURS` (default 72h
  total), the run is auto-skipped — archived as timed-out, nothing posted,
  ledger untouched. Both numbers are plain constants in `config.py`, safe
  to change without touching any logic.

## Bonus: approving without a local checkout

The GitHub Actions workflow also exposes a manual `workflow_dispatch`
trigger with an `approve` action, so a decision can be made from GitHub's
own UI (including the mobile app) by entering the run ID and
approve/reject — no local git checkout needed if that's more convenient
day to day.
