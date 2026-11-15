---
name: install-night-watch
description: Install Night Watch, a guard that asks before risky shell commands (curl piped to a shell, chmod 777, rm -rf) and blocks switching off TLS verification, into the user's project. Use when the user asks to install, set up, or enable Night Watch or the ghostkit hooks, or to remove them.
---

# Install Night Watch

Kiro does not load hooks from a power, so this skill installs them into the project with a script. The script is `scripts/install_night_watch.py` in this skill's folder. It needs Python 3.11 or newer.

## Steps

1. Ask which project folder to install into. Use an absolute path. Do not guess.
2. Run a dry run. It writes nothing and prints what it would write:

   ```sh
   python3 <this skill folder>/scripts/install_night_watch.py <project folder>
   ```

3. Show the user the hook file and the policy copy that the dry run printed. Tell them in plain words what will happen: shell commands in that project will pass through Night Watch, risky ones will ask first, and one will be blocked.
4. Ask for a yes. Do not continue without it.
5. Only after a yes, run the same command with `--yes`.
6. Tell the user:
   - the policy is a normal file at `<project>/.kiro/night-watch.toml`, and they can edit it;
   - a log is written to `<project>/.ghostkit/events.jsonl`, and they may want to add `.ghostkit/` to `.gitignore`;
   - to remove Night Watch, run the script with `--remove`; that deletes the hook file and leaves the policy file.

## Rules

- Never run with `--yes` before the user has seen the dry run and agreed.
- Do not edit the project's hook or policy files by hand to get around the script.
- If the script reports that a policy file already exists, it keeps the user's file. Say so.
