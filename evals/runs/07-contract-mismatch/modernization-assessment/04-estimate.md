# 04 Estimate

**Basis.** No `--delivery` flag was given, so every figure below shows two cases side by side: **conventional** (a team with no AI coding assistance) and **AI-assisted** (engineers using an AI coding agent, with human review). Neither is a headline. Pick the case that matches how the work will be done.

This plugin carries no calibrated productivity data. Every rate here is a planning assumption, not a benchmark. Replace it with the team's measured velocity once wave 1 is done.

## What is being estimated

Two COBOL programs of 16 lines each, two JCL jobs, two 3-line copybooks (`modernization-assessment/01-inventory.md`). The code is small enough that the port is not the cost. The cost is proving the nightly cycle still works.

## Per wave

Engineer-days, ranges. A day is one engineer.

| Wave | Term | Conventional | AI-assisted | Does AI assistance shrink it? | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 (PGMR, READJOB) | Port | 1 to 2 | 0.5 to 1 | Yes. 16 lines of transliteration; assumes review takes about as long as writing it would, since the program is so small | medium | `app/cbl/PGMR.cbl:1` |
| 1 | Boundary work (settle the record length and the layout) | 1 to 2 | 1 to 2 | No. The decision is whose layout wins, and that is a human call | medium | `app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTY.cpy:2` |
| 1 | Equivalence harness | 2 to 4 | 1.5 to 3 | Partly. The code is quick; choosing what to compare is not | medium | inference |
| 1 | Cutover and rehearsal | 1 to 3 | 1 to 3 | No. Depends on client availability and the cycle window | low | inference |
| 2 (PGMW, WRITEJOB) | Port | 1 to 2 | 0.5 to 1 | Yes, as above | medium | `app/cbl/PGMW.cbl:1` |
| 2 | Boundary work (decide: reproduce or initialise the record) | 2 to 4 | 2 to 4 | No. See assumption 2 | low | `app/cbl/PGMW.cbl:14` |
| 2 | Equivalence harness (byte-exact output compare) | 2 to 3 | 1.5 to 2.5 | Partly | medium | inference |
| 2 | Cutover, rollback rehearsal, dataset cleanup | 2 to 4 | 2 to 4 | No | low | `app/jcl/WRITEJOB.jcl:3` |

| Wave | Conventional total | AI-assisted total |
|---|---|---|
| 1 | 5 to 11 days | 4 to 9 days |
| 2 | 7 to 13 days | 6 to 11 days |
| Both | **12 to 24 days** | **10 to 20 days** |

Understanding the code is not charged. This assessment did it. What remains is the client's answers (see Open Questions in `modernization-assessment/00-summary.md`).

The gap between the two columns is small, and that is the point. On a tree this small, the terms that AI assistance does not shrink (the decision on the layout, the oracle, the rehearsals, the cycle window) are most of the work.

## What the range is most sensitive to

1. **The nightly cycle is bigger than these two jobs.** The figures assume `job:READJOB` and `job:WRITEJOB` are the whole must-not-break item. No scheduler is in the tree (`analysis.warnings`). If the cycle holds other jobs that touch `SPARQ.TEST.MASTER`, wave 2 roughly doubles, because each extra consumer needs its own boundary check.
2. **The writer's undefined output.** The figures assume a captured production output file exists to compare against. PGMW writes a record it never fills (`app/cbl/PGMW.cbl:14`). If no archive of that file exists, the oracle falls back to characterization tests from source, which here would test undefined bytes. Then wave 2 grows by the time to arrange a parallel run, roughly 5 to 10 more days, and its confidence is low.
3. **The record length.** The figures assume `LRECL=80` is the real record length and the padding is spaces or low values that the reader ignores (`app/jcl/WRITEJOB.jcl:4`, `app/cbl/PGMR.cbl:14`). If another consumer reads all 80 bytes, the 65 bytes after the layout are part of the contract and the harness must compare them.

## Where Claude Code can do the mechanical work

| Mechanical, strong with a harness | Weak, needs a person |
|---|---|
| Transliterating both programs (read, write, close) | Deciding whether to reproduce or fix the uninitialised record in PGMW |
| Writing the byte-exact comparison harness once the normalization spec is signed | Deciding the one true layout and record length |
| Checking that the two copybooks have equal pictures and offsets | Knowing what else reads the dataset, or what deletes it before `WRITEJOB` |
| Packed decimal (`COMP-3`) encode and decode in a decimal type | Rehearsals, approvals, and the cutover window |

## Not estimated

Any change to the scheduler, the dataset allocation policy, or jobs outside this tree. None of them is in the tree.
