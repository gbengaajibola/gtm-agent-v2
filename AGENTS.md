# AGENTS.md

All code lives in `l2e-runnable/` — a flat Python 3.9+ pipeline (scripts + `lib/`), with no test suite, lint, or typecheck config. Run all commands from inside that directory. Paths below are relative to `l2e-runnable/`.

## Commands

```bash
pip install -r requirements.txt   # then `playwright install chromium`
python setup_check.py             # env check: installs what it can, warns (not fails) on missing secrets
python run_weekly.py              # Stages 1–4 only — stops at the approval gate
python approve_run.py <run_id> approve|reject   # the gate itself; run_id = ISO week tag, e.g. 2026-W37
python check_pending.py           # reminder/timeout sweep of pending_review/
```

There is no test suite. Verification = `python setup_check.py` plus a manual `run_weekly.py` run.

## Autonomous loop

To run the whole cycle end to end in auto mode (preflight → sweep → produce → review → decide → verify, with subagent call map), follow `WORKFLOW_LOOP.md`. It is written env-agnostically so any agent (OpenCode, Claude, Cursor, Copilot, …) can execute it. Approval policy lives there: `AUTO_APPROVE` is on by default — a human owns the gate unless the operator explicitly enables it.

## How the pipeline works (easy to get wrong)

- `run_weekly.py` deliberately stops after posting a draft to the private Discord review channel and writing `pending_review/<run_id>.json`. Nothing public is posted and the ledger is untouched until a human runs `approve_run.py`. Stage 4 LLM failure exits 1 before the gate — nothing is posted. See `GATE_DESIGN.md` (it finalizes/supersedes ARCHITECTURE_v2.md §6e; ARCHITECTURE_v2.md itself is not in this repo).
- Selection (`lib/ledger.py`): CAP=3 fixed. Prefer never-featured (oldest-first FIFO — extractor returns newest-first, so the code reverses) → most-improved (vote-count delta vs previous `output/roster_*.json`) → `none` (no post). A project is retired forever after one `most_improved` featuring. `featured_log.json` is only written on approve.
- State is entirely file-based and git-committed after every writing step via `lib/git_ops.py`: `featured_log.json` (ledger), `output/roster_*.json` snapshots, `pending_review/<run_id>.json` → `processed/<run_id>_{approved,rejected,timed_out}.json`. Git failures (or no git repo at all) are non-fatal by design — scripts warn and continue. `output/*.png` screenshots are gitignored; `.env` is never committed.
- All tuning constants live in `config.py` (CAP, REMINDER_AFTER_HOURS, TIMEOUT_AFTER_HOURS, paths, env loading) — no magic numbers anywhere else for those. Importing `config` creates `output/`, `pending_review/`, `processed/` as a side effect.
- Secrets come from `.env` (never committed; see `.env.example`): `DISCORD_BOT_TOKEN`, `DISCORD_REVIEW_CHANNEL_ID`, `DISCORD_PUBLIC_CHANNEL_ID`, `OPENCODE_GO_API_KEY` (Stage 4; model via `OPENCODE_GO_MODEL`, default `glm-5.3-flash`).
- Approve posts the Discord draft to the public channel and saves the WhatsApp draft to `processed/<run_id>_whatsapp_draft.txt` for manual paste — there is no WhatsApp send API, don't add one.
- To test the reminder/timeout flow without waiting real hours, temporarily lower `REMINDER_AFTER_HOURS` / `TIMEOUT_AFTER_HOURS` in `config.py`, then run `check_pending.py`.
- Subagent routing: `.opencode/SUBAGENT_ROUTING.md` is the delegation protocol (`@planner` → `@executor` → `@evaluator`, models, fallback sentinels) and `opencode.json` loads it into every session — follow it on multi-step work. Launch OpenCode from `l2e-runnable/` and restart the session after changing `opencode.json`/`.opencode/`.

## Intentional quirks — don't "fix" these

- `_escalate_with_browser_use()` in `lib/capture.py` raises `NotImplementedError` on purpose (Browser-Use escalation is a documented stub). Blank captures degrade gracefully; Stage 4 writes around them.
- `lib/extractor.py` clicks the "Newest" sort button because the site's default sort is "Trending" (vote-based, not chronological). Its selectors are pinned to the live site's DOM and will break if the site changes.
- `lib/copywriter.py` expects the LLM to return JSON with `whatsapp`/`discord` keys; on non-JSON output it falls back to using the raw text for both. The prompt text is in `assets/system_prompt.txt`, editable without touching code.

## CI

`.github/workflows/weekly_showcase.yml` (in `l2e-runnable/`): weekly run (Fri 09:00 UTC), 6-hourly `check_pending.py` sweep, and a manual `workflow_dispatch` that can approve/reject a run from the GitHub UI. Requires the four secrets above as repo secrets, plus Actions workflow "Read and write permissions" so it can commit state back.

