#!/usr/bin/env python3
"""Install or remove Night Watch in a project.

Usage:
  python3 install_night_watch.py <project>            # dry run: print what would be written
  python3 install_night_watch.py <project> --yes      # write the policy and the hooks
  python3 install_night_watch.py <project> --remove   # delete the hook file (the policy stays)

The ghostkit engine used by the hooks is the copy that ships inside this power, and
the default policy is the one in the power's `policy/` folder.
"""

import argparse
import shutil
import sys
from pathlib import Path

POWER_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(POWER_ROOT))

from ghostkit import install  # noqa: E402  (the copy vendored inside the power)

POLICY_NAME = "night-watch.toml"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="install_night_watch")
    parser.add_argument("project", help="project folder to install into")
    parser.add_argument("--yes", action="store_true", help="write the files (without it, nothing is written)")
    parser.add_argument("--remove", action="store_true", help="remove the Night Watch hook file")
    args = parser.parse_args(argv)

    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        print(f"Not a folder: {project}", file=sys.stderr)
        return 2

    if args.remove:
        install.remove(project)
        return 0

    engine = POWER_ROOT / "ghostkit" / "run.py"
    default_policy = POWER_ROOT / "policy" / POLICY_NAME
    policy = project / ".kiro" / POLICY_NAME
    log = project / ".ghostkit" / "events.jsonl"

    if policy.exists():
        print(f"Policy: {policy} already exists. It will be kept as it is.")
    else:
        print(f"Policy: will copy the default policy to {policy}")
    print()

    # Hooks are written last, so a hook never points at a policy that is missing.
    if args.yes and not policy.exists():
        policy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default_policy, policy)
        print(f"Wrote: {policy}")

    result = install.apply(project, str(engine), str(policy), str(log), confirm=args.yes)
    if result is not None:
        print()
        print("Night Watch is installed. Add `.ghostkit/` to your .gitignore if you do not want the log committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
