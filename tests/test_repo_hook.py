"""The hook this repository ships in its own .kiro/hooks (Night Watch on Night Watch)."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK_FILE = ROOT / ".kiro" / "hooks" / "ghostkit-night-watch.json"


def hooks():
    return {h["trigger"]: h for h in json.loads(HOOK_FILE.read_text(encoding="utf-8"))["hooks"]}


def run(trigger, command_text, tmp_path):
    # Run it the way Kiro does: through the shell, from the repository root.
    shell_command = hooks()[trigger]["action"]["command"].replace(".ghostkit/events.jsonl", str(tmp_path / "e.jsonl"))
    payload = json.dumps({"session_id": "s", "tool_name": "execute_bash", "tool_input": {"command": command_text}})
    proc = subprocess.run(["/bin/sh", "-c", shell_command], input=payload.encode(), capture_output=True, cwd=ROOT)
    return proc.returncode, proc.stdout.decode(), proc.stderr.decode()


def test_the_repo_ships_the_three_hooks():
    assert set(hooks()) == {"PreToolUse", "PostToolUse", "Stop"}


def test_the_hook_uses_only_repo_relative_paths():
    for hook in hooks().values():
        assert "/Users/" not in hook["action"]["command"]


def test_it_asks_before_a_risky_command(tmp_path):
    code, out, _ = run("PreToolUse", "rm -rf build", tmp_path)
    assert code == 0 and "permissionDecision" in out


def test_it_blocks_switching_off_tls_verification(tmp_path):
    code, _, err = run("PreToolUse", "NODE_TLS_REJECT_UNAUTHORIZED=0 node x.js", tmp_path)
    assert code == 2 and err


def test_it_stays_out_of_the_way_of_ordinary_commands(tmp_path):
    assert run("PreToolUse", "git status", tmp_path) == (0, "", "")
