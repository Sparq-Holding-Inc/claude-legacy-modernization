# 04 Estimate

## Method

This is a judgment-based range, not a model. Lines of code do not drive it: the live tree is 11 lines across the job and two programs (`modernization-assessment/graph.json:46`, `modernization-assessment/graph.json:55`, `modernization-assessment/graph.json:73`). I built the range from the five drivers the skill names, and each is stated below with what the tree shows. The estimate is per wave. There is one wave.

| Driver | What the tree shows | Effect on the estimate | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | None visible. No dataset, contract or ordering edge. | Pushes the port cost down. It may also mean the tree is hiding its real boundary. | `modernization-assessment/graph.json:184` |
| Behavioral oracle | None in the tree. No dataset, report or log. | Makes the harness the largest and least certain cost. | `app/jcl/MAINJOB.jcl:2` |
| God modules in the wave | None. | No facade work. | `modernization-assessment/graph.json:179` |
| Business logic in the database | No SQL in any of the three programs. Inference from reading all three short files. | No DB2 work visible. Could still exist outside the tree. | `app/cbl/PGMMAIN.cbl:4` |
| Someone who can read the source language | Not known. Nothing in the tree says. | The port is trivial. The scheduler and job output are what a reader is needed for. | inference |

## Range for wave 1

| Part of wave 1 | Effort range | Evidence |
|---|---|---|
| Discovery: scheduler export, real outputs, confirm this is production source | 1 to 3 person-days of work, longer in elapsed time because it waits on the client | inference |
| Port of job, PGMMAIN and PGMLIVE | 0.5 to 1 person-day | `app/cbl/PGMMAIN.cbl:4` |
| Oracle capture and comparison harness | 3 to 8 person-days | inference |
| Shadow run beside MAINJOB before cutover | 5 to 10 nights elapsed, about 1 person-day of watching | inference |
| **Total** | **about 5 to 13 person-days of effort, and 3 to 4 weeks elapsed** | inference |

The port is not where the range comes from. The harness and the discovery are.

## What the range is most sensitive to

Stated as claims that can be shown false.

1. **Assumes the source in the tree is the production source.** PGMLIVE holds only a GOBACK and PGMMAIN only calls it (`app/cbl/PGMLIVE.cbl:4`, `app/cbl/PGMMAIN.cbl:4`). If the production versions read files, use DB2 or do arithmetic, then the port and harness numbers above no longer apply, and wave 1 must be cut again.
2. **Assumes MAINJOB is the whole nightly cycle.** The tree holds one job and no scheduler (`modernization-assessment/graph.json:197`). If the cycle is really ten more jobs outside the tree, this range covers a fraction of the work, and the order jobs run in becomes the main constraint on the plan.
3. **Assumes an oracle exists outside the tree.** The harness range assumes job output, logs or reports for at least one month-end can be had. If none exists, the harness cost roughly doubles, because only provisional characterization tests from the source remain.

## Where Claude Code helps and where it does not

| Part | Claude Code | Evidence |
|---|---|---|
| Transliterating the job step and two programs | Strong. There is almost nothing to translate. | `app/cbl/PGMLIVE.cbl:4` |
| Building the comparison harness and the normalization scaffold | Strong, once the client supplies real outputs | inference |
| Deciding what the nightly cycle must produce | Cannot. That intent is not in the source, and there is nothing to infer it from. | `app/jcl/MAINJOB.jcl:2` |
| Confirming MAINJOB is the nightly cycle, or that PGMDEAD never runs | Cannot from source. Needs the scheduler and job logs. | `modernization-assessment/graph.json:197` |
