# 04 Estimate

**Basis: both cases are shown, because `--delivery` was not given.** Conventional means a team without AI coding assistance. AI-assisted means engineers using an AI coding agent, with human review. This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark, and the team's measured velocity from wave 1 replaces it.

Figures are engineer-weeks, as ranges.

| Wave | Conventional | AI-assisted | Which term dominates | Evidence |
|---|---|---|---|---|
| 1. Master file reader (`PGMR`, `job:READJOB`) | 2 to 4 | 1.5 to 3 | Harness set-up and the oracle, not the port | `app/cbl/PGMR.cbl:13`, `app/jcl/READJOB.jcl:3` |
| 2. Master file writer (`PGMW`, `job:WRITEJOB`) | 2 to 5 | 1.5 to 4 | Byte-exact output, the record-length question, rehearsal | `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:4` |
| Total | 4 to 9 | 3 to 7 | | inference |

## Terms per wave, and whether AI assistance shrinks them

| Term | Shrinks with AI? | Assumption (falsifiable) | Evidence |
|---|---|---|---|
| Understanding the code | Already done | This assessment holds it. The programs are 16 lines each, so no discovery weeks are charged. What remains is the client's answers in `00-summary.md`. | `app/cbl/PGMR.cbl:1` |
| Port | Yes | Each program is 16 lines (`app/cbl/PGMR.cbl:16`). Assumes review of the ported code takes about a quarter of the authoring time it replaces, and under a day per program. | `app/cbl/PGMW.cbl:16` |
| Boundary work and harness code | Partly | The harness code is quick to write. Choosing the boundary (the dataset, bytes and all) and the normalization spec is not. Assumes one person-week for the comparison harness, reused in both waves. | inference |
| The oracle, approvals, rehearsals, cutover windows, client availability | **No** | Assumes the client can supply archived generations of the master file and a rehearsal window within two weeks of asking. This is the longest term in the conventional case and the same in the AI-assisted case. | inference |

## What the range is most sensitive to

1. **Assumes the client supplies real prior copies of `SPARQ.TEST.MASTER`, or its production equivalent.** If none exist, the oracle is a characterization test built from the source, and wave 2 is provisional and roughly doubles in effort to cover bad-data cases by hand.
2. **Assumes the 80-byte `LRECL` and the 15-byte copybook record are reconciled by a known convention** (for example, the real file holds 80-byte padded records and the program only needs the first 15). If they are not, wave 2 needs a decision from the client before work starts (`app/jcl/WRITEJOB.jcl:4`, `app/cpy/LAYOUTX.cpy:3`).
3. **Assumes the nightly cycle is these two jobs and nothing else.** If the real cycle has jobs not in this tree, this estimate covers only part of it and the total grows with them (`modernization-assessment/graph.json:383`).

## Where Claude Code can do the port, and where it cannot

- **Strong:** transliterating `PGMR` and `PGMW` once the comparison harness exists. They are straight sequential open, read or write, close (`app/cbl/PGMR.cbl:13`, `app/cbl/PGMW.cbl:13`).
- **Strong:** decoding and encoding `COMP-3` in a decimal type, when checked byte for byte against real records (`app/cpy/LAYOUTX.cpy:3`).
- **Weak:** inferring intent. `PGMW` writes `LAYOUT-REC` without moving any value into it (`app/cbl/PGMW.cbl:14`). Whether that is a deliberate empty test record, a stub or a defect is a question for a person (inference).
- **Weak:** knowing what the cycle is. Nothing in the tree names a nightly schedule.
