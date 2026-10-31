---
inclusion: fileMatch
fileMatchPattern: "**/*"
---

# Product: Trick or Trust (working title)

## What it is

A set of Kiro powers that trains and measures how people supervise AI coding agents inside Kiro. Built for Kiroween 2026, Skeleton Crew category.

- `ghostkit/`: the skeleton. A small policy engine for Kiro hooks.
- `apps/haunted-house/`: app 1. Approval training in practice rooms that hide harmless traps.
- `apps/night-watch/`: app 2. An everyday watch for credit-draining configuration, over-broad permissions, risky operations, and hollow prompts.

## Problems we solve

1. People approve agent actions without reading them (approval fatigue).
2. Approval prompts turn into noise, so people grant over-broad "always allow" rules.
3. Structural credit waste: agent-type hooks on frequent triggers, large always-on context, oversized models for trivial tasks.

## Product principles

- Coach and measure. Do not pretend to enforce: users can remove hooks. Enforcement belongs to Kiro permissions and enterprise permission policies. We suggest rules; humans apply them.
- Every hook we ship is a shell-command hook, because agent-prompt hooks consume credits.
- Never work around Kiro's own safety invariants. Do not write to `~/.kiro/settings/`. Installing hooks always goes through Kiro's approval prompt.
- Target structural waste, not small prompts. Kiro's pricing is designed so users do not micromanage prompts; do not tell people to stop saying "thanks".

## Hackathon constraints

- Category: Skeleton Crew. The two apps live in two separate folders under `apps/`.
- Everything committed to this repository is in English: README, docs, code comments, commit messages. The developer talks to Kiro in Japanese; that is fine.
- The repository will be public on GitHub with an open source license. `/.kiro` is committed and must never be gitignored.
- Only work created on or after 2026-10-30 (Pacific Time) is eligible. Do not copy code from the author's other projects.
- Submission deadline: 2026-12-04 14:00 PT.

## Judging criteria (20% each)

Potential Impact, Technological Implementation (depth of Kiro usage), Design, Innovation, Presentation (demo video under three minutes).
