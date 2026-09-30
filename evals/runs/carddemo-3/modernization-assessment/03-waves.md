# 03 Waves

Target state: refactor. What must not break: daily transaction posting, the account and card master refresh, and the transaction report. The machine-readable plan is `waves.json`. Scores are in `risks.json`. Every unit in the plan is a node in `graph.json`.

The plan has 8 waves. This system is not one job and a handful of programs. It has 44 programs, 55 JCL jobs, three shared-file families, two runtimes on the same files (batch and CICS), and a batch cycle whose order lives in three schedulers. If it were ten times larger I would cut it the same way and add waves inside the online block: one per menu branch behind the router described in wave 5.

## How the waves are ordered

The rule is learning per unit of blast radius, not business value. Low-low first, then high-low, then low-high once the harness is proven, then high-high last and strangled behind a facade. The scores are in `risks.json`. Quadrants: 39 units low-low, 20 high-low, 24 low-high, 16 high-high.

Three places where the plan bends that rule. I say so plainly.

1. **Two high-high units sit in the first half.** CBTRN03C, the transaction report program, is in wave 2, and CBTRN02C, the posting program, is in wave 4. CBTRN03C scores 3 and 3. It goes early because it is the only high-high unit that writes nothing to a system of record, it can be rerun, and its output can be compared byte for byte. It is on the must-not-break list, so it also earns the first real test of the harness. CBTRN02C is in wave 4 because posting is a must-not-break item and everything after it depends on a settled account and transaction master. It is not ported. It runs in shadow beside the legacy run until the diff is clean (see wave 4).
2. **Wave 8 breaks the quadrant rule on purpose.** 15 of its 21 scored units are high-low. By the rule they would go early. They are last because this plugin does not analyze IMS, DB2 or MQ, so their scores are low confidence, and because nothing in the core depends on them. If the client has an IMS and DB2 specialist, pull COBTUPDT, COTRTLIC and COTRTUPC forward to wave 1 to learn embedded SQL where it cannot hurt.
3. **The online programs may form one large cycle.** See `02-coupling.md`. The validator accepts the plan because the extractor found only three small cycles. The menu table is a routing table, and wave 5 must prove a router before wave 6 starts (inference).

Each wave meets the four tests: it deploys behind a flag or facade, it rolls back on its own, it has a testable boundary, and a business person can name what it delivers. The table says what each one is.

## Summary

