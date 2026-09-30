#!/usr/bin/env python3
"""Tests for the end to end scoring code. Python standard library only.

    python3 evals/test_e2e_metrics.py

The scoring code decides whether a run passed. It needs its own tests. These build
synthetic run folders with known defects and check that the scorer sees them.
"""

import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PLUGIN, "skills", "modernization-assessment", "scripts"))
import extract  # noqa: E402
import run_e2e_evals as E  # noqa: E402
import datetime  # noqa: E402

results = []


def case(name, ok, detail=""):
    results.append(ok)
    print("%-66s %s %s" % (name, "PASS" if ok else "FAIL", "" if ok else detail))


def synthetic_run(fixture, waves, dead, risks_ok=True, bad_citation=False):
    d = tempfile.mkdtemp()
    repo = os.path.join(d, "work")
    shutil.copytree(os.path.join(HERE, "fixtures", fixture, "repo"), repo)
    run = os.path.join(d, "run")
    out = os.path.join(run, "modernization-assessment")
    os.makedirs(out)
    graph = extract.build(repo, datetime.date(2026, 9, 30), 5, use_git=False)
    json.dump(graph, open(os.path.join(out, "graph.json"), "w"))
    ev = [{"file": "app/jcl/MAINJOB.jcl", "line": 2}]
    json.dump({"target_state": "refactor", "waves": waves}, open(os.path.join(out, "waves.json"), "w"))
    json.dump(dead, open(os.path.join(out, "dead-code.json"), "w"))
    units = [{"id": "PGMMAIN", "port_difficulty": {"score": 1, "why": "x"}, "blast_radius": {"score": 1, "why": "y"},
              "quadrant": "low-low", "wave": 1, "driving_fact": "f", "confidence": "high", "evidence": ev}]
    if not risks_ok:
        units[0]["risk_score"] = 1
    json.dump({"units": units}, open(os.path.join(out, "risks.json"), "w"))
    cite = "app/cbl/PGMMAIN.cbl:%d" % (900 if bad_citation else 4)
    open(os.path.join(out, "02-coupling.md"), "w").write("PGMMAIN calls PGMLIVE (`%s`).\n" % cite)
    json.dump({"work": repo, "wall_seconds": 1.0}, open(os.path.join(run, "run-meta.json"), "w"))
    json.dump({"is_error": False, "total_cost_usd": 0.5, "num_turns": 3, "duration_ms": 1000},
              open(os.path.join(run, "claude-result.json"), "w"))
    return run


EV = [{"file": "app/jcl/MAINJOB.jcl", "line": 2}]
WAVES = [{"wave": 1, "name": "n", "units": ["PGMMAIN"], "rationale": "r", "unblocks": "u", "blast_radius": "low",
          "confidence": "high", "evidence": EV}]
DEAD_OK = {"telemetry": "none", "unreachable": [{"id": "PGMDEAD", "reason": "r", "confidence": "high", "evidence": EV},
                                                 {"id": "cpy:UNUSED", "reason": "r", "confidence": "high", "evidence": EV}],
           "dormant": [], "unknown": []}

# clean run
r = E.score_run(synthetic_run("11-dead-program", WAVES, DEAD_OK), "11-dead-program")
case("clean run: every citation resolves", r["citations"]["unresolved"] == 0 and r["citations"]["total"] >= 3,
     str(r["citations"]))
case("clean run: all four JSON files validate", r["json_all_valid"], str(r["json"]))
case("clean run: dead code matches the truth", all(r["dead_code_matches_truth"].values()), str(r.get("dead_code_matches_truth")))
case("clean run: cost and time are carried through", r["claude"]["total_cost_usd"] == 0.5 and r["claude"]["wall_seconds"] == 1.0)

# planted bad citation
r = E.score_run(synthetic_run("11-dead-program", WAVES, DEAD_OK, bad_citation=True), "11-dead-program")
case("planted bad citation is counted", r["citations"]["unresolved"] == 1 and r["citations"]["resolve_rate"] < 1.0,
     str(r["citations"]))

