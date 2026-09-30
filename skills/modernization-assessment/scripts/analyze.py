#!/usr/bin/env python3
"""Graph facts computed from nodes and edges. Python standard library only.

Everything here is arithmetic on the graph. Nothing is a judgment call.

Dead code, three buckets, never two
-----------------------------------
reachable   walk call and include edges from every entry point (CSD
            transaction programs, JCL jobs, scheduler jobs, shell wrappers).
unknown     not reached, AND some reachable code makes a call whose target is
            computed. Any program could be that target, so it is not safe to
            call it dead. Copybooks and procs used only by such programs are
            unknown too.
unreachable not reached, and no reachable code makes a computed call.
dormant     reached, but the last change is older than the dormancy window.
            Propose instrumentation, not deletion.
If the tree has no entry point at all, nothing can be called unreachable.
Everything is unknown and a warning says why.
"""

import collections
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema  # noqa: E402

WALK_KINDS = ("call", "include")
BUCKET_TYPES = set(schema.PROGRAM_TYPES) | {"copybook", "proc"}


def _years_ago(d, years):
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        return d.replace(year=d.year - years, day=28)


def _tarjan(nodes, succ):
    index, low, on, stack, out = {}, {}, set(), [], []
    counter = [0]
    for root in nodes:
        if root in index:
            continue
        work = [(root, iter(succ.get(root, ())))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on.add(root)
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on.add(w)
                    work.append((w, iter(succ.get(w, ()))))
                    advanced = True
                    break
                if w in on:
                    low[v] = min(low[v], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                out.append(sorted(comp))
    return out


def _articulation(adj):
    """Iterative articulation points of an undirected graph."""
    disc, low, parent, out = {}, {}, {}, set()
    t = 0
    for root in sorted(adj):
        if root in disc:
            continue
        disc[root] = low[root] = t
        t += 1
        parent[root] = None
        children = 0
        work = [(root, iter(sorted(adj[root])))]
        while work:
            v, it = work[-1]
            moved = False
            for w in it:
                if w not in disc:
                    parent[w] = v
                    disc[w] = low[w] = t
                    t += 1
                    if v == root:
                        children += 1
                    work.append((w, iter(sorted(adj[w]))))
                    moved = True
                    break
                if w != parent[v]:
                    low[v] = min(low[v], disc[w])
            if moved:
                continue
            work.pop()
            p = parent[v]
            if p is not None:
                low[p] = min(low[p], low[v])
                if parent[p] is not None and low[v] >= disc[p]:
                    out.add(p)
        if children > 1:
            out.add(root)
    return sorted(out)


def _p90(values):
    vals = sorted(values)
    return vals[max(0, int(len(vals) * 0.9 + 0.999999) - 1)] if vals else 0


def analyze(nodes, edges, as_of, dormant_years=5):
    by_id = {n["id"]: n for n in nodes}
    succ = collections.defaultdict(list)
    for e in edges:
        if e["kind"] in WALK_KINDS:
            succ[e["src"]].append(e["dst"])

    entries = sorted(n["id"] for n in nodes if n.get("entry_point"))
    reach, work = set(entries), list(entries)
    while work:
        v = work.pop()
        for w in succ.get(v, ()):
            if w not in reach:
                reach.add(w)
                work.append(w)

    dynamic = []
    for e in edges:
        if e["kind"] == "call" and schema.is_dynamic(e["dst"]):
            dynamic.append({"src": e["src"], "dst": e["dst"], "evidence": e["evidence"][0]})
    reachable_dynamic = [d for d in dynamic if d["src"] in reach]

    warnings = []
    cands = [n["id"] for n in nodes if n["unit_type"] in BUCKET_TYPES]
    unreachable, unknown, dormant, reasons = [], [], [], {}
    threshold = _years_ago(as_of, dormant_years)
    if not entries:
        warnings.append("No entry points were found (no CSD transaction, JCL job, scheduler job or "
                        "wrapper). Nothing can be proven unreachable, so every candidate is unknown.")
        unknown = sorted(cands)
        for c in unknown:
            reasons[c] = "no entry points in the tree"
    else:
        unrea = [c for c in cands if c not in reach]
        if reachable_dynamic:
            progs = {c for c in unrea if by_id[c]["unit_type"] in schema.PROGRAM_TYPES}
            seen, work = set(progs), list(progs)
            while work:
                v = work.pop()
                for w in succ.get(v, ()):
                    if w not in reach and w in by_id and by_id[w]["unit_type"] in BUCKET_TYPES and w not in seen:
                        seen.add(w)
                        work.append(w)
            unknown = sorted(seen)
            unreachable = sorted(set(unrea) - seen)
            first = reachable_dynamic[0]
            for c in unknown:
                reasons[c] = ("not reached by any static edge, and %d reachable computed call(s) could "
                              "target it, for example at %s:%d" %
                              (len(reachable_dynamic), first["evidence"]["file"], first["evidence"]["line"]))
        else:
            unreachable = sorted(unrea)
        for c in unreachable:
            reasons[c] = "no static path from any entry point and no reachable computed call in the tree"
        for c in sorted(cands):
            if c in reach and by_id[c]["unit_type"] in set(schema.PROGRAM_TYPES) | {"copybook"}:
                lm = by_id[c].get("last_modified")
                if lm:
                    try:
                        d = datetime.date.fromisoformat(lm[:10])
                    except ValueError:
                        continue
                    if d < threshold:
                        dormant.append(c)
                        reasons[c] = "reachable, last modified %s, older than %d years" % (lm[:10], dormant_years)

    progs = sorted(n["id"] for n in nodes if n["unit_type"] in schema.PROGRAM_TYPES)
    pset = set(progs)
    fan_out, fan_in = collections.defaultdict(set), collections.defaultdict(set)
    call_succ = collections.defaultdict(list)
    for e in edges:
        if e["kind"] == "call" and e["src"] in pset and e["dst"] in pset:
            call_succ[e["src"]].append(e["dst"])
            if e["src"] != e["dst"]:
                fan_out[e["src"]].add(e["dst"])
                fan_in[e["dst"]].add(e["src"])
    fo = {p: len(fan_out[p]) for p in progs}
    fi = {p: len(fan_in[p]) for p in progs}
    god = []
    if len(progs) >= 10:
        ti, to = _p90(fi.values()), _p90(fo.values())
        god = [p for p in progs if ti > 0 and to > 0 and fi[p] >= ti and fo[p] >= to]

    sccs = [c for c in _tarjan(progs, call_succ) if len(c) > 1]
    selfrec = sorted(p for p in progs if p in call_succ.get(p, ()))

    adj = collections.defaultdict(set)
    ds_ids = {n["id"] for n in nodes if n["unit_type"] == "dataset"}
    for e in edges:
        if e["kind"] == "call" and e["src"] in pset and e["dst"] in pset and e["src"] != e["dst"]:
            adj[e["src"]].add(e["dst"])
            adj[e["dst"]].add(e["src"])
        elif e["kind"] == "data" and e["src"] in pset and e["dst"] in ds_ids and not e["dst"].startswith("ds:dd:"):
            adj[e["src"]].add(e["dst"])
            adj[e["dst"]].add(e["src"])
    arts = _articulation(adj) if len(adj) > 2 else []

    hubs = collections.defaultdict(lambda: {"writers": set(), "readers": set()})
    for e in edges:
        if e["kind"] == "data" and e["dst"] in ds_ids:
            if e["mode"] in ("write", "read_write"):
                hubs[e["dst"]]["writers"].add(e["src"])
            if e["mode"] in ("read", "read_write"):
                hubs[e["dst"]]["readers"].add(e["src"])
    data_hubs = sorted(({"id": k, "writers": len(v["writers"]), "readers": len(v["readers"])}
                        for k, v in hubs.items()), key=lambda h: (-(h["writers"] + h["readers"]), h["id"]))[:15]

    sched = [n["id"] for n in nodes if n["unit_type"] == "scheduler_job"]
    unscheduled = []
    if sched:
        called = {e["dst"] for e in edges if e["kind"] == "call" and e["src"].startswith("sch:")}
        unscheduled = sorted(n["id"] for n in nodes if n["unit_type"] == "jcl_job" and n["id"] not in called
                             and n.get("path"))

    kinds = collections.Counter(e["kind"] for e in edges)
    types = collections.Counter(n["unit_type"] for n in nodes)
    return {
        "as_of": as_of.isoformat(),
        "dormant_years": dormant_years,
        "entry_points": entries,
        "reachable_count": len(reach),
        "dead_code_candidates": {"unreachable": unreachable, "dormant": dormant, "unknown": unknown},
        "dead_code_reasons": reasons,
        "unresolved_dynamic": dynamic,
        "fan_in": {k: v for k, v in fi.items() if v},
        "fan_out": {k: v for k, v in fo.items() if v},
        "god_modules": god,
        "sccs": sccs,
        "self_recursive": selfrec,
        "articulation_points": arts,
        "articulation_basis": "call edges between programs plus data edges from programs to datasets",
        "data_hubs": data_hubs,
        "unscheduled_jobs": unscheduled,
        "edge_counts": dict(sorted(kinds.items())),
        "node_counts": dict(sorted(types.items())),
        "warnings": warnings,
    }
