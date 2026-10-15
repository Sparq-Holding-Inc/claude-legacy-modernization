#!/usr/bin/env python3
"""Can the wave quality checks fail? Plant bad plans and expect the matching metric to notice.

    python3 evals/test_wave_quality.py

The baseline is a real plan, the CardDemo run saved in examples/carddemo. Each case damages a copy of it.
Its graph.json is in the evidence repo, claude-legacy-modernization-evidence, cloned next to this one.
Pass another checkout as the first argument. Without the graph the test is skipped, not passed.
Reversing the waves must flip the ordering score and leave the cut alone, which shows the metrics measure
different things. Python standard library only.
"""

import copy
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import wave_quality as Q  # noqa: E402

BASE = os.path.join(PLUGIN, "examples", "carddemo")
EVIDENCE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(PLUGIN), "claude-legacy-modernization-evidence")
GRAPH = os.path.join(EVIDENCE, "examples", "carddemo", "graph.json")
if not os.path.exists(GRAPH):
    print("SKIPPED: %s not found. Clone claude-legacy-modernization-evidence next to this repo, or pass its path."
          % GRAPH)
    sys.exit(0)
graph = json.load(open(GRAPH))
waves = json.load(open(os.path.join(BASE, "waves.json")))
risks = json.load(open(os.path.join(BASE, "risks.json")))
results = []


def case(name, ok, detail=""):
    results.append(ok)
    print("%-70s %s %s" % (name, "PASS" if ok else "FAIL", detail if not ok else ""))


base = Q.score(graph, waves, risks)
case("baseline is scored", base["units_placed"] >= 100 and base["cut_percentile"] is not None, str(base))
case("a real plan beats random plans on cut", base["cut_percentile"] >= Q.BAR_PERCENTILE, str(base["cut_percentile"]))

# shuffled labels keep the wave sizes and destroy the structure
labels = [w["wave"] for w in waves["waves"] for _ in w["units"]]
random.Random(7).shuffle(labels)
shuffled = copy.deepcopy(waves)
i = 0
for w in shuffled["waves"]:
    n = len(w["units"])
    w["units"] = sorted(sum(([u] for u in w["units"]), []))
allunits = sorted(u for w in waves["waves"] for u in w["units"])
random.Random(7).shuffle(allunits)
pos = 0
for w in shuffled["waves"]:
    n = len(w["units"])
    w["units"] = allunits[pos:pos + n]
    pos += n
s = Q.score(graph, shuffled, risks)
case("a shuffled plan does not beat random on cut", s["cut_percentile"] < Q.BAR_PERCENTILE, str(s["cut_percentile"]))
case("a shuffled plan has many more misplaced units", s["misplaced_share"] > base["misplaced_share"] + 0.3,
     "%s vs %s" % (s["misplaced_share"], base["misplaced_share"]))

# reversing the order keeps every boundary and flips the ordering score
rev = copy.deepcopy(waves)
top = max(w["wave"] for w in rev["waves"])
for w in rev["waves"]:
    w["wave"] = top + 1 - w["wave"]
s = Q.score(graph, rev, risks)
case("reversed waves keep the same cut", s["cut_pairs"] == base["cut_pairs"] and s["misplaced_units"] == base["misplaced_units"])
case("reversed waves flip the ordering score", base["order_spearman"] > 0 and s["order_spearman"] < 0,
     "%s vs %s" % (base["order_spearman"], s["order_spearman"]))

# one unit moved to a wave it has no links to
moved = copy.deepcopy(waves)
unit = next(u for u in moved["waves"][2]["units"] if not u.startswith("sch:"))
moved["waves"][2]["units"].remove(unit)
moved["waves"][-1]["units"].append(unit)
s = Q.score(graph, moved, risks)
case("moving one linked unit away from its neighbors raises the cut", s["cut_pairs"] > base["cut_pairs"],
     "%s vs %s" % (s["cut_pairs"], base["cut_pairs"]))

# a tiny plan is not graded on cut
tiny = {"waves": [{"wave": 1, "units": allunits[:5]}]}
s = Q.score(graph, tiny, risks)
case("a plan under 20 units is not graded on cut", s["cut_percentile"] is None and s["cut_bar"].startswith("n/a"))

print("\n%d of %d passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
