"""Scheduler reader. Python standard library only.

Parses
------
* Control-M XML: JOB elements with INCOND and OUTCOND. A job that adds a
  condition (OUTCOND SIGN="+") comes before a job that waits for it (INCOND).
  A deletion (SIGN="-") makes no edge. Conditions match on NAME alone.
* Shell wrappers: a script that names JCL files (put jcl/A.jcl, submit
  A.jcl). Submits in file order give an order between jobs. Comment lines
  are skipped. References built from variables are not followed.

Reports as not parsed
---------------------
Anything that looks like a scheduler artifact and is neither of the above:
CA-7 listings, Autosys JIL, TWS, cron files. It is listed, never skipped
silently.
"""

import os
import re
import xml.parsers.expat

CONTROLM_EXT = {".controlm", ".xml", ".ctm"}
SHELL_EXT = {".sh", ".ksh", ".bash"}
UNPARSED_EXT = {".ca7": "CA-7 listing, not Control-M XML",
                ".jil": "Autosys JIL",
                ".tws": "IBM Workload Scheduler",
                ".cron": "cron table",
                ".crontab": "cron table"}
UNPARSED_NAMES = {"crontab": "cron table"}
JCL_REF = re.compile(r"([A-Za-z0-9#@$_.\-/]*?)([A-Za-z0-9#@$]+)\.jcl\b", re.I)


def looks_like_controlm(text):
    return "<DEFTABLE" in text[:4000] or "<FOLDER" in text[:4000] or "<SMART_FOLDER" in text[:4000]


def parse_controlm(root, rel):
    """Return dict(jobs=[...], error=None). Each job: folder, name, member, line, ins, outs."""
    with open(os.path.join(root, rel), "rb") as fh:
        data = fh.read()
    jobs, stack = [], []
    p = xml.parsers.expat.ParserCreate()

    def start(name, attrs):
        line = p.CurrentLineNumber
        top = name.upper()
        if top in ("FOLDER", "SMART_FOLDER"):
            stack.append((top, attrs.get("FOLDER_NAME") or attrs.get("JOBNAME") or "", line))
        elif top == "JOB":
            folder = next((s[1] for s in reversed(stack) if s[0] in ("FOLDER", "SMART_FOLDER")), "")
            job = {"folder": folder, "name": attrs.get("JOBNAME", ""), "member": attrs.get("MEMNAME") or
                   attrs.get("JOBNAME", ""), "line": line, "ins": [], "outs": [], "dels": []}
            jobs.append(job)
            stack.append(("JOB", job, line))
        elif top in ("INCOND", "OUTCOND") and stack and stack[-1][0] == "JOB":
            job = stack[-1][1]
            if top == "INCOND":
                job["ins"].append((attrs.get("NAME", ""), line))
            elif attrs.get("SIGN", "+") == "+":
                job["outs"].append((attrs.get("NAME", ""), line))
            else:
                job["dels"].append((attrs.get("NAME", ""), line))
            stack.append(("COND", None, line))
        else:
            stack.append(("OTHER", None, line))

    def end(name):
        if stack:
            stack.pop()

    p.StartElementHandler, p.EndElementHandler = start, end
    try:
        p.Parse(data, True)
    except xml.parsers.expat.ExpatError as exc:
        return {"jobs": jobs, "error": str(exc)}
    return {"jobs": jobs, "error": None}


def condition_edges(jobs):
    """(producer job, consumer job, producer line, consumer line) for every matching condition."""
    prod, cons = {}, {}
    for j in jobs:
        for nm, ln in j["outs"]:
            prod.setdefault(nm, []).append((j, ln))
        for nm, ln in j["ins"]:
            cons.setdefault(nm, []).append((j, ln))
    out = []
    for nm in sorted(set(prod) & set(cons)):
        for pj, pl in prod[nm]:
            for cj, cl in cons[nm]:
                if pj is not cj:
                    out.append((pj, cj, pl, cl, nm))
    return out


def condition_notes(jobs, rel):
    """Things the graph cannot show: a condition nobody sets, and a condition a job deletes."""
    made = {nm for j in jobs for nm, _ in j["outs"]}
    notes = []
    for j in jobs:
        for nm, ln in j["ins"]:
            if nm not in made:
                notes.append("%s:%d: job %s waits for condition %s, which no job in this file sets. It is an external input." % (rel, ln, j["name"], nm))
        for nm, ln in j["dels"]:
            notes.append("%s:%d: job %s deletes condition %s (SIGN -). That order is not an edge." % (rel, ln, j["name"], nm))
    return notes


def parse_shell(root, rel, known_jcl):
    """Ordered list of (job file stem, line) for submits of known JCL files.

    known_jcl maps a lower case JCL file stem to something truthy when that file exists.
    """
    with open(os.path.join(root, rel), "rb") as fh:
        text = fh.read().decode("latin-1")
    subs = []
    for i, raw in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        if raw.lstrip().startswith("#"):
            continue
        code = raw.split(" #", 1)[0]
        for m in JCL_REF.finditer(code):
            stem = m.group(2)
            if "$" in m.group(1) or code[max(0, m.start() - 1):m.start()] == "$":
                continue
            if stem.lower() in known_jcl:
                subs.append((stem, i))
    return subs


def unparsed_reason(rel):
    base = os.path.basename(rel).lower()
    ext = os.path.splitext(base)[1]
    if ext in UNPARSED_EXT:
        return UNPARSED_EXT[ext]
    if base in UNPARSED_NAMES:
        return UNPARSED_NAMES[base]
    return None
