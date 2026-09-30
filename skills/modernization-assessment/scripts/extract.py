#!/usr/bin/env python3
"""Entry point. Builds graph.json from a legacy tree. STUB (phase 1)."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema  # noqa: E402


def build(target):
    return {"schema_version": schema.SCHEMA_VERSION, "nodes": [], "edges": [], "unparsed": []}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract a coupling graph from a legacy tree.")
    ap.add_argument("target", help="root of the tree to analyze")
    ap.add_argument("--out", default="modernization-assessment", help="output directory")
    args = ap.parse_args(argv)
    graph = build(os.path.abspath(args.target))
    errs = schema.validate("graph", graph)
    if errs:
        for e in errs:
            print("ERROR", e, file=sys.stderr)
        return 1
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "graph.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh, indent=2)
        fh.write("\n")
    print("wrote %s (%d nodes, %d edges)" % (path, len(graph["nodes"]), len(graph["edges"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