## Self-healing rule — learnings log

Every session must leave this file smarter, so the same mistakes are never made twice:

- **Before ending a session**, append anything hard-won — a mistake made, a surprise, a wrong assumption, a non-obvious constraint — as a dated entry under "Learnings log" below. Keep each entry to 1–3 lines: what happened + the fix/constraint. If nothing was learned the hard way, add nothing.
- **Record only what an agent would get wrong without it.** No generic advice, no one-off context that won't recur.
- **Verify before writing.** Confirm each claim against the code before recording it; if you can't verify it, don't write it.
- **Reconcile, don't append around conflicts.** If a learning contradicts or supersedes anything in the sections above, update those sections in the same edit — this file must never disagree with itself or the code.
- **Promote and prune.** Once a learning recurs or becomes standard practice, fold it into the main sections (Commands / Pipeline / Quirks / CI) and drop the log entry. Delete entries that have become obsolete or were proven wrong.

### Learnings log

**2026-09-11 — provider swap (Anthropic → AgentRouter)**
- Stage 4 provider coupling lives in exactly 5 files: `config.py`, `lib/copywriter.py`, `.env.example`, `README.md`, `.github/workflows/weekly_showcase.yml`. Everything else (`ledger/git_ops/discord_bot/extractor/capture`, `assets/system_prompt.txt`, gate logic) is provider-agnostic — leave it alone on provider changes.
- AgentRouter is OpenAI-compatible: `POST {AGENTROUTER_BASE_URL}/chat/completions` with `Authorization: Bearer <key>`, payload `{model, max_tokens, messages: [system, user]}`, reply at `choices[0].message.content`. No SDK needed (`requests` suffices). Never use `https://co.agentrouter.org` variants here; canonical base is `https://agentrouter.org/v1` (overridable via `AGENTROUTER_BASE_URL`).
- `lib/copywriter.py`'s only contract is `generate_drafts() -> {"whatsapp", "discord"}` with raw-text fallback for non-JSON — verify provider swaps with mocked `requests.post` (JSON round-trip, header/payload shape, missing-key error), not live calls. See `CHANGELOG.md` for the eval checklist.
- If the first live Stage 4 run returns drafts wrapped in prose instead of JSON (GLM can be chatty), harden the JSON parse in `lib/copywriter.py` — don't touch the gate or anything else.
- `setup_check.py` pip-install fails on externally-managed Python envs — use a venv; unrelated to provider config.

**2026-09-15 — AgentRouter 401 / setup_check venv gotcha**
- `setup_check.py`'s browser check (line 45) shells out to the bare `playwright` executable and runs *before* the secrets check, so it must be run as `PATH=.venv/bin:$PATH .venv/bin/python setup_check.py` — otherwise it dies with `FileNotFoundError` before printing anything useful.
- A Stage 4 `401 {"message":"UNAUTHENTICATED","type":"unauthorized_client_error"}` ("unauthorized client detected") is a key/account problem, not a code bug: don't touch `lib/copywriter.py` or the base URL and don't retry — the operator must rotate/refresh `AGENTROUTER_API_KEY`. Nothing is posted and no `pending_review/` gate file is written. (2026-09-15 subagent audit: the `.env` key parses clean — 51 chars, `sk-` prefix, no whitespace/quotes/BOM, byte-exact vs file — so don't re-audit `.env` formatting on this error; mocked-`requests.post` tests of `generate_drafts()` all pass, the code path is fine.)

**2026-09-18 — provider swap (AgentRouter → OpenCode Go)**
- Stage 4 now uses OpenCode Go: `OPENCODE_GO_API_KEY` / `OPENCODE_GO_MODEL` (default `glm-5.3-flash`) / `OPENCODE_GO_BASE_URL` (default `https://opencode.ai/zen/go/v1`), key via Zen console at `https://opencode.ai/auth`. Same 5-file coupling as the 2026-09-11 entry; `lib/copywriter.py` keeps the OpenAI SDK (`_call_agentrouter()` → `_call_opencode_go()`, contract unchanged). Endpoint verified in live `https://opencode.ai/docs/go` (chat/completions, `@ai-sdk/openai-compatible`); SDK base omits the trailing `/chat/completions`.
- Verify Go swaps with mocked `OpenAI` (patch `lib.copywriter.OpenAI`: JSON round-trip, base_url/model/messages shape, non-JSON fallback, missing-key `RuntimeError`), not live calls — the shell env may already export a key even when `.env` doesn't have it, so force `OPENCODE_GO_API_KEY=dummy-test-key` in-process for deterministic results.
- Go requires every client request to send `x-opencode-session` (a stable per-conversation id) and a real client `User-Agent`; omit them and Stage 4 dies with `400 MissingSessionID` ("cannot be routed efficiently") before the gate. `lib/copywriter.py` generates a random uuid session id at import and passes both via the SDK's `extra_headers` — keep them on any future provider/client edit.
