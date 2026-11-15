#!/usr/bin/env python3
"""P4 の記録用: 練習用の部屋で提案・実行されたシェルコマンドを記録する。

部屋を別ウィンドウで開いたときに、その部屋の .kiro/hooks から呼ばれる。
記録先は trick-or-trust/poc/logs/p4-events.jsonl。
目印は使わず、部屋の中のシェルコマンドをすべて記録する（部屋は実験専用）。
"""
import json
import select
import sys
import time
from pathlib import Path

LOG = Path(__file__).resolve().parent / "logs" / "p4-events.jsonl"


def read_stdin() -> str:
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    ready, _, _ = select.select([sys.stdin], [], [], 2.0)
    return sys.stdin.read() if ready else ""


def main() -> None:
    event = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    raw = read_stdin()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    tool_input = payload.get("tool_input") or {}
    record = {
        "event": event,
        "ts": time.time(),
        "session_id": payload.get("session_id"),
        "tool_name": payload.get("tool_name"),
        "command": tool_input.get("command"),
        "tool_cwd": tool_input.get("cwd"),
    }
    if event == "PostToolUse":
        record["tool_response"] = payload.get("tool_response")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # 記録の失敗でセッションを止めない
        pass
    sys.exit(0)
