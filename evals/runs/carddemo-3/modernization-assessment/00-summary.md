# 00 Summary

Assessment of the CardDemo tree (COBOL, CICS, JCL, VSAM) for modernization. Facts come from `extract.py` and `graph.json`. Judgment is mine. Every claim carries a `path:line` citation or the word `inference`.

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Target state | refactor | `--target refactor` flag |
| What must not break | daily transaction posting, the account and card master refresh, and the transaction report | `--must-not-break` flag |
| Runtime telemetry | none | `--telemetry none` flag |

All three came as flags, so the non-interactive defaults were not used. Nobody was asked anything. Because telemetry is `none`, every dead-code claim in `05-dead-code.md` is provisional.

The meaning of "refactor" is not defined in the command or the skill. I took it to mean the code is restructured on a platform that keeps the same file semantics until the online waves finish. That is an assumption, and open question 6 asks the client to confirm it.

## What was assessed

The scope is the whole work folder. `graph.json` has 543 nodes and 1224 edges: 44 programs (17 batch, 25 online, 2 subprograms), 55 JCL jobs, 6 procs, 62 copybooks, 21 maps, 110 datasets and 19 scheduler entries. Edge kinds: 318 call, 235 data, 476 include, 62 contract, 133 temporal. All 62 contract edges are high confidence. The extractor found no god module and three strongly connected components.

## Wave count

**8 waves.** The plan is in `03-waves.md` and `waves.json`. In order: read-only batch extracts and setup, the transaction report, master and reference data refresh, daily transaction posting, online sign-on and inquiry, online maintenance and payment, month-end interest and statements, and the IMS, DB2 and MQ modules. Estimate: 81 to 170 engineer-weeks, low confidence (`04-estimate.md`). All three must-not-break items are in waves 2, 3 and 4.

## The single largest risk

**The daily posting cycle.** The posting program rewrites the account master and the category balances and writes the transaction master in one pass with no restart point (`app/cbl/CBTRN02C.cbl:440`, `app/cbl/CBTRN02C.cbl:441`, `app/cbl/CBTRN02C.cbl:442`). The order of the jobs around it is not held in one place. Control-M omits POSTTRAN (`app/scheduler/CardDemo.controlm:4`). The CA-7 listing runs it after an IMS purge job (`app/scheduler/CardDemo.ca7:43`, `app/scheduler/CardDemo.ca7:70`). The shell script runs a backup that empties the transaction master just before it, with no sleep between the two (`scripts/run_posting.sh:23`, `scripts/run_posting.sh:26`, `app/jcl/TRANBKP.jcl:40`). A port that gets the program right and the order wrong breaks a must-not-break item, and no test on the program alone would show it.

## Findings that changed the plan

