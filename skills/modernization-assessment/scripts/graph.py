#!/usr/bin/env python3
"""Graph builder shared by the extractors. Python standard library only."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema  # noqa: E402

_RANK = {"low": 0, "medium": 1, "high": 2}


class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.unparsed = []

    # ------------------------------------------------------------- nodes

    def node(self, nid, unit_type, lang=None, path=None, loc=0, last_modified=None,
             entry_point=False, line=None, note=None, entry_evidence=None):
        """Create a node, or fill in a placeholder that an edge created earlier."""
        n = self.nodes.get(nid)
        if n is None:
            n = {"id": nid, "path": path, "unit_type": unit_type, "lang": lang, "loc": loc,
                 "last_modified": last_modified, "entry_point": bool(entry_point)}
            self.nodes[nid] = n
        else:
            if n.get("_placeholder"):
                n.update({"path": path, "unit_type": unit_type, "lang": lang, "loc": loc,
                          "last_modified": last_modified})
                del n["_placeholder"]
            if entry_point:
                n["entry_point"] = True
        if line is not None and "line" not in n:
            n["line"] = line
        if note:
            n["note"] = (n["note"] + "; " + note) if n.get("note") and note not in n["note"] else note
        if entry_evidence:
            ev = n.setdefault("entry_evidence", [])
            for e in entry_evidence:
                if e not in ev:
                    ev.append(e)
        return n

    def has(self, nid):
        return nid in self.nodes

    def ext(self, name, note=None):
        nid = schema.ext_id(name)
        if nid not in self.nodes:
            self.node(nid, "external", note=note)
        return nid

    def dynamic(self, source, line):
        nid = schema.dynamic_id(source, line)
        if nid not in self.nodes:
            self.node(nid, "external", note="computed target, cannot be resolved statically")
        return nid

    def dataset(self, nid, note=None):
        if nid not in self.nodes:
            self.node(nid, "dataset", note=note)
        elif note:
            self.node(nid, "dataset", note=note)
        return nid

    # ------------------------------------------------------------- edges

    def edge(self, src, dst, kind, evidence, mode=None, resolved=True, confidence="high", note=""):
        """Add an edge or merge evidence into the existing one."""
        ev = [{"file": f, "line": l} for f, l in evidence]
        key = (src, dst, kind, mode)
        e = self.edges.get(key)
        if e is None:
            self.edges[key] = {"src": src, "dst": dst, "kind": kind, "mode": mode,
                               "evidence": [], "resolved": resolved,
                               "confidence": confidence, "note": note}
            e = self.edges[key]
        else:
            if _RANK[confidence] > _RANK[e["confidence"]]:
                e["confidence"] = confidence
            e["resolved"] = e["resolved"] or resolved
            if note and note not in e["note"]:
                e["note"] = (e["note"] + "; " + note) if e["note"] else note
        seen = {(x["file"], x["line"]) for x in e["evidence"]}
        for x in ev:
            if (x["file"], x["line"]) not in seen:
                e["evidence"].append(x)
                seen.add((x["file"], x["line"]))
        return e

    # ------------------------------------------------------------ output

    def finalize(self):
        """Create placeholder nodes for dangling ends, then return sorted plain lists."""
        for (src, dst, _k, _m) in list(self.edges):
            for nid in (src, dst):
                if nid in self.nodes:
                    continue
                if nid.startswith(schema.EXTERNAL_PREFIX) or schema.is_dynamic(nid):
                    self.node(nid, "external")
                else:
                    self.node(nid, "external", note="referenced but never defined")
                    self.nodes[nid]["id"] = nid
        for e in self.edges.values():
            e["evidence"].sort(key=lambda x: (x["file"], x["line"]))
        nodes = [self.nodes[k] for k in sorted(self.nodes)]
        edges = [self.edges[k] for k in sorted(self.edges, key=lambda k: (k[2], k[0], k[1], str(k[3])))]
        return nodes, edges
