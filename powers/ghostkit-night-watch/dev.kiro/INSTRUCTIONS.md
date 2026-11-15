# Night Watch (ghostkit)

Night Watch is a guard for everyday projects. It uses Kiro hooks to ask the person approving to look before a risky shell command runs, and to block a few commands outright. It also audits a project's setup. It is part of Trick or Trust, a Kiroween 2026 project.

## What it does

- Asks before `curl ... | sh`, `chmod 777`, and `rm -rf`, with a reason shown on the approval prompt.
- Blocks switching off TLS verification (`NODE_TLS_REJECT_UNAUTHORIZED=0`).
- Audits a project, read-only, for always-allow shell rules that can run code or delete files, large always-on steering, and agent-type hooks on frequent triggers.

## Two skills

| Skill | Use it when the user asks to |
| --- | --- |
| `install-night-watch` | install, set up, or enable Night Watch or the ghostkit hooks in a project |
| `audit-kiro-setup` | check a project for risky permissions or credit-hungry configuration |

## Why there is an install step

Kiro does not load hooks from inside a power. So the install skill writes a hook file into the project's `.kiro/hooks/` folder. It shows exactly what it will write first, and it writes nothing until the user says yes.

## Rules for the agent

- Never edit a Kiro settings file such as `permissions.yaml`. The audit only reports and suggests; the user makes the change.
- Do not run an install with `--yes` before the user has seen the dry-run output and agreed.
- Do not read anything under `~/.kiro` for the audit unless the user asks for it.
