"""Merge the independent CardDemo labeler files into evals/carddemo/truth.json.

This file never imports or runs an extractor. It only reads the labeler
output in labels/ and the decisions in adjudication.json.

    merge_labels.py compare   list every disagreement between paired passes
                              and every evidence line that does not match the source
    merge_labels.py build     write truth.json from agreed labels, adjudicated
                              disagreements, and the derived contract edges

Python standard library only.
"""

import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = os.path.join(HERE, "labels")
BENCH = os.environ.get("CARDDEMO_ROOT") or os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "bench", "carddemo"))
COMMIT = "59cc6c2fd7ebd7ef7925cad552a01a4b8b6e4d5e"
PAIRED = ("B", "O1", "O2")
SINGLE = ("J1", "J2", "X")


def load(partition, pas):
    p = os.path.join(LABELS, "%s-%s.json" % (partition, pas))
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def key(e):
    return (e["src"], e["dst"], e["kind"], e.get("mode"))


def ev_set(e):
    return {(x["file"], x["line"]) for x in e.get("evidence", [])}


def index(edges):
    out = {}
    for e in edges:
        k = key(e)
        if k in out:
            out[k]["evidence"] = out[k]["evidence"] + e.get("evidence", [])
            if e.get("layout_copybooks"):
                out[k]["layout_copybooks"] = sorted(
                    set(out[k].get("layout_copybooks", [])) | set(e["layout_copybooks"]))
        else:
            out[k] = json.loads(json.dumps(e))
    return out


_cache = {}


def source_lines(rel):
    if rel not in _cache:
        path = os.path.join(BENCH, rel)
        try:
            with open(path, encoding="latin-1") as fh:
                _cache[rel] = fh.read().splitlines()
        except OSError:
            _cache[rel] = None
    return _cache[rel]


def check_evidence(edge):
    """Return a list of problems with an edge's evidence lines."""
    problems = []
    for x in edge.get("evidence", []):
        lines = source_lines(x["file"])
        if lines is None:
            problems.append("no such file %s" % x["file"])
        elif not 1 <= x["line"] <= len(lines):
            problems.append("%s:%d is out of range (%d lines)" % (x["file"], x["line"], len(lines)))
    return problems


def cmd_compare():
    worklist = []
    for part in PAIRED:
        a, b = index(load(part, "A")["edges"]), index(load(part, "B")["edges"])
        both = set(a) & set(b)
        print("== %s: %d in both, %d only in A, %d only in B" %
              (part, len(both), len(set(a) - set(b)), len(set(b) - set(a))))
        for tag, side, other in (("A", a, b), ("B", b, a)):
            for k in sorted(set(side) - set(other), key=str):
                e = side[k]
                print("   only %s: %-9s %s -> %s %s  ev=%s" % (
                    tag, k[2], k[0], k[1], k[3] or "",
                    sorted(ev_set(e))[:3]))
                worklist.append({"partition": part, "only_in": tag, "key": list(k),
                                 "evidence": [list(x) for x in sorted(ev_set(e))],
                                 "note": e.get("note", "")})
        for k in sorted(both, key=str):
            la = sorted(a[k].get("layout_copybooks", []))
            lb = sorted(b[k].get("layout_copybooks", []))
            if la != lb:
                print("   layout differs: %s -> %s: A=%s B=%s" % (k[0], k[1], la, lb))
                worklist.append({"partition": part, "only_in": "layout", "key": list(k),
                                 "A": la, "B": lb})
    print()
    bad = 0
    for part, pas in [(p, x) for p in PAIRED for x in "AB"] + [(p, "A") for p in SINGLE]:
        for e in load(part, pas)["edges"]:
            for prob in check_evidence(e):
                bad += 1
                print("BAD EVIDENCE %s-%s: %s -> %s: %s" % (part, pas, e["src"], e["dst"], prob))
    print("evidence problems: %d" % bad)
    with open(os.path.join(HERE, "adjudication-worklist.json"), "w") as fh:
        json.dump(worklist, fh, indent=2)
        fh.write("\n")
    print("worklist: %d items -> adjudication-worklist.json" % len(worklist))
    return 0


def derive_contract(data_edges):
    by_ds = collections.defaultdict(lambda: {"w": {}, "r": {}})
    for e in data_edges:
        if e["dst"].startswith("ds:dd:") or e["dst"].startswith("?dynamic:"):
            continue
        if e["src"].startswith("step:"):
            continue
        slot = by_ds[e["dst"]]
        if e["mode"] in ("write", "read_write"):
            slot["w"][e["src"]] = e
        if e["mode"] in ("read", "read_write"):
            slot["r"][e["src"]] = e
    out = []
    for ds, slot in sorted(by_ds.items()):
        for w, we in sorted(slot["w"].items()):
            for r, re_ in sorted(slot["r"].items()):
                if w == r:
                    continue
                lw = set(we.get("layout_copybooks", []))
                lr = set(re_.get("layout_copybooks", []))
                conf = "high" if lw and lr and (lw & lr) else "medium"
                ev = sorted(ev_set(we) | ev_set(re_))
                out.append({"src": w, "dst": r, "kind": "contract", "mode": None,
                            "resolved": True, "confidence": conf,
                            "evidence": [{"file": f, "line": l} for f, l in ev],
                            "note": "dataset %s; layouts %s vs %s" % (ds, sorted(lw), sorted(lr)),
                            "derived_from": ds})
    return out


