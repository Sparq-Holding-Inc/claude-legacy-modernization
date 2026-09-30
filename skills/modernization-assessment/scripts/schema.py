#!/usr/bin/env python3
"""Single source of truth for every JSON shape the plugin reads or writes.

The extractors, the citation hook and the evals all import this file.
Python standard library only.

Files and who writes them
-------------------------
graph.json       extract.py. Facts only. Every edge carries file:line evidence.
waves.json       Claude, from graph.json. Checked here.
dead-code.json   Claude, from graph.json analysis. Checked here.
risks.json       Claude, from graph.json. Checked here.

Node ids
--------
Names collide across kinds in real shops. A job and its program often share
a name. So every node kind except a COBOL program carries a prefix.

    program          NAME                       CBTRN02C
    copybook         cpy:NAME                   cpy:CVTRA05Y
    map (BMS)        map:NAME                   map:COSGN00
    jcl_job          job:NAME                   job:POSTTRAN
    jcl_step         step:JOB.STEP              step:POSTTRAN.STEP15
                     step:JOB.STEP.PROCSTEP     step:TRANREPT.STEP05R.PRC001
                     a repeated step name gets  step:TRANREPT.STEP05R#2
    proc             proc:NAME                  proc:REPROC
    dataset          ds:NAME                    ds:AWS.M2.CARDDEMO.ACCTDATA.VSAM.KSDS
                     a DD with no JCL mapping   ds:dd:PROGRAM.DDNAME
                     a DB2 table                ds:db2:TABLE
    scheduler_job    sch:FOLDER/JOB             sch:DAILY-Backup/CLOSEFIL
                     a shell wrapper            sch:scripts/run_batch.sh
    external         ext:NAME                   ext:CEEDAYS, ext:IDCAMS
                     a computed target          ?dynamic:SOURCE:LINE

Edge semantics
--------------
call      program -> program        CALL, EXEC CICS LINK, EXEC CICS XCTL
          jcl_step -> program       EXEC PGM=
          jcl_step -> proc          EXEC PROC= or EXEC name
          scheduler_job -> jcl_job  Control-M MEMNAME, shell wrapper submit
include   program -> copybook       COPY, EXEC SQL INCLUDE
          copybook -> copybook      nested COPY
          jcl_job -> jcl_step       containment
data      program -> dataset        mode read | write | read_write
          jcl_step -> dataset       only when the program has no source in tree
contract  program -> program        writer -> reader of the same dataset
temporal  jcl_step -> jcl_step      step order inside one job
          scheduler_job -> scheduler_job   Control-M OUTCOND -> INCOND
          jcl_job -> jcl_job        order inside a shell wrapper

Unresolved targets
------------------
A computed target (CALL WS-PGM-NAME) points to a node
"?dynamic:<source>:<line>" and the edge has resolved=false. They are never
dropped. A statically named target that is simply not in the tree (CEEDAYS,
IDCAMS, a system copybook) points to an "ext:" node with resolved=true.

Deviations from the build plan, all logged in TEARDOWN.md
---------------------------------------------------------
* unit_type adds "subprogram" and "external".
* lang adds null (datasets, external nodes).
* Node ids are prefixed by kind (see above).
* Nodes may carry optional line, note, entry_evidence.
* graph.json may carry optional analysis, unparsed, meta.
"""

import json
import re
import sys

SCHEMA_VERSION = "0.2"

UNIT_TYPES = (
    "online_txn", "batch", "subprogram", "copybook", "jcl_job", "jcl_step",
    "proc", "dataset", "map", "scheduler_job", "external",
)
PROGRAM_TYPES = ("online_txn", "batch", "subprogram")
LANGS = ("cobol", "jcl", "bms", "csd", "scheduler", None)
EDGE_KINDS = ("call", "include", "data", "contract", "temporal")
MODES = ("read", "write", "read_write", None)
CONFIDENCE = ("high", "medium", "low")
TARGET_STATES = ("rehost", "replatform", "refactor", "rewrite", "unknown")

