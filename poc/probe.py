#!/usr/bin/env python3
"""PoC probe for Kiro hooks (Trick or Trust).

Records hook events to poc/logs/events.jsonl so we can learn:
- when each hook fires relative to the approval prompt (P1),
- what the event JSON looks like (P1),
- how "ask" and "block" decisions surface in the IDE (P2),
- how UserPromptSubmit output affects the agent (P5),
- how long one hook run takes (P6).

Privacy: unless the payload contains the marker "ghostkit-poc", only the event
name, timestamps, and key names are recorded. Values are never stored.

Safety: any unexpected error exits 0, so the probe never blocks real work.
"""

import json
import os
import select
import sys
import time
from pathlib import Path

PROBE_VERSION = "2026-11-01.1"
MARKER = "ghostkit-poc"
LOG_FILE = Path(__file__).resolve().parent / "logs" / "events.jsonl"
STDIN_WAIT_SECONDS = 2.0
ENV_NAME_HINTS = ("KIRO", "HOOK", "PROMPT")

ASK_REASON = (
    "[ghostkit-poc] A ghost is standing behind this command. "
    "Read it closely before you approve."
)
BLOCK_MESSAGE = "[ghostkit-poc] The PoC probe blocked this command with exit code 2.\n"
REJECT_MESSAGE = "[ghostkit-poc] The PoC probe rejected this prompt with exit code 1.\n"
CLARIFY_NOTE = (
    "[ghostkit-poc] Hook note: if the request does not name a target file, "
    "a goal, and a done condition, ask one clarifying question before doing any work.\n"
)


def read_stdin() -> str:
    """Read the event JSON without hanging when no stdin is provided."""
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    ready, _, _ = select.select([sys.stdin], [], [], STDIN_WAIT_SECONDS)
    return sys.stdin.read() if ready else ""


def shape_of(value, depth: int = 0):
    """Return the structure of a JSON value (key names and types) without values."""
    if depth > 4:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: shape_of(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [shape_of(value[0], depth + 1)] if value else []
    return type(value).__name__


def decide(event: str, text: str):
    """Return (exit_code, stdout_text, stderr_text) for marked events."""
    if event == "PreToolUse":
        if "ghostkit-poc-block" in text:
            return 2, "", BLOCK_MESSAGE
        if "ghostkit-poc-ask" in text:
            decision = {
                "hookSpecificOutput": {
                    "permissionDecision": "ask",
                    "permissionDecisionReason": ASK_REASON,
                }
            }
            return 0, json.dumps(decision), ""
    if event == "UserPromptSubmit":
        if "ghostkit-poc-reject" in text:
            return 1, "", REJECT_MESSAGE
        if "ghostkit-poc-clarify" in text:
            return 0, CLARIFY_NOTE, ""
    return 0, "", ""


def write_record(record: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    start_ns = time.time_ns()
    event = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    raw = read_stdin()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"_unparsed_length": len(raw)}

    env_prompt = os.environ.get("USER_PROMPT", "")
    searchable = raw + "\n" + env_prompt
    marked = MARKER in searchable

    record = {
        "probe_version": PROBE_VERSION,
        "event": event,
        "ts_ns": start_ns,
        "marked": marked,
        # Opaque identifiers only (no prompt or command text), so events from
        # parallel sessions in the same workspace can be told apart.
        "session_id": payload.get("session_id") if isinstance(payload, dict) else None,
        "tool_name": payload.get("tool_name") if isinstance(payload, dict) else None,
        "shape": shape_of(payload),
        "env_names": sorted(
            name for name in os.environ if any(hint in name.upper() for hint in ENV_NAME_HINTS)
        ),
        "cwd": os.getcwd() if marked else None,
    }
    if marked:
        record["payload"] = payload
        if env_prompt:
            record["user_prompt_env"] = env_prompt

    exit_code, stdout_text, stderr_text = decide(event, searchable) if marked else (0, "", "")
    record["decision"] = {"exit": exit_code, "stdout": stdout_text, "stderr": stderr_text}
    record["duration_ms"] = round((time.time_ns() - start_ns) / 1_000_000, 2)
    write_record(record)

    if stdout_text:
        sys.stdout.write(stdout_text)
    if stderr_text:
        sys.stderr.write(stderr_text)
    return exit_code


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:  # never break the user's session because of the probe
        try:
            write_record({"event": "probe_error", "ts_ns": time.time_ns(), "error": repr(exc)[:300]})
        except Exception:
            pass
        code = 0
    sys.exit(code)
