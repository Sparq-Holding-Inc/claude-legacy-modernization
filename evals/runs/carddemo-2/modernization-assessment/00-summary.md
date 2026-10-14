# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | Current directory (the whole tree) | No scope argument given |
| Target state | refactor | `--target refactor` |
| Must not break | Daily transaction posting, the account and card master refresh, and the transaction report | `--must-not-break` |
| Telemetry | none. Every dead-code claim is provisional. | `--telemetry none` |
| Delivery | Not given. The estimate shows conventional and AI-assisted side by side. | `--delivery` absent |
| Defaults applied | No defaults applied | All three scoping answers came as flags |

## What the tree is

A small card-processing demonstration: 44 COBOL programs, 62 copybooks, 55 JCL jobs, 6 procs, 21 BMS maps, one Control-M export, nine wrapper scripts and 22,489 lines of COBOL (`modernization-assessment/graph.json:24`, `modernization-assessment/01-inventory.md:20`). Nine waves, 123 units placed, one unit not placed (`modernization-assessment/waves.json:1`). The extractor found 318 call edges, 62 contract edges, 235 data edges and 133 ordering edges (`modernization-assessment/graph.json:28812`).

How the three must-not-break items map to units. None is missing from the tree.

| Item | Units | Wave | Evidence |
|---|---|---|---|
| Daily transaction posting | job:POSTTRAN, CBTRN02C, and the wrapper `run_posting.sh` | 6 | `app/jcl/POSTTRAN.jcl:23`, `scripts/run_posting.sh:26` |
| Account and card master refresh | job:ACCTFILE (account, wave 6). job:CARDFILE, XREFFILE and CUSTFILE (card, cross-reference, customer, wave 5). "Master refresh" could also mean the weekly reference-data refresh in Control-M. I took the first reading. | 5 and 6 | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:36`, `app/scheduler/CardDemo.controlm:26` |
| Transaction report | job:TRANREPT, CBTRN03C, and the online screen CORPT00C that submits the same procedure | 6 | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

## Largest risk

**The daily cycle is destructive, and there is no oracle in the tree.** The posting wrapper reloads the account master from a flat file, backs up and deletes the transaction master, and CBTRN02C then opens the transaction file for output and adds each posted amount to the account balance (`scripts/run_posting.sh:17`, `app/jcl/TRANBKP.jcl:40`, `app/cbl/CBTRN02C.cbl:256`, `app/cbl/CBTRN02C.cbl:547`). The state of the books at the end of a run is a function of a flat file and a chain of backup generations that are not in this tree. A port that is correct on every paragraph can still be wrong on the state it starts from. Interest truncates rather than rounds (`app/cbl/CBACT04C.cbl:465`), and the report job has its dates hard-coded to 2022 (`app/jcl/TRANREPT.jcl:43`). The risk is not complexity. It is that the three items that must not break all sit in one 29-unit wave (wave 6, blast radius high, confidence low), and the only way to prove them is a parallel run or archived generations that the client has to supply.

`risks.json` rates CBTRN02C, CBACT04C, CBTRN03C, CORPT00C, job:POSTTRAN, job:INTCALC and job:TRANREPT high on both port difficulty and blast radius (`modernization-assessment/risks.json:1`). That file is a first read and most scores are low confidence; only three programs were read closely.

## Estimate

94 to 160 engineer-weeks conventional, or 64 to 112 AI-assisted, for all nine waves. Waves 1 to 6, which carry the three items, are 40 to 68 conventional or 27 to 46 AI-assisted (`modernization-assessment/04-estimate.md:1`). These are planning assumptions with no calibrated data behind them.

## Open Questions for the client's engineers

1. **Is a parallel run possible for wave 6, and do archived generations of `TRANSACT.BKUP`, `DALYREJS` and `TRANREPT` exist for at least one month end and one year end?** Without them the oracle is characterization only (`modernization-assessment/06-test-strategy.md:1`).
2. **Is the account reload in front of posting intended?** `run_posting.sh` rebuilds the account master from `ACCTDATA.PS` before POSTTRAN, and CBTRN02C opens the transaction file for output. Which job writes the flat file back, and who owns the books between runs? (`scripts/run_posting.sh:17`, `app/jcl/ACCTFILE.jcl:57`)
3. **What do the 28 computed calls reach?** The list is at `modernization-assessment/05a-dead-code-candidates.md:61`. Send the program-name tables or the CICS transaction definitions. This decides the confidence of waves 3, 6, 7 and 9, and the status of CBTRN01C.
4. **Is CBTRN01C run?** No JCL runs it, and it reads the daily transaction file (`app/cbl/CBTRN01C.cbl:254`). If it is a pre-posting check, it belongs in wave 6.
5. **What does the CA-7 listing schedule?** `app/scheduler/CardDemo.ca7` is not parsed, so the 35 jobs reported as unscheduled may be scheduled there. Which of them still run? (`modernization-assessment/graph.json:27469`)
6. **Who owns the five shared VSAM masters during the transition?** Batch (wave 6) and online (wave 7) write the same files, and one side must go through an adapter (`modernization-assessment/graph.json:28699`).
7. **Are the transaction report's hard-coded dates (2022-01-01 to 2022-07-06) the production setting?** And is the online screen's report the same output as the batch job's? (`app/jcl/TRANREPT.jcl:43`, `app/cbl/CORPT00C.cbl:94`)
8. **Are the over-limit and expired reject codes the intended behavior when both apply?** The later test wins (`app/cbl/CBTRN02C.cbl:417`). Should the interest divide round? (`app/cbl/CBACT04C.cbl:465`). Both go in the Deviation Register.
9. **Do the assembler routines `COBDATFT` and `MVSWAIT` matter to posting or the batch window?** They are not read (`modernization-assessment/graph.json:27459`).

## Not parsed, and limits that touch this system

| Item | Effect | Evidence |
|---|---|---|
| IMS DBD and PSB files (4 each), DB2 DDL (6) and DCLGEN (3), control cards (8) | Wave 8 and 9 data structures are unseen | `modernization-assessment/graph.json:27435`, `modernization-assessment/graph.json:27449` |
| Assembler source and macros (2 each) | Date and wait routines are unseen | `modernization-assessment/graph.json:27459`, `modernization-assessment/graph.json:27464` |
| CA-7 scheduler listing | Unscheduled job count is overstated | `modernization-assessment/graph.json:27469` |
| DCB, LRECL, RECFM not read | Record length on a DD is not compared with a copybook. Contract edges rated high mean a shared layout, not proven equal. | `modernization-assessment/graph.json:20`, `modernization-assessment/graph.json:21` |
| IF/THEN/ELSE and COND= in JCL not modeled | Conditional steps look unconditional. TRANBKP's define step has `COND=(4,LT)`. | `modernization-assessment/graph.json:16`, `app/jcl/TRANBKP.jcl:51` |
| CICS RETURN TRANSID, START and SEND MAP are not edges | The screen flow is under-counted | `modernization-assessment/graph.json:18` |
| Jobs DEFCUST and TRANREPT repeat a step name | The extractor renamed the second step | `app/jcl/DEFCUST.jcl:32`, `app/jcl/TRANREPT.jcl:37` |
| Control-M `SIGN -` conditions | Deletions of conditions are not edges | `app/scheduler/CardDemo.controlm:10` |

## Files

`01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `03a-wave-seed.md`, `04-estimate.md`, `05-dead-code.md`, `05a-dead-code-candidates.md`, `06-test-strategy.md`, plus `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.
