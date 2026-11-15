"""Night Watch audit."""

import json

from ghostkit import audit

PERMISSIONS = """rules:
  - capability: shell
    match:
      - aws --version
      - ls *
      - rm *
      - bash *
      - "python3 *"
      - curl *
      - FOO=1 node *
      - git status
    effect: allow
  - capability: fs_write
    effect: allow
    match:
      - "**"
  - capability: shell
    match:
      - sudo *
    effect: ask
"""


def write_permissions(tmp_path, text=PERMISSIONS):
    path = tmp_path / "permissions.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_the_parser_reads_rules_matches_and_effects():
    rules = audit.parse_permissions(PERMISSIONS)
    assert [r["capability"] for r in rules] == ["shell", "fs_write", "shell"]
    assert rules[0]["effect"] == "allow" and "rm *" in rules[0]["match"] and "python3 *" in rules[0]["match"]
    assert rules[2]["effect"] == "ask"


def test_the_parser_survives_garbage():
    assert audit.parse_permissions("::: not yaml :::\n\t\t-") == []


def test_risky_wildcard_rules_are_flagged(tmp_path):
    findings = audit.audit_permissions(write_permissions(tmp_path))
    items = [item for f in findings for item in f.items]
    for expected in ("rm *", "bash *", "python3 *", "curl *", "FOO=1 node *"):
        assert expected in items


def test_safe_and_asking_rules_are_not_flagged(tmp_path):
    findings = audit.audit_permissions(write_permissions(tmp_path))
    items = [item for f in findings for item in f.items]
    for unexpected in ("ls *", "git status", "aws --version", "sudo *"):
        assert unexpected not in items


def test_write_anywhere_is_flagged(tmp_path):
    titles = [f.title for f in audit.audit_permissions(write_permissions(tmp_path))]
    assert "File writes are allowed everywhere" in titles


def test_a_catch_all_shell_rule_is_flagged(tmp_path):
    text = "rules:\n  - capability: shell\n    effect: allow\n    match:\n      - \"*\"\n"
    titles = [f.title for f in audit.audit_permissions(write_permissions(tmp_path, text))]
    assert "Every shell command is allowed" in titles


def test_a_missing_permissions_file_gives_no_findings(tmp_path):
    assert audit.audit_permissions(tmp_path / "gone.yaml") == []


def steering(tmp_path, files):
    directory = tmp_path / "steering"
    directory.mkdir()
    for name, text in files.items():
        (directory / name).write_text(text, encoding="utf-8")
    return directory


def test_large_always_on_steering_is_flagged(tmp_path):
    directory = steering(tmp_path, {"big.md": "x" * 20000, "small.md": "# hi\n"})
    findings = audit.audit_steering([directory], limit_kb=16)
    assert len(findings) == 1 and any("big.md" in item for item in findings[0].items)
    assert not any("small.md" in item for item in findings[0].items)


def test_steering_that_is_not_always_on_does_not_count(tmp_path):
    directory = steering(tmp_path, {"manual.md": "---\ninclusion: manual\n---\n" + "y" * 30000,
                                    "match.md": "---\ninclusion: fileMatch\nfileMatchPattern: 'x'\n---\n" + "z" * 30000})
    assert audit.audit_steering([directory], limit_kb=16) == []


def test_small_steering_is_fine(tmp_path):
    assert audit.audit_steering([steering(tmp_path, {"a.md": "short"})], limit_kb=16) == []


def hooks_dir(tmp_path, hooks):
    directory = tmp_path / "hooks"
    directory.mkdir()
    (directory / "h.json").write_text(json.dumps({"version": "v1", "hooks": hooks}), encoding="utf-8")
    return directory


def test_agent_hooks_on_frequent_triggers_are_flagged(tmp_path):
    directory = hooks_dir(tmp_path, [
        {"name": "review", "trigger": "PostFileSave", "action": {"type": "agent", "prompt": "x"}},
        {"name": "lint", "trigger": "PostFileSave", "action": {"type": "command", "command": "ruff ."}},
        {"name": "hello", "trigger": "SessionStart", "action": {"type": "agent", "prompt": "x"}},
    ])
    findings = audit.audit_hooks([directory])
    assert len(findings) == 1 and len(findings[0].items) == 1 and "review" in findings[0].items[0]


def test_broken_hook_files_are_skipped(tmp_path):
    directory = tmp_path / "hooks"
    directory.mkdir()
    (directory / "bad.json").write_text("{nope", encoding="utf-8")
    assert audit.audit_hooks([directory]) == []


def test_an_empty_project_reports_nothing(tmp_path):
    assert audit.run_audit(tmp_path, None, include_user=False) == []
    assert "Nothing found" in audit.format_report([])


def test_the_audit_does_not_modify_the_files_it_reads(tmp_path):
    path = write_permissions(tmp_path)
    before = path.read_bytes()
    audit.run_audit(tmp_path, path, include_user=False)
    assert path.read_bytes() == before
