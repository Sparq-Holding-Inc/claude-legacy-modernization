# 04 Estimate

All figures here are inference. There is no history, no team velocity and no oracle in the tree to calibrate against. Target state is `refactor`. Do not quote a single number from this file. Quote the range and the assumptions.

## Method

Estimated per wave from the factors that move effort, in the order the skill weights them, not from lines of code.

| Factor | Reading for wave 1 | Evidence |
|---|---|---|
| Coupling edges crossing the wave boundary | 0. Both include edges (PROGA and PROGB to SHARED01) sit inside the wave. | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:5` |
| Behavioral oracle available | None in the tree. No dataset, report, log or GDG is present. | inference |
| God modules in the wave | None. No call edges exist. | inference |
| Business logic in the database | Unknown. No SQL, no DB2 include. | inference |
| Team can read COBOL | Unknown. Not stated. | inference |
| Arithmetic sensitivity | Latent. `SH-BALANCE` is packed decimal but neither program uses it. | `app/cpy/SHARED01.cpy:3` |

## Wave 1 range

| Wave | Scope | Range | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Port PROGA and PROGB, re-express SHARED01 once, build the harness for the pair | 3 to 8 person-days for the visible code and its harness scaffolding | low | `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`, `app/cpy/SHARED01.cpy:1-3` |
| 1, if the surroundings turn out to matter | Same, plus the JCL, the file or interface that carries `SHARED-AREA`, and the nightly batch cycle order | 15 to 30 person-days | low | inference |

The first row assumes the visible 19 lines are the whole story. The second row is what happens if they are a fragment. The gap between the rows is the finding. The port itself is hours. The cost is in finding out what the programs are for, and building a definition of "correct" (see `06-test-strategy.md`).

## What the range is most sensitive to

State these as claims a client engineer can check.

1. **Assumes SHARED01 is included only by PROGA and PROGB.** If other programs outside this tree include it, wave 1 grows by one port per includer and the harness must cover each. Effort roughly scales with the number of includers.
2. **Assumes neither program reads or writes a dataset, and neither is started by a job that carries data between them.** The tree contains no `SELECT`, `FD` or JCL. If `SHARED-AREA` is the record of a file one program writes and the other reads, wave 1 gains a contract edge, the harness must diff that file, and the estimate roughly doubles.
3. **Assumes the literals 1 and 2 moved to `SH-CUST-ID` are stubs and not business rules.** If they are hardcoded customer ids, each needs its rule written down and signed off before the port. Evidence: `app/cbl/PROGA.cbl:7`, `app/cbl/PROGB.cbl:7`.

## Where Claude Code can do the mechanical port, and where it cannot

| Part | Claude Code | Evidence |
|---|---|---|
| Transliterate the two procedure divisions (one MOVE and GOBACK each) | Strong. Mechanical. | `app/cbl/PROGA.cbl:6-8`, `app/cbl/PROGB.cbl:6-8` |
| Re-express `SHARED-AREA` as one shared record type, with `SH-BALANCE` as a fixed-point decimal type | Strong, with a test that checks the packed decimal byte layout | `app/cpy/SHARED01.cpy:1-3` |
| Say what customer ids 1 and 2 mean, or where the programs run in the nightly batch cycle | Cannot. This is intent the source does not hold. The client engineers must answer it. | inference |
| Build the harness and choose the oracle | Claude Code can write the harness. It cannot supply the oracle. That has to come from the client (job output, reports, archived files). | inference |
