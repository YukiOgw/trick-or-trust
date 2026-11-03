# Implementation Plan: ghostkit

> Status: draft v1 (2026-11-01). Derived from `requirements.md` and `design.md`.
> Each task is test-driven and references the requirements it satisfies.

- [ ] 1. Package skeleton and test harness
  - Create the `ghostkit/` package with empty modules per the design layout.
  - Add `pyproject.toml` (or equivalent) declaring Python 3.11+, pytest, and a
    test-only dependency on hypothesis. Runtime depends only on the stdlib.
  - Confirm `pytest` collects and runs an empty suite locally (no Docker).
  - _Requirements: R7.1_

- [ ] 2. Event ingestion (event.py)
  - [ ] 2.1 Implement `read_stdin` with a bounded `select` timeout and `parse`
    that tolerates empty/invalid JSON by returning an empty event.
  - [ ] 2.2 Implement `NormalizedEvent` and `command_cwd` (prefer
    `tool_input.cwd`, fall back to event `cwd`).
  - [ ] 2.3 Unit tests: well-formed PreToolUse/PostToolUse/UserPromptSubmit,
    missing fields, empty stdin, malformed JSON.
  - _Requirements: R1_

- [ ] 3. Policy engine (policy.py)
  - [ ] 3.1 Implement `Rule`, `Policy`, and `load` using `tomllib`, returning an
    invalid-policy sentinel (no raise) on missing/malformed files.
  - [ ] 3.2 Implement `evaluate` with precedence block > ask > allow and a
    configured default; every decision carries a reason.
  - [ ] 3.3 Unit tests for matching, default, and reason presence.
  - [ ] 3.4 Property test: for any set of matching rules, the resolved decision
    respects block > ask > allow.
  - _Requirements: R2_

- [ ] 4. Decision output (decision.py)
  - [ ] 4.1 Implement `emit` for allow / ask / block / note with the exact exit
    codes and stdout/stderr shapes from the decision protocol; ensure an `ask`
    reason always embeds the command.
  - [ ] 4.2 Conformance tests using the recorded PoC shapes as fixtures
    (exit codes, `permissionDecision` JSON, stderr on block).
  - _Requirements: R3_

- [ ] 5. Entry point (run.py)
  - [ ] 5.1 Parse trigger from argv, read stdin, and run the cheap relevance
    check before importing policy/safety.
  - [ ] 5.2 Wire parse → evaluate → guard → emit → log, with a top-level handler
    that turns any unexpected exception into exit 0 with no output.
  - [ ] 5.3 Tests: irrelevant event exits 0 without importing the engine;
    exception path exits 0.
  - _Requirements: R1, R3, R7.2, R7.3_

- [ ] 6. Logging (log.py)
  - [ ] 6.1 Implement `append` writing one JSON line (trigger, ts, session_id,
    tool, decision, reason) with verbosity minimal/commands/full; swallow write
    failures.
  - [ ] 6.2 Tests: default minimal stores no command/body; commands stores the
    command; write failure does not raise.
  - _Requirements: R4_

- [ ] 7. Training-mode guard (safety.py)
  - [ ] 7.1 Implement `guard` overriding to block when a command reaches a real
    secret path or a non-`.invalid` external host.
  - [ ] 7.2 Property test: trap-shaped commands only touch `.invalid` names and
    the practice folder; anything reaching a real secret/host is blocked.
  - _Requirements: R7.4, R7.5_

- [ ] 8. Reporting (report.py)
  - [ ] 8.1 Implement `build`: read JSONL, pair Pre/Post by session_id, classify
    executed/rejected/blocked using the protocol table and the configurable
    reject phrase. Emit one self-contained HTML file (stdlib only).
  - [ ] 8.2 Tests: each outcome classified correctly from fixture logs; output
    has no network references.
  - _Requirements: R5_

- [ ] 9. Installer (install.py)
  - [ ] 9.1 Implement `plan`/`apply`/`remove`: absolute-path, existence-guarded
    hook commands; print intended content; write only with an explicit confirm
    flag; provide uninstall.
  - [ ] 9.2 Tests: no write without confirm; written hook is a no-op when the
    engine path is absent; remove deletes what plan wrote.
  - _Requirements: R6_

- [ ] 10. Integration and real-run check
  - [ ] 10.1 Ship a sample `policy.toml` and an end-to-end test driving `run.py`
    with fixture events for allow/ask/block/note.
  - [ ] 10.2 Install the hooks into the P4 practice room and confirm a real Kiro
    session records a proposed command (closes the P3/P4 hook-load gap).
  - _Requirements: R2, R3, R4, R6_
```

What `tasks.md` is for: it becomes the checklist the implementation follows,
one task at a time, each verified by its tests before moving on.
