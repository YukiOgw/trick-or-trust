"""R7: training-mode guard.

Independent of a room's own rules, block a command that points at a real secret
path or at a URL whose host is not an RFC 6761 `.invalid` name (or this machine).
This keeps the practice harmless even if a room's policy is misconfigured.

Limits, stated plainly: the guard reads `http(s)://` URLs and a short list of
secret paths in the command text. It does not understand every way a command can
reach a network (`ssh host`, `nc host 80`, a script that builds its own URL).
It is a safety net for practice rooms, not a sandbox.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from .policy import Decision

SECRET_PATHS = ("~/.aws", "~/.ssh", "/.aws/", "/.ssh/")
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
URL_RE = re.compile(r"https?://[^\s'\"<>|;&)]+", re.IGNORECASE)


def _real_target(command: str) -> str | None:
    for url in URL_RE.findall(command):
        try:
            # urlsplit drops user info and the port, so `https://x.invalid@evil.com/`
            # is read as evil.com, which is where the request really goes.
            host = urlsplit(url).hostname
        except ValueError:
            return f"a URL that cannot be read ({url})"
        if host and host not in LOOPBACK_HOSTS and not host.endswith(".invalid"):
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
