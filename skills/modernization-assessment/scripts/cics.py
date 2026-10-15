"""CICS system definition (CSD) reader. Python standard library only.

Reads DEFINE TRANSACTION, DEFINE PROGRAM and DEFINE FILE entries.

* A transaction maps a transaction id to a program. Those programs are entry
  points.
* A DEFINE PROGRAM marks a program as online.
* A DEFINE FILE maps a CICS file name to a dataset name. That is what lets an
  online program and a batch job meet on the same dataset node.
"""

import os
import re

CSD_EXT = {".csd"}
DEFINE = re.compile(r"^\s*DEFINE\s+([A-Z]+)\s*\(\s*([^)\s]+)\s*\)", re.I)
ATTR = lambda key: re.compile(r"(?<![A-Z0-9_-])" + key + r"\s*\(\s*([^)\s]+)\s*\)", re.I)
PROGRAM_ATTR = ATTR("PROGRAM")
DSNAME_ATTR = ATTR("DSNAME")


def parse_csd(root, rel):
    """Return dict(transactions, programs, files). Each value carries its line number."""
    with open(os.path.join(root, rel), "rb") as fh:
        lines = fh.read().decode("latin-1").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = []                    # [kind, name, first line, text]
    for i, raw in enumerate(lines, start=1):
        if raw.lstrip().startswith("*"):
            continue
        m = DEFINE.match(raw)
        if m:
            blocks.append([m.group(1).upper(), m.group(2).upper(), i, raw])
        elif blocks:
            blocks[-1][3] += " " + raw
    out = {"transactions": {}, "programs": {}, "files": {}}
    for kind, name, line, text in blocks:
        body = text[text.index(")") + 1:] if ")" in text else text
        if kind == "TRANSACTION":
            pm = PROGRAM_ATTR.search(body)
            if pm:
                out["transactions"][name] = (pm.group(1).upper(), line)
        elif kind == "PROGRAM":
            out["programs"][name] = line
        elif kind == "FILE":
            dm = DSNAME_ATTR.search(body)
            if dm:
                out["files"][name] = (dm.group(1).upper(), line)
    return out
