#!/usr/bin/env python3
"""Extractor evals. Python standard library only.

    python3 evals/run_extractor_evals.py [--fixtures-only] [--carddemo PATH]
                                         [--as-of 2026-09-30] [--out evals/scorecard/extractor.json]

Two suites.

Fixtures. Every folder in evals/fixtures holds a small repo and a truth.json
that was written by hand before any extractor code. Every edge kind must score
100% precision and 100% recall, and every field the truth states must match.

CardDemo. The extractor is run on the pinned AWS CardDemo checkout and graded
against evals/carddemo/truth.json, which is a DRAFT. Call, include and data
edges: precision and recall, bar 95%. Contract and temporal edges: recall, bar
75%, reported as is. Scores stay provisional until a domain reviewer confirms
the truth file.

This runner never edits a truth file and never changes a threshold.
"""

import argparse
import collections
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PLUGIN, "skills", "modernization-assessment", "scripts"))
import extract  # noqa: E402
import schema  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
KINDS = ("call", "include", "data", "contract", "temporal")
FIXTURE_BAR = 1.0
CARDDEMO_BAR = {"call": 0.95, "include": 0.95, "data": 0.95}
CARDDEMO_RECALL_BAR = {"contract": 0.75, "temporal": 0.75}


def key(e):
    return (e["src"], e["dst"], e["kind"], e.get("mode"))


def truth_ev(items):
    out = set()
    for s in items:
        f, _, ln = s.rpartition(":")
        out.add((f, int(ln)))
    return out


def graph_ev(e):
    return {(x["file"], x["line"]) for x in e["evidence"]}


def make_git_history(repo, history):
    """Commit each file on its own date so `git log` reports it. history: default plus files."""
    default = history.get("default", "2026-01-01")
    when = history.get("files", {})
    env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    run = lambda *a, **kw: subprocess.run(["git", "-C", repo] + list(a), check=True, capture_output=True,
                                          env=dict(env, **kw.get("env", {})))
    run("init", "-q")
    all_files = sorted(os.path.relpath(os.path.join(dp, f), repo).replace(os.sep, "/")
                       for dp, _, fs in os.walk(repo) if ".git" not in dp for f in fs)
    by_date = collections.defaultdict(list)
    for f in all_files:
        by_date[when.get(f, default)].append(f)
    for d in sorted(by_date):
        run("add", "--", *by_date[d])
        stamp = "%sT12:00:00+0000" % d
        run("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "x",
            env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp})


def evidence_resolves(root, graph):
    """Fraction of evidence entries that point at a real file and a line inside it."""
    cache, ok, total = {}, 0, 0
    seed = [x for w in graph["analysis"].get("wave_seed", {}).get("waves", []) for x in w["evidence"]]
    embedded = [r["evidence"] for r in graph["analysis"].get("embedded_jcl", []) +
                graph["analysis"].get("runtime_named", []) + graph["analysis"].get("utility_writes", [])]
    for x in [x for e in graph["edges"] for x in e["evidence"]] + seed + embedded:
        if True:
            total += 1
            if x["file"] not in cache:
                try:
                    with open(os.path.join(root, x["file"]), "rb") as fh:
                        cache[x["file"]] = fh.read().count(b"\n") + 1
                except OSError:
                    cache[x["file"]] = 0
            if 1 <= x["line"] <= cache[x["file"]]:
                ok += 1
    return ok, total


