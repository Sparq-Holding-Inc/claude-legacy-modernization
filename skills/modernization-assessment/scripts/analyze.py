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
JCL text inside a COBOL literal (an internal reader submit) names a proc or
program the graph has no edge to. Such a target, and the programs its proc
runs, are unknown, not unreachable.

Wave seed
---------
A first cut of the migration waves, from facts alone. Every entry point (a JCL
job or an online transaction) is put in one family, by four tests in order:
it touches DB2, IMS or MQ; it writes a dataset that a different entry point
also uses (a utility step whose mode is only inferred from DISP counts as a
possible write); it is online or batch; it runs an application program or none.
A batch job with no application program that touches shared data is its own
family, because its writes are guesses.
The families have a fixed order. A unit reached from several entry points moves
with the earliest family that uses it. A scheduler job moves with the last
family among the JCL jobs it runs. Programs in one call cycle are reached from
the same entry points, so a cycle always moves whole. Nothing here judges risk.
A family is then cut into groups. Two entry points in the family are bound together when both write the same
dataset, or when they run the same application program. A reader of a dataset another entry point writes is
ordered after the writer, but is not bound to it. Entry points bound to another entry point form a coupled
group and keep one wave. Entry points bound to none form one independent group. The independent group goes
first, then the coupled groups from the smallest up. A family with no independent group and one coupled group
stays one wave. The cut is only a first pass: a coupled group can still be too big to ship as one wave.
"""

import collections
import datetime
import os
import re
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


FAMILIES = (
    ("batch-utility", "Batch jobs that run no application program and touch no dataset another entry point uses"),
    ("batch-readonly", "Batch jobs that run application programs and write nothing another entry point uses"),
    ("online-readonly", "Online transactions that write nothing another entry point uses"),
    ("batch-data-jobs", "Batch jobs that read a dataset another entry point uses through a utility. "
                        "The mode comes from DISP alone, so they may write it"),
    ("batch-writers", "Batch jobs that write a dataset another entry point also uses"),
    ("online-writers", "Online transactions that write a dataset another entry point also uses"),
    ("subsystem", "Entry points that touch DB2, IMS or MQ"),
)
SUBSYSTEM_EXT = re.compile(r"^ext:(MQ[A-Z]{2,}|CBLTDLI|AIBTDLI|DFSRRC00|DSNTEP2|DSNTEP4|DSNTIAD|DSNTIAUL|DSNUTILB|DSN)$")
MOVABLE = set(schema.PROGRAM_TYPES) | {"jcl_job", "proc", "scheduler_job"}


def _spread(seeds, succ, by_id, reach, extra):
    """Candidates that the seeds lead to. Walks through any node, because a step joins a proc to its program."""
    origin = {s: s for s in seeds}
    work = list(seeds)
    while work:
        v = work.pop()
        for w in list(succ.get(v, ())) + list(extra.get(v, ())):
            if w in origin or w in reach or w not in by_id:
                continue
            origin[w] = origin[v]
            work.append(w)
    return {k: v for k, v in origin.items() if by_id[k]["unit_type"] in BUCKET_TYPES}


def wave_seed(nodes, edges, entries, unknown, unreachable, reasons=None, dynamic=None, runtime_named=None,
              utility_writes=None, embedded=None, proc_programs=None):
    by_id = {n["id"]: n for n in nodes}
    succ, edges_from, sched_of = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for e in edges:
        if e["kind"] in WALK_KINDS:
            succ[e["src"]].append(e["dst"])
        if e["kind"] in ("data", "call"):
            edges_from[e["src"]].append(e)
        if e["kind"] == "call" and e["src"].startswith("sch:") and e["dst"].startswith("job:"):
            sched_of[e["src"]].append(e["dst"])
    rt_from, uw_from = collections.defaultdict(list), collections.defaultdict(list)
    for r in runtime_named or []:
        rt_from[r["src"]].append(r)
        if r["dst"] in by_id:
            succ[r["src"]].append(r["dst"])
    for w in utility_writes or []:
        uw_from[w["src"]].append(w)
    submitters = {r["src"] for r in embedded or []}
    for r in embedded or []:
        succ[r["src"]].append(r["dst"])
    for proc, progs in (proc_programs or {}).items():
        succ[proc].extend(progs)
    roots = sorted(i for i in entries if i in by_id and i not in sched_of
                   and (by_id[i]["unit_type"] == "jcl_job" or by_id[i]["unit_type"] in schema.PROGRAM_TYPES))
    owned, roots_of = {}, collections.defaultdict(set)
    for r in roots:
        seen, work = {r}, [r]
        while work:
            v = work.pop()
            for w in succ.get(v, ()):
                if w not in seen:
                    seen.add(w)
                    work.append(w)
        owned[r] = seen
        for v in seen:
            roots_of[v].add(r)
    touch = collections.defaultdict(set)
    for e in edges:
        if e["kind"] == "data":
            touch[e["dst"]] |= roots_of.get(e["src"], set())
    for w in utility_writes or []:
        touch[w["dst"]] |= roots_of.get(w["src"], set())

    wrote, used = collections.defaultdict(set), collections.defaultdict(set)
    for e in edges:
        if e["kind"] == "data" and not e["dst"].startswith("ds:dd:"):
            for r in roots_of.get(e["src"], ()):
                used[r].add(e["dst"])
                if e.get("mode") in ("write", "read_write"):
                    wrote[r].add(e["dst"])
    for w in utility_writes or []:
        for r in roots_of.get(w["src"], ()):
            used[r].add(w["dst"])
            wrote[r].add(w["dst"])

    def ev_of(e):
        return dict(e["evidence"][0])

    def classify(r):
        n = by_id[r]
        online = n["unit_type"] == "online_txn" and r not in submitters
        sub = shared = guess = None
        has_prog = False
        for v in sorted(owned[r]):
            if v in by_id and by_id[v]["unit_type"] in schema.PROGRAM_TYPES:
                has_prog = True
            for e in edges_from.get(v, ()):
                if e["kind"] == "data" and e["dst"].startswith("ds:db2:") or \
                        e["kind"] == "call" and SUBSYSTEM_EXT.match(e["dst"]):
                    sub = sub or ev_of(e)
                elif e["kind"] == "data" and not e["dst"].startswith("ds:dd:") and len(touch[e["dst"]]) > 1:
                    if e.get("mode") in ("write", "read_write"):
                        shared = shared or ev_of(e)
                    elif "inferred from DISP" in (e.get("note") or ""):
                        guess = guess or ev_of(e)
            for w in uw_from.get(v, ()):
                if len(touch[w["dst"]]) > 1:
                    shared = shared or dict(w["evidence"])
            for q in rt_from.get(v, ()):
                if SUBSYSTEM_EXT.match(q["dst"]):
                    sub = sub or dict(q["evidence"])
        if sub:
            return "subsystem", sub
        if shared:
            return ("online-writers" if online else "batch-writers"), shared
        if guess and not online:
            return "batch-data-jobs", guess
        own = None
        for e in edges_from.get(r, ()):
            own = own or ev_of(e)
        own = own or ({"file": n["path"], "line": n.get("line") or 1} if n.get("path") else None)
        if online:
            return "online-readonly", (n["entry_evidence"][0] if n.get("entry_evidence") else own)
        return ("batch-readonly" if has_prog else "batch-utility"), own

    order = {name: i for i, (name, _) in enumerate(FAMILIES)}
    fam_of, basis_of = {}, {}
    for r in roots:
        fam_of[r], basis_of[r] = classify(r)

    # Jobs a scheduler chains together move together, in the latest family of the chain. A job that touches
    # DB2, IMS or MQ keeps its own family.
    tadj = collections.defaultdict(set)
    for e in edges:
        if e["kind"] == "temporal" and e["src"][:4] in ("job:", "sch:") and e["dst"][:4] in ("job:", "sch:"):
            tadj[e["src"]].add(e["dst"])
            tadj[e["dst"]].add(e["src"])
    for sch, jobs in sched_of.items():
        for j in jobs:
            tadj[sch].add(j)
            tadj[j].add(sch)
    seen_chain = set()
    for start in sorted(tadj):
        if start in seen_chain:
            continue
        comp, work = set(), [start]
        while work:
            x = work.pop()
            if x not in comp:
                comp.add(x)
                work.extend(tadj[x] - comp)
        seen_chain |= comp
        chained = [j for j in comp if j in fam_of and fam_of[j] != "subsystem"]
        if len(chained) > 1:
            latest = max((fam_of[j] for j in chained), key=order.get)
            tev = next((dict(e["evidence"][0]) for e in edges if e["kind"] == "temporal" and e["src"] in comp
                        and e["dst"] in comp), None)
            for j in chained:
                if fam_of[j] != latest:
                    fam_of[j] = latest
                    basis_of[j] = tev or basis_of[j]

    def family_of(u):
        if u in sched_of:
            fams = [family_of(j) for j in sched_of[u] if j in by_id]
            return max(fams, key=order.get) if fams and None not in fams else None
        rs = roots_of.get(u, set())
        if not rs:
            return None
        return min((fam_of[r] for r in rs), key=order.get)

    unassigned, assign = [], {}
    dead, hidden = set(unreachable), set(unknown)
    for n in nodes:
        u = n["id"]
        if n["unit_type"] not in MOVABLE:
            continue
        if u in dead:
            unassigned.append({"id": u, "reason": (reasons or {}).get(u) or "dead code candidate, unreachable"})
        elif u in hidden and not roots_of.get(u):
            unassigned.append({"id": u, "reason": (reasons or {}).get(u) or "reachability unknown"})
        elif u.startswith("sch:") and u not in sched_of:
            unassigned.append({"id": u, "reason": "scheduler job that names no JCL job in the tree"})
        else:
            fam = family_of(u)
            if fam is None:
                unassigned.append({"id": u, "reason": "no entry point owns it"})
            else:
                assign[u] = fam
    def cut_groups(fam_roots):
        """Entry points of one family, cut into (label, entry points) groups. See the module docstring."""
        parent = {r: r for r in fam_roots}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def join(a, b):
            parent[find(a)] = find(b)

        by_ds, by_prog = collections.defaultdict(list), collections.defaultdict(list)
        for r in fam_roots:
            for d in used[r]:
                by_ds[d].append(r)
            for v in owned[r]:
                if v != r and v in by_id and by_id[v]["unit_type"] in schema.PROGRAM_TYPES:
                    by_prog[v].append(r)
        for d, rs in by_ds.items():
            ws = [r for r in rs if d in wrote[r]]
            for x in ws[1:]:
                join(ws[0], x)
        for rs in by_prog.values():
            for x in rs[1:]:
                join(rs[0], x)
        comps = collections.defaultdict(list)
        for r in fam_roots:
            comps[find(r)].append(r)
        alone = sorted(r for c in comps.values() if len(c) == 1 for r in c)
        coupled = sorted((sorted(c) for c in comps.values() if len(c) > 1), key=lambda c: (len(c), c[0]))
        if not coupled or (len(coupled) == 1 and not alone):
            return [(None, sorted(fam_roots))]
        out = [("independent", alone)] if alone else []
        for i, c in enumerate(coupled, 1):
            out.append(("coupled" if len(coupled) == 1 else "coupled-%d" % i, c))
        return out

    waves = []
    for name, text in FAMILIES:
        fam_roots = [r for r in roots if fam_of[r] == name]
        units = sorted(u for u, f in assign.items() if f == name)
        if not units:
            continue
        groups = cut_groups(fam_roots) if len(fam_roots) > 1 else [(None, fam_roots)]
        rank = {r: i for i, (_, rs) in enumerate(groups) for r in rs}

        def group_of(u):
            if u in sched_of:
                gs = [rank[j] for j in sched_of[u] if j in rank]
            else:
                gs = [rank[r] for r in roots_of.get(u, ()) if r in rank]
            if not gs:
                return 0
            return max(gs) if u in sched_of else min(gs)

        for gi, (label, grs) in enumerate(groups):
            gunits = [u for u in units if group_of(u) == gi]
            if not gunits:
                continue
            evs = {(b["file"], b["line"]) for r in grs for b in [basis_of[r]] if b}
            w = {"wave": len(waves) + 1, "family": name, "description": text, "units": gunits,
                 "entry_points": grs,
                 "computed_calls": sorted({d["src"] for d in (dynamic or [])} & set(gunits)),
                 "evidence": [{"file": f, "line": l} for f, l in sorted(evs)[:3]]}
            if label:
                w["group"] = label
            waves.append(w)
    return {"basis": "family of the entry points that use a unit, in a fixed order. Facts only, no risk judgment.",
            "waves": waves, "unassigned": sorted(unassigned, key=lambda x: x["id"])}


def analyze(nodes, edges, as_of, dormant_years=5, notices=None, embedded=None, proc_programs=None,
            runtime_named=None, utility_writes=None):
    by_id = {n["id"]: n for n in nodes}
    succ = collections.defaultdict(list)
    for e in edges:
        if e["kind"] in WALK_KINDS:
            succ[e["src"]].append(e["dst"])

    for r in runtime_named or []:
        if r["dst"] in by_id:
            succ[r["src"]].append(r["dst"])

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

    warnings = list(notices or [])
    if nodes and not any(n.get("last_modified") for n in nodes if n["unit_type"] in schema.PROGRAM_TYPES):
        warnings.append("No last-modified dates exist (the target is not a git repository, or --no-git was used). "
                        "The dormant bucket was NOT computed. An empty dormant list means not measured.")
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
        emb = {}
        for r in embedded or []:
            if r["src"] in reach and r["dst"] in set(unreachable) and r["dst"] not in emb:
                emb[r["dst"]] = r
        if emb:
            moved = _spread(emb, succ, by_id, reach, proc_programs or {})
            moved = {k: v for k, v in moved.items() if k in set(unreachable)}
            for c, o in sorted(moved.items()):
                r = emb[o]
                at = "%s:%d" % (r["evidence"]["file"], r["evidence"]["line"])
                reasons[c] = ("named in JCL text inside %s at %s, which a running program can submit" % (r["src"], at)
                              if c == o else "run by %s, which JCL text inside %s names at %s" % (o, r["src"], at))
            unknown = sorted(set(unknown) | set(moved))
            unreachable = sorted(set(unreachable) - set(moved))
            warnings.append("%d proc or program(s) are named only in JCL text inside COBOL. No edge exists, so they "
                            "are unknown, not unreachable. See dead_code_reasons." % len(moved))
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

    all_progs = sorted(n["id"] for n in nodes if n["unit_type"] in schema.PROGRAM_TYPES)
    # Structure is computed over programs a job or transaction can actually reach. A dead caller must
    # not raise a program's fan-in or make it look like a wave boundary.
    progs = [p for p in all_progs if p in reach] if entries else all_progs
    pset = set(progs)
    basis = ("programs reachable from an entry point (%d of %d)" % (len(progs), len(all_progs))
             if entries else "all programs (no entry points were found)")
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
        if e["kind"] == "data" and e["dst"] in ds_ids and (e["src"] in pset or e["src"].startswith("step:")):
            if e["mode"] in ("write", "read_write"):
                hubs[e["dst"]]["writers"].add(e["src"])
            if e["mode"] in ("read", "read_write"):
                hubs[e["dst"]]["readers"].add(e["src"])
    data_hubs = sorted(({"id": k, "writers": len(v["writers"]), "readers": len(v["readers"])}
                        for k, v in hubs.items()), key=lambda h: (-(h["writers"] + h["readers"]), h["id"]))[:15]

    sched = [n["id"] for n in nodes if n["unit_type"] == "scheduler_job"]
    unscheduled = []
    jobs = [n for n in nodes if n["unit_type"] == "jcl_job" and n.get("path")]
    if jobs and not sched:
        warnings.append("%d JCL job(s) are in the tree but no scheduler artifact was parsed. The order jobs run "
                        "in across jobs is unknown. Ask for the scheduler's job definitions." % len(jobs))
    if jobs and sched:
        called = {e["dst"] for e in edges if e["kind"] == "call" and e["src"].startswith("sch:")}
        unscheduled = sorted(n["id"] for n in nodes if n["unit_type"] == "jcl_job" and n["id"] not in called
                             and n.get("path"))
        if unscheduled:
            warnings.append("%d JCL job(s) are not named by any parsed scheduler or wrapper. Every job counts as an "
                            "entry point, so none of them appears in the dead code buckets. Ask whether they still "
                            "run. See unscheduled_jobs." % len(unscheduled))

    kinds = collections.Counter(e["kind"] for e in edges)
    types = collections.Counter(n["unit_type"] for n in nodes)
    return {
        "as_of": as_of.isoformat(),
        "dormant_years": dormant_years,
        "entry_points": entries,
        "reachable_nodes": len(reach),
        "reachable_programs": len([p for p in all_progs if p in reach]),
        "dead_code_candidates": {"unreachable": unreachable, "dormant": dormant, "unknown": unknown},
        "dead_code_reasons": reasons,
        "unresolved_dynamic": dynamic,
        "embedded_jcl": list(embedded or []),
        "runtime_named": list(runtime_named or []),
        "utility_writes": list(utility_writes or []),
        "structure_basis": basis,
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
        "wave_seed": wave_seed(nodes, edges, entries, unknown, unreachable, reasons, dynamic, runtime_named, utility_writes,
                              embedded, proc_programs),
        "warnings": warnings,
    }