def cmd_build():
    adj_path = os.path.join(HERE, "adjudication.json")
    adj = json.load(open(adj_path)) if os.path.exists(adj_path) else {"decisions": []}
    decided = {(d["partition"], tuple(d["key"])): d for d in adj["decisions"]}
    layout_pick = {(d["partition"], tuple(d["key"])): d for d in adj.get("layout", [])}

    edges = []
    provenance = collections.Counter()
    for part in PAIRED:
        a, b = index(load(part, "A")["edges"]), index(load(part, "B")["edges"])
        for k in sorted(set(a) | set(b), key=str):
            if k in a and k in b:
                e = json.loads(json.dumps(a[k]))
                e["evidence"] = [{"file": f, "line": l} for f, l in sorted(ev_set(a[k]) | ev_set(b[k]))]
                pick = layout_pick.get((part, k))
                if pick:
                    e["layout_copybooks"] = pick["use"]
                else:
                    e["layout_copybooks"] = sorted(set(a[k].get("layout_copybooks", []))
                                                   | set(b[k].get("layout_copybooks", [])))
                e["labeled_by"] = "%s: A+B agree" % part
                provenance["agreed"] += 1
                edges.append(e)
            else:
                d = decided.get((part, k))
                if d is None:
                    raise SystemExit("UNADJUDICATED %s %s" % (part, k))
                if d["decision"] == "include":
                    src = a.get(k) or b.get(k)
                    e = json.loads(json.dumps(src))
                    if d.get("evidence"):
                        e["evidence"] = [{"file": f, "line": l} for f, l in d["evidence"]]
                    e["labeled_by"] = "%s: adjudicated include (%s)" % (part, d["reason"])
                    provenance["adjudicated_include"] += 1
                    edges.append(e)
                else:
                    provenance["adjudicated_exclude"] += 1
    nodes, entry_points, unparsed, notes = {}, [], [], []
    for part in SINGLE:
        lab = load(part, "A")
        for e in lab["edges"]:
            e = json.loads(json.dumps(e))
            e["labeled_by"] = "%s: single pass" % part
            provenance["single_pass"] += 1
            edges.append(e)
        for n in lab.get("nodes", []):
            nodes[n["id"]] = n
        entry_points += lab.get("entry_points", [])
        unparsed += lab.get("unparsed", [])
        notes += ["%s: %s" % (part, n) for n in lab.get("notes", [])]
    for part in PAIRED:
        for pid, meta in load(part, "A")["programs"].items():
            nodes.setdefault(pid, {"id": pid, "has_exec_cics": meta.get("has_exec_cics")})

    edges = list(index(edges).values())
    data = [e for e in edges if e["kind"] == "data"]
    contracts = derive_contract(data)
    for c in contracts:
        c["labeled_by"] = "derived by rule from data edges"
    edges += contracts
    merged = {}
    for e in edges:
        k = key(e)
        if k in merged:
            merged[k]["evidence"] += e["evidence"]
            merged[k]["note"] = (merged[k].get("note", "") + "; " + e.get("note", "")).strip("; ")
            if e.get("confidence") == "high":
                merged[k]["confidence"] = "high"
        else:
            merged[k] = e
    edges = list(merged.values())

    out_edges = []
    for e in sorted(edges, key=lambda e: (e["kind"], e["src"], e["dst"], str(e.get("mode")))):
        out_edges.append({
            "src": e["src"], "dst": e["dst"], "kind": e["kind"], "mode": e.get("mode"),
            "resolved": e.get("resolved", True),
            "confidence": e.get("confidence"),
            "layout_copybooks": e.get("layout_copybooks"),
            "evidence": ["%s:%d" % (x["file"], x["line"]) for x in
                         sorted(e["evidence"], key=lambda x: (x["file"], x["line"]))],
            "status": "draft",
            "labeled_by": e.get("labeled_by", ""),
        })
        if out_edges[-1]["confidence"] is None:
            del out_edges[-1]["confidence"]
        if out_edges[-1]["layout_copybooks"] is None:
            del out_edges[-1]["layout_copybooks"]
    entry = sorted({p["id"] if isinstance(p, dict) else p for p in entry_points})
    truth = {
        "case": "carddemo",
        "status": "DRAFT. Labeled by independent subagents from the source. "
                  "Not confirmed by a domain reviewer. Scores against this file are provisional.",
        "source": {"repo": "aws-samples/aws-mainframe-modernization-carddemo", "commit": COMMIT},
        "scope_dirs": ["app/cbl", "app/cpy", "app/cpy-bms", "app/bms", "app/jcl", "app/proc",
                       "app/csd", "app/scheduler", "scripts"],
        "provenance": dict(provenance),
        "entry_points": entry,
        "unparsed": unparsed,
        "edges": out_edges,
        "notes": notes,
    }
    with open(os.path.join(HERE, "truth.json"), "w") as fh:
        json.dump(truth, fh, indent=1)
        fh.write("\n")
    kinds = collections.Counter(e["kind"] for e in out_edges)
    print("truth.json: %d edges %s, %d entry programs, provenance %s" %
          (len(out_edges), dict(kinds), len(entry), dict(provenance)))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "compare":
        sys.exit(cmd_compare())
    if len(sys.argv) == 2 and sys.argv[1] == "build":
        sys.exit(cmd_build())
    print(__doc__)
    sys.exit(2)
