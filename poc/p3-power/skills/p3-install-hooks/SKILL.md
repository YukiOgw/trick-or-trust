---
name: p3-install-hooks
description: PoC only (Trick or Trust P3). Installs one probe hook into a workspace's .kiro/hooks folder to test a two-step install path. Use only when the user explicitly asks to install the tot-p3 probe hook.
---

# Install the tot-p3 probe hook

This skill tests whether a power can install hooks with a script, because Kiro does not load hooks from inside a power.

## Steps

1. Ask the user which workspace root to install into. Do not guess.
2. Run the script with that root:

   ```sh
   python3 scripts/install_hooks.py <workspace-root>
   ```

3. Show the user the path of the created file and its content.
4. Tell the user how to remove it: delete `<workspace-root>/.kiro/hooks/tot-p3-installed.json`.

## What the hook does

It appends one line with a timestamp to `/tmp/tot-p3-hooks.log` before each shell command. It reads nothing and sends nothing.