# id prefix required for each unit_type. Programs carry none.
ID_PREFIX = {
    "copybook": "cpy:", "map": "map:", "jcl_job": "job:", "jcl_step": "step:",
    "proc": "proc:", "dataset": "ds:", "scheduler_job": "sch:",
}
DYNAMIC_PREFIX = "?dynamic:"
EXTERNAL_PREFIX = "ext:"


# ---------------------------------------------------------------- id helpers

def program_id(name):
    return name.upper()


def cpy_id(name):
    return "cpy:" + name.upper()


def map_id(name):
    return "map:" + name.upper()


def job_id(name):
    return "job:" + name.upper()


def step_id(job, step):
    return "step:%s.%s" % (job.upper(), step.upper())


def proc_id(name):
    return "proc:" + name.upper()


def ds_id(name):
    return "ds:" + name.upper()


def sch_id(folder, job):
    return "sch:%s/%s" % (folder, job)


def ext_id(name):
    return EXTERNAL_PREFIX + name.upper()


def dynamic_id(source, line):
    return "%s%s:%d" % (DYNAMIC_PREFIX, source, line)


def is_dynamic(node_id):
    return isinstance(node_id, str) and node_id.startswith(DYNAMIC_PREFIX)


def edge_key(edge):
    """Identity of an edge for matching and de-duplication."""
    return (edge["src"], edge["dst"], edge["kind"], edge.get("mode"))


# ---------------------------------------------------------------- validators

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ].*)?$")


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _evidence_errors(ev, where):
    errs = []
    if not isinstance(ev, list) or not ev:
        return ["%s: evidence must be a non-empty list" % where]
    for i, e in enumerate(ev):
        if not isinstance(e, dict):
            errs.append("%s: evidence[%d] is not an object" % (where, i))
            continue
        if not isinstance(e.get("file"), str) or not e.get("file"):
            errs.append("%s: evidence[%d].file must be a non-empty string" % (where, i))
        if not _is_int(e.get("line")) or e.get("line") < 1:
            errs.append("%s: evidence[%d].line must be an integer >= 1" % (where, i))
    return errs


