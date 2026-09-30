#!/usr/bin/env python3
"""Is the eval able to fail? Break the extractor on purpose and see who notices.

    python3 evals/mutation_check.py

Each mutation swaps one snippet of extractor source for a broken version, runs
the seeded fixtures, and lists the fixtures that fail. A mutation that no
fixture catches is a blind spot in the fixtures, and it is reported as one.
The plugin source on disk is never modified. Python standard library only.
"""

import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
SCRIPTS = os.path.join(PLUGIN, "skills", "modernization-assessment", "scripts")
sys.path.insert(0, HERE)
sys.path.insert(0, SCRIPTS)

MODULES = ["extract", "cobol", "jcl", "scheduler", "analyze", "cics", "graph", "schema"]

# (name, module, old snippet, new snippet)
MUTATIONS = [
    ("string literals not masked", "cobol", "        self.masked = mask(code)", "        self.masked = code"),
    ("COPY never expanded", "cobol", "found = lib.find(name) if do_expand else None", "found = None"),
    ("quoted COPY names unsupported", "cobol",
     'COPY_STMT = re.compile(r"COPY\\s+(?:([\'\\"])(" + MASK + r"+)\\1|(" + NAME + r"))", I)',
     'COPY_STMT = re.compile(r"COPY\\s+()()(" + NAME + r")", I)'),
    ("columns 73 to 80 read as code", "cobol", 'code = line[7:72] if len(line) > 7 else ""',
     'code = line[7:80] if len(line) > 7 else ""'),
    ("comment indicator ignored", "cobol", 'if ind in "*/":\n            continue', 'if False:\n            continue'),
    ("dash continuation ignored", "cobol", 'if ind == "-" and segs:', 'if False and segs:'),
    ("constants not resolved", "cobol",
     "if up in self.values and up not in self.receivers and up not in self.literal_moves:", "if False:"),
    ("OPEN OUTPUT read as read", "cobol", '"OUTPUT": "write"', '"OUTPUT": "read"'),
    ("layout from READ INTO and WRITE FROM off", "cobol",
     "if rec is None or rec in f.local_records:", "if True:"),
    ("layout from FD COPY off", "cobol", "f.fd_layout[fname] = cpys", "f.fd_layout[fname] = []"),
    ("PROC DD overrides ignored", "jcl", "for (pstep, dname, params, line) in st.overrides:",
     "for (pstep, dname, params, line) in []:"),
    ("symbolic parameters not substituted", "jcl", "        if key in symbols:", "        if False:"),
    ("repeated step names not suffixed", "jcl",
     'sid = "%s.%s" % (unit.name, name) + ("#%d" % seen[name] if seen[name] > 1 else "")',
     'sid = "%s.%s" % (unit.name, name)'),
    ("Control-M deletions counted as producers", "scheduler", 'elif attrs.get("SIGN", "+") == "+":', "else:"),
    ("shell comments read as submits", "scheduler", 'if raw.lstrip().startswith("#"):\n            continue',
     'if False:\n            continue'),
    ("step order edges off", "extract", "for a, b in zip(execs, execs[1:]):", "for a, b in []:"),
    ("contract edges off", "extract", "for dsid, side in sorted(by_ds.items()):", "for dsid, side in []:"),
    ("contract confidence always high", "extract", 'shared = ws["layouts"] & rs["layouts"]',
     'shared = {"cpy:X"}'),
    ("computed calls dropped", "extract", 'if kind != "constant":\n                g.edge(pid, dyn_id',
     'if False:\n                g.edge(pid, dyn_id'),
    ("CSD entry points off", "extract", '        n["entry_point"] = True\n        n.setdefault',
     '        n.setdefault'),
    ("git dates off", "extract", "dates = git_dates(root) if use_git else {}", "dates = {}"),
    ("subscripted names resolved like plain names", "cobol", 'if subscripted:\n            return "dynamic", []',
     'if False:\n            return "dynamic", []'),
    ("EXEC SQL text visible to CALL scan", "cobol", 'nonexec = "".join(nonexec)', 'nonexec = masked'),
    ("CICS DELETE read as read", "cobol", '"DELETE": "write"', '"DELETE": "read"'),
    ("CICS REWRITE read as read", "cobol", '"REWRITE": "write"', '"REWRITE": "read"'),
    ("OPEN I-O read as read", "cobol", '"I-O": "read_write"', '"I-O": "read"'),
    ("generation and member suffix kept on DSN", "jcl", "up = re.sub(r\"\\([^)]*\\)$\", \"\", up)", "up = up"),
    ("temporary datasets kept (equivalent: a later guard drops any name still holding an ampersand)",
     "jcl", 'if raw.startswith("&&"):', 'if False:', "equivalent"),
    ("dead code: dynamic calls ignored", "analyze", "if reachable_dynamic:", "if False:"),
    ("dead code: dormancy off", "analyze", "if d < threshold:", "if False:"),
    ("dead code: no entry point guard", "analyze", "if not entries:", "if False:"),
]


def load_fresh(mutation):
    """Import the extractor from source with one snippet swapped."""
    for m in MODULES:
        sys.modules.pop(m, None)
    if mutation:
        _name, mod, old, new = mutation[:4]
        path = os.path.join(SCRIPTS, mod + ".py")
        src = open(path).read()
        if old not in src:
            raise SystemExit("mutation target not found in %s.py: %r" % (mod, old[:60]))
        module = types.ModuleType(mod)
        module.__file__ = path
        sys.modules[mod] = module
        exec(compile(src.replace(old, new, 1), path, "exec"), module.__dict__)
    import extract
    return extract


def run(runner, extract_mod):
    runner.extract = extract_mod
    runner.schema = sys.modules["schema"]
    results, _total, _ev = runner.run_fixtures("2026-09-30")
    return [c for c, r in results.items() if not r["pass"]]


def main():
    import run_extractor_evals as runner
    baseline = run(runner, load_fresh(None))
    if baseline:
        print("Baseline already fails: %s. Fix that first." % baseline)
        return 2
    print("baseline: all fixtures pass\n")
    blind, table = [], []
    for mut in MUTATIONS:
        failed = run(runner, load_fresh(mut))
        tag = ", ".join(c.split("-")[0] for c in failed) if failed else "NOT CAUGHT"
        table.append({"mutation": mut[0], "caught_by": [c.split("-")[0] for c in failed],
                      "equivalent": len(mut) > 4})
        print("%-46s %s" % (mut[0], tag))
        if not failed and len(mut) > 4 and mut[4] == "equivalent":
            print("    (equivalent mutant, not counted as a blind spot)")
        elif not failed:
            blind.append(mut[0])
    load_fresh(None)
    import json
    os.makedirs(os.path.join(HERE, "scorecard"), exist_ok=True)
    json.dump({"mutations": table, "blind_spots": blind}, open(os.path.join(HERE, "scorecard", "mutation.json"), "w"),
              indent=1)
    eq = sum(1 for m in MUTATIONS if len(m) > 4)
    print("\n%d mutations: %d caught, %d equivalent, %d blind spots" %
          (len(MUTATIONS), len(MUTATIONS) - len(blind) - eq, eq, len(blind)))
    for b in blind:
        print("  blind spot:", b)
    return 1 if blind else 0


if __name__ == "__main__":
    sys.exit(main())
