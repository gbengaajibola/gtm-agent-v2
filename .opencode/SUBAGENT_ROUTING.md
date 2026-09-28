# Subagent Routing

## Routing Table

| Task | Agent | Model | Provider |
|------|-------|-------|----------|
| Planning & analysis | `@planner` | `opencode-go/kimi-k3` | OpenCode Go |
| Planning (fallback) | `@planner-fallback` | `opencode-go/deepseek-v4-pro` | OpenCode Go |
| Code execution | `@executor` | `opencode/muse-spark-1.2-contributor-free` | OpenCode Zen |
| Review & approval | `@evaluator` | `opencode-go/kimi-k3` | OpenCode Go |
| Review (fallback) | `@evaluator-fallback` | `opencode-go/deepseek-v4-pro` | OpenCode Go |

## Routing Rules

### Role Separation
- **Planners/evaluators** NEVER execute code, edit files, or run bash commands.
- **Executor** NEVER plans or self-approves.

### Primary-First with Fallback
- Always invoke the primary agent first (`@planner`, `@evaluator`).
- Fallback agents (`@planner-fallback`, `@evaluator-fallback`) are invoked ONLY when:
  - The primary emits its sentinel string (e.g., `PLANNER_UNAVAILABLE: ...`), OR
  - The Task tool reports a model/rate-limit/auth error for the primary.
- Never invoke fallbacks proactively. Never invoke both primary and fallback simultaneously.

### Execution Flow

```
User request
    ↓
@planner → produces implementation plan
    ↓
@executor → implements the plan
    ↓
@evaluator → reviews the changes
    ├─ APPROVE → done
    └─ REQUEST_CHANGES → @executor applies fixes → @evaluator re-reviews
```

### Sentinel Strings
- `PLANNER_UNAVAILABLE: invoke @planner-fallback instead`
- `EVALUATOR_UNAVAILABLE: invoke @evaluator-fallback instead`

### Fallback Limitations
OpenCode has no native automatic model fallback. The primary+fallback-twin pattern defined here IS the fallback mechanism. Do not attempt to put two models in one agent's `model` field.

### Config Limitations
- OpenCode agent config has no `variant` field (variants are session-level, switched with `variant_cycle`). Unknown keys like `variant:` are silently passed through to the provider and ignored — so all agents run model defaults. Do not re-add `variant` to agent frontmatter.
- After changing `opencode.json` or anything under `.opencode/`, restart the OpenCode session — config/agents load at session start.
- Launch OpenCode from `l2e-runnable/` (the git root). OpenCode looks for config in the cwd then up to the nearest git dir — launching from the parent folder means no project config and no custom agents load.
