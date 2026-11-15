"""R4, R5: logging and the graveyard report."""

import json

from ghostkit import log, report
from ghostkit.event import NormalizedEvent
from ghostkit.policy import Decision

CMD = "npm run analyze"


def pre_event(command=CMD):
    return NormalizedEvent(trigger="PreToolUse", session_id="s", tool_name="execute_bash", command=command)


def read(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_minimal_log_does_not_store_the_command(tmp_path):
    path = tmp_path / "e.jsonl"
    log.append(path, pre_event(), Decision("ask", "look"), "minimal")
    assert "command" not in read(path)[0]


def test_commands_verbosity_stores_the_command(tmp_path):
    path = tmp_path / "e.jsonl"
    log.append(path, pre_event(), Decision("ask", "look"), "commands")
    assert read(path)[0]["command"] == CMD


def test_full_verbosity_stores_the_response(tmp_path):
    path = tmp_path / "e.jsonl"
    event = NormalizedEvent(trigger="PostToolUse", session_id="s", command=CMD, tool_response="Output: ok")
    log.append(path, event, Decision("allow"), "full")
    assert read(path)[0]["tool_response"] == "Output: ok"


def test_rejection_is_recorded_without_storing_the_response(tmp_path):
    path = tmp_path / "e.jsonl"
    event = NormalizedEvent(trigger="PostToolUse", session_id="s", command=CMD,
                            tool_response="Output:\nThe user rejected this tool call.")
    log.append(path, event, Decision("allow"), "minimal", "The user rejected this tool call.")
    record = read(path)[0]
    assert record["rejected"] is True and "tool_response" not in record


def test_a_failing_log_write_never_raises(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    log.append(blocker / "inside" / "e.jsonl", pre_event(), Decision("allow"))  # parent is a file


def ev(trigger, ts, session, decision="allow", command=CMD, **extra):
    return {"trigger": trigger, "ts": ts, "session_id": session, "decision": decision, "command": command, **extra}


def outcomes(events):
    return {e["session"]: e["outcome"] for e in report.classify(events)}


def test_approved_is_a_trick():
    events = [ev("PreToolUse", 1, "a", "ask"), ev("PostToolUse", 2, "a", rejected=False)]
    assert outcomes(events) == {"a": "trick"}


def test_a_rejected_post_is_a_treat():
    events = [ev("PreToolUse", 1, "a", "ask"), ev("PostToolUse", 2, "a", rejected=True)]
    assert outcomes(events) == {"a": "treat"}


def test_a_denied_hook_approval_is_a_treat_once_the_turn_has_ended():
    events = [ev("PreToolUse", 1, "a", "ask"), ev("Stop", 3, "a", command=None)]
    assert outcomes(events) == {"a": "treat"}


def test_an_ask_with_nothing_after_it_is_pending():
    assert outcomes([ev("PreToolUse", 1, "a", "ask")]) == {"a": "pending"}


def test_a_block_is_blocked():
    assert outcomes([ev("PreToolUse", 1, "a", "block", command="x")]) == {"a": "blocked"}


def test_sessions_are_kept_apart():
    events = [ev("PreToolUse", 1, "a", "ask"), ev("PostToolUse", 2, "b", rejected=False),
              ev("PostToolUse", 3, "a", rejected=False)]
    assert outcomes(events) == {"a": "trick"}


def test_report_html_has_no_network_references_and_escapes_commands(tmp_path):
    path = tmp_path / "e.jsonl"
    rows = [ev("PreToolUse", 1, "a", "ask", command="<script>alert(1)</script>"),
            ev("PostToolUse", 2, "a", command="<script>alert(1)</script>", rejected=False)]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    html = report.build([path])
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "http://" not in html and "https://" not in html and "src=" not in html


def test_an_empty_log_gives_a_page_that_says_so(tmp_path):
    assert "No encounters yet" in report.build([tmp_path / "missing.jsonl"])
