# Requirements: ghostkit

> Status: draft v1 (2026-11-01). Grounded in the PoC results (see `kiroween2026/04`
> in the author's private notes). Written in English because repository artifacts
> ship in English.

## Introduction

ghostkit is the small, dependency-free toolkit that powers the hooks behind
Trick or Trust. It reads a Kiro hook event from stdin, evaluates it against a
policy written in TOML, returns an allow / ask / block decision in the exact
shape Kiro expects, records the event, and renders a graveyard-style report.

Both apps are built on ghostkit:

- **Haunted House** — a practice repository whose rooms each hide one harmless
  trap, used to train approval judgment.
- **Night Watch** — a guard that runs inside a real project to flag risky
  operations, vague prompts, and credit-wasting configuration.

ghostkit itself is not a guard and not a trainer. It is the engine the two apps
configure. This spec covers the engine only.

### Scope boundaries

- In scope: event parsing, policy evaluation, decision output, logging,
  reporting, the hook installer, and the Python-only runtime.
- Out of scope (separate specs): the specific rooms of Haunted House, the
  specific checks of Night Watch, and the presentation/theming of the report.

### Constraints carried from the PoC

- PreToolUse fires before the approval prompt; a block uses exit code 2; an
  `ask` decision is exit 0 with a JSON decision on stdout (P1, P2).
- UserPromptSubmit cannot block the prompt; it only adds stdout to context, so
  prompt-level behavior must use exit 0 notes (P5).
- Hooks are not loaded from inside a power, so installation writes hook files
  into `.kiro/hooks/` (P3).
- One hook run must stay well under 100 ms; the budget is spent almost entirely
  on Python startup, so the engine uses only the standard library (P6).
- Hooks fire for every session in a workspace; events must be correlated by
  `session_id` (P1).

## Requirements

### R1: Event ingestion

**User story:** As a hook author, I want ghostkit to parse any Kiro hook event
into one normalized shape, so that my policy and logging code does not depend on
per-event JSON differences.

#### Acceptance criteria

1. WHEN ghostkit is invoked with a trigger name and a JSON event on stdin, THE
   SYSTEM SHALL parse it into a normalized event exposing at least
   `trigger`, `session_id`, `cwd`, `tool_name`, `tool_input` (with `command`),
   and `tool_response` when present.
2. WHEN a field is absent for a given trigger, THE SYSTEM SHALL expose it as a
   null/None value rather than raising.
3. WHEN stdin is empty or is not valid JSON, THE SYSTEM SHALL treat the event as
   empty and continue without raising.
4. WHEN resolving a relative path in a command, THE SYSTEM SHALL prefer
   `tool_input.cwd` and fall back to the event `cwd`.
5. THE SYSTEM SHALL NOT block waiting on stdin for longer than a short, bounded
   timeout.

### R2: Policy evaluation

**User story:** As a room or project owner, I want to express rules in TOML, so
that I can decide which commands are allowed, which need a prompt, and which are
blocked, without editing Python.

#### Acceptance criteria

1. THE SYSTEM SHALL load policy rules from a TOML file using the standard-library
   `tomllib` (Python 3.11+).
2. A rule SHALL match on at least: trigger, tool name, and a pattern tested
   against the command string.
3. WHEN more than one rule matches, THE SYSTEM SHALL apply a documented
   precedence in which `block` wins over `ask`, and `ask` wins over `allow`.
4. WHEN no rule matches, THE SYSTEM SHALL apply a configured default decision.
5. A decision SHALL carry a human-readable reason string.
6. WHEN the policy file is missing or invalid, THE SYSTEM SHALL fail safe by
   making no decision (exit 0, no output) and recording the error, so that it
   never blocks the user because of its own misconfiguration.

### R3: Decision output

**User story:** As Kiro, I want ghostkit to speak my hook protocol exactly, so
that allow / ask / block behave as documented.

#### Acceptance criteria

1. WHEN the decision is allow, THE SYSTEM SHALL exit 0 with no decision output.
2. WHEN the decision is ask on a PreToolUse event, THE SYSTEM SHALL exit 0 and
   write a JSON object on stdout containing
   `hookSpecificOutput.permissionDecision = "ask"` and a
   `permissionDecisionReason`.
3. WHEN the decision is block on a PreToolUse event, THE SYSTEM SHALL exit 2 and
   write the reason to stderr.
4. THE SYSTEM SHALL include the command text in an `ask` reason, so that the
   reason never hides what is being approved.
5. WHEN the event is UserPromptSubmit, THE SYSTEM SHALL only ever exit 0 and add
   a note to stdout; it SHALL NOT attempt to block the prompt.
6. THE SYSTEM SHALL phrase reasons and notes as explanation, not as commands to
   the agent.

### R4: Event logging

**User story:** As an operator, I want a local record of what was proposed,
approved, rejected, or blocked, so that the report can be built and traps scored,
without capturing private content by default.

#### Acceptance criteria

1. THE SYSTEM SHALL append one JSON line per handled event to a configured log
   file.
2. A log line SHALL include trigger, timestamp, `session_id`, tool name, and the
   decision with its reason.
3. THE SYSTEM SHALL correlate a PreToolUse with its PostToolUse by `session_id`,
   so that approve / reject / blocked can be told apart.
4. BY DEFAULT THE SYSTEM SHALL NOT store prompt bodies or full command output;
   capturing them SHALL require explicit opt-in.
5. WHEN writing the log fails, THE SYSTEM SHALL not raise into the user's session.

### R5: Reporting

**User story:** As a learner or team lead, I want a readable report built from
the log, so that I can see which traps were caught, approved, or blocked.

#### Acceptance criteria

1. THE SYSTEM SHALL read one or more JSONL logs and produce a single self-
   contained HTML report with no network dependencies.
2. THE SYSTEM SHALL classify each correlated event as executed, rejected by the
   user, or blocked by a hook, using the PoC decision table (R3, and the
   PostToolUse `tool_response` text for reject).
3. THE SYSTEM SHALL keep the classification strings (for example the reject
   phrase) in configuration, so a Kiro change can be absorbed without code edits.
4. THE SYSTEM SHALL run offline using only the standard library.

### R6: Hook installation

**User story:** As someone adopting Night Watch, I want a script that installs
the hooks into my project, so that I do not hand-write hook JSON, and I can see
exactly what will run before it is written.

#### Acceptance criteria

1. THE SYSTEM SHALL write hook definitions into a target `.kiro/hooks/`
   directory, given an explicit target path.
2. BEFORE writing, THE SYSTEM SHALL print the full content it intends to write.
3. THE SYSTEM SHALL NOT write unless the caller passes an explicit confirmation
   flag, because shell-invoked writes do not trigger a Kiro approval prompt (P3).
4. Installed hook commands SHALL reference the engine by absolute path and SHALL
   guard with an existence check, so a removed engine makes the hook a no-op.
5. THE SYSTEM SHALL provide a matching uninstall path.

### R7: Safety and performance

**User story:** As the author, I want the engine to be fast, self-contained, and
safe during training, so that it never harms the user or slows their session.

#### Acceptance criteria

1. THE SYSTEM SHALL depend only on the Python standard library (no third-party
   packages), and SHALL target Python 3.11 or newer.
2. One hook run SHALL complete well under 100 ms on the reference machine
   (PoC median was ~71 ms); for events outside its matchers, THE SYSTEM SHALL
   take an early-exit path before heavy imports.
3. WHEN any unexpected error occurs, THE SYSTEM SHALL exit 0 without output, so a
   bug in ghostkit never blocks the user's work.
4. DURING training mode, THE SYSTEM SHALL block any command that reaches a real
   secret path or an external host other than an `.invalid` name, independent of
   the room's own rules.
5. THE SYSTEM SHALL be verifiable by property-based tests asserting that trap
   commands only ever touch `.invalid` names and the practice folder.

## Open questions (to resolve in design)

- Confirm that a practice repo shipping `.kiro/hooks/` loads the hook in one step
  (unverified in P3/P4).
- Whether ask-decision approvals from a hook can create session-scoped allow
  rules (the IDE 1.4.62 approval had only Allow/Deny).
- Exact TOML schema for rules (fields, match syntax, defaults).
- Where the ghost is surfaced when a trap is approved (not observed in P4, since
  no run approved a trap).
