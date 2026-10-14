# 02 Coupling

The tree holds one JCL job and three COBOL programs. There is no shared data, no copybook, no computed call and no scheduler, so coupling is almost entirely temporal. `analysis` lists no strongly connected components, no god modules and no articulation points (`02a-edge-tables.md`, "Structure computed from the call graph").

## Patterns that constrain the sequence

| # | Pattern | Detail | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Temporal: strict step order in one job | STEP1 runs PGMA, then STEP2 runs PGMB, then STEP3 runs PGMC. The extractor reads step order as file order. | high | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4` |
| 2 | Duplicate step name | A fourth step is also named STEP2 and runs IEFBR14, a system no-op. The extractor renamed it STEP2#2. On z/OS, a repeated step name in one job is normally a JCL error and the job is rejected at conversion. This is `inference` from JCL rules. Nothing in the tree shows whether the real job runs. | low | `app/jcl/SEQJOB.jcl:5` |
| 3 | No data contract | No DD statements and no file I/O exist. The programs share no dataset, so the order in pattern 1 is not forced by data. The order may be the intent of the job, or only a habit. `inference` | medium | `app/cbl/PGMA.cbl:3`, `app/cbl/PGMB.cbl:3`, `app/cbl/PGMC.cbl:3` |

## Cluster graph

```mermaid
graph LR
  SEQJOB[job SEQJOB] --> A[PGMA]
  A --> B[PGMB]
  B --> C[PGMC]
  C --> N[IEFBR14 no-op]
```

Edges are sequence, not calls. The job runs each program in turn (`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5`).

## Structure

- Strongly connected components: none. Nothing to keep together.
- God modules: none. Each program is 4 lines (`app/cbl/PGMA.cbl:4`).
- Articulation points: none. There is no call graph to cut.

## Honest boundary

- Computed calls: 0 (`analysis` field `unresolved_dynamic` is empty). Each program only does `GOBACK` (`app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4`).
- The scheduler is missing. One JCL job has no parsed scheduler, so the order of this job against other jobs is unknown. The extractor warned on this.
- "The nightly batch cycle" maps to `job:SEQJOB` only by `inference`. Nothing in the tree says SEQJOB is nightly.
- The programs are stubs. Real logic may live elsewhere, so the tree may be a fragment of the real system. `inference`
