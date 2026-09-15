# WORKFLOW_LOOP.md — end-to-end autonomous runbook

Any coding agent (OpenCode, Claude, Cursor, Copilot, …) can execute the full
weekly-showcase cycle by following this file top to bottom in **auto mode**:
no interactive prompts, decide from files, stop-and-report only where listed.
run on **auto Approve**
Run everything with cwd = `l2e-runnable/`.

## The loop

```
Phase 0  PREFLIGHT   → setup_check.py; abort on missing secrets
Phase 1  SWEEP       → check_pending.py (clear stale gates first)
Phase 2  PRODUCE     → run_weekly.py (Stages 1–4, opens the gate)
Phase 3  REVIEW      → reviewer subagent scores pending_review/<run_id>.json
Phase 4  DECIDE      → approve_run.py <run_id> approve|reject (policy below)
Phase 5  VERIFY      → git status + ledger/processed files confirm landed
Loop back to Phase 1 on next trigger (weekly cron or manual re-run).
```

## Phase details

### 0 — Preflight
- `python setup_check.py`. If `config.missing_secrets()` is non-empty → **STOP**,
  report which keys are missing, do not touch network stages.
- Use a venv (`setup_check.py` pip-install fails on externally-managed Pythons).

### 1 — Sweep stale state (before opening a new gate)
- `python check_pending.py`. This sends due reminders and archives timed-out
  runs as `processed/<run_id>_timed_out.json` (no post, ledger untouched).
- Rationale: never open a second gate while one is still pending for the week.

### 2 — Produce the week's draft
- `python run_weekly.py`. Expect: `output/roster_<WEEK>.json` snapshot,
  draft posted to the private review channel, `pending_review/<WEEK>.json`
  written, then the script **stops by design**.
- `run_mode == "none"` → nothing eligible, run ends here (no post, no gate).
- Stage 4 failure → script exits 1 **before** the gate, nothing posted.
  Do not retry blindly: inspect the error (bad key? model id rejected?
  chatty non-JSON output?) then fix once.

### 3 — Review (subagent, not the producer)
Spawn a **reviewer subagent** with exactly this brief:
> Read `pending_review/<run_id>.json` + `assets/system_prompt.txt`. Score the
> drafts PASS/FAIL on: (a) both `whatsapp` + `discord` keys present and
> non-empty; (b) WhatsApp ~120 words, plain text, no markdown; (c) never uses
> the word "Showcase"; (d) builder handles credited; (e) `most_improved` mode
> never implies novelty; (f) reset-day deadline only if in input data —
> no invented numbers/testimonials/deadlines. Return PASS or FAIL + reasons.
> Do not edit files, do not approve.

### 4 — Decide (approval policy)
- `AUTO_APPROVE` default: **OFF**. With it off, a reviewer PASS means: report
  the draft and wait — a human runs `python approve_run.py <run_id>
  approve|reject` (or the GitHub `workflow_dispatch` approve action).
- With `AUTO_APPROVE` explicitly enabled by the operator: reviewer PASS →
  run `python approve_run.py <run_id> approve` yourself; reviewer FAIL →
  leave pending and report reasons (or `reject` if the draft is unusable).
- Reject path archives to `processed/<run_id>_rejected.json`, ledger untouched.
- Approve path posts Discord-public + saves
  `processed/<run_id>_whatsapp_draft.txt` for **manual** paste (no WhatsApp
  send API — never add one).
- A human decision always overrides the loop; never re-approve a rejected run.

### 5 — Verify landed state
- `git status --short` clean apart from intended files; ledger
  (`featured_log.json`) updated **only** on approve; pending file moved to
  `processed/<run_id>_{approved,rejected,timed_out}.json`.
- Git push failures are non-fatal (commit still saved locally) — report, don't
  re-run the pipeline over them.

## Subagent call map (auto mode)

| Spawn when | Subagent brief |
|---|---|
| Every run, Phase 3 | Reviewer (brief above) — validates the draft |
| Roster empty / Stage 1 crash | Extractor-triage: distinguish site-down vs DOM-change (selectors in `lib/extractor.py` are pinned to the live DOM) vs bot-block; report, don't guess-fix selectors |
| >1 blank Stage-2 capture | Capture-triage: confirm graceful-degradation path (`usable=False`, Stage 4 writes around it); do **not** implement the `Browser-Use` stub in `lib/capture.py` — it is intentional |
| Anything else | Main agent handles it inline; prefer fewer agents over more |

Rules: batch independent subagent calls in parallel; give each a tight brief
with files to read and exactly what to return; never delegate secret handling
(keys stay in `.env`, never in prompts, logs, or commits).

## Stop-and-report (do not loop past these)

- Missing secrets (Phase 0 fails).
- Stage 4 exit 1 twice in a row → escalate, don't hammer the provider.
- `pending_review/` gate still awaiting human with `AUTO_APPROVE` off.
- Live site unreachable or selectors returning zero cards two runs running.

## Schedules (mirror of CI)

- Weekly produce: Fri 09:00 UTC (`run_weekly.py`).
- Sweep: every 6h (`check_pending.py`).
- Manual: `workflow_dispatch` with `run_weekly` / `check_pending` / `approve`.
