"""R4: append handled events to a JSONL log, correlated by session_id."""

from __future__ import annotations

import json
import time
from pathlib import Path


def append(log_path, event, decision, verbosity: str = "minimal") -> None:
    """Append one JSON line. Never raise into the user's session.

    verbosity:
      - "minimal" (default): no command/prompt/response bodies.
      - "commands": also store the command string (used by Haunted House scoring).
      - "full": also store the tool_response.
    """
    try:
        record = {
            "trigger": event.trigger,
            "ts": time.time(),
            "session_id": event.session_id,
            "tool_name": event.tool_name,
            "decision": decision.kind,
            "reason": decision.reason,
        }
        if verbosity in ("commands", "full"):
            record["command"] = event.command
        if verbosity == "full":
            record["tool_response"] = event.tool_response
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Logging must never break the session.
        pass
