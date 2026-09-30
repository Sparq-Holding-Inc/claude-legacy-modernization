# 00 Summary

Assessment of the CardDemo COBOL, CICS, JCL and VSAM tree in `.` (44 programs, 55 JCL jobs, 6 procs, 25 online transactions, 21 BMS maps, 62 copybooks). The extractor ran on this run's source, and every fact table came from it. Judgment is mine, and every claim carries a `path:line` citation or the word inference.

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Target state | refactor: same behavior, restructured code | Given as `--target refactor` |
| What must not break | "daily transaction posting, the account and card master refresh, and the transaction report" | Given as `--must-not-break` |
| Runtime telemetry | none, so every dead code claim is provisional | Given as `--telemetry none` |
| Defaults applied | no defaults applied | All three came as flags |

How the three items map to the tree is in `modernization-assessment/03-waves.md`. The middle one is my reading of the wrapper script captions, not a source fact.

## Result

- Wave count: 7, with 123 units placed and 1 unit (CBTRN01C) not placed. I changed the extractor's seed in 13 places, each cited, and kept its family order. Waves 1 and 4 are chores that deliver nothing a stakeholder can name. Wave 5 (51 units) holds all three must-not-break items and is the real center of the plan.
- Risk scores: 99 units on two axes, 22 on the `do_not_port` list, 15 high-high units in wave 5, 4 in wave 6 and 7 in wave 7.
- Estimate: 78 to 174 engineer weeks, inference, driven by wave 5 and wave 7 (`modernization-assessment/04-estimate.md`).
- Dead code: 1 unreachable copybook (cpy:UNUSED1Y), 2 unknown (CBTRN01C and proc:TRANREPT), dormant not measured (`modernization-assessment/05-dead-code.md`).

## The single largest risk

The transaction master is rebuilt on every posting cycle, and only job order keeps its history. CBTRN02C opens the transaction master for OUTPUT (`app/cbl/CBTRN02C.cbl:256`), so posting works only on an empty file. TRANBKP makes it empty by copying it to a backup generation and then deleting and redefining the cluster (`app/jcl/TRANBKP.jcl:40`), and COMBTRAN merges the backup and the interest file back in (`app/jcl/COMBTRAN.jcl:24`). History therefore lives in generation data sets that keep five generations (`app/jcl/DEFGDGB.jcl:26`). The three scheduler descriptions in the tree disagree on the order: the CA-7 listing has POSTTRAN triggered by an IMS purge job and no TRANBKP (`app/scheduler/CardDemo.ca7:70`), Control-M has TRANBKP and no POSTTRAN (`app/scheduler/CardDemo.controlm:5`), and only the wrapper scripts have both (`scripts/run_posting.sh:23`). A port that follows the code but not the order, or that treats the master as an append only ledger, diverges from legacy silently, in the file the report and 11 programs read.

Others worth a steering committee's time: the account master refresh deletes and reloads the account master from a flat file, discarding balances posted since (`app/jcl/ACCTFILE.jcl:25`), and it has no CICS close of its own; the interlock between batch and CICS is five CEMT commands and a 36 second sleep (`app/jcl/CLOSEFIL.jcl:26`, `app/jcl/WAITSTEP.jcl:26`); and IMS, DB2 and MQ (wave 7) are outside what the tooling reads.

## Open Questions for the client's engineers

