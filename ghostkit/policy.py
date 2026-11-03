"""R2: load a TOML policy and evaluate events against it."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field

# Higher wins. block > ask > allow.
PRECEDENCE = {"block": 3, "ask": 2, "allow": 1, "note": 1}


@dataclass
class Decision:
    kind: str  # "allow" | "ask" | "block" | "note"
    reason: str = ""


@dataclass
class Rule:
    trigger: str
    pattern: str
    decision: str
    reason: str = ""
    tool: str | None = None
    regex: re.Pattern | None = None


@dataclass
class Policy:
    rules: list[Rule] = field(default_factory=list)
    default: str = "allow"
    training_mode: bool = True
    log_verbosity: str = "minimal"
    reject_phrase: str = "The user rejected this tool call."
    valid: bool = True
    error: str | None = None

    @classmethod
    def invalid(cls, error: str) -> "Policy":
        return cls(valid=False, error=error)


def load(path) -> Policy:
    """Load a TOML policy. On any problem, return an invalid sentinel (no raise)."""
    try:
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return Policy.invalid(f"policy load failed: {exc}")

    rules: list[Rule] = []
    for raw in data.get("rule", []):
        try:
            rule = Rule(
                trigger=raw["trigger"],
                pattern=raw["pattern"],
                decision=raw["decision"],
                reason=raw.get("reason", ""),
                tool=raw.get("tool"),
                regex=re.compile(raw["pattern"]),
            )
        except (KeyError, TypeError, re.error) as exc:
            return Policy.invalid(f"invalid rule: {exc}")
        if rule.decision not in PRECEDENCE:
            return Policy.invalid(f"unknown decision: {rule.decision}")
        rules.append(rule)

    return Policy(
        rules=rules,
        default=data.get("default", "allow"),
        training_mode=bool(data.get("training_mode", True)),
        log_verbosity=data.get("log_verbosity", "minimal"),
        reject_phrase=data.get("reject_phrase", "The user rejected this tool call."),
    )


def evaluate(policy: Policy, event) -> Decision:
    """Return the highest-precedence matching decision, else the default."""
    best: Decision | None = None
    command = event.command or ""
    for rule in policy.rules:
        if rule.trigger != event.trigger:
            continue
        if rule.tool and rule.tool != event.tool_name:
            continue
        if rule.regex is not None and not rule.regex.search(command):
            continue
        if best is None or PRECEDENCE[rule.decision] > PRECEDENCE[best.kind]:
            best = Decision(rule.decision, rule.reason)
    return best or Decision(policy.default, "")
