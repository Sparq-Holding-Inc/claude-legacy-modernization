#!/usr/bin/env python3
"""JCL reader. Python standard library only.

Reads jobs, steps, DD statements, in-stream and cataloged PROCs.

* Statements end at column 71. Text after the operand field is a comment.
* An operand field ending in a comma continues on the next // line.
* Data after DD * or DD DATA is kept on the DD. Only three kinds of step have it read: IDCAMS
  (which datasets a step deletes, defines or loads), IKJEFT01 (the program a RUN PROGRAM card names,
  and a DSN command), and DFSRRC00 (the program named in PARM). Anything else is skipped.
* PROCs are expanded under the calling step. Symbolic parameters come from
  the EXEC statement first, then the PROC defaults. A DD named
  PROCSTEP.DDNAME on the calling job overrides that DD parameter by parameter.
* A repeated step name in one job gets a #2, #3 suffix.
* A PROC is known by its member name (the file stem), as z/OS resolves it.

Not read: SORT and other in-stream control cards, IF/THEN/ELSE logic,
COND=, nested PROC calls, INCLUDE members, and jobs submitted through the
internal reader. Those are reported as limits, not guessed.
"""

import os
import re

JCL_EXT = {".jcl", ".job"}
PROC_EXT = {".prc", ".proc"}
RESERVED = {"PGM", "PROC", "PARM", "COND", "REGION", "TIME", "ACCT", "ADDRSPC", "DPRTY",
            "DYNAMNBR", "PERFORM", "RD", "CCSID", "MEMLIMIT", "PARMDD"}
SKIP_DD = {"STEPLIB", "JOBLIB", "SYSPRINT", "SYSOUT", "SYSUDUMP", "SYSABEND", "SYSDBOUT",
           "SYSTSPRT", "SYSMDUMP", "CEEDUMP"}
STMT = re.compile(r"^([^\s]*)\s+([A-Za-z]+)(?:\s+(.*))?$")


class Dd:
    def __init__(self, name, params, line, file):
        self.name, self.params, self.line, self.file = name, params, line, file
        self.inline = False
        self.data = []        # (file, line, text) of in-stream data


class Step:
    def __init__(self, name, params, line, file, unit):
        self.name, self.params, self.line, self.file, self.unit = name, params, line, file, unit
        self.pgm = params.get("PGM")
        self.proc = params.get("PROC")
        self.symbols = {k: v for k, v in params.items() if k not in RESERVED and "." not in k}
        self.dds = []
        self.overrides = []   # (procstep, ddname, params, line)
        self.override_data = {}   # (procstep, ddname) -> [(file, line, text)]


class Unit:
    """A job or a proc."""

    def __init__(self, kind, name, file, line):
        self.kind, self.name, self.file, self.line = kind, name.upper(), file, line
        self.defaults = {}
        self.steps = []


def take_operands(s):
    """Split off the operand field. It ends at the first blank outside quotes and parentheses."""
    depth, q, i = 0, None, 0
    while i < len(s):
        ch = s[i]
        if q:
            if ch == q:
                q = None
        elif ch in "'\"":
            q = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch in " \t" and depth == 0:
            break
        i += 1
    return s[:i], s[i:]


def split_params(ops):
    parts, cur, depth, q = [], [], 0, None
    for ch in ops:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in "'\"":
            q = ch
            cur.append(ch)
        elif ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p for p in parts if p != ""]


def param_dict(ops):
    d = {}
    for i, p in enumerate(split_params(ops)):
        if "=" in p and not p.startswith("'"):
            k, v = p.split("=", 1)
            d[k.strip().upper()] = v.strip()
        else:
            d.setdefault("_pos", []).append(p.strip())
    return d