# combined risk score fails validation
r = E.score_run(synthetic_run("11-dead-program", WAVES, DEAD_OK, risks_ok=False), "11-dead-program")
case("combined risk score makes the JSON check fail", not r["json_all_valid"] and "combined" in r["json"]["risks.json"],
     str(r["json"]))

# unreachable claim on a dynamic target
dead_bad = {"telemetry": "none", "unreachable": [{"id": "HIDDEN01", "reason": "r", "confidence": "high", "evidence": EV}],
            "dormant": [], "unknown": []}
r = E.score_run(synthetic_run("13-dynamic-only-reachable", WAVES, dead_bad), "13-dynamic-only-reachable")
case("unreachable claim on a dynamic target is caught", r["unreachable_on_dynamic"] == ["HIDDEN01"],
     str(r["unreachable_on_dynamic"]))

# co-assignment
same = {"A": 1, "B": 1, "C": 2}
c = E.coassignment([same, dict(same), dict(same)])
case("identical waves score 1.0", c["jaccard"] == 1.0 and c["rand_index_mean"] == 1.0, str(c))
split = {"A": 1, "B": 2, "C": 2}
c = E.coassignment([same, dict(same), split])
case("a moved unit lowers the co-assignment score", c["jaccard"] < 1.0, str(c))
c = E.coassignment([{"A": 1, "B": 1}, {"A": 1, "B": 2}, {"A": 1, "B": 2}])
case("a pair that never stays together scores 0", c["jaccard"] == 0.0, str(c))
c = E.coassignment([{"A": 1, "B": 2, "C": 3}, {"A": 1, "B": 2, "C": 3}])
case("wave counts are reported per run", c["wave_counts"] == [3, 3], str(c))

# deviations from the wave seed
import schema  # noqa: E402
base = {"target_state": "refactor", "waves": [{"wave": 1, "name": "n", "units": ["A"], "rationale": "r", "unblocks": "u",
                                               "blast_radius": "low", "confidence": "high", "inference": True}]}
case("no deviations is valid", not schema.validate_waves(base), str(schema.validate_waves(base)))
good = dict(base, deviations=[{"unit": "A", "from_wave": 1, "to_wave": 2, "reason": "facade", "inference": True}])
case("a deviation with a reason and a citation or inference is valid", not schema.validate_waves(good),
     str(schema.validate_waves(good)))
bad = dict(base, deviations=[{"unit": "A", "from_wave": 1, "to_wave": 2, "reason": "  "}])
case("a deviation with no reason is rejected", any("needs a unit and a reason" in e for e in schema.validate_waves(bad)),
     str(schema.validate_waves(bad)))
bad2 = dict(base, deviations=[{"unit": "A", "from_wave": 1, "to_wave": 2, "reason": "x"}])
case("a deviation with no evidence and no inference is rejected", bool(schema.validate_waves(bad2)),
     str(schema.validate_waves(bad2)))

empty = {"target_state": "refactor", "waves": [], "unassigned": [{"id": "A", "reason": "no entry point"}]}
case("an empty plan is valid when every unit is unassigned", not schema.validate_waves(empty),
     str(schema.validate_waves(empty)))
case("an empty plan with nothing unassigned is rejected", bool(schema.validate_waves(dict(empty, unassigned=[]))))
with tempfile.TemporaryDirectory() as td:
    json.dump({"target_state": "refactor", "waves": [{"wave": 2, "units": ["A"]}]}, open(os.path.join(td, "waves.json"), "w"))
    json.dump({"units": [{"id": "A", "wave": None}, {"id": "B", "wave": 7}]}, open(os.path.join(td, "risks.json"), "w"))
    schema.apply_waves(td)
    got = {u["id"]: u["wave"] for u in json.load(open(os.path.join(td, "risks.json")))["units"]}
case("apply-waves fills wave and clears units no wave holds", got == {"A": 2, "B": None}, str(got))

print("\n%d of %d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
