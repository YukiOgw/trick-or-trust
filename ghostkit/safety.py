"""R7: training-mode guard.

Independent of a room's own rules, block any command that reaches a real secret
path or an external host that is not an RFC 6761 `.invalid` name. This keeps the
practice harmless even if a room's policy is misconfigured.
"""

from __future__ import annotations

import re

from .policy import Decision

SECRET_PATHS = ("~/.aws", "~/.ssh", "/.aws/", "/.ssh/")
HOST_RE = re.compile(r"https?://([a-zA-Z0-9._\-]+)")


def _real_target(command: str) -> str | None:
    for host in HOST_RE.findall(command):
        if not host.endswith(".invalid"):
            return f"external host '{host}'"
    for path in SECRET_PATHS:
        if path in command:
            return f"secret path '{path}'"
    return None


def guard(decision: Decision, event, training_mode: bool) -> Decision:
    """In training mode, force a block when a command reaches a real target."""
    if not training_mode:
        return decision
    hit = _real_target(event.command or "")
    if hit and decision.kind != "block":
        return Decision(
            "block",
            f"[ghostkit] Training guard: this command reaches {hit}. "
            f"Practice rooms must only touch .invalid hosts and the practice folder.",
        )
    return decision
