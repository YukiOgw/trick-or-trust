"""R6: write or remove ghostkit hook files in a project's .kiro/hooks/.

Shell-invoked writes do not trigger a Kiro approval prompt (PoC P3), so `apply`
prints the exact content first and refuses to write without an explicit confirm.
"""

from __future__ import annotations

import json
from pathlib import Path

HOOK_FILE = "ghostkit.json"


def _command(engine_path: str, trigger: str, policy_path: str, log_path: str, tail: str = "") -> str:
    return (
        f'P={engine_path}; if [ -f "$P" ]; then '
        f'python3 -I -S "$P" {trigger} --policy {policy_path} --log {log_path}{tail}; fi'
    )


def hook_definition(engine_path: str, policy_path: str, log_path: str) -> dict:
    return {
        "version": "v1",
        "hooks": [
            {
                "name": "ghostkit: PreToolUse (shell)",
                "trigger": "PreToolUse",
                "matcher": "shell",
                "action": {
                    "type": "command",
                    "command": _command(engine_path, "PreToolUse", policy_path, log_path),
                    "timeout": 10,
                },
            },
            {
                "name": "ghostkit: PostToolUse (shell)",
                "trigger": "PostToolUse",
                "matcher": "shell",
                "action": {
                    "type": "command",
                    "command": _command(engine_path, "PostToolUse", policy_path, log_path, tail=" || true"),
                    "timeout": 10,
                },
            },
        ],
    }


def plan(target, engine_path: str, policy_path: str, log_path: str):
    path = Path(target) / ".kiro" / "hooks" / HOOK_FILE
    content = json.dumps(hook_definition(engine_path, policy_path, log_path), indent=2) + "\n"
    return path, content


def apply(target, engine_path: str, policy_path: str, log_path: str, confirm: bool = False):
    path, content = plan(target, engine_path, policy_path, log_path)
    print(f"Will write hook file: {path}")
    print(content)
    if not confirm:
        print("Not written. Re-run with confirm=True (or --yes) after reading the above.")
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Wrote: {path}")
    return path


def remove(target):
    path = Path(target) / ".kiro" / "hooks" / HOOK_FILE
    if path.exists():
        path.unlink()
        print(f"Removed: {path}")
        return path
    print(f"Nothing to remove at {path}")
    return None
