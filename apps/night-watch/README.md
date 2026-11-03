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

## Install

```sh
python3 /path/to/trick-or-trust/ghostkit/install.py apply . --yes
```

Then open the project in Kiro as usual. Approvals for risky commands now come
with a reason to read first; the log in `.ghostkit/events.jsonl` feeds the same
report as Haunted House.