def validate_graph(g):
    """Return a list of error strings. Empty list means valid."""
    errs = []
    if not isinstance(g, dict):
        return ["graph: top level must be an object"]
    nodes, edges = g.get("nodes"), g.get("edges")
    if not isinstance(nodes, list):
        errs.append("graph: nodes must be a list")
        nodes = []
    if not isinstance(edges, list):
        errs.append("graph: edges must be a list")
        edges = []

    ids = {}
    for i, n in enumerate(nodes):
        w = "node[%d]" % i
        if not isinstance(n, dict):
            errs.append("%s: not an object" % w)
            continue
        nid = n.get("id")
        if not isinstance(nid, str) or not nid:
            errs.append("%s: id must be a non-empty string" % w)
            continue
        w = "node %s" % nid
        if nid in ids:
            errs.append("%s: duplicate id" % w)
        ids[nid] = n
        ut = n.get("unit_type")
        if ut not in UNIT_TYPES:
            errs.append("%s: unit_type %r not in %s" % (w, ut, list(UNIT_TYPES)))
        if n.get("lang") not in LANGS:
            errs.append("%s: lang %r not in %s" % (w, n.get("lang"), list(LANGS)))
        if not (n.get("path") is None or isinstance(n.get("path"), str)):
            errs.append("%s: path must be a string or null" % w)
        if not _is_int(n.get("loc")) or n.get("loc") < 0:
            errs.append("%s: loc must be an integer >= 0" % w)
        lm = n.get("last_modified")
        if not (lm is None or (isinstance(lm, str) and _DATE.match(lm))):
            errs.append("%s: last_modified must be an ISO date or null" % w)
        if not isinstance(n.get("entry_point"), bool):
            errs.append("%s: entry_point must be a boolean" % w)
        if "line" in n and not (_is_int(n["line"]) and n["line"] >= 1):
            errs.append("%s: line must be an integer >= 1" % w)
        if "entry_evidence" in n:
            errs += _evidence_errors(n["entry_evidence"], w + " entry_evidence")
        if ut in ID_PREFIX and not nid.startswith(ID_PREFIX[ut]):
            errs.append("%s: %s ids must start with %r" % (w, ut, ID_PREFIX[ut]))
        if ut in PROGRAM_TYPES and (":" in nid or nid.startswith("?")):
            errs.append("%s: program ids carry no prefix" % w)
        if ut == "external" and not (nid.startswith(EXTERNAL_PREFIX) or is_dynamic(nid)):
            errs.append("%s: external ids must start with 'ext:' or '?dynamic:'" % w)

    seen = set()
    for i, e in enumerate(edges):
        w = "edge[%d]" % i
        if not isinstance(e, dict):
            errs.append("%s: not an object" % w)
            continue
        w = "edge %s -> %s (%s)" % (e.get("src"), e.get("dst"), e.get("kind"))
        if e.get("src") not in ids:
            errs.append("%s: src is not a node" % w)
        if e.get("dst") not in ids:
            errs.append("%s: dst is not a node" % w)
        kind, mode = e.get("kind"), e.get("mode")
        if kind not in EDGE_KINDS:
            errs.append("%s: kind not in %s" % (w, list(EDGE_KINDS)))
        if mode not in MODES:
            errs.append("%s: mode %r not in %s" % (w, mode, list(MODES)))
        if kind == "data" and mode is None:
            errs.append("%s: data edges need a mode" % w)
        if kind != "data" and mode is not None:
            errs.append("%s: only data edges carry a mode" % w)
        errs += _evidence_errors(e.get("evidence"), w)
        if not isinstance(e.get("resolved"), bool):
            errs.append("%s: resolved must be a boolean" % w)
        if e.get("confidence") not in CONFIDENCE:
            errs.append("%s: confidence not in %s" % (w, list(CONFIDENCE)))
        if not isinstance(e.get("note", ""), str):
            errs.append("%s: note must be a string" % w)
        if is_dynamic(e.get("dst")) and e.get("resolved") is not False:
            errs.append("%s: a ?dynamic target must have resolved=false" % w)
        if e.get("resolved") is False and e.get("confidence") == "high":
            errs.append("%s: an unresolved edge cannot have high confidence" % w)
        try:
            k = edge_key(e)
        except KeyError:
            continue
        if k in seen:
            errs.append("%s: duplicate edge (merge the evidence)" % w)
        seen.add(k)

    unparsed = g.get("unparsed", [])
    if not isinstance(unparsed, list):
        errs.append("graph: unparsed must be a list")
    else:
        for i, u in enumerate(unparsed):
            if not (isinstance(u, dict) and isinstance(u.get("file"), str)
                    and isinstance(u.get("reason"), str)):
                errs.append("unparsed[%d]: needs string file and reason" % i)
    return errs


def _citation_or_inference(obj, where):
    """Findings carry evidence or an explicit inference flag."""
    if obj.get("inference") is True:
        return []
    if obj.get("evidence"):
        return _evidence_errors(obj["evidence"], where)
    return ["%s: needs evidence or \"inference\": true" % where]


def _scc_of(graph):
    out = {}
    for i, comp in enumerate((graph or {}).get("analysis", {}).get("sccs", [])):
        for m in comp:
            out[m] = i
    return out


def validate_waves(w, graph=None):
    errs = []
    if not isinstance(w, dict):
        return ["waves: top level must be an object"]
    if w.get("target_state") not in TARGET_STATES:
        errs.append("waves: target_state not in %s" % list(TARGET_STATES))
    waves = w.get("waves")
    if not isinstance(waves, list) or not waves:
        return errs + ["waves: waves must be a non-empty list"]
    numbers = []
    placed = {}
    for i, wave in enumerate(waves):
        wh = "wave[%d]" % i
        if not isinstance(wave, dict):
            errs.append("%s: not an object" % wh)
            continue
        n = wave.get("wave")
        numbers.append(n)
        wh = "wave %s" % n
        if not _is_int(n) or n < 1:
            errs.append("%s: wave must be an integer >= 1" % wh)
        units = wave.get("units")
        if not isinstance(units, list) or not units or not all(isinstance(u, str) for u in units):
            errs.append("%s: units must be a non-empty list of ids" % wh)
            units = []
        for u in units:
            if u in placed:
                errs.append("%s: unit %s is also in wave %s" % (wh, u, placed[u]))
            placed[u] = n
        for k in ("name", "rationale", "unblocks"):
            if not isinstance(wave.get(k), str) or not wave.get(k).strip():
                errs.append("%s: %s must be a non-empty string" % (wh, k))
        if wave.get("blast_radius") not in ("low", "medium", "high"):
            errs.append("%s: blast_radius must be low, medium or high" % wh)
        if wave.get("confidence") not in CONFIDENCE:
            errs.append("%s: confidence not in %s" % (wh, list(CONFIDENCE)))
        errs += _citation_or_inference(wave, wh)
    if sorted(x for x in numbers if _is_int(x)) != list(range(1, len(waves) + 1)):
        errs.append("waves: wave numbers must be 1..%d with no gaps" % len(waves))
    if graph is not None:
        known = {n["id"] for n in graph.get("nodes", [])}
        for u in placed:
            if u not in known:
                errs.append("waves: unit %s is not a node in graph.json" % u)
        comp = _scc_of(graph)
        by_comp = {}
        for u, n in placed.items():
            if u in comp:
                by_comp.setdefault(comp[u], set()).add(n)
        for c, ns in by_comp.items():
            if len(ns) > 1:
                errs.append("waves: strongly connected component %d is split across waves %s"
                            % (c, sorted(ns)))
    return errs


