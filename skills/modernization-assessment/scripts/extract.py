#!/usr/bin/env python3
"""Entry point. Builds graph.json from a legacy tree. Python standard library only.

    python3 extract.py TARGET [--out DIR] [--as-of YYYY-MM-DD] [--dormant-years N] [--no-git]

Writes DIR/graph.json (default DIR is modernization-assessment). Every edge
carries file:line evidence. Nothing is read from the network. If `cloc` is on
the PATH it is used for line counts, and git history is used for last
modified dates when the target is a git repository. Neither is required.
"""

import argparse
import collections
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402
import cics  # noqa: E402
import cobol  # noqa: E402
import jcl  # noqa: E402
import scheduler  # noqa: E402
import schema  # noqa: E402
from graph import Graph  # noqa: E402

VERSION = "0.2.0"
SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
             "modernization-assessment"}
LIMITS = [
    "COBOL is read as fixed format. Free format files are listed as not parsed.",
    "COPY REPLACING is not applied. A copybook is expanded as written.",
    "A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program.",
    "A called subprogram gets no DDs from its caller's JCL step.",
    "IDCAMS, SORT and other in-stream control cards are not read. Dataset modes on utility steps come from DISP only.",
    "IF/THEN/ELSE and COND= in JCL are not modeled. Step order is file order.",
    "Nested PROC calls, INCLUDE members and jobs submitted through the internal reader are not followed.",
    "EXEC CICS RETURN TRANSID, START and SEND MAP are not edges.",
    "Only Control-M XML and shell wrappers that name JCL files are read as schedulers.",
    "DCB, LRECL and RECFM are not read, so a record length on a DD is not compared with a copybook.",
    "LINK and XCTL are both call edges. XCTL never returns, and control flow is not modeled.",
]


