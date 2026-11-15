"""R3, R7: the entry point, driven the way Kiro drives a hook."""

import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1] / "ghostkit" / "run.py"

POLICY = """default = "allow"
training_mode = true
log_verbosity = "commands"

[[rule]]
trigger = "PreToolUse"
pattern = "analyze"
decision = "ask"
reason = "look first"

[[rule]]
trigger = "PreToolUse"
pattern = "NODE_TLS_REJECT_UNAUTHORIZED=0"
decision = "block"
reason = "no tls bypass"
"""


def call(args, stdin=""):
    proc = subprocess.run([sys.executable, "-I", "-S", str(RUN), *args], input=stdin.encode(), capture_output=True)
    return proc.returncode, proc.stdout.decode(), proc.stderr.decode()


def pre(command):
    return json.dumps({"session_id": "s", "tool_name": "execute_bash", "tool_input": {"command": command}})


def policy_file(tmp_path, text=POLICY):
    path = tmp_path / "ghostkit.toml"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_ask(tmp_path):
    code, out, _ = call(["PreToolUse", "--policy", policy_file(tmp_path)], pre("npm run analyze"))
    assert code == 0 and "permissionDecision" in out


def test_block(tmp_path):
    code, _, err = call(["PreToolUse", "--policy", policy_file(tmp_path)], pre("NODE_TLS_REJECT_UNAUTHORIZED=0 node x"))
    assert code == 2 and "no tls bypass" in err


def test_the_training_guard_blocks_a_real_host(tmp_path):
    code, _, _ = call(["PreToolUse", "--policy", policy_file(tmp_path)], pre("curl https://evil.example.com"))
    assert code == 2


def test_allow(tmp_path):
    assert call(["PreToolUse", "--policy", policy_file(tmp_path)], pre("ls -la")) == (0, "", "")


def test_a_missing_policy_never_blocks(tmp_path):
    code, out, _ = call(["PreToolUse", "--policy", str(tmp_path / "gone.toml")], pre("npm run analyze"))
    assert code == 0 and out == ""


def test_a_broken_policy_never_blocks(tmp_path):
    code, out, _ = call(["PreToolUse", "--policy", policy_file(tmp_path, "= = =")], pre("npm run analyze"))
    assert code == 0 and out == ""


def test_a_hook_with_no_policy_argument_never_blocks():
    assert call(["PreToolUse"], pre("npm run analyze"))[0] == 0


def test_no_arguments_at_all_never_blocks():
    assert call([])[0] == 0


def test_garbage_on_stdin_never_blocks(tmp_path):
    code, _, _ = call(["PreToolUse", "--policy", policy_file(tmp_path)], "{{{ not json")
    assert code == 0


def test_the_log_records_the_ask_and_a_denial_marker(tmp_path):
    log = tmp_path / "events.jsonl"
    args = ["--policy", policy_file(tmp_path), "--log", str(log)]
    call(["PreToolUse", *args], pre("npm run analyze"))
    post = json.dumps({"session_id": "s", "tool_name": "execute_bash",
                       "tool_input": {"command": "npm run analyze"},
                       "tool_response": "Output:\nThe user rejected this tool call.\n\nExit Code: -1"})
    call(["PostToolUse", *args], post)
    lines = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert lines[0]["decision"] == "ask" and lines[0]["command"] == "npm run analyze"
    assert lines[1]["trigger"] == "PostToolUse" and lines[1]["rejected"] is True