def compare_fixture(truth, graph):
    problems = []
    t = {key(e): e for e in ({**x, "mode": x.get("mode")} for x in truth["edges"])}
    g = {key(e): e for e in graph["edges"]}
    stats = {k: {"tp": 0, "fp": 0, "fn": 0} for k in KINDS}
    for k, e in t.items():
        if k in g:
            stats[e["kind"]]["tp"] += 1
            ge = g[k]
            if ge["resolved"] != e["resolved"]:
                problems.append("resolved differs on %s: truth %s got %s" % (k, e["resolved"], ge["resolved"]))
            if ge["confidence"] != e["confidence"]:
                problems.append("confidence differs on %s: truth %s got %s" % (k, e["confidence"], ge["confidence"]))
            if truth_ev(e["evidence"]) != graph_ev(ge):
                problems.append("evidence differs on %s: truth %s got %s" %
                                (k, sorted(truth_ev(e["evidence"])), sorted(graph_ev(ge))))
        else:
            stats[e["kind"]]["fn"] += 1
            problems.append("MISSING %s" % (k,))
    for k, ge in g.items():
        if k not in t:
            stats[ge["kind"]]["fp"] += 1
            problems.append("EXTRA %s evidence %s" % (k, sorted(graph_ev(ge))))
    nodes = {n["id"]: n for n in graph["nodes"]}
    for n in truth.get("nodes", []):
        got = nodes.get(n["id"])
        if not got:
            problems.append("node %s missing" % n["id"])
            continue
        for field in ("unit_type", "entry_point", "last_modified"):
            if field in n and got.get(field) != n[field]:
                problems.append("node %s %s: truth %r got %r" % (n["id"], field, n[field], got.get(field)))
    if "dead_code" in truth:
        got = graph["analysis"]["dead_code_candidates"]
        for b in ("unreachable", "dormant", "unknown"):
            if sorted(truth["dead_code"][b]) != sorted(got[b]):
                problems.append("dead code %s: truth %s got %s" % (b, sorted(truth["dead_code"][b]), sorted(got[b])))
    if "wave_seed" in truth:
        got = graph["analysis"]["wave_seed"]
        want_w = [(w["family"], sorted(w["units"])) for w in truth["wave_seed"]["waves"]]
        have_w = [(w["family"], sorted(w["units"])) for w in got["waves"]]
        if want_w != have_w:
            problems.append("wave seed: truth %s got %s" % (want_w, have_w))
        want_u = sorted(x["id"] for x in truth["wave_seed"]["unassigned"])
        have_u = sorted(x["id"] for x in got["unassigned"])
        if want_u != have_u:
            problems.append("wave seed unassigned: truth %s got %s" % (want_u, have_u))
        if any(not w["evidence"] for w in got["waves"]):
            problems.append("wave seed: a wave has no evidence")
    if "runtime_named" in truth:
        want_r = sorted((x["src"], x["dst"], x["file"], x["line"]) for x in truth["runtime_named"])
        have_r = sorted((x["src"], x["dst"], x["evidence"]["file"], x["evidence"]["line"])
                        for x in graph["analysis"]["runtime_named"])
        if want_r != have_r:
            problems.append("runtime named: truth %s got %s" % (want_r, have_r))
    if "utility_writes" in truth:
        want_w = sorted((x["src"], x["dst"], x["verb"], x["file"], x["line"]) for x in truth["utility_writes"])
        have_w = sorted((x["src"], x["dst"], x["verb"], x["evidence"]["file"], x["evidence"]["line"])
                        for x in graph["analysis"]["utility_writes"])
        if want_w != have_w:
            problems.append("utility writes: truth %s got %s" % (want_w, have_w))
    if "embedded_jcl" in truth:
        want_e = sorted((x["src"], x["dst"], x["file"], x["line"]) for x in truth["embedded_jcl"])
        have_e = sorted((x["src"], x["dst"], x["evidence"]["file"], x["evidence"]["line"])
                        for x in graph["analysis"]["embedded_jcl"])
        if want_e != have_e:
            problems.append("embedded jcl: truth %s got %s" % (want_e, have_e))
    for want in truth.get("unparsed", []):
        if not any(want in "%s: %s" % (u["file"], u["reason"]) for u in graph["unparsed"]):
            problems.append("expected an unparsed entry containing %r" % want)
    for bad in truth.get("must_not_unreachable", []):
        if bad in graph["analysis"]["dead_code_candidates"]["unreachable"]:
            problems.append("%s was called unreachable" % bad)
    return stats, problems


