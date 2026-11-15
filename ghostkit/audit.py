"""Night Watch audit: find over-broad permissions and credit-draining setup.

Read-only. It never edits a Kiro settings file; it only reports and suggests.

Two kinds of finding:
  - Zombie Permission: an always-allow rule that was probably meant for one moment
    and now lets a whole class of commands through.
  - Credit Vampire: setup that spends credits on every turn, such as a large
    always-on steering file or an agent-type hook on a frequent trigger.

Standard library only. The permissions file is read with a tiny parser for the
shape Kiro writes (rules / capability / effect / match), so no YAML package is needed.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

# First words that can run arbitrary code, fetch from the network, or destroy data.
RISKY_COMMANDS = {
    "bash", "sh", "zsh", "eval", "source", "sudo",
    "python", "python3", "node", "npx", "uv", "uvx", "pip", "pip3",
    "curl", "wget", "ssh", "scp",
    "rm", "shred", "mv", "chmod", "chown", "kill", "pkill", "dd",
}

# Triggers that fire many times per session. An agent-type hook there costs credits each time.
FREQUENT_TRIGGERS = {
    "PostFileSave", "PostFileCreate", "PostFileDelete",
    "PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop",
}

DEFAULT_STEERING_KB = 16.0


@dataclass
class Finding:
    monster: str  # "Zombie Permission" | "Credit Vampire"
    title: str
    detail: str
    suggestion: str
    items: list[str] = field(default_factory=list)


def _value(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def parse_permissions(text: str) -> list[dict]:
    """Parse the rules list of a Kiro permissions.yaml. Unknown lines are ignored."""
    rules: list[dict] = []
    current: dict | None = None
    in_match = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line == "rules:":
            continue
        if line.startswith("- capability:"):
            current = {"capability": _value(line[len("- capability:"):]), "effect": None, "match": []}
            rules.append(current)
            in_match = False
        elif current is None:
            continue
        elif line.startswith("effect:"):
            current["effect"] = _value(line[len("effect:"):])
            in_match = False
        elif line == "match:":
            in_match = True
        elif in_match and line.startswith("- "):
            current["match"].append(_value(line[2:]))
    return rules


def _first_word(entry: str) -> str:
    for token in entry.split():
        if "=" in token and not token.startswith("-"):
            continue  # skip leading VAR=value assignments
        return os.path.basename(token)
    return ""


def audit_permissions(path: Path) -> list[Finding]:
    try:
        rules = parse_permissions(path.read_text(encoding="utf-8"))
    except OSError:
        return []

    risky: list[str] = []
    everything = False
    write_anywhere = False
    for rule in rules:
        if rule.get("effect") != "allow":
            continue
        capability = rule.get("capability")
        for entry in rule.get("match", []):
            if capability == "shell":
                if entry.strip() == "*":
                    everything = True
                elif "*" in entry and _first_word(entry) in RISKY_COMMANDS:
                    risky.append(entry)
            elif capability == "fs_write" and entry.strip() in ("**", "*"):
                write_anywhere = True

    findings: list[Finding] = []
    if everything:
        findings.append(Finding(
            "Zombie Permission",
            "Every shell command is allowed",
            f"{path} has a shell allow rule that matches everything, so no command asks for approval.",
            "Remove the catch-all rule and keep only the exact commands you trust.",
        ))
    if risky:
        findings.append(Finding(
            "Zombie Permission",
            f"{len(risky)} always-allow shell rule(s) can run code or delete files",
            f"In {path}: wildcard rules for commands that can run arbitrary code, fetch from the network, or remove files.",
            "Take these out of the allow list so each use asks again, or narrow them to exact subcommands. "
            "ghostkit never edits this file; make the change yourself.",
            items=risky,
        ))
    if write_anywhere:
        findings.append(Finding(
            "Zombie Permission",
            "File writes are allowed everywhere",
            f"{path} allows writing to any path without asking.",
            "Limit fs_write to the folders you work in.",
        ))
    return findings


def _inclusion(text: str) -> str:
    """Return the steering inclusion mode. No front matter means always-on (Kiro's default)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "always"
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("inclusion:"):
            return _value(stripped[len("inclusion:"):]) or "always"
    return "always"


def audit_steering(directories: list[Path], limit_kb: float) -> list[Finding]:
    sized: list[tuple[int, Path]] = []
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if _inclusion(text) == "always":
                sized.append((len(text.encode("utf-8")), path))
    total_kb = sum(size for size, _ in sized) / 1024
    if total_kb <= limit_kb:
        return []
    sized.sort(reverse=True)
    top = [f"{path} ({size / 1024:.1f} KB)" for size, path in sized[:5] if size >= 1024]
    return [Finding(
        "Credit Vampire",
        f"{total_kb:.1f} KB of steering is loaded into every conversation",
        f"Always-on steering files add up to {total_kb:.1f} KB, over the {limit_kb:.0f} KB guide. "
        "Larger context makes each request cost more credits.",
        "Switch rarely needed files to `inclusion: fileMatch`, `auto`, or `manual`, "
        "and move long records out of always-on files.",
        items=top,
    )]


def audit_hooks(directories: list[Path]) -> list[Finding]:
    costly: list[str] = []
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            hooks = data.get("hooks", []) if isinstance(data, dict) else []
            for hook in hooks if isinstance(hooks, list) else []:
                if not isinstance(hook, dict):
                    continue
                action = hook.get("action") or {}
                trigger = hook.get("trigger")
                if action.get("type") == "agent" and trigger in FREQUENT_TRIGGERS:
                    costly.append(f"{path.name}: {hook.get('name', '(unnamed)')} [{trigger}]")
    if not costly:
        return []
    return [Finding(
        "Credit Vampire",
        f"{len(costly)} agent-type hook(s) run on a frequent trigger",
        "An agent-type hook starts a new agent loop, which uses credits, every time its trigger fires. "
        "Shell-command hooks do not use credits.",
        "Turn these into shell-command hooks, or move them to a rare trigger.",
        items=costly,
    )]


def run_audit(
    project: Path,
    permissions: Path | None,
    include_user: bool,
    steering_kb: float = DEFAULT_STEERING_KB,
) -> list[Finding]:
    home = Path.home() / ".kiro"
    steering_dirs = [project / ".kiro" / "steering"]
    hook_dirs = [project / ".kiro" / "hooks"]
    if include_user:
        steering_dirs.append(home / "steering")
        hook_dirs.append(home / "hooks")
        if permissions is None:
            permissions = home / "settings" / "permissions.yaml"

    findings: list[Finding] = []
    if permissions is not None and permissions.exists():
        findings += audit_permissions(permissions)
    findings += audit_steering(steering_dirs, steering_kb)
    findings += audit_hooks(hook_dirs)
    return findings


ICONS = {"Zombie Permission": "🧟", "Credit Vampire": "🧛"}


def format_report(findings: list[Finding]) -> str:
    lines = ["🌙 Night Watch audit", ""]
    if not findings:
        return "\n".join(lines + ["Nothing found tonight. 🌕"])
    for monster in ("Zombie Permission", "Credit Vampire"):
        group = [f for f in findings if f.monster == monster]
        if not group:
            continue
        lines.append(f"{ICONS[monster]} {monster} ({len(group)})")
        for finding in group:
            lines.append(f"  - {finding.title}")
            lines.append(f"    {finding.detail}")
            for item in finding.items[:10]:
                lines.append(f"      * {item}")
            if len(finding.items) > 10:
                lines.append(f"      * ... and {len(finding.items) - 10} more")
            lines.append(f"    Try: {finding.suggestion}")
        lines.append("")
    return "\n".join(lines).rstrip()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ghostkit-audit", description="Read-only Night Watch audit.")
    parser.add_argument("--project", default=".", help="project root (default: current directory)")
    parser.add_argument("--permissions", default=None, help="permissions.yaml to check")
    parser.add_argument("--no-user", action="store_true", help="do not read anything under ~/.kiro")
    parser.add_argument("--steering-kb", type=float, default=DEFAULT_STEERING_KB,
                        help="always-on steering size that counts as large (default: %(default)s)")
    args = parser.parse_args(argv)

    permissions = Path(args.permissions).expanduser() if args.permissions else None
    findings = run_audit(Path(args.project).expanduser(), permissions, not args.no_user, args.steering_kb)
    print(format_report(findings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
