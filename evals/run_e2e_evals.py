#!/usr/bin/env python3
"""End to end evals. Python standard library only.

    python3 evals/run_e2e_evals.py --cases all            run headless, then score
    python3 evals/run_e2e_evals.py --cases carddemo       three CardDemo runs
    python3 evals/run_e2e_evals.py --cases fixtures       each numbered fixture once
    python3 evals/run_e2e_evals.py --score-only           score run folders that already exist

Each run starts a fresh copy of the target in ../bench/runs/<case>-<n>/work and
calls `claude -p` with the plugin loaded from this folder (`--plugin-dir`). The
run's assessment folder and Claude's JSON result are saved under
evals/runs/<case>-<n>/. Scoring reads only those saved files.

Metrics (the ship bar, section 7 of the build plan)
    citations that resolve                     bar 100%
    unreachable claims on dynamic targets      bar 0
    wave count across the CardDemo runs        bar identical
    pairwise wave co-assignment                bar 80%+
    every JSON output validates                bar 100%
    cost and wall time per run                 published, no bar

This runner never edits a truth file and never changes a threshold.
"""

import argparse
import collections
import datetime
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PLUGIN, "skills", "modernization-assessment", "scripts"))
sys.path.insert(0, os.path.join(PLUGIN, "hooks"))
sys.path.insert(0, HERE)
import check_citations as cc  # noqa: E402
import schema  # noqa: E402

RUNS = os.path.join(HERE, "runs")
BENCH = os.path.normpath(os.path.join(PLUGIN, "..", "bench"))
CARDDEMO = os.path.join(BENCH, "carddemo")
FIXTURES = os.path.join(HERE, "fixtures")
NUMBERED = ["01-static-call", "02-dynamic-call", "03-cics-link-xctl", "04-shared-copybook", "05-vsam-cics-pair",
            "06-contract-match", "07-contract-mismatch", "08-temporal-steps", "09-temporal-controlm",
            "10-temporal-shell", "11-dead-program", "12-dormant-program", "13-dynamic-only-reachable"]
MUST_NOT_BREAK = {
    "carddemo": "daily transaction posting, the account and card master refresh, and the transaction report",
}
DEFAULT_MNB = "the nightly batch cycle"
CARDDEMO_RUNS = 3


def prompt_for(case):
    mnb = MUST_NOT_BREAK.get(case, DEFAULT_MNB)
    return ('/legacy-modernization:modernize-scan --target refactor --must-not-break "%s" --telemetry none' % mnb)


# ---------------------------------------------------------------- running

def prepare_workdir(case, run_dir):
    work = os.path.join(BENCH, "runs", os.path.basename(run_dir), "work")
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(os.path.dirname(work), exist_ok=True)
    if case == "carddemo":
        shutil.copytree(CARDDEMO, work)
    else:
        import run_extractor_evals as R
        cdir = os.path.join(FIXTURES, case)
        shutil.copytree(os.path.join(cdir, "repo"), work)
        hp = os.path.join(work, "history.json")
        if os.path.exists(hp):
            hist = json.load(open(hp))
            os.remove(hp)
            R.make_git_history(work, hist)
    return work


def run_names(case, n_runs):
    return ["%s-%d" % (case, i) for i in range(1, n_runs + 1)] if case == "carddemo" else [case]


def prepare_only(cases, n_runs):
    """Create fresh work folders and print them. Used when the runs are done another way."""
    out = []
    for case in cases:
        for name in run_names(case, n_runs):
            run_dir = os.path.join(RUNS, name)
            os.makedirs(run_dir, exist_ok=True)
            work = prepare_workdir(case, run_dir)
            out.append({"case": case, "name": name, "work": work, "prompt": prompt_for(case)})
    return out


