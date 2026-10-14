# 02 Coupling

Full edge list: `02a-edge-tables.md`. This tree holds two JCL jobs and one Control-M file. There are no COBOL programs, copybooks or datasets, so call, data and contract coupling are all empty. The only coupling that exists is temporal.

## Patterns that constrain the sequence

### 1. Temporal: JOBA must finish before JOBB (the whole cycle)

JOBA sets condition `JOBA-DONE` (`app/scheduler/nightly.xml:6`). JOBB requires it as an input condition (`app/scheduler/nightly.xml:9`). The extractor records this as one `temporal` edge from `sch:NIGHTLY/JOBA` to `sch:NIGHTLY/JOBB`, high confidence (`app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`). The two jobs cannot be split across a cutover boundary unless the scheduler that enforces the condition spans the boundary.

| Pattern | Edge | Confidence | Evidence |
|---|---|---|---|
| JOBA-DONE gates JOBB | `sch:NIGHTLY/JOBA` to `sch:NIGHTLY/JOBB` | high | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |

### 2. An external input the tree does not define

JOBA waits on `EXTERNAL-FEED` (`app/scheduler/nightly.xml:5`). No job in the file sets it, so something outside the tree does: another scheduler folder, a file watcher, an operator, or an upstream system. The extractor warns about this. The nightly cycle starts on it, so it is the true start of the cycle and it is not in scope of anything we can read. Confidence that it is external: high (nothing sets it in the file). What sets it: `inference`, unknown.

### 3. JOBB consumes the condition it was gated on

JOBB deletes `JOBA-DONE` with `SIGN="-"` (`app/scheduler/nightly.xml:10`). This is not an edge, as the extractor says. It is behavior. After JOBB is ordered, the condition is gone, so a second submit of JOBB in the same ODATE will wait until JOBA runs again. A port that models `JOBA-DONE` as a plain dependency (a DAG edge that stays satisfied) loses this one-shot behavior. Whether the delete is meant as run-once protection or housekeeping: `inference`. Ask the scheduler owner. Evidence: `app/scheduler/nightly.xml:10`.

## Strongly connected components

None (`analysis.sccs` is empty). No wave can split one.

## God modules and articulation points

None (`analysis.god_modules` and `analysis.articulation_points` are empty). There are no programs, so both are empty by construction rather than by finding.

## Cluster view

```mermaid
graph LR
    EXT[External feed<br/>EXTERNAL-FEED] --> A[NIGHTLY: JOBA]
    A -- JOBA-DONE --> B[NIGHTLY: JOBB]
```

## The honest boundary

- Computed calls: none (`analysis.unresolved_dynamic` is empty). Nothing to resolve.
- Both jobs run `IEFBR14` only (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). IEFBR14 is an IBM utility that does nothing. The JCL has no DD statements, so these jobs create and delete nothing. As written they sequence work and do no work. Either this is a stub, or the real work lives somewhere the scan did not see. This is the largest gap in the assessment, and it is Open Question 1 in `00-summary.md`.
- The extractor does not model JCL `IF/THEN/ELSE` or `COND=`, and reads only Control-M XML and shell wrappers as schedulers (`graph.json` `meta.limits`). Nothing in the tree uses them, so this limit does not change the result here.
- Control-M settings the XML does not carry in this file, such as run calendars, time windows (`FROM`/`TO`), `CONFIRM`, resources and quantitative or control resources, are absent from `nightly.xml`. We cannot see when the cycle is scheduled. `inference`: the ODAT-scoped conditions mean the cycle is date-driven.
