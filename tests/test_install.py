"""R6: the installer."""

import json
import os

from ghostkit import install


def paths():
    return "/abs/ghostkit/run.py", "/abs/room/ghostkit.toml", "/abs/room/.ghostkit/events.jsonl"


def hook_file(tmp_path):
    return tmp_path / ".kiro" / "hooks" / install.HOOK_FILE


def test_nothing_is_written_without_confirmation(tmp_path, capsys):
    result = install.apply(tmp_path, *paths(), confirm=False)
    assert result is None and not hook_file(tmp_path).exists()
    assert "Not written" in capsys.readouterr().out


def test_the_content_is_shown_before_anything_is_written(tmp_path, capsys):
    install.apply(tmp_path, *paths(), confirm=False)
    shown = capsys.readouterr().out
    assert "ghostkit: PreToolUse" in shown and "/abs/ghostkit/run.py" in shown


def test_it_writes_valid_hooks_when_confirmed(tmp_path):
    install.apply(tmp_path, *paths(), confirm=True)
    data = json.loads(hook_file(tmp_path).read_text(encoding="utf-8"))
    triggers = {h["trigger"] for h in data["hooks"]}
    assert triggers == {"PreToolUse", "PostToolUse", "Stop"}


def test_only_shell_tools_are_matched_for_pre_and_post(tmp_path):
    install.apply(tmp_path, *paths(), confirm=True)
    hooks = json.loads(hook_file(tmp_path).read_text(encoding="utf-8"))["hooks"]
    by_trigger = {h["trigger"]: h for h in hooks}
    assert by_trigger["PreToolUse"]["matcher"] == "shell" and by_trigger["PostToolUse"]["matcher"] == "shell"
    assert "matcher" not in by_trigger["Stop"]


def test_commands_use_python_isolated_mode_and_an_existence_guard(tmp_path):
    install.apply(tmp_path, *paths(), confirm=True)
    for hook in json.loads(hook_file(tmp_path).read_text(encoding="utf-8"))["hooks"]:
        command = hook["action"]["command"]
        assert command.startswith("P=/abs/ghostkit/run.py; if [ -f ")
        assert "python3 -I -S" in command and command.rstrip().endswith("fi")


def test_a_hook_that_cannot_find_the_engine_does_nothing(tmp_path):
    import subprocess
    install.apply(tmp_path, "/definitely/not/here/run.py", "/p.toml", "/l.jsonl", confirm=True)
    command = json.loads(hook_file(tmp_path).read_text(encoding="utf-8"))["hooks"][0]["action"]["command"]
    result = subprocess.run(["/bin/sh", "-c", command], capture_output=True)
    assert result.returncode == 0 and result.stdout == b"" and result.stderr == b""


def test_stop_and_post_hooks_can_never_fail_the_turn(tmp_path):
    install.apply(tmp_path, *paths(), confirm=True)
    hooks = {h["trigger"]: h["action"]["command"] for h in
             json.loads(hook_file(tmp_path).read_text(encoding="utf-8"))["hooks"]}
    assert "|| true" in hooks["PostToolUse"] and "|| true" in hooks["Stop"]


def test_resolved_paths_are_absolute_even_for_a_relative_room():
    engine, policy, log = install._resolve("some/relative/room")
    assert all(os.path.isabs(p) for p in (engine, policy, log))


def test_remove_deletes_what_apply_wrote(tmp_path):
    install.apply(tmp_path, *paths(), confirm=True)
    assert install.remove(tmp_path) is not None and not hook_file(tmp_path).exists()


def test_remove_on_a_clean_folder_is_harmless(tmp_path):
    assert install.remove(tmp_path) is None
