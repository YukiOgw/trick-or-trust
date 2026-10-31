#!/usr/bin/env python3
"""PoC (P3): install one probe hook into <workspace-root>/.kiro/hooks/.

Usage: python3 install_hooks.py <workspace-root> [--force]

The hook only appends a timestamp line to /tmp/tot-p3-hooks.log before each shell command.
"""

import json
import sys
from pathlib import Path

HOOK_FILE_NAME = "tot-p3-installed.json"
HOOK = {
    "version": "v1",
    "hooks": [
        {
            "name": "tot-p3: installed by skill script (PreToolUse)",
            "trigger": "PreToolUse",
            "matcher": "shell",
            "action": {
                "type": "command",
                "command": "date '+%s installed-by-skill PreToolUse' >> /tmp/tot-p3-hooks.log || true",
                "timeout": 5,
            },
        }
    ],
}


def main(argv: list[str]) -> int:
    print("install_hooks v1")
    print(f"script location: {Path(__file__).resolve()}")
    args = [a for a in argv if not a.startswith("--")]
    force = "--force" in argv
    if len(args) != 1:
        print("usage: python3 install_hooks.py <workspace-root> [--force]", file=sys.stderr)
        return 2
    root = Path(args[0]).expanduser().resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    target = root / ".kiro" / "hooks" / HOOK_FILE_NAME
    if target.exists() and not force:
        print(f"already exists (use --force to overwrite): {target}", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(HOOK, indent=2) + "\n", encoding="utf-8")
    print(f"installed: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
