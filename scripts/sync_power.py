#!/usr/bin/env python3
"""Copy the engine and the default Night Watch policy into the power.

A power has to carry its own copy of ghostkit, because it is copied into
~/.kiro/powers/installed/ and cannot reach the rest of this repository.
`tests/test_power.py` fails when the copy drifts from the source, so run this
after changing anything under ghostkit/ or apps/night-watch/ghostkit.toml.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POWER = ROOT / "powers" / "ghostkit-night-watch"


def main() -> None:
    target = POWER / "ghostkit"
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.glob("*.py"):
        stale.unlink()
    for source in sorted((ROOT / "ghostkit").glob("*.py")):
        shutil.copy2(source, target / source.name)

    policy_dir = POWER / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "apps" / "night-watch" / "ghostkit.toml", policy_dir / "night-watch.toml")
    print(f"Synced {len(list(target.glob('*.py')))} modules and the policy into {POWER.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