| Finding | Confidence | Evidence |
|---|---|---|
| The extractor calls proc TRANREPT unreachable. It is live: the online report screen submits a job that runs it. | high | `app/cbl/CORPT00C.cbl:94`, `app/cbl/CORPT00C.cbl:517` |
| Three schedulers disagree on the daily order, and the shell scripts submit jobs and sleep instead of waiting. | high | `app/scheduler/CardDemo.controlm:4`, `app/scheduler/CardDemo.ca7:70`, `scripts/run_posting.sh:11` |
| Refresh jobs delete the master before reloading it. A failed reload leaves no master. | high | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/ACCTFILE.jcl:61` |
| The report double counts the last amount into the page and grand totals, and never prints the last account total. | medium | `app/cbl/CBTRN03C.cbl:200`, `app/cbl/CBTRN03C.cbl:203`, `app/cbl/CBTRN03C.cbl:183` |
| Posting records only the last failing reason, and ignores a failed account rewrite. | high | `app/cbl/CBTRN02C.cbl:410`, `app/cbl/CBTRN02C.cbl:417`, `app/cbl/CBTRN02C.cbl:556` |
| The interest program never updates the last account, and its run date is fixed in the JCL. | medium | `app/cbl/CBACT04C.cbl:220`, `app/jcl/INTCALC.jcl:22` |
| The transaction layout is copied as literal offsets into six control cards and COBOL text that no include edge connects. | medium | `app/jcl/TRANREPT.jcl:41`, `app/cbl/CORPT00C.cbl:100`, `app/jcl/CREASTMT.JCL:53` |
| Three writers share one transaction key space with three different id schemes. | medium | `app/cbl/COBIL00C.cbl:212`, `app/cbl/CBACT04C.cbl:476`, `app/cbl/CBTRN02C.cbl:425` |
| Sign-on compares a clear-text password. The seed job and the FTP job carry clear-text credentials. | high | `app/cbl/COSGN00C.cbl:223`, `app/jcl/DUSRSECJ.jcl:35`, `app/jcl/FTPJCL.JCL:34` |

## Open Questions

For the client's own engineers.

1. **Which scheduler runs production, and what is the real order of the daily cycle?** Control-M, CA-7 and the shell scripts each hold a different slice (`03-waves.md`, `02-coupling.md`). Is the CA-7 listing current? Its header carries an old-looking date (`app/scheduler/CardDemo.ca7:19`).
2. **Who produces the daily transaction file and the report date parameter?** POSTTRAN reads `AWS.M2.CARDDEMO.DALYTRAN.PS` (`app/jcl/POSTTRAN.jcl:31`) and the batch report reads `AWS.M2.CARDDEMO.DATEPARM` (`app/proc/TRANREPT.prc:72`). Nothing in the tree writes either.
3. **Why does TRANBKP empty the transaction master, and where is the full transaction history kept between COMBTRAN runs?** TRANBKP deletes the cluster (`app/jcl/TRANBKP.jcl:40`). COMBTRAN reloads it only in the monthly flow (`app/jcl/COMBTRAN.jcl:48`, `scripts/run_full_batch.sh:58`). The posting script never runs COMBTRAN (`scripts/run_posting.sh:26`).
4. **Does the mainframe hold anything that is not in this tree?** The REXX exec for PDF conversion (`app/jcl/TXT2PDF1.JCL:31`), the load library (`app/jcl/POSTTRAN.jcl:25`), the JCL library named in CA-7 (`app/scheduler/CardDemo.ca7:35`), and the jobs CA-7 names CLOSEFIL1 and CLOSEFIL2 (`app/scheduler/CardDemo.ca7:216`, `app/scheduler/CardDemo.ca7:217`).
5. **Are the legacy quirks intended?** The report totals (`app/cbl/CBTRN03C.cbl:200`), the single reject reason (`app/cbl/CBTRN02C.cbl:417`), the last account with no interest (`app/cbl/CBACT04C.cbl:220`). Someone with authority has to decide each one. They are D-001 to D-008 in `06-test-strategy.md`.
6. **Where do the shared masters live during waves 1 to 6?** The plan assumes batch and online use the same files in place. If the batch moves first, a two-way sync is needed and the estimate grows (`04-estimate.md`).
7. **Is CBTRN01C live?** No JCL runs it and none of its six DDs is mapped (`app/cbl/CBTRN01C.cbl:5`).
8. **Who on the team reads COBOL, JCL, assembler and IMS DL/I, and who owns DB2 and MQ?** The estimate assumes COBOL and JCL readers. Wave 8 needs the others.
9. **Can the client supply the oracle?** Archived generations, job logs, statements and CICS logs (list at the end of `06-test-strategy.md`). Without them every test is a characterization test and provisional.
10. **Which archived reports and extracts leave the building?** Partner and regulatory consumers decide which output formats are contracts. The tree names an FTP job and no consumer (`app/jcl/FTPJCL.JCL:30`).

### Files the extractor listed as not parsed

| File | Reason | What I did | Evidence |
|---|---|---|---|
| `app/scheduler/CardDemo.ca7` | CA-7 listing, not Control-M XML, not parsed | Read it by hand for the job chains. Findings are `inference`, and the temporal edges from it are not in `graph.json`. | `app/scheduler/CardDemo.ca7:18` |

### Files in the tree the extractor did not read and did not list

These are not in `unparsed` or `files_seen`. I found them by listing the tree.

| Files | What they are | Evidence |
|---|---|---|
| `app/asm/COBDATFT.asm`, `app/asm/MVSWAIT.asm` | Assembler routines called from COBOL. Wave 1 has to replace COBDATFT. | `app/asm/COBDATFT.asm:1`, `app/asm/MVSWAIT.asm:1` |
| `app/ctl/REPROCT.ctl` | The REPRO control card that REPROC feeds to IDCAMS | `app/ctl/REPROCT.ctl:15` |
| `app/maclib/COCDATFT.mac`, `app/maclib/ASMWAIT.mac` | Assembler macros | `app/maclib/COCDATFT.mac:1` |
| `app/app-authorization-ims-db2-mq/ims/` and `ddl/`, `dcl/` | IMS database and PSB definitions, DB2 DDL | `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl:1` |
| `app/data/ASCII/`, `app/data/EBCDIC/` | Seed data | `app/data/ASCII/dailytran.txt:1` |
| `scripts/markers/` | 45 marker files. I did not read what they record. | inference |

### Limits in `meta.limits` that touch this system

| Limit | Touches this system? | Evidence |
|---|---|---|
| A variable call target is resolved only from VALUE clauses and literal MOVEs in the same program | Yes. It left the 28 computed calls, and it never resolved the menu tables. The real online cycle is larger than the three in `graph.json`. | `app/cbl/COMEN01C.cbl:156` |
| IDCAMS, SORT and other in-stream control cards are not read | Yes. Account master writers are undercounted, and the layout offsets in control cards are not contract edges. | `app/jcl/ACCTFILE.jcl:61`, `app/jcl/TRANREPT.jcl:41` |
| IF/THEN/ELSE and COND= in JCL are not modeled | Yes, in TRANBKP. | `app/jcl/TRANBKP.jcl:51` |
| Nested PROC calls and jobs submitted through the internal reader are not followed | Yes. It made proc TRANREPT look dead. | `app/proc/TRANREPT.prc:21`, `app/cbl/CORPT00C.cbl:517` |
| Only Control-M XML and shell wrappers that name JCL files are read as schedulers | Yes. CA-7 is not read. | `app/scheduler/CardDemo.ca7:18` |
| A called subprogram gets no DDs from its caller's JCL step | Yes. The statement subprogram's four files and the DDs of CBTRN01C show as unmapped. | `app/cbl/CBSTM03B.CBL:31`, `app/cbl/CBTRN01C.cbl:29` |
| COPY REPLACING is not applied | Yes, for the account update screen. | `app/cbl/COACTUPC.cbl:3208` |
| EXEC CICS RETURN TRANSID, START and SEND MAP are not edges | Probably. Not checked screen by screen. | inference |
| COBOL is read as fixed format | No file was listed as free format. | inference |

## Where the extractor was blind and how it changed the result

- The unknown dead-code bucket holds five programs that a JCL `PARM` or a DSN command names. The extractor cannot read either, so it could not link them to their jobs. I left them in the bucket, with the linking evidence (`05-dead-code.md`).
- Its `unscheduled_jobs` list has 8 jobs that CA-7 schedules.
- Its cycles miss the menu-driven online cycle. The plan splits the online programs on the condition that wave 5 proves a router (`02-coupling.md`).

## Files

- `00-summary.md` this file
- `01-inventory.md` generated inventory
- `02-coupling.md` the coupling argument
- `02a-edge-tables.md` generated edge tables
- `03-waves.md` and `waves.json` the wave plan
- `04-estimate.md` the estimate
- `05-dead-code.md`, `05a-dead-code-candidates.md` and `dead-code.json` the register
- `06-test-strategy.md` the definition of correct
- `risks.json` port difficulty and blast radius for 99 units
- `graph.json` the extracted graph
