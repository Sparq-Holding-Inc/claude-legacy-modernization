"""Is a wave plan a good cut, apart from whether runs agree on it? Python standard library only.

    python3 evals/wave_quality.py RUN_DIR            # RUN_DIR holds graph.json and waves.json (and risks.json)
    python3 evals/wave_quality.py --history          # score the CardDemo plans of every loop, from git

Repeatability asks whether three runs made the same plan. This asks whether the plan cuts the coupling the
extractor found in sensible places. The two are separate. A plan every run copies can still be a bad cut.

What is measured, all from graph.json, waves.json and risks.json:

  cut          call, contract and temporal links between units that end up in different waves, compared with
               400 random plans that have the same wave sizes. The percentile is the share of random plans
               that cut MORE. Bar, declared before any plan was scored: 95% or higher, on plans of 20 units
               or more. A plan that cannot beat random has no structure.
  misplaced    units with strictly more links into another wave than into their own. A plan with many of them
               has weak boundaries, and the random baseline above cannot see that. Reported, no bar, because
               the wave order is set by learning-first sequencing and not by cut alone.
  hub split    datasets that a writer and other units touch, counted by how many waves they span, compared
               with the same random plans. Reported, no bar. Shared masters span many waves in every plan.
  chains       scheduler chains (jobs tied by temporal edges or a wrapper) that stay in one wave. Reported,
               no bar. The wave seed keeps chains whole by rule, so a high number is partly circular.
  medium       contract links with confidence medium (the layouts were not proven equal) that cross a wave
               boundary. Each one is a place a port can break silently. Reported, no bar.
  order        rank correlation between wave number and blast radius from risks.json (early waves should be
               the low blast radius ones), and how many high-high units sit in the first half. Reported.
  size         waves of more than 25 units. Reported.

Limits, stated plainly. Every number here comes from the same extracted graph the wave seed is built from, so
a plan that follows the seed's own rules will score well by construction. Gaps in the graph (an unparsed
scheduler, unread control members) carry straight through. This checks that a plan is consistent with the
facts. It does not check that the facts are complete, or that a wave is safe to ship. A person who has run a
migration still has to read the plan.
"""

import itertools
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PLUGIN, "skills", "modernization-assessment", "scripts"))
import schema  # noqa: E402

TRIALS = 400
MIN_UNITS = 20
BAR_PERCENTILE = 0.95
MOVABLE = set(schema.PROGRAM_TYPES) | {"jcl_job", "proc", "scheduler_job"}


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _owner(nid, units):
    if nid in units:
        return nid
    if nid.startswith("step:"):
        job = "job:" + nid[5:].split(".")[0]
        return job if job in units else None
    return None


def _links(graph, units):
    """Distinct unit pairs joined by a call, contract or temporal edge, and the units around each dataset."""
    pairs, sch_of = set(), {}
    hubs = {}
    for e in graph["edges"]:
        s, d = _owner(e["src"], units), _owner(e["dst"], units)
        if e["kind"] in ("call", "contract", "temporal") and s and d and s != d:
            pairs.add((e["kind"],) + tuple(sorted((s, d))))
            if e["kind"] == "call" and s.startswith("sch:") and d.startswith("job:"):
                sch_of.setdefault(s, set()).add(d)
        if e["kind"] == "data" and e["dst"].startswith("ds:") and not e["dst"].startswith("ds:dd:") and s:
            slot = hubs.setdefault(e["dst"], {"units": set(), "writers": set()})
            slot["units"].add(s)
            if e.get("mode") in ("write", "read_write"):
                slot["writers"].add(s)
    hubs = {k: v["units"] for k, v in hubs.items() if v["writers"] and len(v["units"]) > 1}
    medium = {tuple(sorted((_owner(e["src"], units), _owner(e["dst"], units))))
              for e in graph["edges"] if e["kind"] == "contract" and e.get("confidence") == "medium"
              and _owner(e["src"], units) and _owner(e["dst"], units)}
    return pairs, hubs, medium, sch_of


def _chains(graph, units, sch_of):
    adj = {}
    for e in graph["edges"]:
        if e["kind"] == "temporal" and e["src"][:4] in ("job:", "sch:") and e["dst"][:4] in ("job:", "sch:"):
            adj.setdefault(e["src"], set()).add(e["dst"])
            adj.setdefault(e["dst"], set()).add(e["src"])
    for sch, jobs in sch_of.items():
        for j in jobs:
            adj.setdefault(sch, set()).add(j)
            adj.setdefault(j, set()).add(sch)
    seen, comps = set(), []
    for start in sorted(adj):
        if start in seen:
            continue
        comp, work = set(), [start]
        while work:
            x = work.pop()
            if x not in comp:
                comp.add(x)
                work.extend(adj[x] - comp)
        seen |= comp
        members = {m for m in comp if m in units}
        if len(members) > 1:
            comps.append(members)
    return comps


def _cut(pairs, wave):
    return sum(1 for _, a, b in pairs if a in wave and b in wave and wave[a] != wave[b])


def _spread(hubs, wave):
    return sum(len({wave[u] for u in us if u in wave}) - 1 for us in hubs.values() if len(us & set(wave)) > 1)


def _misplaced(pairs, wave):
    """Units whose links into some other wave outnumber the links into their own."""
    counts = {}
    for _, a, b in pairs:
        counts.setdefault(a, {}).setdefault(wave[b], 0)
        counts[a][wave[b]] += 1
        counts.setdefault(b, {}).setdefault(wave[a], 0)
        counts[b][wave[a]] += 1
    bad = []
    for u, per in counts.items():
        own = per.get(wave[u], 0)
        if any(n > own for w, n in per.items() if w != wave[u]):
            bad.append(u)
    return sorted(bad)


