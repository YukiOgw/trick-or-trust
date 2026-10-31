---
inclusion: fileMatch
fileMatchPattern: "**/*"
---

# Structure

```
trick-or-trust/
├── .kiro/              specs, steering, and hooks used to build this project (committed)
├── ghostkit/           skeleton: event parsing, policy engine, logging, report rendering, installer
├── apps/
│   ├── haunted-house/  app 1: approval training (rooms with harmless traps)
│   └── night-watch/    app 2: everyday watch
├── docs/               GitHub Pages: landing page and sample report
├── poc/                experiments run before the specs (kept for the write-up; logs are gitignored)
└── tests/              tests mirror the package layout
```

## Conventions

- Python modules and functions use `snake_case`. Classes use `PascalCase`.
- Each app is self-contained under `apps/<name>/` and depends on `ghostkit` only through its public functions.
- The monster vocabulary is shared across apps, reports, and docs: Credit Vampire, Zombie Permission, Phantom Approval, Hollow Prompt, Skeleton Key, Secret Web. Use these names consistently.
