# LearnToEarn Weekly Showcase — Runnable v2

Implements `ARCHITECTURE_v2.md` end to end. Read `GATE_DESIGN.md` for
exactly how approval works — it finalizes and slightly supersedes what
`ARCHITECTURE_v2.md` Section 6e originally assumed.

## What's real vs. stubbed

- **Real and tested:** Stage 1 extraction selectors (validated against a
  real captured page — see the architecture delivery's
  `validate_selectors.py`), the ledger/selection logic, the gate/reminder/
  timeout flow, git versioning.
- **Real but not yet run live:** the actual Playwright browser automation
  (Stage 1 and Stage 2) — couldn't be executed against the live site from
  the sandbox this was built in due to a network allowlist restriction.
  Structurally correct, needs a real first run to confirm.
- **Intentionally stubbed:** Browser-Use escalation in `lib/capture.py`
  (see the docstring there for why) — a project whose plain-Playwright
  capture comes back blank just proceeds without a captured visual detail
  rather than blocking the run.

## One-time setup

1. **Install dependencies and the browser binary:**
   ```
   pip install -r requirements.txt
   python setup_check.py
   ```
   `setup_check.py` installs what it can and warns (without failing) about
   anything that needs a human, like secrets.

2. **Create the Discord bot** (used for both the review channel and the
   public channel — see `lib/discord_bot.py`'s docstring for the exact
   click-path): make an Application at discord.com/developers/applications,
   add a Bot, copy its token, invite it to your server with "Send Messages"
   permission, then copy both channel IDs (Developer Mode → right-click a
   channel → Copy Channel ID).

3. **Copy `.env.example` to `.env`** and fill in:
   - `DISCORD_BOT_TOKEN`, `DISCORD_REVIEW_CHANNEL_ID`, `DISCORD_PUBLIC_CHANNEL_ID`
   - `AGENTROUTER_API_KEY` (Stage 4 uses AgentRouter's OpenAI-compatible API,
     default model `glm-5.3` — override with `AGENTROUTER_MODEL` if needed)
   - `WEEKLY_RESET_DAY` (used honestly in the copy's closing line)

4. **If using GitHub Actions:** add the same four values as repo secrets
   (Settings → Secrets and variables → Actions), and make sure Actions has
   write permission to the repo (Settings → Actions → General → Workflow
   permissions → "Read and write permissions") so it can commit snapshots
   back.

## Running it locally

```
python run_weekly.py
```

This runs Stages 1–4, posts the draft to your private review channel, and
stops. Then:

```
python approve_run.py <run_id> approve
# or
python approve_run.py <run_id> reject
```

The `run_id` is printed by `run_weekly.py` (an ISO week tag like
`2026-W37`) and is also the filename in `pending_review/`.

To test the reminder/timeout sweep without waiting real hours, temporarily
lower `REMINDER_AFTER_HOURS` / `TIMEOUT_AFTER_HOURS` in `config.py`, then
run:

```
python check_pending.py
```

## Files

| File | Stage |
|---|---|
| `run_weekly.py` | 0–4, opens the gate |
| `lib/extractor.py` | 1 |
| `lib/ledger.py` | 1b, 1c, 7 |
| `lib/capture.py` | 2 |
| `lib/copywriter.py` | 4 |
| `assets/system_prompt.txt` | 4 (the actual prompt text, editable without touching code) |
| `approve_run.py` | 5 (the gate itself), 6, 7 |
| `check_pending.py` | 5 (reminder/timeout sweep) |
| `lib/discord_bot.py` | 5, 6 |
| `lib/git_ops.py` | 7 (and every other state-writing step) |
| `.github/workflows/weekly_showcase.yml` | 0 (scheduling) |

## Known gaps for v3 (see ARCHITECTURE_v2.md Section 9 too)

- Browser-Use escalation is a stub — wire it in once real runs show how
  often it's actually needed.
- LinkedIn / Twitter-X versions of Stage 4 — deliberately not built yet.
- This hasn't had a real live run against the actual site yet — treat the
  first run as a test, not a trusted unattended run.