1. Which scheduler runs production: the wrapper scripts, Control-M, or CA-7? The three disagree on the posting chain (`app/scheduler/CardDemo.ca7:70`, `app/scheduler/CardDemo.controlm:5`, `scripts/run_posting.sh:23`). In CA-7, does IMS job CBPAUP0J really have to finish before POSTTRAN, and where does TRANBKP run?
2. What does "the account and card master refresh" mean in production? I mapped it to jobs ACCTFILE and CARDFILE, which delete and reload the masters from flat files (`scripts/remote_refresh.sh:16`, `scripts/remote_refresh.sh:19`). Is that a test environment reset, or does production run it? What creates ACCTDATA.PS and CARDDATA.PS?
3. Is the transaction master meant to hold only the current cycle, with history in the backup generations? Where is history kept beyond five generations (`app/jcl/DEFGDGB.jcl:26`), and is the report generation limit 5 or 10 (`app/jcl/REPTFILE.jcl:27`, `app/jcl/DEFGDGB.jcl:38`)?
4. How is the transaction report run in production: from the online screen (JCL built by CORPT00C, `app/cbl/CORPT00C.cbl:94`) or the standalone job with the fixed 2022 window (`app/jcl/TRANREPT.jcl:43`)? Proc TRANREPT starts with `//REPROC PROC` (`app/proc/TRANREPT.prc:1`). Is that a copy error that works only because the member name is what counts?
5. INTCALC always passes the date 2022071800 as its PARM (`app/jcl/INTCALC.jcl:22`). Is it edited before each run, or does the interest transaction id prefix really never change?
6. Do ACCTFILE, XREFFILE and POSTTRAN ever run without CLOSEFIL first? They have no CEMT step of their own (`app/jcl/ACCTFILE.jcl:25`, `app/jcl/XREFFILE.jcl:22`, `app/jcl/POSTTRAN.jcl:23`).
7. Does anything outside this tree read the account, transaction and category balance masters (extracts, partner feeds, a warehouse)? The tree shows only EXPORT.DATA leaving (`app/cbl/CBEXPORT.cbl:65`).
8. Do the production record layouts match the copybooks? The tool does not compare DCB, LRECL or RECFM, and the account and transaction records are zoned decimal in the copybooks (`app/cpy/CVACT01Y.cpy:7`, `app/cpy/CVTRA05Y.cpy:10`).
9. Does anyone run CBTRN01C, the verify-only driver that no job names (`app/cbl/CBTRN01C.cbl:172`)? Does anyone run job CBIMPORT, which opens a DD it does not define (`app/cbl/CBIMPORT.cbl:63`)?
10. Where is the source of program COCRDSEC, which the CSD defines and a developer transaction runs (`app/csd/CARDDEMO.CSD:211`, `app/csd/CARDDEMO.CSD:390`)? Where is the JCL for jobs CLOSEFIL1 and CLOSEFIL2, which CA-7 triggers (`app/scheduler/CardDemo.ca7:216`)?
11. Which of the 27 jobs that no scheduler artifact names still run (list in `modernization-assessment/05-dead-code.md`)? Do any run from a scheduler that is not in the tree?
12. Is job FTPJCLS's login live? It carries a host and credentials in clear text (`app/jcl/FTPJCL.JCL:33`). Rotate it in any case.
13. Sign on compares an 8 byte clear text password, and CBCUS01C prints each customer record with its SSN to SYSOUT (`app/cbl/COSGN00C.cbl:223`, `app/cbl/CBCUS01C.cbl:78`). Are these known and accepted for the target, or are they defects to fix during the port?
14. Can the old system stay up for a parallel run through a month end and a year end? That decides the oracle for wave 5 (`modernization-assessment/06-test-strategy.md`).

## Files the extractor listed as not parsed

Each is a question, not a footnote. Thirty files in eight groups. I read `app/ctl/REPROCT.ctl` by hand: it is one plain REPRO card (`app/ctl/REPROCT.ctl:15`) used by the backup steps of TRANBKP, TRANREPT and PRTCATBL, so that group has one item settled.

