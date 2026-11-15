"""R3: decisions in Kiro's hook protocol."""

import io
import json

from ghostkit.decision import emit
from ghostkit.event import NormalizedEvent
from ghostkit.policy import Decision


def run(decision, trigger="PreToolUse", command="npm run analyze"):
    out, err = io.StringIO(), io.StringIO()
    code = emit(decision, NormalizedEvent(trigger=trigger, command=command), out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_allow_exits_zero_with_no_output():
    assert run(Decision("allow")) == (0, "", "")


def test_ask_is_exit_zero_with_a_json_decision():
    code, out, err = run(Decision("ask", "read it"))
    body = json.loads(out)["hookSpecificOutput"]
    assert code == 0 and err == ""
    assert body["permissionDecision"] == "ask"
    assert "read it" in body["permissionDecisionReason"]


def test_ask_reason_always_contains_the_command():
    _, out, _ = run(Decision("ask", "read it"), command="npm run analyze")
    assert "npm run analyze" in json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


def test_ask_does_not_repeat_a_command_the_reason_already_has():
    _, out, _ = run(Decision("ask", "this runs npm run analyze"), command="npm run analyze")
    assert json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"].count("npm run analyze") == 1


def test_block_exits_two_with_the_reason_on_stderr():
    code, out, err = run(Decision("block", "no"))
    assert code == 2 and out == "" and "no" in err


def test_a_prompt_is_never_blocked():
    code, _, _ = run(Decision("block", "no"), trigger="UserPromptSubmit")
    assert code == 0


def test_a_prompt_note_goes_to_stdout():
    code, out, _ = run(Decision("note", "ask one question first"), trigger="UserPromptSubmit")
    assert code == 0 and "ask one question first" in out
