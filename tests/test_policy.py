"""R2: policy loading and evaluation."""

import re

from hypothesis import given, strategies as st

from ghostkit.event import NormalizedEvent
from ghostkit.policy import PRECEDENCE, Policy, Rule, evaluate, load


def write(tmp_path, text):
    path = tmp_path / "policy.toml"
    path.write_text(text, encoding="utf-8")
    return path


def event(command="npm run analyze", trigger="PreToolUse", tool="execute_bash"):
    return NormalizedEvent(trigger=trigger, tool_name=tool, command=command)


def test_missing_policy_is_invalid_not_an_exception(tmp_path):
    policy = load(tmp_path / "nope.toml")
    assert not policy.valid and policy.error


def test_malformed_toml_is_invalid(tmp_path):
    assert not load(write(tmp_path, "this is = = not toml")).valid


def test_bad_regex_is_invalid(tmp_path):
    text = '[[rule]]\ntrigger="PreToolUse"\npattern="("\ndecision="ask"\n'
    assert not load(write(tmp_path, text)).valid


def test_unknown_decision_is_invalid(tmp_path):
    text = '[[rule]]\ntrigger="PreToolUse"\npattern="x"\ndecision="explode"\n'
    assert not load(write(tmp_path, text)).valid


def test_loads_a_rule_and_defaults(tmp_path):
    text = 'default="allow"\ntraining_mode=false\n[[rule]]\ntrigger="PreToolUse"\npattern="analyze"\ndecision="ask"\nreason="look"\n'
    policy = load(write(tmp_path, text))
    assert policy.valid and not policy.training_mode and len(policy.rules) == 1


def test_no_matching_rule_uses_the_default():
    policy = Policy(rules=[], default="ask")
    assert evaluate(policy, event()).kind == "ask"


def test_matching_rule_returns_its_decision_and_reason():
    rule = Rule(trigger="PreToolUse", pattern="analyze", decision="ask", reason="look", regex=re.compile("analyze"))
    decision = evaluate(Policy(rules=[rule]), event())
    assert decision.kind == "ask" and decision.reason == "look"


def test_trigger_must_match():
    rule = Rule(trigger="PostToolUse", pattern="analyze", decision="block", regex=re.compile("analyze"))
    assert evaluate(Policy(rules=[rule]), event()).kind == "allow"


def test_tool_filter_must_match():
    rule = Rule(trigger="PreToolUse", pattern="analyze", decision="block", tool="other", regex=re.compile("analyze"))
    assert evaluate(Policy(rules=[rule]), event()).kind == "allow"


def test_block_beats_ask_beats_allow():
    def r(decision):
        return Rule(trigger="PreToolUse", pattern="x", decision=decision, reason=decision, regex=re.compile("x"))
    policy = Policy(rules=[r("allow"), r("ask"), r("block")])
    assert evaluate(policy, event("x")).kind == "block"


@given(st.lists(st.sampled_from(["allow", "ask", "block"]), min_size=1, max_size=8))
def test_resolved_decision_is_the_highest_precedence(decisions):
    rules = [Rule(trigger="PreToolUse", pattern="x", decision=d, reason=d, regex=re.compile("x")) for d in decisions]
    expected = max(decisions, key=lambda d: PRECEDENCE[d])
    assert evaluate(Policy(rules=rules), event("x")).kind == expected
