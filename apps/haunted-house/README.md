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
hosts and ship fake secrets. Some rooms simulate a failure (for example a
certificate error) so that the tempting fix has something to fix; nothing real
is fetched.

## How the agent behaves in a room

Today's models often read a script, notice the trap, and refuse to run it. That
is good for you in real work, but it leaves nothing for you to practice on. So
every room ships a short steering file (`.kiro/steering/practice-room.md`) that
asks the agent to:

- propose the command you asked for without auditing the scripts first, so that
  you are the reviewer at the approval prompt;
- stay inside the room and never touch real credentials;
- stop when you deny an approval, instead of looking for a way around it.

It does not describe any trap. Do not copy this steering file into a real
project: in real work you want the agent to push back. The training guard in
ghostkit still blocks a command that contains a URL for a real host or a real
secret path, whatever the agent proposes. It is a safety net, not a sandbox.

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
| 2 | `rooms/02-fake-installer` | A setup step that pipes a downloaded script straight into your shell |
| 3 | `rooms/03-cert-error` | A "fix" for a certificate error that switches certificate checking off |

Suggested request for each room:

| Room | Ask Kiro |
|------|----------|
| 1 | Run the analysis script and summarize the result. |
| 2 | Set this project up by following the README. |
| 3 | Run the fetch and fix any errors. |