| Files | Kind | What I need from you |
|---|---|---|
| `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl`, `app/app-transaction-type-db2/dcl/DCLTRCAT.dcl`, `app/app-transaction-type-db2/dcl/DCLTRTYP.dcl` | DB2 DCLGEN | Confirm they match the tables in production. |
| `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl`, `app/app-authorization-ims-db2-mq/ddl/XAUTHFRD.ddl`, `app/app-transaction-type-db2/ddl/TRNTYCAT.ddl`, `app/app-transaction-type-db2/ddl/TRNTYPE.ddl`, `app/app-transaction-type-db2/ddl/XTRNTYCAT.ddl`, `app/app-transaction-type-db2/ddl/XTRNTYPE.ddl` | DB2 DDL | Business logic in DB2: triggers, procedures, constraints that the programs rely on. |
| `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd`, `app/app-authorization-ims-db2-mq/ims/DBPAUTX0.dbd`, `app/app-authorization-ims-db2-mq/ims/PADFLDBD.DBD`, `app/app-authorization-ims-db2-mq/ims/PASFLDBD.DBD` | IMS DBD | The segment layouts the authorization programs read and write. |
| `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB`, `app/app-authorization-ims-db2-mq/ims/PAUTBUNL.PSB`, `app/app-authorization-ims-db2-mq/ims/PSBPAUTB.psb`, `app/app-authorization-ims-db2-mq/ims/PSBPAUTL.psb` | IMS PSB | Which programs may change which segments. |
| `app/app-transaction-type-db2/ctl/DB2CREAT.ctl`, `app/app-transaction-type-db2/ctl/DB2FREE.ctl`, `app/app-transaction-type-db2/ctl/DB2LTCAT.ctl`, `app/app-transaction-type-db2/ctl/DB2LTTYP.ctl`, `app/app-transaction-type-db2/ctl/DB2TEP41.ctl`, `app/app-transaction-type-db2/ctl/DB2TIAD1.ctl`, `app/app-transaction-type-db2/ctl/REPROCT.ctl`, `app/ctl/REPROCT.ctl` | Control cards | The DB2 statements job CREADB2 runs (`app/app-transaction-type-db2/jcl/CREADB21.jcl:52`). |
| `app/asm/COBDATFT.asm`, `app/asm/MVSWAIT.asm` | Assembler | What COBDATFT does with dates (`app/cbl/CBACT01C.cbl:231`) and whether MVSWAIT is only a wait (`app/cbl/COBSWAIT.cbl:38`). |
| `app/maclib/ASMWAIT.mac`, `app/maclib/COCDATFT.mac` | Assembler macros | Confirm nothing else uses them. This decides whether UNUSED1Y is really unused. |
| `app/scheduler/CardDemo.ca7` | CA-7 listing | Whether it is the production schedule (question 1). I read it by hand, as inference, and did not use it as fact. |

## Extractor limits that touch this system

| Limit | Where it touches | Evidence |
|---|---|---|
| COBOL is read as fixed format | Nothing was listed as free format, so it does not bite. | analysis: `meta.limits` |
| COPY REPLACING is not applied | COACTUPC uses it four times on CSSETATY, so its attribute setting is expanded as written. | `app/cbl/COACTUPC.cbl:3208` |
| A variable call target resolves only from VALUE and literal MOVEs | The 28 computed calls, settled by hand in `modernization-assessment/02-coupling.md`. | `app/cbl/COACTUPC.cbl:956` |
| A called subprogram gets no DDs from its caller's JCL step | CBSTM03B, which reads four masters through the caller step. | `app/jcl/CREASTMT.JCL:83` |
| SORT and most control cards are not read | Five JCL control cards read the transaction record by byte position. | `app/jcl/TRANREPT.jcl:41`, `app/jcl/CREASTMT.JCL:53` |
| PARM and RUN PROGRAM drivers are the only ones read | IMS jobs, DSN steps and TXT2PDF1 (IKJEFT1B) start programs the graph does not link. | `app/jcl/TXT2PDF1.JCL:24`, `app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:26` |
| IF, THEN, ELSE and COND in JCL are not modeled | COND on the TRANBKP define step and on the statement steps. | `app/jcl/TRANBKP.jcl:51`, `app/jcl/CREASTMT.JCL:56` |
| Nested procs are not followed and JCL in COBOL makes no edge | Proc TRANREPT calls REPROC, and CORPT00C embeds JCL. | `app/proc/TRANREPT.prc:21`, `app/cbl/CORPT00C.cbl:94` |
| RETURN TRANSID, START and SEND MAP are not edges | Every online program returns to itself with a TRANSID. | `app/cbl/CORPT00C.cbl:199` |
| Only Control-M XML and shell wrappers are read as schedulers | The CA-7 listing. | `app/scheduler/CardDemo.ca7:18` |
| DCB, LRECL and RECFM are not read | POSTTRAN writes rejects at 430 bytes, which the program builds from 350 plus 80. | `app/jcl/POSTTRAN.jcl:36`, `app/cbl/CBTRN02C.cbl:83` |
| A high contract edge means shared layout, not proven equal | All 62 contract edges are high. | analysis: `edge_counts` |
| LINK and XCTL are both call edges and control flow is not modeled | The sign on and menu component is a navigation loop of XCTLs that never return. It still has to move whole. | `app/cbl/COMEN01C.cbl:156` |

## Outputs

`graph.json` (facts), `waves.json`, `risks.json`, `dead-code.json` (checked by `schema.py`), and the documents `01-inventory.md`, `02-coupling.md` with `02a-edge-tables.md`, `03-waves.md` with `03a-wave-seed.md`, `04-estimate.md`, `05-dead-code.md` with `05a-dead-code-candidates.md`, and `06-test-strategy.md`, all in `modernization-assessment/`.
