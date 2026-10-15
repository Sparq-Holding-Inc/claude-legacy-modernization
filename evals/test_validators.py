"""Can the validators reject a wrong assessment? Each case plants one defect and expects an error.

    python3 evals/test_validators.py

The baseline is a small graph (fixture 26) with a valid plan, dead code file and risk file. Every
case copies it, breaks one thing, and checks that validation says no. The last cases run the same
checks through `schema.py validate-dir` and `check_citations.py --check`, the way a run does.
Python standard library only.
"""

import copy
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
SCRIPTS = os.path.join(PLUGIN, "skills", "modernization-assessment", "scripts")
sys.path.insert(0, SCRIPTS)
import extract  # noqa: E402
import schema  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "26-wave-seed-families", "repo")
results = []


def case(name, ok, detail=""):
    results.append(ok)
    print("%-72s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))


def expect_error(name, errs, needle):
    hit = [e for e in errs if needle in e]
    case(name, bool(hit), "errors were: %s" % errs[:3])


graph = extract.build(FIX, datetime.date(2026, 9, 30), 5, use_git=False)
seed = graph["analysis"]["wave_seed"]
node = {n["id"]: n for n in graph["nodes"]}


def good_waves():
    waves = []
    for w in seed["waves"]:
        waves.append({"wave": w["wave"], "name": "n", "units": list(w["units"]), "rationale": "r", "unblocks": "u",
                      "blast_radius": "low", "confidence": "medium", "evidence": w["evidence"]})
    return {"target_state": "refactor", "waves": waves, "unassigned": []}


def good_risks(waves):
    placed = {u: w["wave"] for w in waves["waves"] for u in w["units"]}
    return {"units": [{"id": u, "port_difficulty": {"score": 2, "why": "w"}, "blast_radius": {"score": 2, "why": "w"},
                       "quadrant": "low-low", "wave": placed[u], "driving_fact": "x", "confidence": "low",
                       "inference": True} for u in sorted(placed)][:6]}


def good_dead():
    return {"telemetry": "none", "unreachable": [], "dormant": [], "unknown": []}


W = good_waves()
R = good_risks(W)
V = schema.validate
case("baseline plan validates", not V("waves", W, graph), str(V("waves", W, graph)))
case("baseline dead code file validates", not V("dead-code", good_dead(), graph), str(V("dead-code", good_dead(), graph)))
case("baseline risks validate against the plan", not V("risks", R, graph, W), str(V("risks", R, graph, W)))

# ------------------------------------------------------------------ dead code
entry = "PGMVIEW"
case("setup: PGMVIEW is a reachable entry point", entry in graph["analysis"]["entry_points"]
     and entry not in graph["analysis"]["dead_code_candidates"]["unreachable"])
d = good_dead()
d["unreachable"].append({"id": entry, "reason": "x", "confidence": "low", "inference": True})
expect_error("an entry point called unreachable is rejected", V("dead-code", d, graph), "must match the extractor")

d = good_dead()
d["unknown"].append({"id": "PGMRPT", "reason": "x", "confidence": "low", "inference": True})
expect_error("a reachable program called unknown is rejected", V("dead-code", d, graph), "not an extractor candidate")

d = good_dead()
d["dormant"].append({"id": "PGMRPT", "reason": "x", "confidence": "low", "inference": True, "last_modified": None})
expect_error("a dormant claim the extractor did not make is rejected", V("dead-code", d, graph), "did not put it in the dormant")

g2 = copy.deepcopy(graph)
g2["analysis"]["dead_code_candidates"] = {"unreachable": ["PGMRPT"], "dormant": [], "unknown": ["PGMDB"]}
g2["analysis"]["dead_code_reasons"] = {}
d = good_dead()
expect_error("dropping every extractor candidate is rejected", V("dead-code", d, g2), "in no bucket")
d = {"telemetry": "none", "unknown": [{"id": "PGMRPT", "reason": "x", "confidence": "low", "inference": True},
                                       {"id": "PGMDB", "reason": "x", "confidence": "low", "inference": True}],
     "unreachable": [], "dormant": []}
case("moving an unreachable candidate toward unknown is allowed", not V("dead-code", d, g2), str(V("dead-code", d, g2)))
d = {"telemetry": "none", "unreachable": [{"id": "PGMDB", "reason": "x", "confidence": "low", "inference": True},
                                           {"id": "PGMRPT", "reason": "x", "confidence": "low", "inference": True}],
     "unknown": [], "dormant": []}
expect_error("moving an unknown candidate to unreachable is rejected", V("dead-code", d, g2), "PGMDB")

# ---------------------------------------------------------------------- waves
w = {"target_state": "refactor", "waves": [], "unassigned": [{"id": "NONEXISTENT", "reason": "test"}]}
errs = V("waves", w, graph)
expect_error("an empty plan with a made-up unassigned id is rejected", errs, "NONEXISTENT is not a node")
expect_error("an empty plan is rejected when the extractor placed units", errs, "the plan is empty but the extractor placed")
expect_error("an empty plan that leaves units out is rejected", errs, "are in no wave and not in unassigned")

w = good_waves()
w["waves"][0]["units"].pop()
expect_error("a unit left out of the plan is rejected", V("waves", w, graph), "in no wave and not in unassigned")

w = good_waves()
victim = w["waves"][0]["units"][0]
w["unassigned"] = [{"id": victim, "reason": "x"}]
expect_error("a unit both placed and unassigned is rejected", V("waves", w, graph), "is also in wave")

w = good_waves()
victim = w["waves"][0]["units"].pop()
w["unassigned"] = [{"id": victim, "reason": "x"}, {"id": victim, "reason": "y"}]
expect_error("a unit listed twice as unassigned is rejected", V("waves", w, graph), "listed twice")

w = good_waves()
victim = w["waves"][0]["units"].pop()
w["unassigned"] = [{"id": victim, "reason": " "}]
expect_error("an unassigned unit with no reason is rejected", V("waves", w, graph), "reason must be a non-empty string")

w = good_waves()
w["unassigned"] = [{"id": "ds:SPARQ.TEST.MASTER", "reason": "x"}]
expect_error("a dataset in unassigned is rejected", V("waves", w, graph), "A wave holds programs")

g3 = copy.deepcopy(graph)
a, b = w2 = good_waves()["waves"][3]["units"][:1] + good_waves()["waves"][0]["units"][:1]
g3["analysis"]["sccs"] = [[a, b]]
w = good_waves()
expect_error("a call cycle split across two waves is rejected", V("waves", w, g3), "strongly connected component")
w = good_waves()
w["waves"][3]["units"].remove(a)
w["unassigned"] = [{"id": a, "reason": "x"}]
w["waves"][0]["units"] = [u for u in w["waves"][0]["units"]]
expect_error("a call cycle split between a wave and unassigned is rejected", V("waves", w, g3), "unassigned")

w = good_waves()
w["deviations"] = [{"unit": "NOSUCH", "from_wave": 1, "to_wave": 2, "reason": "x", "inference": True}]
expect_error("a deviation about a unit that does not exist is rejected", V("waves", w, graph), "not a node")
w = good_waves()
w["deviations"] = [{"unit": victim, "from_wave": 1, "to_wave": 99, "reason": "x", "inference": True}]
expect_error("a deviation to a wave that does not exist is rejected", V("waves", w, graph), "not a wave in this plan")

# empty plan is fine for a tree with no entry point
g4 = extract.build(os.path.join(HERE, "fixtures", "28-no-entry-points", "repo"), datetime.date(2026, 9, 30), 5, use_git=False)
w = {"target_state": "refactor", "waves": [], "unassigned": [{"id": "PROGA", "reason": "no entry point"},
                                                                {"id": "PROGB", "reason": "no entry point"}]}
case("an empty plan is valid for a tree with no entry point", not V("waves", w, g4), str(V("waves", w, g4)))

# ----------------------------------------------------------------------- risks
r = copy.deepcopy(R)
r["units"][0]["wave"] = 999
expect_error("a risk pointing at wave 999 is rejected", V("risks", r, graph, W), "not a wave in waves.json")
r = copy.deepcopy(R)
r["units"][0]["wave"] = 1 if r["units"][0]["wave"] != 1 else 2
expect_error("a risk in the wrong wave is rejected", V("risks", r, graph, W), "waves.json puts it in")
r = copy.deepcopy(R)
r["units"][0]["wave"] = None
expect_error("a risk with no wave for a placed unit is rejected", V("risks", r, graph, W), "waves.json puts it in")
case("without a plan the risk wave is not cross checked", not V("risks", R, graph), str(V("risks", R, graph)))

# ----------------------------------------------------- the same checks in a run
tmp = tempfile.mkdtemp()
out = os.path.join(tmp, "modernization-assessment")
os.makedirs(out)
json.dump(graph, open(os.path.join(out, "graph.json"), "w"))
json.dump(W, open(os.path.join(out, "waves.json"), "w"))
json.dump(good_dead(), open(os.path.join(out, "dead-code.json"), "w"))
json.dump(R, open(os.path.join(out, "risks.json"), "w"))
run = lambda *a: subprocess.run([sys.executable] + list(a), capture_output=True, text=True, cwd=tmp)
r0 = run(os.path.join(SCRIPTS, "schema.py"), "validate-dir", out)
case("validate-dir accepts the baseline", r0.returncode == 0, r0.stdout[-200:])
bad = copy.deepcopy(R)
bad["units"][0]["wave"] = 999
json.dump(bad, open(os.path.join(out, "risks.json"), "w"))
r1 = run(os.path.join(SCRIPTS, "schema.py"), "validate-dir", out)
case("validate-dir rejects a risk in wave 999", r1.returncode != 0 and "wave 999" in r1.stdout, r1.stdout[-200:])
r2 = run(os.path.join(PLUGIN, "hooks", "check_citations.py"), "--check", out, "--target", FIX)
case("the citation self-check rejects a risk in wave 999", r2.returncode != 0 and "wave 999" in r2.stdout, r2.stdout[-200:])
shutil.rmtree(tmp)

# the exact cases from a review on the CardDemo graph, when the checkout is present
cd = os.path.normpath(os.path.join(PLUGIN, "..", "bench", "carddemo"))
if os.path.isdir(cd):
    gc = extract.build(cd, datetime.date(2026, 9, 30), 5, use_git=False)
    d = good_dead()
    d["unreachable"].append({"id": "COACCT01", "reason": "x", "confidence": "low", "inference": True})
    expect_error("CardDemo: entry point COACCT01 called unreachable is rejected", V("dead-code", d, gc),
                 "must match the extractor")
    w = {"target_state": "refactor", "waves": [], "unassigned": [{"id": "NONEXISTENT", "reason": "test"}]}
    expect_error("CardDemo: an empty plan with a made-up unassigned id is rejected", V("waves", w, gc), "NONEXISTENT")

print("\n%d of %d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
