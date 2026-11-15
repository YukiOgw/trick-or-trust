---
name: audit-kiro-setup
description: Audit a project's Kiro setup, read-only, for over-broad always-allow shell permissions, large always-on steering, and agent-type hooks on frequent triggers that use credits. Use when the user asks to check their permissions, find what is wasting credits, or review their Kiro setup.
---

# Audit a Kiro setup

The audit is `ghostkit/audit.py` at the root of this power. It only reads files. It needs Python 3.11 or newer.

## Steps

1. Ask which project folder to audit. Use an absolute path.
2. Run the audit on the project only:

   ```sh
   python3 <power folder>/ghostkit/audit.py --project <project folder> --no-user
   ```

3. Summarize what it found in plain words, grouped as it prints them:
   - Zombie Permission: always-allow rules that were probably meant for one moment;
   - Credit Vampire: setup that spends credits on every turn.
4. If the user also wants their personal settings checked (`~/.kiro/settings/permissions.yaml`, user steering, user hooks), ask first. Only then run it again without `--no-user`, or with `--permissions <file>`.

## Rules

- Never edit `permissions.yaml` or any other Kiro settings file. Report and suggest only; the user makes the change.
- Do not paste the contents of a settings file into the chat. Quote only the rules the audit flagged.
- A finding is a prompt to look, not proof of a problem. Say so when a rule may be intentional.
