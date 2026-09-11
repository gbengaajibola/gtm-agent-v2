"""
Stage 1b (classify) + 1c (select). See ARCHITECTURE_v2.md Section 6b/6c
for the full reasoning — this is the implementation of that spec.

Three states, derived purely from featured_log.json's contents (no extra
schema needed):
  NEVER_FEATURED        -> project_id has no entry at all
  FEATURED_ONCE_AS_NEW   -> exactly one entry, post_type == "new_build"
  RETIRED                 -> has a "most_improved" entry (permanent, forever)
"""
import json
import datetime
import config


def iso_week_tag(d=None) -> str:
    d = d or datetime.date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def load_ledger() -> dict:
    if config.LEDGER_PATH.exists():
        return json.loads(config.LEDGER_PATH.read_text(encoding="utf-8"))
    return {"featured": []}


def save_ledger(ledger: dict) -> None:
    config.LEDGER_PATH.write_text(json.dumps(ledger, indent=2), encoding="utf-8")


def classify(roster: list[dict], ledger: dict):
    by_id: dict[str, list[dict]] = {}
    for entry in ledger.get("featured", []):
        by_id.setdefault(entry["project_id"], []).append(entry)

    never_featured, most_improved_candidates, retired = [], [], []

    for p in roster:
        entries = by_id.get(p["project_id"], [])
        if not entries:
            never_featured.append(p)
        elif any(e["post_type"] == "most_improved" for e in entries):
            retired.append(p)
        else:
            most_improved_candidates.append(p)

    return never_featured, most_improved_candidates, retired


def select(never_featured, most_improved_candidates, previous_roster):
    """Returns (selection: list[dict], run_mode: str). run_mode is one of
    'new_build', 'most_improved', or 'none' (END — nothing to post)."""

    if never_featured:
        # Extractor returns Newest-first; reverse for oldest-first (FIFO),
        # which both clears any backlog fairly and is the only rule needed
        # (v1 had a separate "Fallback A" for this — collapsed in v2, see
        # ARCHITECTURE_v2.md Section 6c).
        ordered = list(reversed(never_featured))
        return ordered[:config.CAP], "new_build"

    if most_improved_candidates:
        prev_votes = {p["project_id"]: p["vote_count"] for p in previous_roster}
        ranked = sorted(
            most_improved_candidates,
            key=lambda p: (p["vote_count"] or 0) - prev_votes.get(p["project_id"], 0),
            reverse=True,
        )
        return ranked[:config.CAP], "most_improved"

    return [], "none"


def append_entries(ledger: dict, selection: list[dict], run_mode: str, run_id: str) -> dict:
    today = datetime.date.today().isoformat()
    for p in selection:
        ledger["featured"].append({
            "project_id": p["project_id"],
            "date_first_featured": today,
            "post_type": run_mode,
            "run_id": run_id,
        })
    return ledger
