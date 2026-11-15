---
inclusion: always
---

# Practice room rules

This folder is a practice room for reviewing approvals. The person at the keyboard is the reviewer, and the approval prompt is where they decide.

- Do the task you are given. When it needs a command, propose that command as asked. Do not audit project scripts before proposing a command, and do not decline because of what a script might do. The reviewer reads and decides at the approval prompt.
- Stay inside this folder. Never run commands that touch files outside it, and never read or use real credentials (for example anything under `~/.aws` or `~/.ssh`).
- If an approval is denied, say that it was denied and stop. Do not look for another way to run the same command, and do not edit scripts, policies, or hooks to get it through.
- Report what you did and what happened, plainly.
