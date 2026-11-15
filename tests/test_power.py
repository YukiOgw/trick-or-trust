"""The Night Watch power: manifest, skills, vendored copy, and the install skill end to end."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POWER = ROOT / "powers" / "ghostkit-night-watch"
INSTALL = POWER / "skills" / "install-night-watch" / "scripts" / "install_night_watch.py"
NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")


def manifest():
    return json.loads((POWER / "plugin.json").read_text(encoding="utf-8"))


def test_the_manifest_has_the_required_fields():
    data = manifest()
    assert data["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert data["name"] and data["version"] and data["description"] and data["author"]["name"]
    assert data["keywords"]


def test_the_name_is_valid_and_matches_the_folder():
    # Kiro names an imported power after its folder (observed in IDE 1.4.62), so keep them equal.
    name = manifest()["name"]
    assert NAME_RE.match(name) and "--" not in name and ".." not in name and len(name) <= 64
    assert name == POWER.name


def test_the_manifest_only_uses_allowed_top_level_fields():
    allowed = {"$schema", "name", "version", "description", "author", "homepage",
               "repository", "license", "keywords", "extensions"}
    assert set(manifest()) <= allowed


def test_the_power_does_not_pretend_to_ship_hooks():
    # Kiro does not load hooks from a power, so none may be placed where a reader would expect them.
    assert not (POWER / "hooks").exists() and not (POWER / "dev.kiro" / "hooks").exists()


def test_every_skill_has_frontmatter_that_matches_its_folder():
    skills = sorted((POWER / "skills").iterdir())
    assert skills
    for skill in skills:
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\n")
        front = text.split("---", 2)[1]
        assert f"name: {skill.name}" in front
        assert "description:" in front


def test_the_instructions_file_exists():
    assert "Night Watch" in (POWER / "dev.kiro" / "INSTRUCTIONS.md").read_text(encoding="utf-8")


def test_the_vendored_engine_matches_the_source():
    # Run `python3 scripts/sync_power.py` if this fails.
    sources = {p.name: p.read_bytes() for p in (ROOT / "ghostkit").glob("*.py")}
    vendored = {p.name: p.read_bytes() for p in (POWER / "ghostkit").glob("*.py")}
    assert vendored == sources


def test_the_vendored_policy_matches_the_night_watch_app():
    assert (POWER / "policy" / "night-watch.toml").read_bytes() == (ROOT / "apps" / "night-watch" / "ghostkit.toml").read_bytes()


def run_install(project, *flags):
    proc = subprocess.run([sys.executable, str(INSTALL), str(project), *flags], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_a_dry_run_writes_nothing_and_shows_what_it_would_write(tmp_path):
    code, out, _ = run_install(tmp_path)
    assert code == 0 and "Not written" in out and "ghostkit: PreToolUse" in out
    assert not (tmp_path / ".kiro").exists()


def test_install_writes_the_policy_and_the_hooks(tmp_path):
    code, _, _ = run_install(tmp_path, "--yes")
    assert code == 0
    assert (tmp_path / ".kiro" / "night-watch.toml").exists()
    hooks = json.loads((tmp_path / ".kiro" / "hooks" / "ghostkit.json").read_text(encoding="utf-8"))["hooks"]
    assert {h["trigger"] for h in hooks} == {"PreToolUse", "PostToolUse", "Stop"}
    assert all(str(POWER / "ghostkit" / "run.py") in h["action"]["command"] for h in hooks)


def test_the_installed_hook_asks_before_a_risky_command(tmp_path):
    run_install(tmp_path, "--yes")
    hooks = json.loads((tmp_path / ".kiro" / "hooks" / "ghostkit.json").read_text(encoding="utf-8"))["hooks"]
    pre = next(h for h in hooks if h["trigger"] == "PreToolUse")["action"]["command"]
    payload = json.dumps({"session_id": "s", "tool_name": "execute_bash", "tool_input": {"command": "rm -rf build"}})
    proc = subprocess.run(["/bin/sh", "-c", pre], input=payload.encode(), capture_output=True, cwd=tmp_path)
    assert proc.returncode == 0 and b"permissionDecision" in proc.stdout


def test_an_existing_policy_is_kept(tmp_path):
    policy = tmp_path / ".kiro" / "night-watch.toml"
    policy.parent.mkdir(parents=True)
    policy.write_text('default = "allow"\n# mine\n', encoding="utf-8")
    run_install(tmp_path, "--yes")
    assert "# mine" in policy.read_text(encoding="utf-8")


def test_remove_deletes_the_hooks_and_leaves_the_policy(tmp_path):
    run_install(tmp_path, "--yes")
    run_install(tmp_path, "--remove")
    assert not (tmp_path / ".kiro" / "hooks" / "ghostkit.json").exists()
    assert (tmp_path / ".kiro" / "night-watch.toml").exists()


def test_a_missing_project_folder_is_an_error(tmp_path):
    assert run_install(tmp_path / "nope")[0] == 2
