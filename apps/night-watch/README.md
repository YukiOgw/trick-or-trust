# Night Watch

A guard you drop into an everyday project. It does not train you — it watches for
risky commands and asks you to look before you approve, using the same ghostkit
engine as Haunted House.

## What it flags (default policy)

- Piping a downloaded script straight into a shell (`curl ... | sh`) — ask
- Disabling TLS verification (`NODE_TLS_REJECT_UNAUTHORIZED=0`) — block
- `chmod 777`, recursive force deletes (`rm -rf`) — ask

Edit `ghostkit.toml` to fit your project. Reasons are explanations, not commands
to the agent, so the agent surfaces them without treating them as instructions.

## Audit your setup

Night Watch also looks at the setup around the agent, read-only. It never edits
a Kiro settings file; it reports and suggests.

```sh
python3 /path/to/trick-or-trust/ghostkit/audit.py --project .
```

| Monster | What it finds |
| --- | --- |
| 🧟 Zombie Permission | Always-allow shell rules that can run code, fetch from the network, or delete files (`rm *`, `bash *`, `curl *` ...), a catch-all shell rule, and file writes allowed everywhere |
| 🧛 Credit Vampire | Always-on steering that adds up to a lot of context, and agent-type hooks on triggers that fire often (each run uses credits; shell-command hooks do not) |

By default it also reads `~/.kiro/settings/permissions.yaml` and the steering and hooks under `~/.kiro/`.
Pass `--no-user` to look at the project only, and `--permissions FILE` to check
a specific file. The size guide for always-on steering is a heuristic (16 KB);
change it with `--steering-kb`.

## Install

```sh
python3 /path/to/trick-or-trust/ghostkit/install.py apply . --yes
```

Then open the project in Kiro as usual. Approvals for risky commands now come
with a reason to read first; the log in `.ghostkit/events.jsonl` feeds the same
report as Haunted House.
