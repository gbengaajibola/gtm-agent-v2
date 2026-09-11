# Changelog — Anthropic → AgentRouter (glm-5.3)

Date: 2026-09-11. Stage 4 provider swap, clean break (no Anthropic fallback).

## Process (as requested)
1. **Small-model survey** (explore subagent): inventoried every `ANTHROPIC`/Claude reference — coupling lived only in `config.py`, `lib/copywriter.py`, `.env.example`, `README.md`, `.github/workflows/weekly_showcase.yml`. Zero coupling in `ledger/git_ops/discord_bot/extractor/capture`, `assets/system_prompt.txt`, gate logic.
2. **Plan** (Kimi K3 planner subagent): 5-file change plan + 8-check confined eval suite (mocked HTTP, no live network).
3. **Execution** (GLM 5.3 role): applied the plan below, ran the eval suite, all green.

## What changed (5 files, nothing else)
- `config.py`: removed `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` (`claude-sonnet-4-6`); added `AGENTROUTER_API_KEY` (= `""`), `AGENTROUTER_MODEL` (default `"glm-5.3"`), `AGENTROUTER_BASE_URL` (default `"https://agentrouter.org/v1"`). `missing_secrets()` now requires `AGENTROUTER_API_KEY`.
- `lib/copywriter.py`: `_call_anthropic()` → `_call_agentrouter()`. Was `POST https://api.anthropic.com/v1/messages` with `x-api-key` + `anthropic-version` headers and `{model, max_tokens, system, messages:[user]}` payload, parsed via `data["content"]` text blocks. Now `POST {BASE_URL}/chat/completions` (OpenAI-compatible) with `Authorization: Bearer` header and `{model, max_tokens, messages:[system, user]}` payload, parsed via `data["choices"][0]["message"]["content"]`. `generate_drafts() → {"whatsapp", "discord"}` contract and non-JSON fallback unchanged.
- `.env.example`: `ANTHROPIC_API_KEY` → `AGENTROUTER_API_KEY` (+ commented `AGENTROUTER_MODEL` / `AGENTROUTER_BASE_URL` overrides).
- `README.md`: setup step 3 secret names updated.
- `.github/workflows/weekly_showcase.yml`: `ANTHROPIC_API_KEY` secret → `AGENTROUTER_API_KEY` (+ optional `AGENTROUTER_MODEL`).
- No new dependencies (`requests` already in `requirements.txt`; no SDK needed).

## Eval results (no live calls; `requests.post` mocked)
1. `git diff --name-only` = exactly the 5 files above — PASS
2. Contract-JSON: mocked `{"whatsapp":"W","discord":"D"}` round-trips — PASS
3. Payload/headers: URL ends `/chat/completions`, `Bearer` auth, no `x-api-key`/`anthropic-version`, `model == "glm-5.3"`, `messages == [system, user]` — PASS
4. Non-JSON fallback (raw text → both keys) — PASS
5. Missing key raises `RuntimeError` naming `AGENTROUTER_API_KEY` — PASS
6. Defaults (`glm-5.3`, `https://agentrouter.org/v1`) with env unset — PASS
7. `grep -ri anthropic` over the 5 files: clean — PASS
8. `missing_secrets()` consistency; `setup_check.py`/all untouched files unmodified; `py_compile` clean — PASS

## To configure (reviewer action)
- `.env`: set `AGENTROUTER_API_KEY` (key from `https://agentrouter.org/console/token`); optionally `AGENTROUTER_MODEL=glm-5.3`, `AGENTROUTER_BASE_URL=https://agentrouter.org/v1`.
- GitHub repo secrets: replace `ANTHROPIC_API_KEY` with `AGENTROUTER_API_KEY` (add `AGENTROUTER_MODEL` only to pin/override).
- Pre-existing, unrelated: `setup_check.py` pip install fails on externally-managed Python envs (`error: externally-managed-environment`) — use a venv; not caused by this change.

## Not yet verified
- No live AgentRouter call made (deliberate). First real `run_weekly.py` Stage 4 will confirm model id `glm-5.3` is accepted and JSON shape holds; GLM reasoning models can be chatty — if drafts come back wrapped in prose, harden the JSON parse, don't touch the gate.

## Rollback
- `git log` → revert this commit; restore `ANTHROPIC_API_KEY` in `.env` and repo secrets.