| Wave | Name | Units | Quadrants | Blast | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | Read-only batch extracts and setup | 6 programs, 10 jobs, 1 proc | 13 low-low, 3 high-low | low | medium | `app/jcl/READACCT.jcl:32`, `app/jcl/CBEXPORT.jcl:43`, `app/cbl/CBACT01C.cbl:231` |
| 2 | Transaction report | 1 program, 1 job, 1 proc | 1 high-high, 1 low-high | medium | medium | `app/jcl/TRANREPT.jcl:59`, `app/proc/TRANREPT.prc:57`, `app/cbl/CORPT00C.cbl:94` |
| 3 | Master and reference data refresh | 12 jobs, 2 scheduler entries | 5 low-low, 7 low-high | high | medium | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:75`, `scripts/remote_refresh.sh:20` |
| 4 | Daily transaction posting | 1 program, 4 jobs, 2 scheduler entries | 4 low-high, 1 high-high | high | medium | `app/jcl/POSTTRAN.jcl:23`, `app/jcl/TRANBKP.jcl:40`, `scripts/run_posting.sh:26` |
| 5 | Online sign-on, menus and inquiry | 8 programs, 1 job | 4 low-high, 3 low-low, 2 high-high | medium | low | `app/cbl/COMEN01C.cbl:156`, `app/cbl/COSGN00C.cbl:223` |
| 6 | Online maintenance and payment | 10 programs | 4 high-high, 3 low-high, 2 low-low, 1 high-low | high | low | `app/cbl/COBIL00C.cbl:212`, `app/cbl/COACTUPC.cbl:573` |
| 7 | Month-end interest and statements | 3 programs, 4 jobs, 4 scheduler entries | 4 high-high, 2 low-high, 1 high-low | high | medium | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBSTM03A.CBL:300`, `app/jcl/INTCALC.jcl:22` |
| 8 | Authorization (IMS, DB2, MQ) and transaction-type (DB2) | 13 programs, 8 jobs, 2 scheduler entries | 15 high-low, 4 high-high, 1 low-high, 1 low-low | medium | low | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/app-transaction-type-db2/jcl/MNTTRDB2.jcl:30` |

## Wave 1. Read-only batch extracts and setup

Units: CBACT01C, CBACT02C, CBACT03C, CBCUS01C, CBEXPORT, CBIMPORT, their jobs, PRTCATBL, the three setup jobs that define generation datasets (DEFGDGB, DALYREJS, REPTFILE), and the proc REPROC.

- Why first: every unit reads a master or writes a dataset that nothing else reads. A wrong result cannot reach a master. The three small readers are about 130 lines each and each reads one file through one layout copybook (`app/cbl/CBACT02C.cbl:29`).
- Port order: CBACT02C, CBACT03C, CBCUS01C (prove the toolchain and the KSDS access layer), then the generation dataset jobs (the archive that later waves use as oracle), then CBACT01C (assembler date routine, `app/cbl/CBACT01C.cbl:231`), then CBEXPORT and CBIMPORT (COMP-3 export, `app/cpy/CVEXPORT.cpy:41`).
- Unblocks: the toolchain, four record layouts, the decimal type mapping, and a CBEXPORT snapshot of five masters to seed the oracle for waves 2 to 4.
- Rollback: rerun the legacy job. Nothing shared has changed.
- Delivers: the master file listings and the export and import utilities that the business uses for branch migration (`app/jcl/CBEXPORT.jcl:19`).

## Wave 2. Transaction report

Units: CBTRN03C, job TRANREPT, proc TRANREPT.

- Must-not-break item 3. It reads a copy of the transaction master, three reference files and a date parameter, and writes one report generation.
- What ships behind what: the new report program runs against the same input generation and the outputs are diffed. The proc name `TRANREPT` stays resolvable, so the JCL text that the online screen submits (`app/cbl/CORPT00C.cbl:94`) runs the new implementation without a change to CORPT00C (inference).
- The legacy report has behavior a port must copy or a person must decide to drop. See `06-test-strategy.md`, deviations D-001 and D-002.
- Unblocks: the first byte-level comparison against a must-not-break output, and a settled definition of the offsets in `02-coupling.md` pattern 3.
- Rollback: point the proc name back at the legacy step. The report is read only.
- Delivers: the transaction report.

## Wave 3. Master and reference data refresh

Units: ACCTFILE, CARDFILE, CUSTFILE, XREFFILE, DISCGRP, TCATBALF, TRANCATG, TRANTYPE, DUSRSECJ, ESDSRRDS, DEFGDGD, DEFCUST, the refresh wrapper script, and the weekly disclosure-group entry.

- Must-not-break item 2, the account and card master refresh. No COBOL runs. Each job deletes a cluster, defines it, and loads it from a flat file (`app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:61`).
- The port is a data-store load. The check is a state diff of the loaded file against the legacy file. That is a different harness from wave 2, and the reason it follows wave 2.
- Two hazards to fix in the port, not copy: the delete comes before the reload, so a failed load leaves no master (`app/jcl/ACCTFILE.jcl:25`), and the CICS close and open commands are spread over CLOSEFIL, OPENFIL and three of the refresh jobs, each with the region name written in (`app/jcl/CARDFILE.jcl:26`, `app/jcl/CUSTFILE.jcl:26`, `app/jcl/TRANFILE.jcl:26`).
- Unblocks: masters in a known state to seed the wave 4 harness. A reset path between test runs.
- Rollback: reload the previous generation. Take the backup before the wave, because these jobs destroy the file.
- Delivers: the refresh of the account, card, customer and cross-reference masters and the reference tables.

## Wave 4. Daily transaction posting

Units: CBTRN02C, jobs POSTTRAN, TRANBKP, TRANIDX and TRANFILE, the posting wrapper script, and the daily backup entry.

- Must-not-break item 1. High-high, so it is strangled. The new posting reads the same daily file and runs in shadow on a copy of the masters. Its account master, category balance file and transaction master are diffed against the legacy result. The legacy run stays the system of record until the diff is clean for a full month cycle.
- The cut is at the datasets: the daily transaction file in, the reject generation out, and the three masters. That is the testable boundary (`app/jcl/POSTTRAN.jcl:28`, `app/jcl/POSTTRAN.jcl:38`).
- Two things to decide before any code moves. First, which order is real: see the four in `02-coupling.md` pattern 2. Second, what the transaction master is for. TRANBKP backs it up and then empties it (`app/jcl/TRANBKP.jcl:40`), and only COMBTRAN, in the monthly flow, puts it back (`app/jcl/COMBTRAN.jcl:48`).
- Unblocks: a settled account and transaction master for waves 5 to 7.
- Rollback: keep the legacy job as the primary, switch the flag back, and restore the masters from the pre-run generation.
- Delivers: the daily posting of transactions.

## Wave 5. Online sign-on, menus and inquiry

Units: COSGN00C, COMEN01C, COADM01C, COACTVWC, COTRN00C, COTRN01C, CORPT00C, CSUTLDTC, and the CSD definition job CBADMCDJ.

- The sign-on and menu programs are one cycle and move together. So do the transaction list and detail (`02-coupling.md`).
- The key deliverable is the router. Menu options are program names in a table (`app/cpy/COMEN02Y.cpy:28`), and the router resolves an entry to the legacy screen or the new one. Without it, wave 6 cannot move one screen at a time.
- Authentication cannot be a copy. Sign-on compares a clear-text 8 character password (`app/cbl/COSGN00C.cbl:223`) and user maintenance stores it (`app/cbl/COUSR01C.cbl:157`). That is a deviation, D-009.
- CORPT00C moves here. Its submitted JCL text names the proc that wave 2 already ported (`app/cbl/CORPT00C.cbl:94`).
- Rollback: route every menu entry back to the legacy screen.
- Delivers: sign-on, menus, account view, transaction list and view, and the report screen.

## Wave 6. Online maintenance and payment

Units: COACTUPC, COCRDLIC, COCRDSLC, COCRDUPC, COBIL00C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C.

- These screens write the masters. They go after posting so there is one writer model for the account and transaction masters.
- The transaction key is the highest key plus one (`app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`). Two sessions can collide. Pick one key scheme for all writers, including batch, before this wave (deviation D-010).
- COACTUPC is 3368 lines. It is not a god module by the extractor's rule. Port it by screen section, behind the router, not in one commit.
- The card screens move together. COCRDLIC hands off to the view and update screens (`app/cbl/COCRDLIC.cbl:195`, `app/cbl/COCRDLIC.cbl:203`).
- Unblocks: retirement of CLOSEFIL and OPENFIL and of the close and open steps inside three refresh jobs (`app/jcl/CLOSEFIL.jcl:26`), because no CICS file remains to close.
- Rollback: route the screen back through the router.
- Delivers: account, card, customer and user maintenance, bill payment and add-transaction.

## Wave 7. Month-end interest and statements

Units: CBACT04C, CBSTM03A, CBSTM03B, jobs INTCALC, COMBTRAN, CREASTMT and TXT2PDF1, and the monthly scheduler entries and full-batch wrapper.

- The hardest code and the paths that only run at month end. It is high-high, so it is strangled: run in shadow through at least one real month end.
- CBACT04C has a defect a port must decide on. The last account read is never updated (`app/cbl/CBACT04C.cbl:220`). INTCALC fixes the run date in the JCL (`app/jcl/INTCALC.jcl:22`).
- CBSTM03A uses ALTER, TIOT control-block addressing and a two-dimensional array (`app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBSTM03A.CBL:272`, `app/cbl/CBSTM03A.CBL:226`). Claude Code should not translate it line by line. Rewrite the file-open dispatch and keep the statement content as the oracle.
- The PDF step runs a REXX exec that is not in the tree (`app/jcl/TXT2PDF1.JCL:31`). It stays open until the client supplies it.
- Unblocks: retirement of the full-batch script and the monthly folder.
- Rollback: rerun the legacy month end from the pre-run backup.
- Delivers: monthly interest and customer statements.

## Wave 8. Authorization (IMS, DB2, MQ) and transaction-type (DB2) modules

Units: the authorization screens and MQ programs, the IMS batch programs and jobs, the DB2 transaction-type screens and jobs, and the two MQ services.

- This plugin does not analyze IMS, DB2 or MQ. Every score in this wave is low confidence, and the sequence is provisional until a specialist reviews the DL/I and SQL.
- The one dependency into the core: the authorization decision program reads the account balance that posting rewrites (`app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35`).
- CBPAUP0J is chained ahead of POSTTRAN in the CA-7 listing (`app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70`). If CA-7 is live, wave 4 depends on this wave's job. Confirm which scheduler is live before wave 4.
- Rollback: each module is independent and can stay on the mainframe.
- Delivers: authorization review, fraud flagging and the transaction-type reference maintenance.

## Retired, not ported

`waves.json` lists 30 `unassigned` units and `risks.json` lists 17 `do_not_port` entries. They fall into four groups.

| Group | Units | Why | Evidence |
|---|---|---|---|
| CICS file close and open | CLOSEFIL, OPENFIL and their scheduler entries | The target needs locking, not console commands against a fixed region name. Retire after wave 6. | `app/jcl/CLOSEFIL.jcl:26`, `app/jcl/OPENFIL.jcl:26` |
| Timers | WAITSTEP, COBSWAIT | A 36 second sleep stands in for a dependency. Use a scheduler condition. | `app/jcl/WAITSTEP.jcl:26`, `app/cbl/COBSWAIT.cbl:38` |
| Build and sample jobs | CBLDBMS, CICCMP, CIDBCMP, CNJBATMP, IMSMQCMP, the four build procs, LISTFILS, RACFCMDS, REPRTEST, SORTTEST | Build and setup for the source platform. The new pipeline replaces them. | `samples/jcl/BMSCMP.jcl:38`, `samples/jcl/CICCMP.jcl:41` |
| Test scaffolding | INTRDRJ1, INTRDRJ2, FTPJCLS | FTPJCLS carries a user id and a password in the job (`app/jcl/FTPJCL.JCL:34`, `app/jcl/FTPJCL.JCL:35`). Do not carry it over. | `app/jcl/FTPJCL.JCL:33` |

CBTRN01C is also unassigned. No JCL runs it. If the client says it is live, it moves with wave 4. See `05-dead-code.md`.
