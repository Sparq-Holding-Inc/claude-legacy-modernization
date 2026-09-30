#!/usr/bin/env python3
"""Stop hook. A finished assessment cannot leave with a citation that does not resolve.

It does nothing unless modernization-assessment/.in-progress exists and its
state is "done". The command writes that marker (see marker.py). Plugin hooks
fire in every session where the plugin is enabled. The marker keeps this out of
unrelated work.

When the marker says done, it checks:
  1. every path:line or path:line-line in the markdown files resolves to a real
     file and a line inside it,
  2. every row of a findings table (a table with an Evidence or Citation
     column) carries a citation or the word "inference",
  3. every required JSON output exists and validates against schema.py, and
     every evidence entry in them resolves.

First failure: it blocks the stop and lists what to fix.
Second failure: it lets the stop through and appends an "Unresolved citations"
section to 00-summary.md. It never loops. The loop guard is the marker's own
attempt counter, and the stop_hook_active flag as well.
On a clean check it removes the marker.

Python standard library only. Any error inside the hook lets the stop through.
"""

import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "modernization-assessment", "scripts"))
import schema  # noqa: E402

OUT = "modernization-assessment"
MARKER = ".in-progress"
STALE_HOURS = 12
MAX_LISTED = 30

EXT = ("cbl|cob|cobol|cpy|copy|jcl|job|prc|proc|csd|bms|xml|controlm|sh|ksh|bash|ctl|asm|mac|txt|md|json|"
       "py|ddl|dcl|dbd|psb|sql|ca7")
CITATION = re.compile(r"(?<![\w/.\-:])((?:[\w.\-]+/)*[\w.\-]+\.(?:%s)):(\d+)(?:-(\d+))?(?![\w])" % EXT, re.I)
FENCE = re.compile(r"^\s*(```|~~~)")
EVIDENCE_HEADER = re.compile(r"\b(evidence|citation|cite)\b", re.I)


def find_out_dir(cwd):
    for base in (cwd, os.environ.get("CLAUDE_PROJECT_DIR") or ""):
        if base and os.path.exists(os.path.join(base, OUT, MARKER)):
            return os.path.join(base, OUT)
    return None


class Resolver:
    def __init__(self, roots):
        self.roots = [r for r in roots if r]
        self.lines = {}

    def count(self, path):
        if path not in self.lines:
            n = None
            if os.path.isabs(path):
                cands = [path]
            else:
                cands = [os.path.join(r, path) for r in self.roots]
            for c in cands:
                if os.path.isfile(c):
                    with open(c, "rb") as fh:
                        n = fh.read().count(b"\n") + 1
                    break
            self.lines[path] = n
        return self.lines[path]

    def problem(self, path, start, end):
        n = self.count(path)
        if n is None:
            return "%s:%d does not exist (no such file)" % (path, start)
        hi = end if end else start
        if start < 1 or hi < start or hi > n:
            return "%s:%d%s is outside the file (%d lines)" % (path, start, "-%d" % end if end else "", n)
        return None


