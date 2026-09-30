# 02 Coupling

Scope: `.` (three files: `app/jcl/JOBA.jcl`, `app/jcl/JOBB.jcl`, `app/scheduler/nightly.xml`). The edge facts are in `02a-edge-tables.md`. This file is the argument. Anything not read straight from `graph.json` is labeled `inference`.

## What is coupled to what

The extractor found 7 edges: 4 call, 2 include, 1 temporal. It found no data edge, no contract edge and no copybook include, because neither JCL member has a DD statement (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). There are no COBOL programs in the tree (`meta.files_seen`, cobol is 0). So the only coupling that constrains the sequence is temporal coupling.

| Pattern | What it does to the sequence | Confidence | Evidence |
|---|---|---|---|
| Temporal: JOBA posts condition JOBA-DONE and JOBB waits for it | JOBA and JOBB must move together and keep this order. The two JCL members do not mention each other, so a port that carries only the JCL keeps both jobs and loses the order | high | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |
| Consumed condition: JOBB deletes JOBA-DONE when it ends (SIGN `-`) and posts JOBB-DONE | The target scheduler must reproduce a condition that is posted, waited on, and then removed. The extractor deliberately does not draw an edge for the removal. Effect on a rerun of JOBB is `inference`: after the delete, a second run of JOBB would wait until JOBA posts the condition again | high for the fact, low for the effect | `app/scheduler/nightly.xml:10`, `app/scheduler/nightly.xml:11`, inference |
| External input: JOBA waits on EXTERNAL-FEED, which no job in the file sets | The start of the cycle depends on something outside the tree (another folder, another scheduler, a file watcher or an operator). It cannot be moved or tested from this tree | high for the fact | `app/scheduler/nightly.xml:5` |
| Unconsumed output: JOBB posts JOBB-DONE and no job in the file waits on it | Something outside the tree may depend on the end of the cycle. Whether anything does is `inference` | low | `app/scheduler/nightly.xml:11`, inference |

## Cluster graph

There is one cluster, the `NIGHTLY` folder (`app/scheduler/nightly.xml:3`). Both edges that leave it end outside the tree.

```mermaid
graph LR
  EXT["EXTERNAL-FEED (source unknown)"] --> A["NIGHTLY: JOBA"]
  A -- "JOBA-DONE" --> B["NIGHTLY: JOBB"]
  B --> OUT["JOBB-DONE (consumer unknown)"]
```

## Structure computed by the extractor

All of these are empty, from `analysis`: strongly connected components, self recursive programs, articulation points, god modules, data hubs. `analysis.structure_basis` says 0 of 0 programs were reachable, so there is no call graph to measure. This is an absence of application code in the tree, not evidence that the estate is simple. `analysis`

- Strongly connected components: none. No wave can split one. `analysis` field `sccs`
- God modules: none. `analysis` field `god_modules`
- Articulation points: none. The only candidate wave boundary is the condition JOBA-DONE, and cutting there means bridging a condition across two schedulers. That is not recommended. `analysis` field `articulation_points`

## The honest boundary

- Computed calls: 0 (`analysis` field `unresolved_dynamic`). Nothing here is open because of a computed call. There is no COBOL, so none can exist.
- Not parsed: nothing (`unparsed` is empty). Still, only Control-M XML and shell wrappers are read as schedulers (`meta.limits`). Any other scheduler folder, a calendar, or a run-time trigger for the same jobs would be invisible.
- The extractor does not model JCL `IF/THEN/ELSE` or `COND=` (`meta.limits`). Both members are two lines and contain neither, so nothing is hidden on that count (`app/jcl/JOBA.jcl:1`, `app/jcl/JOBB.jcl:1`).
- The scheduler entries carry no run time, calendar, cyclic or return code handling attributes (`app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`). When the cycle starts, on which days, and what happens when JOBA ends badly are not in the tree. Ending badly means JOBA-DONE is not posted and JOBB keeps waiting. That last effect is `inference` from how Control-M output conditions work.
- Both steps run IEFBR14, a system program outside the tree (`ext:IEFBR14`, `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). IEFBR14 does nothing. Either these are placeholders, or the real work is submitted from somewhere not in this tree. Which one is `inference` and is the first open question.

## Dependency work

The skill says to hand more than about 20 open edges to the dependency-cartographer. There are none: 0 computed calls, no `resolved: false` edge, and no `medium` or `low` confidence edge in `graph.json`. Nothing was handed off. All seven edges are `high` confidence.