def validate_dead_code(d, graph=None):
    errs = []
    if not isinstance(d, dict):
        return ["dead-code: top level must be an object"]
    if d.get("telemetry") not in ("none", "partial", "provided"):
        errs.append("dead-code: telemetry must be none, partial or provided")
    seen = {}
    for bucket in ("unreachable", "dormant", "unknown"):
        items = d.get(bucket)
        if not isinstance(items, list):
            errs.append("dead-code: bucket %r is required and must be a list "
                        "(three buckets, never two)" % bucket)
            continue
        for i, it in enumerate(items):
            wh = "%s[%d]" % (bucket, i)
            if not isinstance(it, dict) or not isinstance(it.get("id"), str):
                errs.append("%s: needs a string id" % wh)
                continue
            wh = "%s %s" % (bucket, it["id"])
            if it["id"] in seen:
                errs.append("%s: also listed in %s" % (wh, seen[it["id"]]))
            seen[it["id"]] = bucket
            if not isinstance(it.get("reason"), str) or not it["reason"].strip():
                errs.append("%s: reason must be a non-empty string" % wh)
            if it.get("confidence") not in CONFIDENCE:
                errs.append("%s: confidence not in %s" % (wh, list(CONFIDENCE)))
            errs += _citation_or_inference(it, wh)
            if bucket == "dormant" and not (it.get("last_modified") is None
                                            or _DATE.match(str(it.get("last_modified")))):
                errs.append("%s: last_modified must be an ISO date or null" % wh)
    if graph is not None:
        known = {n["id"] for n in graph.get("nodes", [])}
        cand = graph.get("analysis", {}).get("dead_code_candidates", {})
        dyn = set(cand.get("unknown", []))
        for i, it in enumerate(d.get("unreachable", []) or []):
            if isinstance(it, dict) and it.get("id") in dyn:
                errs.append("unreachable %s: could be the target of an unresolved dynamic "
                            "call. It belongs in the unknown bucket." % it["id"])
        for b, items in ((b, d.get(b) or []) for b in ("unreachable", "dormant", "unknown")):
            for it in items:
                if isinstance(it, dict) and it.get("id") not in known:
                    errs.append("%s %s: not a node in graph.json" % (b, it.get("id")))
    return errs


_FORBIDDEN_COMBINED = ("risk_score", "score", "combined", "total", "overall",
                       "risk", "composite", "priority_score")


def quadrant_for(difficulty, blast):
    """1-2 is low. 3-5 is high. A three is not low."""
    return "%s-%s" % ("high" if difficulty >= 3 else "low",
                      "high" if blast >= 3 else "low")