def collect_only(cases, n_runs, harness):
    """Copy each finished work folder's assessment into evals/runs and record how it was produced."""
    for case in cases:
        for name in run_names(case, n_runs):
            run_dir = os.path.join(RUNS, name)
            work = os.path.join(BENCH, "runs", name, "work")
            src = os.path.join(work, "modernization-assessment")
            if not os.path.isdir(src):
                print("no output for %s" % name)
                continue
            dst = os.path.join(run_dir, "modernization-assessment")
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            json.dump({"case": case, "harness": harness, "work": work}, open(os.path.join(run_dir, "run-meta.json"), "w"),
                      indent=1)
            print("collected %s" % name)


def run_one(case, n, budget, model):
    name = "%s-%d" % (case, n) if case == "carddemo" else case
    run_dir = os.path.join(RUNS, name)
    os.makedirs(run_dir, exist_ok=True)
    work = prepare_workdir(case, run_dir)
    cmd = ["claude", "-p", prompt_for(case), "--plugin-dir", PLUGIN, "--permission-mode", "acceptEdits",
           "--output-format", "json", "--max-budget-usd", str(budget), "--max-turns", "120",
           "--no-session-persistence"]
    if model:
        cmd += ["--model", model]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=work, capture_output=True, text=True)
    wall = time.time() - t0
    with open(os.path.join(run_dir, "claude-result.json"), "w") as fh:
        fh.write(r.stdout)
    with open(os.path.join(run_dir, "claude-stderr.txt"), "w") as fh:
        fh.write(r.stderr)
    src = os.path.join(work, "modernization-assessment")
    dst = os.path.join(run_dir, "modernization-assessment")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    if os.path.isdir(src):
        shutil.copytree(src, dst)
    json.dump({"case": case, "wall_seconds": round(wall, 1), "returncode": r.returncode, "command": cmd,
               "work": work}, open(os.path.join(run_dir, "run-meta.json"), "w"), indent=1)
    return run_dir


# ---------------------------------------------------------------- scoring

def load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def citation_stats(out_dir, roots):
    """(total citations, unresolved) over the markdown and the evidence entries in JSON."""
    res = cc.Resolver(roots)
    total = bad = 0
    for name in sorted(os.listdir(out_dir)):
        path = os.path.join(out_dir, name)
        if name.endswith(".md"):
            text = open(path, encoding="utf-8", errors="replace").read()
            in_fence = False
            for line in text.split("\n"):
                if cc.FENCE.match(line):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                for m in cc.CITATION.finditer(line):
                    if "://" in line[max(0, m.start() - 8):m.start()]:
                        continue
                    total += 1
                    if res.problem(m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None):
                        bad += 1
            bad_rows = len([p for p in cc.check_markdown(path, res) if "findings table row" in p])
            total += bad_rows
            bad += bad_rows
        elif name.endswith(".json"):
            doc = load_json(path)
            if doc is None:
                continue
            for e in cc.evidence_lists(doc):
                total += 1
                if not isinstance(e["line"], int) or res.problem(e["file"], e["line"], None):
                    bad += 1
    return total, bad


def json_status(out_dir):
    graph = load_json(os.path.join(out_dir, "graph.json"))
    files = {"graph.json": "graph", "waves.json": "waves", "dead-code.json": "dead-code", "risks.json": "risks"}
    out = {}
    for name, kind in files.items():
        doc = load_json(os.path.join(out_dir, name))
        if doc is None:
            out[name] = "missing or unreadable"
            continue
        errs = schema.validate(kind, doc, graph if kind != "graph" else None)
        out[name] = "valid" if not errs else "%d errors: %s" % (len(errs), errs[0])
    return out


def wave_map(out_dir):
    doc = load_json(os.path.join(out_dir, "waves.json"))
    if not doc:
        return None
    return {u: w["wave"] for w in doc.get("waves", []) for u in w.get("units", [])}


