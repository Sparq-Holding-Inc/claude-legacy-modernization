#!/usr/bin/env python3
"""Tests for the citation hook. Python standard library only.

    python3 evals/test_hook.py

Each case builds a small project in a temp folder, runs the hook the way Claude
Code does (JSON on stdin, cwd set), and checks what it prints and what it
leaves behind.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
HOOK = os.path.join(PLUGIN, "hooks", "check_citations.py")
MARKER = os.path.join(PLUGIN, "skills", "modernization-assessment", "scripts", "marker.py")
FIX = os.path.join(HERE, "fixtures", "01-static-call", "repo")


def run_hook(cwd, active=False):
    ev = {"hook_event_name": "Stop", "cwd": cwd, "stop_hook_active": active}
    r = subprocess.run([sys.executable, HOOK], input=json.dumps(ev), capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def project():
    d = tempfile.mkdtemp()
    shutil.copytree(FIX, os.path.join(d, "repo"))
    os.makedirs(os.path.join(d, "repo", "modernization-assessment"))
    return os.path.join(d, "repo")


def marker(proj, state="done", mode="wave"):
    subprocess.run([sys.executable, MARKER, "start", "--target", proj, "--mode", mode],
                   cwd=proj, check=True, capture_output=True)
    if state == "done":
        subprocess.run([sys.executable, MARKER, "done"], cwd=proj, check=True, capture_output=True)


def write(proj, name, text):
    with open(os.path.join(proj, "modernization-assessment", name), "w") as fh:
        fh.write(text)


def exists_marker(proj):
    return os.path.exists(os.path.join(proj, "modernization-assessment", ".in-progress"))


GOOD = "# Coupling\n\nPROGA calls PROGB (`app/cbl/PROGA.cbl:6`).\n"
BAD = "# Coupling\n\nPROGA calls PROGB (`app/cbl/PROGA.cbl:600`).\n"
results = []


def case(name, ok, detail=""):
    results.append(ok)
    print("%-62s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))


# 1 unrelated session: no marker, even with a bad citation lying around
p = project()
write(p, "02-coupling.md", BAD)
os.remove(os.path.join(p, "modernization-assessment", "02-coupling.md")) if False else None
os.remove(os.path.join(p, "modernization-assessment", ".in-progress")) if exists_marker(p) else None
rc, out, err = run_hook(p)
case("no marker: hook is silent and does nothing", rc == 0 and out == "" and err == "")

# 2 a run in progress is not checked
p = project(); marker(p, "running"); write(p, "02-coupling.md", BAD)
rc, out, _ = run_hook(p)
case("marker running: not checked yet", rc == 0 and out == "" and exists_marker(p))

# 3 planted bad citation is caught on the first stop
p = project(); marker(p); write(p, "02-coupling.md", BAD)
rc, out, _ = run_hook(p)
blocked = out.startswith("{") and json.loads(out).get("decision") == "block"
case("bad citation: first stop is blocked", rc == 0 and blocked and "PROGA.cbl:600" in out)

# 4 after the fix it passes and removes the marker
write(p, "02-coupling.md", GOOD)
rc, out, _ = run_hook(p, active=True)
case("fixed citation: passes and removes the marker", rc == 0 and out == "" and not exists_marker(p))

# 5 second failure lets the stop through and records it
p = project(); marker(p); write(p, "02-coupling.md", BAD)
run_hook(p)
rc, out, _ = run_hook(p, active=True)
summary = open(os.path.join(p, "modernization-assessment", "00-summary.md")).read() if os.path.exists(
    os.path.join(p, "modernization-assessment", "00-summary.md")) else ""
case("still bad on the second stop: allowed, section appended, no loop",
     rc == 0 and out == "" and "## Unresolved citations" in summary and "PROGA.cbl:600" in summary
     and not exists_marker(p))

# 6 the guard holds even when stop_hook_active is missing but attempts is set
p = project(); marker(p); write(p, "02-coupling.md", BAD)
run_hook(p)
rc, out, _ = run_hook(p, active=False)
case("attempt counter alone stops a loop", rc == 0 and out == "" and not exists_marker(p))

# 7 findings tables need a citation or the word inference
p = project(); marker(p)
write(p, "03-waves.md", "| Wave | Rationale | Evidence |\n|---|---|---|\n| 1 | easy | `app/cbl/PROGA.cbl:6` |\n"
                        "| 2 | hard | inference |\n| 3 | odd | |\n")
rc, out, _ = run_hook(p)
case("table row with no citation and no inference label is flagged",
     out.startswith("{") and "| 3 | odd" in out and "| 2 | hard" not in out and "| 1 | easy" not in out)

# 8 citations inside code fences and URLs are ignored
p = project(); marker(p)
write(p, "02-coupling.md", "```\nexample.cbl:9999\n```\nSee https://example.com/a.md:80 for context.\n")
rc, out, _ = run_hook(p)
case("fenced code and URLs are not treated as citations", rc == 0 and out == "" and not exists_marker(p))

# 9 a required JSON output that is missing, then one that does not validate
p = project(); marker(p, mode="full"); write(p, "02-coupling.md", GOOD)
rc, out, _ = run_hook(p)
case("missing required JSON output blocks", out.startswith("{") and "waves.json is missing" in out)
p = project(); marker(p, mode="wave"); write(p, "risks.json", json.dumps({"units": [{"id": "A", "risk_score": 9}]}))
rc, out, _ = run_hook(p)
case("invalid JSON output blocks with the schema error", out.startswith("{") and "risks.json does not validate" in out)

# 10 stale marker is dropped
p = project(); marker(p)
mp = os.path.join(p, "modernization-assessment", ".in-progress")
d = json.load(open(mp)); d["started"] = "2020-01-01T00:00:00+00:00"; json.dump(d, open(mp, "w"))
write(p, "02-coupling.md", BAD)
rc, out, _ = run_hook(p)
case("stale marker is ignored and removed", rc == 0 and out == "" and not exists_marker(p))

print("\n%d of %d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
