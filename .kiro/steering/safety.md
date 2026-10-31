---
inclusion: fileMatch
fileMatchPattern: "**/*"
---

# Safety rules for traps and data

- Network targets in traps use only the reserved `.invalid` top-level domain (RFC 6761). Never use real domains, including `example.com`, which resolves.
- Secrets in traps are fake. For AWS keys, use the example values from the AWS documentation (`AKIAIOSFODNN7EXAMPLE`). Never read, print, or copy real secrets such as `~/.aws`, `~/.ssh`, keychains, or `.env` files outside a practice room.
- Destructive traps only touch git-tracked files inside a practice room.
- Never use typosquatted package names from public registries, because a real malicious package may exist under that name. Use local paths instead.
- Drills run only inside a practice room the trainee opened on purpose. Never plant traps in a real project.
- Privacy: prompt text and command arguments are stored only inside a drill. Nothing leaves the machine unless the user exports it.
- Every new trap comes with a test that proves it stays within these rules.