def split_row(line):
    parts = re.split(r"(?<!\\)\|", line.strip())
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def check_markdown(path, res):
    problems = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")
    rel = os.path.basename(path)
    in_fence = False
    table_ev_col = None
    for i, raw in enumerate(lines, start=1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in CITATION.finditer(raw):
            if "://" in raw[max(0, m.start() - 8):m.start()]:
                continue
            p = res.problem(m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
            if p:
                problems.append("%s line %d: %s" % (rel, i, p))
        stripped = raw.strip()
        if stripped.startswith("|"):
            cells = split_row(stripped)
            if table_ev_col is None:
                hdr = [k for k, c in enumerate(cells) if EVIDENCE_HEADER.search(c)]
                table_ev_col = ("header", hdr[0] if hdr else -1)
                continue
            if table_ev_col[0] == "header":
                table_ev_col = ("body", table_ev_col[1])       # this is the |---|---| rule
                continue
            k = table_ev_col[1]
            if k >= 0:
                cell = cells[k] if k < len(cells) else ""
                if not (CITATION.search(cell) or re.search(r"\binference\b", cell, re.I)):
                    problems.append("%s line %d: a findings table row has no citation and is not labeled "
                                    "inference: %s" % (rel, i, stripped[:90]))
        else:
            table_ev_col = None
    return problems


def evidence_lists(obj):
    """Yield every evidence entry found anywhere in a JSON output."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "evidence" and isinstance(v, list):
                for e in v:
                    if isinstance(e, dict) and "file" in e and "line" in e:
                        yield e
            else:
                yield from evidence_lists(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from evidence_lists(v)


def check_json(out_dir, marker, res):
    problems, graph, docs = [], None, {}
    kinds = {"graph.json": "graph", "waves.json": "waves", "dead-code.json": "dead-code", "risks.json": "risks"}
    required = marker.get("require", [])
    for name in kinds:
        p = os.path.join(out_dir, name)
        if not os.path.exists(p):
            if name in required:
                problems.append("%s is missing. The assessment must write it." % name)
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                docs[name] = json.load(fh)
        except ValueError as exc:
            problems.append("%s is not valid JSON: %s" % (name, exc))
    graph = docs.get("graph.json")
    for name, doc in docs.items():
        errs = schema.validate(kinds[name], doc, graph if name != "graph.json" else None)
        for e in errs[:10]:
            problems.append("%s does not validate: %s" % (name, e))
        if len(errs) > 10:
            problems.append("%s has %d more schema errors" % (name, len(errs) - 10))
        bad = 0
        for e in evidence_lists(doc):
            p = res.problem(e["file"], int(e["line"]), None) if isinstance(e["line"], int) else "bad line"
            if p:
                bad += 1
                if bad <= 5:
                    problems.append("%s evidence: %s" % (name, p))
        if bad > 5:
            problems.append("%s has %d more evidence entries that do not resolve" % (name, bad - 5))
    return problems


def write_marker(path, data):
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    cwd = event.get("cwd") or os.getcwd()
    out_dir = find_out_dir(cwd)
    if not out_dir:
        return 0
    mpath = os.path.join(out_dir, MARKER)
    try:
        with open(mpath) as fh:
            marker = json.load(fh)
    except (OSError, ValueError):
        return 0
    try:
        started = datetime.datetime.fromisoformat(marker.get("started", ""))
        if datetime.datetime.now(datetime.timezone.utc) - started > datetime.timedelta(hours=STALE_HOURS):
            os.remove(mpath)
            return 0
    except (ValueError, OSError):
        pass
    if marker.get("state") != "done":
        return 0

    project = os.path.dirname(out_dir)
    res = Resolver([marker.get("target"), project, cwd])
    problems = []
    for name in sorted(os.listdir(out_dir)):
        if name.endswith(".md"):
            problems += check_markdown(os.path.join(out_dir, name), res)
    problems += check_json(out_dir, marker, res)

    if not problems:
        os.remove(mpath)
        return 0

    already_tried = bool(event.get("stop_hook_active")) or marker.get("attempts", 0) >= 1
    if already_tried:
        summary = os.path.join(out_dir, "00-summary.md")
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n## Unresolved citations\n\n"
                     "The citation check failed twice. These problems were still present when the "
                     "assessment finished. Treat the affected claims as unverified.\n\n")
            for p in problems[:MAX_LISTED]:
                fh.write("- %s\n" % p)
            if len(problems) > MAX_LISTED:
                fh.write("- and %d more\n" % (len(problems) - MAX_LISTED))
        os.remove(mpath)
        return 0

    marker["attempts"] = marker.get("attempts", 0) + 1
    write_marker(mpath, marker)
    listed = "\n".join("- " + p for p in problems[:MAX_LISTED])
    more = "\n- and %d more" % (len(problems) - MAX_LISTED) if len(problems) > MAX_LISTED else ""
    reason = ("The assessment is not finished. The citation check found %d problem(s):\n%s%s\n\n"
              "Fix each one. A citation must name a real file and a line inside it. If you cannot "
              "cite a claim, label it 'inference'. Every JSON output must validate: run "
              "`python3 \"${CLAUDE_PLUGIN_ROOT}/skills/modernization-assessment/scripts/schema.py\" "
              "validate-dir modernization-assessment`. Then finish again."
              % (len(problems), listed, more))
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # a broken hook must never trap the user
        print("check_citations.py: %r" % (exc,), file=sys.stderr)
        sys.exit(0)
