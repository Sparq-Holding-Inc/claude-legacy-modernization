"""Run marker for the citation hook. Python standard library only.

    marker.py start --scope PATH [--mode full|wave]   run begins
    marker.py done                                     assessment written, ready for the check
    marker.py status                                   print the marker

The Stop hook (hooks/check_citations.py) does nothing unless this marker exists
and its state is "done". Plugin hooks fire in every session where the plugin is
enabled. The marker keeps the check out of unrelated work.

The hook, not this script, removes the marker after a clean check. Removing it
before the final Stop would defeat the check.
"""

import argparse
import datetime
import json
import os
import sys

OUT = "modernization-assessment"
NAME = ".in-progress"
FULL_OUTPUTS = ["graph.json", "waves.json", "dead-code.json", "risks.json"]


def path(out):
    return os.path.join(out, NAME)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["start", "done", "status"])
    ap.add_argument("--scope", default=".", help="the folder being assessed")
    ap.add_argument("--mode", choices=["full", "wave"], default="full")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    p = path(a.out)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    if a.action == "start":
        os.makedirs(a.out, exist_ok=True)
        data = {"state": "running", "target": os.path.abspath(a.scope), "mode": a.mode,
                "require": FULL_OUTPUTS if a.mode == "full" else [], "started": now, "attempts": 0}
        with open(p, "w") as fh:
            json.dump(data, fh, indent=1)
            fh.write("\n")
        print("marker written: %s" % p)
        return 0
    if not os.path.exists(p):
        print("no marker at %s" % p, file=sys.stderr)
        return 1
    with open(p) as fh:
        data = json.load(fh)
    if a.action == "done":
        data["state"] = "done"
        data["finished"] = now
        with open(p, "w") as fh:
            json.dump(data, fh, indent=1)
            fh.write("\n")
        print("marker set to done: the citation check runs when you finish")
        return 0
    print(json.dumps(data, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