def coassignment(maps):
    """Jaccard of the sets of co-assigned pairs across runs, plus the Rand index between run pairs."""
    pair_sets = []
    for m in maps:
        by_wave = collections.defaultdict(list)
        for u, w in m.items():
            by_wave[w].append(u)
        pair_sets.append({frozenset(p) for units in by_wave.values() for p in itertools.combinations(sorted(units), 2)})
    union = set().union(*pair_sets)
    inter = set.intersection(*pair_sets) if pair_sets else set()
    jaccard = len(inter) / len(union) if union else 1.0
    rands = []
    for a, b in itertools.combinations(range(len(maps)), 2):
        common = sorted(set(maps[a]) & set(maps[b]))
        agree = total = 0
        for x, y in itertools.combinations(common, 2):
            total += 1
            agree += ((maps[a][x] == maps[a][y]) == (maps[b][x] == maps[b][y]))
        rands.append(agree / total if total else 1.0)
    units = [set(m) for m in maps]
    overlap = len(set.intersection(*units)) / len(set.union(*units)) if units and set.union(*units) else 1.0
    return {"jaccard": jaccard, "rand_index_mean": sum(rands) / len(rands) if rands else 1.0,
            "unit_overlap": overlap, "wave_counts": [len(set(m.values())) for m in maps]}


def unreachable_on_dynamic(out_dir, must_not=None):
    """Programs Claude called unreachable that a computed call could reach."""
    graph = load_json(os.path.join(out_dir, "graph.json"))
    dead = load_json(os.path.join(out_dir, "dead-code.json"))
    if not graph or not dead:
        return None
    unknown = set(graph["analysis"]["dead_code_candidates"]["unknown"]) | set(must_not or [])
    claimed = {x.get("id") for x in dead.get("unreachable", []) if isinstance(x, dict)}
    return sorted(claimed & unknown)


def score_run(run_dir, case):
    out_dir = os.path.join(run_dir, "modernization-assessment")
    res = {"case": case, "run": os.path.basename(run_dir)}
    meta = load_json(os.path.join(run_dir, "run-meta.json")) or {}
    cr = load_json(os.path.join(run_dir, "claude-result.json")) or {}
    usage = load_json(os.path.join(run_dir, "subagent-usage.json")) or {}
    res["harness"] = meta.get("harness", "claude -p")
    res["subagent_usage"] = usage or None
    res["claude"] = {"is_error": cr.get("is_error"), "num_turns": cr.get("num_turns"),
                     "duration_ms": cr.get("duration_ms"), "wall_seconds": meta.get("wall_seconds"),
                     "total_cost_usd": cr.get("total_cost_usd"), "terminal_reason": cr.get("terminal_reason"),
                     "error_text": (cr.get("result") or "")[:200] if cr.get("is_error") else None}
    if not os.path.isdir(out_dir):
        res["ran"] = False
        return res
    res["ran"] = True
    work = meta.get("work") or ""
    roots = [work, out_dir]
    total, bad = citation_stats(out_dir, roots)
    res["citations"] = {"total": total, "unresolved": bad,
                        "resolve_rate": (1 - bad / total) if total else None}
    summary = os.path.join(out_dir, "00-summary.md")
    res["hook_gave_up"] = os.path.exists(summary) and "## Unresolved citations" in open(summary, errors="replace").read()
    res["json"] = json_status(out_dir)
    res["json_all_valid"] = all(v == "valid" for v in res["json"].values())
    must = None
    if case != "carddemo":
        t = load_json(os.path.join(FIXTURES, case, "truth.json")) or {}
        must = t.get("must_not_unreachable")
        dc = t.get("dead_code")
        dead = load_json(os.path.join(out_dir, "dead-code.json"))
        if dc and dead:
            res["dead_code_matches_truth"] = {b: sorted(x.get("id") for x in dead.get(b, []) if isinstance(x, dict))
                                              == sorted(dc[b]) for b in ("unreachable", "dormant", "unknown")}
    res["unreachable_on_dynamic"] = unreachable_on_dynamic(out_dir, must)
    wm = wave_map(out_dir)
    res["wave_count"] = len(set(wm.values())) if wm else None
    return res