def run_fixtures(as_of):
    results, total = {}, {k: {"tp": 0, "fp": 0, "fn": 0} for k in KINDS}
    ev_ok = ev_all = 0
    for case in sorted(os.listdir(FIXTURES)):
        cdir = os.path.join(FIXTURES, case)
        if not os.path.isfile(os.path.join(cdir, "truth.json")):
            continue
        truth = json.load(open(os.path.join(cdir, "truth.json")))
        with tempfile.TemporaryDirectory() as tmp:
            repo = os.path.join(tmp, "repo")
            shutil.copytree(os.path.join(cdir, "repo"), repo)
            hist_path = os.path.join(cdir, "repo", "history.json")
            hist = json.load(open(hist_path)) if os.path.exists(hist_path) else None
            if hist:
                os.remove(os.path.join(repo, "history.json"))
                make_git_history(repo, hist)
            when = datetime.date.fromisoformat(truth.get("as_of", as_of))
            graph = extract.build(repo, when, 5, use_git=bool(hist))
            errs = schema.validate("graph", graph)
            ok, n = evidence_resolves(repo, graph)
            ev_ok, ev_all = ev_ok + ok, ev_all + n
        stats, problems = compare_fixture(truth, graph)
        if errs:
            problems += ["SCHEMA " + e for e in errs[:5]]
        for k in KINDS:
            for f in ("tp", "fp", "fn"):
                total[k][f] += stats[k][f]
        results[case] = {"pass": not problems, "problems": problems, "edges": len(truth["edges"])}
    return results, total, (ev_ok, ev_all)


def prf(s):
    p = s["tp"] / (s["tp"] + s["fp"]) if (s["tp"] + s["fp"]) else 1.0
    r = s["tp"] / (s["tp"] + s["fn"]) if (s["tp"] + s["fn"]) else 1.0
    return p, r


def _file_in_scope(f, scope):
    return any(f == d or f.startswith(d + "/") for d in scope)


def _owner_path(nid, paths):
    """File that owns a node. A JCL step belongs to the job that runs it, even when the step
    text comes from a shared PROC in another folder."""
    if nid.startswith("step:"):
        job = "job:" + nid[5:].split(".")[0].split("#")[0]
        return paths.get(job) or paths.get(nid)
    return paths.get(nid)


def in_scope(edge, scope, paths):
    """Graded only when every evidence file and the owning file of the source are in graded folders."""
    if not edge["evidence"] or not all(_file_in_scope(x["file"], scope) for x in edge["evidence"]):
        return False
    owner = _owner_path(edge["src"], paths)
    return owner is None or _file_in_scope(owner, scope)