def walk(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP_DIRS)
        for f in sorted(fn):
            out.append(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
    return out


def git_dates(root):
    """Newest commit date per path (YYYY-MM-DD) from one pass over the history."""
    try:
        r = subprocess.run(["git", "-C", root, "-c", "core.quotepath=off", "log", "--relative",
                            "--name-only", "--no-renames", "--format=%x00%cs"],
                           capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError):
        return {}
    if r.returncode != 0:
        return {}
    dates = {}
    for chunk in r.stdout.split("\x00"):
        lines = [x for x in chunk.splitlines() if x.strip()]
        for path in lines[1:]:
            dates.setdefault(path, lines[0].strip())
    return dates


def cloc_counts(root):
    """Line counts from cloc when it is installed. Empty dict otherwise."""
    exe = shutil.which("cloc")
    if not exe:
        return {}
    try:
        r = subprocess.run([exe, "--by-file", "--json", "--quiet", root], capture_output=True,
                           text=True, timeout=300)
        data = json.loads(r.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return {}
    out = {}
    for path, v in data.items():
        if isinstance(v, dict) and "code" in v and path not in ("header", "SUM"):
            out[os.path.relpath(path, root).replace(os.sep, "/")] = int(v["code"])
    return out


def loc_plain(text, comment=()):
    return sum(1 for line in text.splitlines()
               if line.strip() and not any(line.strip().startswith(c) for c in comment))


def read(root, rel):
    return cobol.read_text(os.path.join(root, rel))


def _merge_modes(modes):
    return "read_write" if len(modes) > 1 else next(iter(modes))


def build(root, as_of, dormant_years=5, use_git=True):
    files = walk(root)
    dates = git_dates(root) if use_git else {}
    cloc = cloc_counts(root)
    g = Graph()

    def unparsed(kind, rel, reason):
        g.unparsed.append({"kind": kind, "file": rel, "reason": reason})

    def loc_of(rel, text, comment=()):
        return cloc.get(rel, loc_plain(text, comment))

    notices = []
    buckets = collections.defaultdict(list)
    for rel in files:
        ext = os.path.splitext(rel)[1].lower()
        why = scheduler.unparsed_reason(rel)
        if why:
            unparsed("scheduler", rel, why + ", not parsed")
            continue
        if ext in cobol.CODE_EXT:
            buckets["cobol"].append(rel)
        elif ext in cobol.COPY_EXT:
            buckets["copy"].append(rel)
        elif ext in jcl.JCL_EXT:
            buckets["jcl"].append(rel)
        elif ext in jcl.PROC_EXT:
            buckets["proc"].append(rel)
        elif ext == ".bms":
            buckets["bms"].append(rel)
        elif ext in cics.CSD_EXT:
            buckets["csd"].append(rel)
        elif ext in scheduler.SHELL_EXT:
            buckets["shell"].append(rel)
        elif ext in scheduler.CONTROLM_EXT:
            with open(os.path.join(root, rel), "rb") as fh:
                if scheduler.looks_like_controlm(fh.read(4000).decode("latin-1")):
                    buckets["controlm"].append(rel)

    # ---------------------------------------------------------- copybooks
    lib = cobol.CopyLibrary(root, buckets["copy"])
    for rel in buckets["copy"]:
        cid = lib.path_to_id.get(rel)
        if not cid:
            unparsed("duplicate", rel, "copybook name already defined by %s, first one kept" %
                     lib.by_name[os.path.splitext(os.path.basename(rel))[0].upper()])
            continue
        try:
            incs, loc = cobol.parse_copybook_includes(root, rel, lib)
        except Exception as exc:  # never drop a file silently
            unparsed("error", rel, "copybook parse error: %r" % (exc,))
            continue
        g.node(cid, "copybook", "cobol", rel, cloc.get(rel, loc), dates.get(rel))
        for name, fl, ln in incs:
            found = lib.find(name)
            dst = found[0] if found else g.ext(name, "copybook not in the scanned tree")
            g.edge(cid, dst, "include", [(fl, ln)])

    # ----------------------------------------------------------- programs
    facts = {}
    for rel in buckets["cobol"]:
        try:
            res = cobol.parse_program(root, rel, lib)
        except Exception as exc:
            unparsed("error", rel, "COBOL parse error: %r" % (exc,))
            continue
        if res == "free-format":
            unparsed("cobol", rel, "free-format COBOL is not supported, not parsed")
            continue
        if res is None:
            unparsed("cobol", rel, "no PROGRAM-ID found, not parsed")
            continue
        if res.program_id in facts:
            unparsed("duplicate", rel, "PROGRAM-ID %s already defined by %s, first one kept" %
                     (res.program_id, facts[res.program_id].path))
            continue
        facts[res.program_id] = res
        for pf, pl, why in res.problems:
            unparsed("cobol", pf, "line %d: %s" % (pl, why))
        text = read(root, rel)
        g.node(res.program_id, "batch", "cobol", rel, cloc.get(rel, cobol.count_loc(text)), dates.get(rel))
    prog_set = set(facts)

    # --------------------------------------------------------------- maps
    for rel in buckets["bms"]:
        text = read(root, rel)
        m = re.search(r"^(\S+)\s+DFHMSD\b", text, re.M | re.I)
        name = m.group(1) if m else os.path.splitext(os.path.basename(rel))[0]
        g.node(schema.map_id(name), "map", "bms", rel, loc_of(rel, text, ("*",)), dates.get(rel))

    # ---------------------------------------------------------------- CSD
    csd_tx, csd_prog, csd_file = {}, {}, {}
    for rel in buckets["csd"]:
        try:
            r = cics.parse_csd(root, rel)
        except Exception as exc:
            unparsed("error", rel, "CSD parse error: %r" % (exc,))
            continue
        for k, (prog, line) in r["transactions"].items():
            csd_tx.setdefault(k, (prog, rel, line))
        for k, line in r["programs"].items():
            csd_prog.setdefault(k, (rel, line))
        for k, (dsn, line) in r["files"].items():
            csd_file.setdefault(k, (dsn, rel, line))

    # ---------------------------------------------------------------- JCL
    procs, job_units = {}, []
    for rel in buckets["proc"] + buckets["jcl"]:
        try:
            units = jcl.parse_file(root, rel)
        except Exception as exc:
            unparsed("error", rel, "JCL parse error: %r" % (exc,))
            continue
        text = read(root, rel)
        floc = loc_of(rel, text, ("//*",))
        for u in units:
            if u.kind == "proc":
                if u.name not in procs:
                    procs[u.name] = u
                    g.node(schema.proc_id(u.name), "proc", "jcl", rel, floc, dates.get(rel), line=u.line)
            else:
                u.loc = floc
                job_units.append(u)

    runs = collections.defaultdict(list)
    job_files = collections.defaultdict(list)
    for u in job_units:
        jid = schema.job_id(u.name)
        if g.has(jid):
            unparsed("duplicate", u.file, "job %s already defined, first one kept" % u.name)
            continue
        g.node(jid, "jcl_job", "jcl", u.file, u.loc, dates.get(u.file), entry_point=True, line=u.line)
        job_files[os.path.splitext(os.path.basename(u.file))[0].lower()].append(jid)
        steps = jcl.expand_job(u, procs)
        for s in steps:
            if s["parent"] is None and "#" in s["id"]:
                notices.append("%s:%d: job %s repeats a step name. The extractor calls this one %s." % (s["file"], s["line"], u.name, s["id"].split(".", 1)[1]))
        by_id = {s["id"]: s for s in steps}
        execs = []
        for s in steps:
            sid = "step:" + s["id"]
            g.node(sid, "jcl_step", "jcl", s["file"], 0, None, line=s["line"])
            if s["parent"] is None:
                g.edge(jid, sid, "include", [(s["file"], s["line"])])
            else:
                par = by_id[s["parent"]]
                g.edge("step:" + s["parent"], sid, "include", [(par["file"], par["line"]),
                                                               (s["file"], s["line"])])
            if s["container"]:
                dst = schema.proc_id(s["proc"]) if s["proc_found"] else g.ext(
                    s["proc"], "cataloged PROC not in the scanned tree")
                g.edge(sid, dst, "call", [(s["file"], s["line"])])
            if s["pgm"]:
                dst = s["pgm"] if s["pgm"] in prog_set else g.ext(s["pgm"], "program not in the scanned tree")
                g.edge(sid, dst, "call", [(s["file"], s["line"])])
                execs.append(s)
                if s["pgm"] in prog_set:
                    runs[s["pgm"]].append(s)
                else:
                    for d in s["dds"]:
                        if d["skip"] or d["mode"] is None or not d["dsn"]:
                            continue
                        dsid = schema.ds_id(d["dsn"])
                        g.dataset(dsid)
                        g.edge(sid, dsid, "data", d["lines"], mode=d["mode"], confidence="medium",
                               note="mode inferred from DISP, the program is not in the tree")
        for a, b in zip(execs, execs[1:]):
            g.edge("step:" + a["id"], "step:" + b["id"], "temporal",
                   [(a["file"], a["line"]), (b["file"], b["line"])])

    # ------------------------------------------------------- COBOL edges
    def program_or_ext(name):
        return name if name in prog_set else g.ext(name, "program not in the scanned tree")

    prog_data = {}

    def accumulate(pid, dsid, modes, ev, layouts, conf):
        slot = prog_data.setdefault((pid, dsid), {"modes": set(), "ev": [], "layouts": set(), "conf": conf})
        slot["modes"] |= set(modes)
        slot["ev"] += ev
        slot["layouts"] |= set(layouts)
        if conf != "high":
            slot["conf"] = conf

    def dyn_id(pid, f, where):
        src = pid if where.file == f.path else "%s/%s" % (pid, os.path.splitext(os.path.basename(where.file))[0])
        return g.dynamic(src, where.line)

    for pid, f in sorted(facts.items()):
        for name, fl, ln in f.includes + f.sql_includes:
            found = lib.find(name)
            dst = found[0] if found else g.ext(name, "copybook not in the scanned tree")
            g.edge(pid, dst, "include", [(fl, ln)])

        for c in f.calls:
            where = c["at"]
            ev = cobol.ev(where)
            if c["literal"] is not None:
                g.edge(pid, program_or_ext(c["literal"]), "call", ev)
                continue
            kind, cands = f.resolve(c["var"], c["subscripted"])
            for lit, locs in cands:
                extra = [t for loc in locs for t in cobol.ev(loc)]
                if kind == "constant":
                    g.edge(pid, program_or_ext(lit), "call", ev + extra, confidence="high",
                           note="via constant %s" % c["var"].upper())
                else:
                    g.edge(pid, program_or_ext(lit), "call", ev + extra, confidence="medium",
                           note="via %s, a literal is moved to it" % c["var"].upper())
            if kind != "constant":
                g.edge(pid, dyn_id(pid, f, where), "call", ev, resolved=False, confidence="low",
                       note=("target %s is computed" % (c["var"] or "?").upper()) +
                            ("" if kind == "dynamic" else "; the literals found may not be all of them"))

        for op in f.cics_files:
            where = op["at"]
            ev = cobol.ev(where)
            layouts = cobol.layout_of_record(f, op["rec"])
            if op["literal"] is not None:
                kind, cands = "literal", [(op["literal"], [])]
            else:
                kind, cands = f.resolve(op["var"], op["subscripted"])
            for name, locs in cands:
                extra = [t for loc in locs for t in cobol.ev(loc)]
                if name in csd_file:
                    dsid = schema.ds_id(csd_file[name][0])
                    note = "CICS file %s, CSD DSNAME" % name
                else:
                    dsid = schema.ds_id(name)
                    note = "CICS file %s, no CSD DEFINE FILE found" % name
                g.dataset(dsid, note)
                accumulate(pid, dsid, [op["mode"]], ev + extra, layouts,
                           "medium" if kind == "var-literal" else "high")
            if kind in ("var-literal", "dynamic"):
                g.edge(pid, dyn_id(pid, f, where), "data", ev, mode=op["mode"], resolved=False,
                       confidence="low", note="file name %s is computed" % (op["var"] or "?").upper())

        for fname, sel in f.selects.items():
            o = f.opens.get(fname)
            if not o:
                continue
            base = cobol.ev(sel["at"]) + [t for loc in o["lines"] for t in cobol.ev(loc)]
            layouts = cobol.layouts_for(f, fname)
            org = {"INDEXED": "VSAM KSDS", "RELATIVE": "VSAM RRDS"}.get(sel["org"] or "", None)
            matched = False
            for step in runs.get(pid, []):
                for d in step["dds"]:
                    if d["name"] != sel["dd"]:
                        continue
                    matched = True
                    if d["skip"] or not d["dsn"]:
                        continue
                    dsid = schema.ds_id(d["dsn"])
                    g.dataset(dsid, org)
                    accumulate(pid, dsid, _expand_modes(o["modes"]), base + d["lines"], layouts, "high")
            if not matched:
                dsid = schema.ds_dd_id(pid, sel["dd"])
                g.dataset(dsid, "no JCL step in the tree maps DD %s for %s" % (sel["dd"], pid))
                g.edge(pid, dsid, "data", base, mode=_merge_modes(_expand_modes(o["modes"])), resolved=False,
                       confidence="low", note="DD %s is not mapped by any JCL in the tree" % sel["dd"])

        for q in f.sql:
            dsid = schema.ds_db2_id(q["table"])
            g.dataset(dsid, "DB2 table")
            accumulate(pid, dsid, _expand_modes([q["mode"]]), cobol.ev(q["at"]), set(), "high")

    for (pid, dsid), slot in sorted(prog_data.items()):
        g.edge(pid, dsid, "data", slot["ev"], mode=_merge_modes(slot["modes"]), confidence=slot["conf"])

    # ---------------------------------------------------------- contracts
    by_ds = collections.defaultdict(lambda: {"w": {}, "r": {}})
    for (pid, dsid), slot in prog_data.items():
        if dsid.startswith("ds:db2:"):
            continue
        if "write" in slot["modes"]:
            by_ds[dsid]["w"][pid] = slot
        if "read" in slot["modes"]:
            by_ds[dsid]["r"][pid] = slot
    for dsid, side in sorted(by_ds.items()):
        for w, ws in sorted(side["w"].items()):
            for r, rs in sorted(side["r"].items()):
                if w == r:
                    continue
                shared = ws["layouts"] & rs["layouts"]
                if shared:
                    conf, note = "high", "%s: same layout copybook %s on both sides" % (dsid[3:], sorted(shared)[0][4:])
                else:
                    conf = "medium"
                    note = ("%s: same dataset, layout copybooks differ or are unknown (writer %s, reader %s). "
                            "Verify by hand." % (dsid[3:], sorted(ws["layouts"]) or "none", sorted(rs["layouts"]) or "none"))
                g.edge(w, r, "contract", ws["ev"] + rs["ev"], confidence=conf, note=note)

    # ---------------------------------------------------------- scheduler
    def ensure_job(jid, member):
        if not g.has(jid):
            g.node(jid, "jcl_job", "jcl", None, 0, None, note="JCL member %s is not in the scanned tree" % member)

    for rel in buckets["controlm"]:
        try:
            r = scheduler.parse_controlm(root, rel)
        except Exception as exc:
            unparsed("error", rel, "Control-M parse error: %r" % (exc,))
            continue
        if r["error"]:
            unparsed("scheduler", rel, "Control-M XML did not parse: %s" % r["error"])
        text = read(root, rel)
        for j in r["jobs"]:
            sid = schema.sch_id(j["folder"], j["name"])
            g.node(sid, "scheduler_job", "scheduler", rel, 0, dates.get(rel), entry_point=True, line=j["line"])
            jid = schema.job_id(j["member"])
            ensure_job(jid, j["member"])
            g.edge(sid, jid, "call", [(rel, j["line"])])
        notices += scheduler.condition_notes(r["jobs"], rel)
        for pj, cj, pl, cl, nm in scheduler.condition_edges(r["jobs"]):
            g.edge(schema.sch_id(pj["folder"], pj["name"]), schema.sch_id(cj["folder"], cj["name"]),
                   "temporal", [(rel, pl), (rel, cl)], note="condition %s" % nm)

    for rel in buckets["shell"]:
        try:
            subs = scheduler.parse_shell(root, rel, job_files)
        except Exception as exc:
            unparsed("error", rel, "shell parse error: %r" % (exc,))
            continue
        if not subs:
            continue
        sid = "sch:" + rel
        g.node(sid, "scheduler_job", "scheduler", rel, 0, dates.get(rel), entry_point=True)
        ordered = []
        for stem, line in subs:
            jid = job_files[stem.lower()][0]
            g.edge(sid, jid, "call", [(rel, line)])
            ordered.append((jid, line))
        for (a, la), (b, lb) in zip(ordered, ordered[1:]):
            if a != b:
                g.edge(a, b, "temporal", [(rel, la), (rel, lb)], confidence="medium",
                       note="order of submits in %s" % rel)

    # ------------------------------------------------ entry points from CSD
    online = {p for p, f in facts.items() if f.has_cics} | {k for k in csd_prog} | {v[0] for v in csd_tx.values()}
    for tx, (prog, rel, line) in sorted(csd_tx.items()):
        nid = prog if prog in prog_set else g.ext(prog, "CSD transaction %s maps to a program with no source in the tree" % tx)
        n = g.nodes[nid]
        n["entry_point"] = True
        n.setdefault("entry_evidence", []).append({"file": rel, "line": line})
        note = "CSD transaction %s" % tx
        n["note"] = (n["note"] + "; " + note) if n.get("note") else note

    # ----------------------------------------------------- unit types
    inbound = {e["dst"] for e in g.edges.values()
               if e["kind"] == "call" and e["src"] in prog_set and e["dst"] in prog_set and e["src"] != e["dst"]}
    for pid in prog_set:
        if pid in online:
            ut = "online_txn"
        elif pid in runs:
            ut = "batch"
        elif pid in inbound:
            ut = "subprogram"
        else:
            ut = "batch"
        g.nodes[pid]["unit_type"] = ut

    nodes, edges = g.finalize()
    return {
        "schema_version": schema.SCHEMA_VERSION,
        "meta": {
            "tool": "extract.py", "version": VERSION, "target": os.path.basename(os.path.abspath(root)),
            "git_dates": bool(dates), "cloc": bool(cloc), "limits": LIMITS,
            "files_seen": {k: len(v) for k, v in sorted(buckets.items())},
        },
        "nodes": nodes,
        "edges": edges,
        "unparsed": sorted(g.unparsed, key=lambda u: (u["file"], u["reason"])),
        "analysis": analyze.analyze(nodes, edges, as_of, dormant_years, notices),
    }


def _expand_modes(modes):
    out = set()
    for m in modes:
        if m == "read_write":
            out |= {"read", "write"}
        else:
            out.add(m)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract a coupling graph from a legacy tree.")
    ap.add_argument("target", help="root of the tree to analyze")
    ap.add_argument("--out", default="modernization-assessment", help="output directory")
    ap.add_argument("--as-of", default=None, help="date used for dormancy, YYYY-MM-DD (default today)")
    ap.add_argument("--dormant-years", type=int, default=5, help="years without a change that mean dormant")
    ap.add_argument("--no-git", action="store_true", help="do not read git history")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.target):
        print("not a directory: %s" % args.target, file=sys.stderr)
        return 2
    as_of = datetime.date.fromisoformat(args.as_of) if args.as_of else datetime.date.today()
    t0 = time.time()
    graph = build(os.path.abspath(args.target), as_of, args.dormant_years, not args.no_git)
    errs = schema.validate("graph", graph)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "graph.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=1)
        fh.write("\n")
    a = graph["analysis"]
    print("wrote %s: %d nodes, %d edges %s in %.1fs" %
          (path, len(graph["nodes"]), len(graph["edges"]), a["edge_counts"], time.time() - t0))
    print("entry points: %d, unresolved dynamic calls: %d, not parsed: %d" %
          (len(a["entry_points"]), len(a["unresolved_dynamic"]), len(graph["unparsed"])))
    for u in graph["unparsed"]:
        print("NOT PARSED %s: %s" % (u["file"], u["reason"]))
    for w in a["warnings"]:
        print("WARNING", w)
    if errs:
        for e in errs[:30]:
            print("SCHEMA ERROR", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
