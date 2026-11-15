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
            {
                # A hook-raised approval that is denied produces no PostToolUse, so the
                # end of the agent's turn is what tells the report the approval was resolved.
                "name": "ghostkit: Stop",
                "trigger": "Stop",
                "action": {
                    "type": "command",
                    "command": _command(engine_path, "Stop", policy_path, log_path, tail=" || true"),
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


def _resolve(room: str):
    """Derive engine/policy/log paths from the ghostkit location and the room."""
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    # Always absolute: hooks run with the workspace as cwd, so relative paths
    # would not resolve and ghostkit would silently fail safe (no ghost).
    room = os.path.abspath(os.path.expanduser(room))
    engine = os.path.join(here, "run.py")
    policy = os.path.join(room, "ghostkit.toml")
    log = os.path.join(room, ".ghostkit", "events.jsonl")
    return engine, policy, log


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="ghostkit-install")
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser("apply", help="write ghostkit hooks into a room/project")
    apply_parser.add_argument("room", help="target directory that will receive .kiro/hooks/")
    apply_parser.add_argument("--yes", action="store_true", help="write without the confirmation gate")

    remove_parser = subparsers.add_parser("remove", help="remove ghostkit hooks from a room/project")
    remove_parser.add_argument("room")

    args = parser.parse_args(argv)
    if args.command == "apply":
        engine, policy, log = _resolve(args.room)
        apply(args.room, engine, policy, log, confirm=args.yes)
    elif args.command == "remove":
        remove(args.room)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