def run_carddemo(path, as_of):
    truth = json.load(open(os.path.join(HERE, "carddemo", "truth.json")))
    scope = truth["scope_dirs"]
    t0 = time.time()
    graph = extract.build(path, as_of, 5, True)
    seconds = time.time() - t0
    errs = schema.validate("graph", graph)
    t = {}
    for e in truth["edges"]:
        t[(e["src"], e["dst"], e["kind"], e.get("mode"))] = e
    paths = {n["id"]: n.get("path") for n in graph["nodes"]}
    g = {}
    for e in graph["edges"]:
        if in_scope(e, scope, paths):
            g[key(e)] = e
    stats = {k: {"tp": 0, "fp": 0, "fn": 0} for k in KINDS}
    diffs = {k: {"missing": [], "extra": [], "confidence": []} for k in KINDS}
    ev_agree = collections.Counter()
    for k, e in t.items():
        if k in g:
            stats[k[2]]["tp"] += 1
            ev_agree[k[2] + ":total"] += 1
            if truth_ev(e["evidence"]) & graph_ev(g[k]):
                ev_agree[k[2] + ":overlap"] += 1
            if k[2] == "contract" and e.get("confidence") != g[k]["confidence"]:
                diffs["contract"]["confidence"].append([list(k[:2]), e.get("confidence"), g[k]["confidence"]])
        else:
            stats[k[2]]["fn"] += 1
            diffs[k[2]]["missing"].append(list(k))
    for k in g:
        if k not in t:
            stats[k[2]]["fp"] += 1
            diffs[k[2]]["extra"].append(list(k))
    entry_t = sorted(x for x in truth["entry_points"] if not x.startswith("job:"))
    graded = {n["id"] for n in graph["nodes"]
              if n.get("entry_evidence") and all(_file_in_scope(e["file"], scope) for e in n["entry_evidence"])}
    entry_g = sorted(x[4:] if x.startswith("ext:") else x for x in graded)
    ok, n = evidence_resolves(path, graph)
    unparsed_files = {u["file"] for u in graph["unparsed"]}
    return {
        "seconds": round(seconds, 1), "stats": stats, "diffs": diffs, "schema_errors": errs[:10],
        "truth_edges": len(t), "graph_edges_in_scope": len(g), "graph_edges_total": len(graph["edges"]),
        "entry_programs": {"truth": entry_t, "graph": entry_g, "match": entry_t == entry_g},
        "ca7_reported_unparsed": "app/scheduler/CardDemo.ca7" in unparsed_files,
        "evidence_resolves": [ok, n],
        "evidence_overlap_with_truth": dict(ev_agree),
        "unresolved_dynamic": len(graph["analysis"]["unresolved_dynamic"]),
        "dead_code_counts": {k: len(v) for k, v in graph["analysis"]["dead_code_candidates"].items()},
        "unparsed": graph["unparsed"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures-only", action="store_true")
    ap.add_argument("--carddemo", default=os.path.normpath(os.path.join(PLUGIN, "..", "bench", "carddemo")))
    ap.add_argument("--as-of", default="2026-09-30")
    ap.add_argument("--out", default=os.path.join(HERE, "scorecard", "extractor.json"))
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    as_of = args.as_of

    results, total, (ev_ok, ev_all) = run_fixtures(as_of)
    print("FIXTURES")
    for case, r in results.items():
        print("  %-30s %s  (%d edges)" % (case, "PASS" if r["pass"] else "FAIL", r["edges"]))
        if not r["pass"]:
            for p in r["problems"][: 12 if not args.verbose else 999]:
                print("      ", p)
    fixture_ok = True
    print("  per kind (all fixtures):")
    for k in KINDS:
        p, r = prf(total[k])
        good = p >= FIXTURE_BAR and r >= FIXTURE_BAR
        fixture_ok &= good
        print("    %-9s precision %.3f  recall %.3f  tp %d fp %d fn %d  %s" %
              (k, p, r, total[k]["tp"], total[k]["fp"], total[k]["fn"], "ok" if good else "BELOW BAR"))
    all_pass = all(r["pass"] for r in results.values())
    print("  fixtures passing: %d of %d" % (sum(r["pass"] for r in results.values()), len(results)))
    print("  evidence lines that resolve: %d of %d" % (ev_ok, ev_all))
    out = {"as_of": as_of, "fixtures": {"cases": results, "per_kind": total,
                                        "all_pass": all_pass, "evidence_resolves": [ev_ok, ev_all]}}

    if not args.fixtures_only:
        if not os.path.isdir(args.carddemo):
            print("CardDemo checkout not found at %s" % args.carddemo)
            return 2
        cd = run_carddemo(args.carddemo, datetime.date.fromisoformat(as_of))
        out["carddemo"] = cd
        print("CARDDEMO (draft truth, provisional)  %.1fs" % cd["seconds"])
        for k in KINDS:
            p, r = prf(cd["stats"][k])
            bar = CARDDEMO_BAR.get(k)
            rbar = CARDDEMO_RECALL_BAR.get(k)
            note = ""
            if bar:
                note = "ok" if p >= bar and r >= bar else "BELOW %.0f%% BAR" % (bar * 100)
            elif rbar:
                note = "ok" if r >= rbar else "BELOW %.0f%% RECALL BAR" % (rbar * 100)
            s = cd["stats"][k]
            print("    %-9s precision %.3f  recall %.3f  tp %d fp %d fn %d  %s" %
                  (k, p, r, s["tp"], s["fp"], s["fn"], note))
        print("  entry programs match: %s   CA-7 reported: %s   evidence resolves: %d/%d   dynamic calls: %d" %
              (cd["entry_programs"]["match"], cd["ca7_reported_unparsed"],
               cd["evidence_resolves"][0], cd["evidence_resolves"][1], cd["unresolved_dynamic"]))
        eo = cd["evidence_overlap_with_truth"]
        print("  evidence lines overlap truth on matched edges:",
              ", ".join("%s %d/%d" % (k, eo.get(k + ":overlap", 0), eo.get(k + ":total", 0)) for k in KINDS))
        print("  dead code candidates (not graded):", cd["dead_code_counts"])
        if cd["schema_errors"]:
            print("  SCHEMA ERRORS", cd["schema_errors"])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    return 0 if (all_pass and fixture_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