def statements(text):
    """Yield dicts: name, op, ops, line. Comments are skipped. In-stream data comes as op DATA."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i, n, in_data = 0, len(lines), False
    while i < n:
        raw = lines[i]
        ln = i + 1
        if in_data:
            if raw.startswith("/*") or raw.startswith("//"):
                in_data = False
            else:
                yield {"name": "", "op": "DATA", "ops": raw.rstrip(), "line": ln}
                i += 1
                continue
        if raw.startswith("//*") or raw.startswith("/*") or not raw.startswith("//"):
            i += 1
            continue
        body = raw[2:71]
        m = STMT.match(body.rstrip())
        if not m:
            i += 1
            continue
        name, op, rest = m.group(1), m.group(2).upper(), (m.group(3) or "").strip()
        ops, _ = take_operands(rest)
        end = i
        while ops.endswith(",") and end + 1 < n:
            nxt = end + 1
            while nxt < n and lines[nxt].startswith("//*"):
                nxt += 1
            if nxt >= n or not lines[nxt].startswith("//"):
                break
            piece, _ = take_operands(lines[nxt][2:71].strip())
            ops += piece
            end = nxt
        if op == "DD" and (ops.startswith("*") or ops.upper().startswith("DATA")):
            in_data = True
        yield {"name": name.upper(), "op": op, "ops": ops, "line": ln}
        i = end + 1


def parse_file(root, rel):
    """Return a list of Unit (jobs and procs) found in a JCL or PROC file."""
    with open(os.path.join(root, rel), "rb") as fh:
        raw = fh.read()
    text = (raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw).decode("latin-1")
    ext = os.path.splitext(rel)[1].lower()
    stem = os.path.splitext(os.path.basename(rel))[0].upper()
    units, cur, cur_step, last_dd, last_key = [], None, None, None, None
    for st in statements(text):
        op, name, ops, line = st["op"], st["name"], st["ops"], st["line"]
        if op == "JOB":
            cur = Unit("job", name or stem, rel, line)
            units.append(cur)
            cur_step = None
            last_dd = last_key = None
        elif op == "DATA":
            if last_dd is not None and last_dd.inline:
                last_dd.data.append((rel, line, ops))
                if last_key is not None and cur_step is not None:
                    cur_step.override_data.setdefault(last_key, []).append((rel, line, ops))
        elif op == "PROC":
            pu = Unit("proc", stem if ext in PROC_EXT else (name or stem), rel, line)
            pu.defaults = {k: v for k, v in param_dict(ops).items() if k != "_pos"}
            units.append(pu)
            cur = pu
            cur_step = None
        elif op == "PEND":
            # after PEND we are back in the enclosing job, if there is one
            cur = next((u for u in reversed(units) if u.kind == "job"), None)
            cur_step = None
        elif op == "EXEC":
            if cur is None:
                cur = Unit("proc" if ext in PROC_EXT else "job", stem, rel, line)
                units.append(cur)
            params = param_dict(ops)
            pos = params.pop("_pos", [])
            if "PGM" not in params and "PROC" not in params and pos:
                params["PROC"] = pos[0]
            cur_step = Step(name, params, line, rel, cur)
            cur.steps.append(cur_step)
            last_dd = last_key = None
        elif op == "DD":
            if cur is None:
                continue
            params = param_dict(ops)
            pos = params.pop("_pos", [])
            dd = Dd(name, params, line, rel)
            last_dd, last_key = dd, None
            if pos and pos[0] == "*" or pos and pos[0].upper() == "DATA":
                dd.inline = True
            if "DUMMY" in [p.upper() for p in pos]:
                dd.params["DUMMY"] = "1"
            if cur_step is None:
                continue
            if "." in name and cur_step.proc:
                ps, dn = name.split(".", 1)
                cur_step.overrides.append((ps, dn, params, line))
                last_key = (ps.upper(), dn.upper())
            else:
                if not name and cur_step.dds:
                    dd.name = cur_step.dds[-1].name
                    dd.concat = True
                cur_step.dds.append(dd)
    return units


# ------------------------------------------------------------ expansion

def _subst(value, symbols, sources):
    """Replace &NAME and &NAME. Return (text, [(file,line)] for symbols that were filled in)."""
    used = []

    def rep(m):
        key = m.group(1).upper()
        if key in symbols:
            if key in sources:
                used.append(sources[key])
            return symbols[key]
        return m.group(0)
    return re.sub(r"&([A-Za-z0-9#@$]+)\.?", rep, value), used


def _dsn(dd, symbols, sources):
    """Normalized dataset name and evidence, or (None, reason)."""
    raw = dd.params.get("DSN") or dd.params.get("DSNAME")
    if not raw:
        return None, "no DSN", []
    if raw.startswith("&&"):
        return None, "temporary dataset", []
    val, used = _subst(raw.strip("'"), symbols, sources)
    up = val.upper()
    if "&" in up:
        return None, "unresolved symbolic parameter", []
    if up.startswith("*.") or up in ("NULLFILE",):
        return None, "reference or NULLFILE", []
    up = re.sub(r"\([^)]*\)$", "", up)
    return up, "", used


def disp_mode(dd):
    raw = dd.params.get("DISP")
    if raw is None:
        return None
    first = raw.strip("()").split(",")[0].strip().upper()
    return "read" if first in ("OLD", "SHR") else "write"


def expand_job(unit, procs):
    """Flat list of executable and container steps with ids, DDs and evidence.

    Each item: id, name, parent, container, pgm, proc, parm, file, line, dds.
    Each dd: name, dsn, disp_mode, skip, lines, concat, data.
    """
    out, seen = [], {}
    for idx, st in enumerate(unit.steps, start=1):
        name = st.name or "S%03d" % idx
        seen[name] = seen.get(name, 0) + 1
        sid = "%s.%s" % (unit.name, name) + ("#%d" % seen[name] if seen[name] > 1 else "")
        proc = procs.get(st.proc.upper()) if st.proc else None
        top = {"id": sid, "name": name, "parent": None, "container": bool(st.proc),
               "pgm": (st.pgm or "").upper() or None, "proc": (st.proc or "").upper() or None,
               "proc_found": proc is not None, "file": st.file, "line": st.line, "dds": [],
               "parm": st.params.get("PARM")}
        if not st.proc:
            top["dds"] = _dds(st.dds, {}, {}, st.file)
        out.append(top)
        if not proc:
            continue
        symbols = {k.upper(): v for k, v in proc.defaults.items()}
        sources = {k: (proc.file, proc.line) for k in symbols}
        for k, v in st.symbols.items():
            symbols[k.upper()] = v
            sources[k.upper()] = (st.file, st.line)
        pseen = {}
        for ps in proc.steps:
            pname = ps.name or "S%03d" % (proc.steps.index(ps) + 1)
            pseen[pname] = pseen.get(pname, 0) + 1
            pid = "%s.%s" % (sid, pname) + ("#%d" % pseen[pname] if pseen[pname] > 1 else "")
            pgm = ps.pgm
            if pgm:
                pgm, _ = _subst(pgm, symbols, sources)
            dds = list(ps.dds)
            extra = []
            for (pstep, dname, params, line) in st.overrides:
                if pstep.upper() != pname.upper():
                    continue
                target = next((d for d in dds if d.name == dname.upper()), None)
                if target is None:
                    nd = Dd(dname.upper(), dict(params), line, st.file)
                    key = (pstep.upper(), dname.upper())
                    if key in st.override_data:
                        nd.inline, nd.data = True, list(st.override_data[key])
                    extra.append(nd)
                else:
                    merged = Dd(target.name, dict(target.params), line, st.file)
                    merged.params.update(params)
                    merged.overridden = True
                    key = (pstep.upper(), dname.upper())
                    if key in st.override_data:
                        merged.inline, merged.data = True, list(st.override_data[key])
                    dds[dds.index(target)] = merged
            out.append({"id": pid, "name": pname, "parent": sid, "container": False,
                        "pgm": (pgm or "").upper() or None, "proc": None, "proc_found": False,
                        "file": proc.file, "line": ps.line, "parm": ps.params.get("PARM"),
                        "dds": _dds(dds + extra, symbols, sources, proc.file)})
    return out


def _dds(dds, symbols, sources, default_file):
    res = []
    for d in dds:
        dsn, why, used = _dsn(d, symbols, sources)
        skip = ""
        if d.name in SKIP_DD or d.name.startswith("SORTWK"):
            skip = "utility DD"
        elif d.inline:
            skip = "in-stream data"
        elif "SYSOUT" in d.params:
            skip = "SYSOUT"
        elif "DUMMY" in d.params:
            skip = "DUMMY"
        elif dsn is None:
            skip = why
        lines = [(d.file, d.line)] + used
        res.append({"name": d.name, "dsn": dsn, "mode": disp_mode(d), "skip": skip, "lines": lines,
                    "concat": getattr(d, "concat", False), "data": list(d.data)})
    return res


# ------------------------------------------------- facts inside utility steps

FACT_PGMS = {"IDCAMS", "IKJEFT01", "IKJEFT1A", "IKJEFT1B", "DFSRRC00"}
TSO_PGMS = {"IKJEFT01", "IKJEFT1A", "IKJEFT1B"}
IMS_REGIONS = {"DLI", "DBB", "BMP"}
_TOKEN = r"([A-Z0-9#@$][A-Z0-9#@$.\-]*)"
RUN_PROGRAM = re.compile(r"\bRUN\s+PROG(?:RAM)?\s*\(\s*([A-Z0-9#@$]{1,8})\s*\)", re.I)
DSN_COMMAND = re.compile(r"^\s*DSN\s+SYSTEM\s*\(", re.I)
_IDC_DELETE = re.compile(r"^\s*(DELETE|ALTER)\s*\(?\s*" + _TOKEN, re.I)
_IDC_DEFINE = re.compile(r"^\s*DEFINE\s+\w+.*?\bNAME\s*\(\s*" + _TOKEN, re.I)
_IDC_COPY = re.compile(r"^\s*(REPRO|BLDINDEX|IMPORT|EXPORT)\b", re.I)
_OUTFILE = re.compile(r"\bOUTFILE\s*\(\s*([A-Z0-9#@$]+)", re.I)
_OUTDATASET = re.compile(r"\bOUTDATASET\s*\(\s*" + _TOKEN, re.I)


def _cards(data):
    """Join in-stream lines that end in - or + into one command. Yield (file, line, text)."""
    cur = None
    for f, ln, raw in data:
        t = re.sub(r"/\*.*?\*/", " ", raw[:72]).rstrip()
        if not t.strip():
            continue
        cont = t.endswith("-") or t.endswith("+")
        piece = (t[:-1] if cont else t).strip()
        if cur is None:
            cur = [f, ln, piece]
        else:
            cur[2] += " " + piece
        if not cont:
            yield tuple(cur)
            cur = None
    if cur:
        yield tuple(cur)


def utility_facts(step):
    """Facts a step holds in its PARM and in-stream cards. step is an expand_job item.

    Returns (runtime, writes). runtime: programs and subsystems the step starts by name, each with
    dst, how, file, line. writes: datasets an IDCAMS card changes, each with dsn, verb, file, line.
    Nothing here becomes an edge. A name with an ampersand (a symbol) is skipped.
    """
    pgm = step.get("pgm") or ""
    runtime, writes = [], []
    if pgm == "DFSRRC00":
        toks = [t.strip().upper() for t in (step.get("parm") or "").strip().strip("'\"()").split(",")]
        if len(toks) >= 2 and toks[0] in IMS_REGIONS and re.match(r"^[A-Z0-9#@$]{1,8}$", toks[1]):
            runtime.append({"dst": toks[1], "how": "IMS region PARM", "file": step["file"], "line": step["line"]})
    dd_dsn = {d["name"]: d["dsn"] for d in step["dds"] if d.get("dsn")}
    for dd in step["dds"]:
        if not dd.get("data"):
            continue
        for f, ln, text in _cards(dd["data"]):
            if pgm in TSO_PGMS:
                m = RUN_PROGRAM.search(text)
                if m:
                    runtime.append({"dst": m.group(1).upper(), "how": "TSO RUN PROGRAM", "file": f, "line": ln})
                if DSN_COMMAND.match(text):
                    runtime.append({"dst": "DSN", "how": "DB2 command processor", "file": f, "line": ln})
            elif pgm == "IDCAMS":
                m = _IDC_DELETE.match(text)
                if m:
                    writes.append({"dsn": m.group(2).upper(), "verb": m.group(1).upper(), "file": f, "line": ln})
                    continue
                m = _IDC_DEFINE.match(text)
                if m:
                    writes.append({"dsn": m.group(1).upper(), "verb": "DEFINE", "file": f, "line": ln})
                    continue
                m = _IDC_COPY.match(text)
                if m:
                    out = _OUTFILE.search(text)
                    dsn = dd_dsn.get(out.group(1).upper()) if out else None
                    if not dsn:
                        od = _OUTDATASET.search(text)
                        dsn = od.group(1).upper() if od else None
                    if dsn:
                        writes.append({"dsn": dsn, "verb": m.group(1).upper(), "file": f, "line": ln})
    return runtime, writes
