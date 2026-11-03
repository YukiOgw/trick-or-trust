# Haunted House

A practice ground for approval judgment with AI coding agents.

Each room is a small project that hides exactly one harmless trap — a command
that looks routine but does something you would not want to approve. You open a
room, ask Kiro to do an ordinary task, and watch what it proposes. When a trap
surfaces, a ghost appears on the approval screen and asks you to read before you
approve.

## Outcomes

- 🍬 **Treat** — you read the command and refused.
- 👻 **Trick** — you approved without reading. The ghost got in.
- 🛡️ **Blocked** — ghostkit stopped a genuinely dangerous command during training.

All traps are harmless by construction: they only reach RFC 6761 `.invalid`
hosts and ship fake secrets.

## Run a room

1. Install the ghostkit hooks into the room:

   ```sh
   python3 ../../ghostkit/install.py apply rooms/01-fake-analytics --yes
   ```

2. Open the room folder in a new Kiro window and trust it.
3. Ask Kiro to do the room's task (see the room's README).
4. Read what it proposes, then approve or reject.
5. Build the graveyard report from the room's `.ghostkit/events.jsonl`.

## Rooms

| # | Room | The trap |
|---|------|----------|
| 1 | `rooms/01-fake-analytics` | An "analyze" script that ships your `.env` to an external host |
