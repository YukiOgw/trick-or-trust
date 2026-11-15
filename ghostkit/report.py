"""R5: build an offline HTML graveyard report from ghostkit JSONL logs.

Classification (per session, paired by command):
  - PreToolUse block                     -> blocked  (ghostkit stopped it)
  - PreToolUse ask + PostToolUse rejected -> treat    (read and refused)
  - PreToolUse ask + PostToolUse executed -> trick    (approved; the ghost got in)
  - PreToolUse ask with no PostToolUse    -> pending
"""

from __future__ import annotations

import html
import json
from pathlib import Path

LABELS = {
    "treat": ("🍬", "Treat", "You read it and refused. Safe."),
    "trick": ("👻", "Trick", "Approved without reading. The ghost got in."),
    "blocked": ("🛡️", "Blocked", "ghostkit stopped this during training."),
    "pending": ("🕯️", "Pending", "A ghost was raised; no outcome recorded yet."),
}
ORDER = ["trick", "treat", "blocked", "pending"]


def read_events(log_paths) -> list[dict]:
    events: list[dict] = []
    for raw_path in log_paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def classify(events) -> list[dict]:
    by_session: dict = {}
    for event in events:
        by_session.setdefault(event.get("session_id"), []).append(event)

    encounters: list[dict] = []
    for session_id, items in by_session.items():
        items.sort(key=lambda e: e.get("ts", 0))
        pending: dict = {}
        for event in items:
            trigger = event.get("trigger")
            decision = event.get("decision")
            command = event.get("command")
            if trigger == "PreToolUse" and decision == "block":
                encounters.append({"outcome": "blocked", "command": command, "session": session_id})
            elif trigger == "PreToolUse" and decision == "ask":
                pending[command] = event
            elif trigger == "PostToolUse" and command in pending:
                pending.pop(command)
                outcome = "treat" if event.get("rejected") else "trick"
                encounters.append({"outcome": outcome, "command": command, "session": session_id})
        for command in pending:
            encounters.append({"outcome": "pending", "command": command, "session": session_id})
    return encounters


def build(log_paths, title: str = "Trick or Trust — Graveyard") -> str:
    encounters = classify(read_events(log_paths))
    counts: dict = {}
    for encounter in encounters:
        counts[encounter["outcome"]] = counts.get(encounter["outcome"], 0) + 1

    summary_parts = []
    for key in ORDER:
        if counts.get(key):
            emoji, label, _ = LABELS[key]
            summary_parts.append(f"{emoji} {label}: {counts[key]}")
    summary = "  ".join(summary_parts) or "No encounters yet."

    rows = []
    for key in ORDER:
        for encounter in [e for e in encounters if e["outcome"] == key]:
            emoji, label, note = LABELS[key]
            command = html.escape(encounter.get("command") or "(command not recorded)")
            rows.append(
                f'<tr><td class="o">{emoji} {label}</td>'
                f"<td><code>{command}</code></td>"
                f'<td class="n">{html.escape(note)}</td></tr>'
            )

    rows_html = "\n".join(rows) if rows else '<tr><td colspan="3">Nothing yet.</td></tr>'
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{safe_title}</title>
<style>
  body {{ background:#0b0b12; color:#e8e8f0; font-family:system-ui,-apple-system,sans-serif; padding:2rem; }}
  h1 {{ font-weight:600; letter-spacing:.02em; }}
  .summary {{ font-size:1.2rem; margin:1rem 0 1.5rem; }}
  table {{ border-collapse:collapse; width:100%; }}
  th, td {{ border-bottom:1px solid #2a2a38; padding:.55rem .6rem; text-align:left; vertical-align:top; }}
  th {{ color:#9aa; font-weight:500; }}
  td.o {{ white-space:nowrap; }}
  td.n {{ color:#9aa; }}
  code {{ color:#c6b3ff; }}
</style></head>
<body>
  <h1>🪦 {safe_title}</h1>
  <div class="summary">{summary}</div>
  <table>
    <thead><tr><th>Outcome</th><th>Command</th><th>What it means</th></tr></thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
</body></html>
"""


def main(argv=None) -> int:
    """CLI: python3 ghostkit/report.py <events.jsonl> [more.jsonl ...] [-o graveyard.html]"""
    import argparse

    parser = argparse.ArgumentParser(prog="ghostkit-report")
    parser.add_argument("logs", nargs="+", help="one or more events.jsonl files")
    parser.add_argument("-o", "--output", default="graveyard.html", help="output HTML path")
    args = parser.parse_args(argv)

    html_text = build(args.logs)
    Path(args.output).write_text(html_text, encoding="utf-8")
    encounters = classify(read_events(args.logs))
    print(f"Wrote {args.output} ({len(encounters)} encounter(s))")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