def _rank(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return ranks


def _spearman(xs, ys):
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    rx, ry = _rank(xs), _rank(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


def score(graph, waves, risks=None, trials=TRIALS, seed=20260930):
    units = {n["id"] for n in graph["nodes"] if n["unit_type"] in MOVABLE}
    wave = {u: w["wave"] for w in waves.get("waves", []) for u in w.get("units", []) if u in units}
    pairs, hubs, medium, sch_of = _links(graph, units)
    pairs = {p for p in pairs if p[1] in wave and p[2] in wave}
    out = {"units_placed": len(wave), "waves": len({*wave.values()}), "linked_pairs": len(pairs)}
    plan_cut, plan_spread = _cut(pairs, wave), _spread(hubs, wave)
    out["cut_pairs"] = plan_cut
    out["cut_share"] = round(plan_cut / len(pairs), 3) if pairs else None
    out["hub_spread"] = plan_spread
    bad = _misplaced(pairs, wave)
    out["misplaced_units"] = len(bad)
    out["misplaced_share"] = round(len(bad) / len(wave), 3) if wave else None
    if len(wave) >= MIN_UNITS and pairs:
        rng = random.Random(seed)
        labels = list(wave.values())
        names = sorted(wave)
        cuts, spreads = [], []
        for _ in range(trials):
            rng.shuffle(labels)
            trial = dict(zip(names, labels))
            cuts.append(_cut(pairs, trial))
            spreads.append(_spread(hubs, trial))

        def pct(plan, rand):
            return (sum(1 for r in rand if r > plan) + 0.5 * sum(1 for r in rand if r == plan)) / len(rand)
        out["random_cut_mean"] = round(sum(cuts) / len(cuts), 1)
        out["cut_percentile"] = round(pct(plan_cut, cuts), 3)
        out["hub_spread_percentile"] = round(pct(plan_spread, spreads), 3)
        out["cut_bar"] = "PASS" if out["cut_percentile"] >= BAR_PERCENTILE else "FAIL"
    else:
        out["cut_percentile"] = out["hub_spread_percentile"] = None
        out["cut_bar"] = "n/a (fewer than %d units)" % MIN_UNITS
    chains = _chains(graph, units, sch_of)
    whole = [c for c in chains if len({wave[m] for m in c if m in wave}) <= 1]
    out["chains"] = len(chains)
    out["chains_kept_whole"] = len(whole)
    out["medium_contracts_crossing"] = sum(1 for a, b in medium if a in wave and b in wave and wave[a] != wave[b])
    out["medium_contracts_total"] = len(medium)
    sizes = {}
    for u, w in wave.items():
        sizes[w] = sizes.get(w, 0) + 1
    out["waves_over_25_units"] = sum(1 for n in sizes.values() if n > 25)
    out["order_spearman"] = out["high_high_first_half"] = None
    if risks:
        rows = [(wave[u["id"]], u["blast_radius"]["score"], u.get("quadrant")) for u in risks.get("units", [])
                if u.get("id") in wave and isinstance(u.get("blast_radius"), dict)]
        rho = _spearman([r[0] for r in rows], [r[1] for r in rows])
        out["order_spearman"] = round(rho, 3) if rho is not None else None
        half = (max(wave.values()) + 1) // 2 if wave else 0
        out["high_high_first_half"] = sum(1 for w, _, q in rows if q == "high-high" and w <= half)
    return out


def score_dir(run_dir):
    graph = _load(os.path.join(run_dir, "graph.json"))
    waves = _load(os.path.join(run_dir, "waves.json"))
    rp = os.path.join(run_dir, "risks.json")
    return score(graph, waves, _load(rp) if os.path.exists(rp) else None)


# loop -> the commit that recorded that loop's CardDemo runs. Read through git at that commit, when the runs
# were still in this repo under evals/runs. The current runs are in the evidence repo.
LOOP_COMMITS = [(0, "8777f8d"), (1, "37ec46f"), (2, "cdaa9fc"), (3, "9bdd91a")]


def history():
    rows = []
    for loop, commit in LOOP_COMMITS:
        for n in (1, 2, 3):
            base = "evals/runs/carddemo-%d/modernization-assessment/" % n
            try:
                get = lambda f: json.loads(subprocess.run(["git", "show", "%s:%s%s" % (commit, base, f)], cwd=PLUGIN,
                                                          capture_output=True, text=True, check=True).stdout)
                risks = None
                try:
                    risks = get("risks.json")
                except (subprocess.CalledProcessError, ValueError):
                    pass
                s = score(get("graph.json"), get("waves.json"), risks)
            except (subprocess.CalledProcessError, ValueError):
                continue
            rows.append(dict(s, loop=loop, run=n, commit=commit))
    return rows


def main(argv):
    if "--history" in argv:
        rows = history()
        out = os.path.join(HERE, "scorecard", "wave-quality.json")
        json.dump({"note": "CardDemo plans of every loop, scored from git. Quality is separate from repeatability.",
                   "rows": rows}, open(out, "w"), indent=1)
        for r in rows:
            print("loop %d run %d  waves %d  cut pct %s  misplaced %s  chains whole %d/%d  medium %d/%d  order %s"
                  % (r["loop"], r["run"], r["waves"], r["cut_percentile"], r["misplaced_share"],
                     r["chains_kept_whole"], r["chains"], r["medium_contracts_crossing"], r["medium_contracts_total"],
                     r["order_spearman"]))
        print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    print(json.dumps(score_dir(argv[1]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
