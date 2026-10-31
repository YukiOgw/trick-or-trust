# Proof of concept

Experiments run before writing the specs. Results feed the design and the "how we used Kiro" write-up.

## Experiments

| ID | Question |
| --- | --- |
| P1 | Does PreToolUse fire before or after the approval prompt? What does each event's JSON contain? |
| P2 | Can PreToolUse force an approval prompt with a reason (`permissionDecision: "ask"`)? Where does an exit-2 block message appear? |
| P3 | Can a power ship hooks, or do we install them with a skill script? |
| P4 | In a practice room, how often does the agent propose the trap command? |
| P5 | Does UserPromptSubmit output make the agent ask a clarifying question for a vague request? |
| P6 | How long does one hook run take? |

## Probe

`probe.py` is attached to SessionStart, UserPromptSubmit, PreToolUse (shell), PostToolUse (shell), and Stop.
It appends one JSON line per event to `poc/logs/events.jsonl` (gitignored).

- Without the marker `ghostkit-poc`, it records only the event name, timestamps, and key names.
- With the marker, it records the full payload.
- Marker variants change behavior:
  - `ghostkit-poc-ask` (PreToolUse): returns an "ask" decision with a reason.
  - `ghostkit-poc-block` (PreToolUse): blocks with exit code 2.
  - `ghostkit-poc-clarify` (UserPromptSubmit): adds a note to the agent context.
  - `ghostkit-poc-reject` (UserPromptSubmit): exits 1 to test prompt blocking.
- Any unexpected error exits 0.

Hook command pattern used during the PoC (the path points to this file):

```sh
P=<repo>/poc/probe.py; if [ -f "$P" ]; then python3 "$P" PreToolUse; fi
```

Hooks that never need a non-zero exit append `|| true`.
