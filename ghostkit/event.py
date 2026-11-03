"""R1: parse and normalize a Kiro hook event read from stdin."""

from __future__ import annotations

import json
import select
import sys
from dataclasses import dataclass, field


@dataclass
class NormalizedEvent:
    trigger: str
    session_id: str | None = None
    cwd: str | None = None
    tool_name: str | None = None
    command: str | None = None
    tool_input: dict = field(default_factory=dict)
    tool_response: str | None = None
    raw: dict = field(default_factory=dict)


def read_stdin(timeout: float = 2.0) -> str:
    """Read the event JSON without hanging when no stdin is provided."""
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    return sys.stdin.read() if ready else ""


def parse(trigger: str, raw: str) -> NormalizedEvent:
    """Parse a raw JSON event into a NormalizedEvent, tolerating bad input."""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    return NormalizedEvent(
        trigger=trigger,
        session_id=data.get("session_id"),
        cwd=data.get("cwd"),
        tool_name=data.get("tool_name"),
        command=tool_input.get("command"),
        tool_input=tool_input,
        tool_response=data.get("tool_response"),
        raw=data,
    )


def command_cwd(event: NormalizedEvent) -> str | None:
    """Resolve the working directory: prefer tool_input.cwd, fall back to event cwd."""
    return event.tool_input.get("cwd") or event.cwd