def score_all(cases, n_runs=CARDDEMO_RUNS):
    scores = []
    for case in cases:
        names = ["%s-%d" % (case, i) for i in range(1, n_runs + 1)] if case == "carddemo" else [case]
        for name in names:
            rd = os.path.join(RUNS, name)
            if os.path.isdir(rd):
                scores.append(score_run(rd, case))
            else:
                scores.append({"case": case, "run": name, "ran": False, "claude": {}})
    summary = {}
    ran = [s for s in scores if s.get("ran")]
    tot = sum(s["citations"]["total"] for s in ran)
    bad = sum(s["citations"]["unresolved"] for s in ran)
    summary["citations"] = {"total": tot, "unresolved": bad, "resolve_rate": (1 - bad / tot) if tot else None}
    summary["runs_scored"] = len(ran)
    summary["runs_expected"] = len(scores)
    summary["json_all_valid_runs"] = sum(1 for s in ran if s["json_all_valid"])
    summary["unreachable_on_dynamic_total"] = sum(len(s["unreachable_on_dynamic"] or []) for s in ran)
    cd = [s for s in ran if s["case"] == "carddemo"]
    maps = [wave_map(os.path.join(RUNS, s["run"], "modernization-assessment")) for s in cd]
    maps = [m for m in maps if m]
    if len(maps) >= 2:
        c = coassignment(maps)
        c["runs_compared"] = len(maps)
        c["wave_count_identical"] = len(set(c["wave_counts"])) == 1
        summary["carddemo_waves"] = c
    costs = [s["claude"].get("total_cost_usd") for s in ran if s["claude"].get("total_cost_usd") is not None]
    summary["cost_usd_total"] = round(sum(costs), 2) if costs else None
    return {"generated": datetime.date.today().isoformat(), "summary": summary, "runs": scores}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", choices=["all", "carddemo", "fixtures"], default="all")
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--prepare", action="store_true", help="create work folders and print them, run nothing")
    ap.add_argument("--collect", default=None, metavar="HARNESS",
                    help="copy finished work folders into evals/runs and label how they were produced")
    ap.add_argument("--budget-usd", type=float, default=8.0, help="cap per run")
    ap.add_argument("--fixture-budget-usd", type=float, default=2.0)
    ap.add_argument("--model", default=None)
    ap.add_argument("--only", default=None, help="run one case name, for example carddemo or 11-dead-program")
    ap.add_argument("--carddemo-runs", type=int, default=CARDDEMO_RUNS)
    ap.add_argument("--out", default=os.path.join(HERE, "scorecard", "e2e.json"))
    a = ap.parse_args()
    cases = []
    if a.cases in ("all", "carddemo"):
        cases.append("carddemo")
    if a.cases in ("all", "fixtures"):
        cases += NUMBERED
    if a.only:
        cases = [c for c in cases if c == a.only] or [a.only]
    if a.prepare:
        print(json.dumps(prepare_only(cases, a.carddemo_runs), indent=1))
        return 0
    if a.collect:
        collect_only(cases, a.carddemo_runs, a.collect)
    if not a.score_only and not a.collect:
        for case in cases:
            n = range(1, a.carddemo_runs + 1) if case == "carddemo" else [1]
            for i in n:
                print("running %s run %d ..." % (case, i), flush=True)
                rd = run_one(case, i, a.budget_usd if case == "carddemo" else a.fixture_budget_usd, a.model)
                cr = load_json(os.path.join(rd, "claude-result.json")) or {}
                print("   error=%s cost=%s turns=%s" % (cr.get("is_error"), cr.get("total_cost_usd"), cr.get("num_turns")),
                      flush=True)
                if cr.get("is_error") and "authenticate" in (cr.get("result") or ""):
                    print("Claude Code is not signed in. Run `claude auth login`, then rerun this command.")
                    return 3
    result = score_all(cases, a.carddemo_runs)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(result, open(a.out, "w"), indent=1)
    s = result["summary"]
    print("\nruns scored: %d of %d" % (s["runs_scored"], s["runs_expected"]))
    print("citations: %s" % s["citations"])
    print("runs with all JSON valid: %d" % s["json_all_valid_runs"])
    print("unreachable claims on dynamic targets: %d" % s["unreachable_on_dynamic_total"])
    if "carddemo_waves" in s:
        print("carddemo waves:", s["carddemo_waves"])
    print("total cost usd: %s" % s["cost_usd_total"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
