"""R3: emit a decision in Kiro's hook protocol (exit code + stdout/stderr)."""

from __future__ import annotations

import json
import sys


def emit(decision, event, out=None, err=None) -> int:
    """Write the decision and return the process exit code.

    - UserPromptSubmit: always exit 0; a note goes to stdout, never a block.
    - block (PreToolUse): exit 2, reason on stderr.
    - ask (PreToolUse): exit 0, JSON decision on stdout; the reason embeds the command.
    - allow / anything else: exit 0, no output.
    """
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err

    if event.trigger == "UserPromptSubmit":
        if decision.reason:
            out.write(decision.reason)
        return 0

    if decision.kind == "block":
        err.write(decision.reason or "[ghostkit] Blocked.\n")
        return 2

    if decision.kind == "ask":
        command = event.command or ""
        reason = decision.reason or "[ghostkit] Read this command before you approve."
        if command and command not in reason:
            reason = f"{reason}\n\nCommand: {command}"
        out.write(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "permissionDecision": "ask",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
        return 0

    # allow / note-on-non-prompt / unknown: no output.
    return 0
