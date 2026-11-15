"""R1: event ingestion."""

import json

from hypothesis import given, strategies as st

from ghostkit.event import command_cwd, parse


def test_parses_a_pretooluse_event():
    raw = json.dumps({
        "session_id": "sess_1",
        "hook_event_name": "PreToolUse",
        "cwd": "/work",
        "tool_name": "execute_bash",
        "tool_input": {"command": "ls -la", "cwd": None},
    })
    event = parse("PreToolUse", raw)
    assert event.trigger == "PreToolUse"
    assert event.session_id == "sess_1"
    assert event.tool_name == "execute_bash"
    assert event.command == "ls -la"
    assert event.tool_response is None


def test_parses_a_posttooluse_response():
    raw = json.dumps({"session_id": "s", "tool_name": "execute_bash",
                      "tool_input": {"command": "ls"}, "tool_response": "Output:\nok"})
    assert parse("PostToolUse", raw).tool_response == "Output:\nok"


def test_missing_fields_are_none_not_errors():
    event = parse("Stop", json.dumps({"session_id": "s"}))
    assert event.tool_name is None and event.command is None and event.cwd is None


def test_empty_input_gives_an_empty_event():
    event = parse("PreToolUse", "")
    assert event.session_id is None and event.command is None


def test_malformed_json_gives_an_empty_event():
    assert parse("PreToolUse", "{not json").command is None


def test_json_that_is_not_an_object_gives_an_empty_event():
    assert parse("PreToolUse", "[1, 2, 3]").command is None


def test_tool_input_that_is_not_an_object_is_ignored():
    event = parse("PreToolUse", json.dumps({"tool_input": "ls"}))
    assert event.command is None and event.tool_input == {}


def test_command_cwd_prefers_tool_input_cwd():
    event = parse("PreToolUse", json.dumps({"cwd": "/event", "tool_input": {"command": "x", "cwd": "/tool"}}))
    assert command_cwd(event) == "/tool"


def test_command_cwd_falls_back_to_event_cwd():
    event = parse("PreToolUse", json.dumps({"cwd": "/event", "tool_input": {"command": "x", "cwd": None}}))
    assert command_cwd(event) == "/event"


@given(st.text())
def test_parse_never_raises_on_any_text(raw):
    parse("PreToolUse", raw)