def validate_risks(r, graph=None):
    errs = []
    if not isinstance(r, dict):
        return ["risks: top level must be an object"]
    units = r.get("units")
    if not isinstance(units, list) or not units:
        return ["risks: units must be a non-empty list"]
    seen = set()
    for i, u in enumerate(units):
        wh = "unit[%d]" % i
        if not isinstance(u, dict) or not isinstance(u.get("id"), str):
            errs.append("%s: needs a string id" % wh)
            continue
        wh = "unit %s" % u["id"]
        if u["id"] in seen:
            errs.append("%s: duplicate" % wh)
        seen.add(u["id"])
        for bad in _FORBIDDEN_COMBINED:
            if bad in u:
                errs.append("%s: field %r is a combined score. Two axes, never multiplied "
                            "or summed." % (wh, bad))
        scores = {}
        for axis in ("port_difficulty", "blast_radius"):
            a = u.get(axis)
            if not isinstance(a, dict):
                errs.append("%s: %s must be an object with score and why" % (wh, axis))
                continue
            if not _is_int(a.get("score")) or not 1 <= a["score"] <= 5:
                errs.append("%s: %s.score must be an integer 1-5" % (wh, axis))
            else:
                scores[axis] = a["score"]
            if not isinstance(a.get("why"), str) or not a["why"].strip():
                errs.append("%s: %s.why must be a one line justification" % (wh, axis))
            elif "\n" in a["why"].strip():
                errs.append("%s: %s.why must be one line" % (wh, axis))
        if len(scores) == 2:
            want = quadrant_for(scores["port_difficulty"], scores["blast_radius"])
            if u.get("quadrant") != want:
                errs.append("%s: quadrant %r does not match scores (expected %r)"
                            % (wh, u.get("quadrant"), want))
        if not isinstance(u.get("driving_fact"), str) or not u["driving_fact"].strip():
            errs.append("%s: driving_fact must be a non-empty string" % wh)
        if u.get("confidence") not in CONFIDENCE:
            errs.append("%s: confidence not in %s" % (wh, list(CONFIDENCE)))
        if not (u.get("wave") is None or _is_int(u.get("wave"))):
            errs.append("%s: wave must be an integer or null" % wh)
        errs += _citation_or_inference(u, wh)
    if not isinstance(r.get("do_not_port", []), list):
        errs.append("risks: do_not_port must be a list")
    if graph is not None:
        known = {n["id"] for n in graph.get("nodes", [])}
        for u in units:
            if isinstance(u, dict) and u.get("id") not in known:
                errs.append("unit %s: not a node in graph.json" % u.get("id"))
    return errs


VALIDATORS = {
    "graph": validate_graph,
    "waves": validate_waves,
    "dead-code": validate_dead_code,
    "risks": validate_risks,
}


def validate(kind, obj, graph=None):
    """validate("graph", obj) or validate("waves", obj, graph=graph_obj)."""
    fn = VALIDATORS[kind]
    return fn(obj) if kind == "graph" else fn(obj, graph)


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv):
    usage = ("usage: schema.py validate {graph|waves|dead-code|risks} FILE [--graph graph.json]\n"
             "       schema.py validate-dir DIR    (checks every output that exists)")
    if len(argv) >= 4 and argv[1] == "validate" and argv[2] in VALIDATORS:
        graph = None
        if "--graph" in argv:
            graph = _load(argv[argv.index("--graph") + 1])
        errs = validate(argv[2], _load(argv[3]), graph)
        for e in errs:
            print("ERROR", e)
        print("%s: %s" % (argv[3], "INVALID (%d errors)" % len(errs) if errs else "valid"))
        return 1 if errs else 0
    if len(argv) == 3 and argv[1] == "validate-dir":
        import os
        base, bad, graph = argv[2], 0, None
        gp = os.path.join(base, "graph.json")
        if os.path.exists(gp):
            graph = _load(gp)
        for name, kind in (("graph.json", "graph"), ("waves.json", "waves"),
                           ("dead-code.json", "dead-code"), ("risks.json", "risks")):
            p = os.path.join(base, name)
            if not os.path.exists(p):
                print("MISSING", p)
                bad += 1
                continue
            try:
                errs = validate(kind, _load(p), graph)
            except (ValueError, OSError) as exc:
                errs = ["cannot read: %s" % exc]
            for e in errs:
                print("ERROR", name, e)
            print("%s: %s" % (name, "INVALID (%d errors)" % len(errs) if errs else "valid"))
            bad += 1 if errs else 0
        return 1 if bad else 0
    print(usage)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
