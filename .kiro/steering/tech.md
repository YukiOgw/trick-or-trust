---
inclusion: fileMatch
fileMatchPattern: "**/*"
---

# Tech

## Runtime

- Python 3.11 or later (`tomllib` is required).
- ghostkit and every hook script use the standard library only. No third-party runtime dependencies.
- Development-only dependencies are allowed: `pytest`, `hypothesis`.
- Must run on macOS, Linux, and Windows without Docker or WSL. Use `pathlib`. Do not assume bash on Windows.

## Hooks

- Hooks read the event JSON from stdin.
- PreToolUse: exit 0 allows, exit 2 blocks and returns stderr to the agent.
- PreToolUse may print `{"hookSpecificOutput":{"permissionDecision":"ask","permissionDecisionReason":"..."}}` to force an approval prompt. How the IDE shows this is being verified in PoC P2.
- Hook scripts fail open by default: an unexpected error exits 0 and writes a diagnostic to the log, so a bug never blocks the user's work. Whether drill guard rules should fail closed is decided in the design phase.
- Hooks that never need a non-zero exit (SessionStart, PostToolUse, Stop) end with `|| true` in their command. A failing Stop hook would otherwise start another agent turn.

## Data

- Policies are TOML files. A decision is `allow`, `ask`, or `block`, always with a human-readable reason.
- Logs are local JSONL files. Prompt text and command arguments are not stored outside an explicit drill.

## Web

- The report and landing page are static HTML, CSS, and JavaScript with no build step, hosted on GitHub Pages.
