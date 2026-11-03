"""Entry point invoked by Kiro hooks.

Hook command shape (absolute paths, guarded by an existence check):

    P=/abs/ghostkit/run.py
    if [ -f "$P" ]; then python3 -I -S "$P" PreToolUse --policy /abs/policy.toml --log /abs/log.jsonl; fi

`-I -S` keeps startup fast. This file adds its parent's parent to sys.path so the
`ghostkit` package imports even under `-I`, then delegates. Any unexpected error
exits 0 so the probe never blocks the user's work.
"""

from __future__ import annotations

import argparse
import os
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ghostkit", add_help=False)
    parser.add_argument("trigger")
    parser.add_argument("--policy", required=True)
    parser.add_argument("--log", default=None)
    args, _ = parser.parse_known_args(argv)

    # Make the ghostkit package importable even under `python3 -I file.py`.
    package_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if package_parent not in sys.path:
        sys.path.insert(0, package_parent)

    from ghostkit import event as event_mod
    from ghostkit import policy as policy_mod
    from ghostkit import safety as safety_mod
    from ghostkit import log as log_mod
    from ghostkit import decision as decision_mod

    event = event_mod.parse(args.trigger, event_mod.read_stdin())

    pol = policy_mod.load(args.policy)
    if not pol.valid:
        # Fail safe: make no decision, record nothing that could block the user.
        return 0

    result = policy_mod.evaluate(pol, event)
    result = safety_mod.guard(result, event, pol.training_mode)

    if args.log:
        log_mod.append(args.log, event, result, pol.log_verbosity)

    return decision_mod.emit(result, event)


def entry() -> int:
    try:
        return main()
    except SystemExit:
        raise
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(entry())
