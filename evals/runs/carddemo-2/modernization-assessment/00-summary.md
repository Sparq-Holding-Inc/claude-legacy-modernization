# 00 Summary

Assessment of the CardDemo tree in the current directory: COBOL, CICS, JCL, VSAM, with optional IMS, DB2 and MQ modules. 44 programs, 55 JCL jobs, 62 copybooks, 21 BMS maps, 6 procs and 19 scheduler entries. The extractor found 1224 edges and 28 computed calls.

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Target state | refactor | Given as a flag |
| What must not break | Daily transaction posting, the account and card master refresh, and the transaction report | Given as a flag |
| Runtime telemetry | none | Given as a flag |

This was a non-interactive run and all three answers arrived as flags, so no defaults were needed. Because telemetry is none, every dead code claim in `05-dead-code.md` is provisional.

## Result

- **Waves: 9.** Read-only listings, packed decimal patterns, master refresh, transaction report, online front door, daily posting, month end, online writers, and the optional IMS, DB2 and MQ modules. The three must-not-break items are waves 3, 4 and 6. Wave 9 is a placeholder that should be cut into three once someone assesses those technologies. See `03-waves.md`.
- **Effort:** about 51 to 95 engineer-weeks for waves 1 to 8, and about 67 to 135 with wave 9. There is no calibration behind it. See `04-estimate.md` for the four assumptions it is most sensitive to.
- **Dead code:** 1 unreachable unit, 0 dormant, 11 unknown. The extractor's only other unreachable unit, `proc:TRANREPT`, is live, and I moved it to unknown. See `05-dead-code.md`.

## The single largest risk

**The transaction master is destroyed and rebuilt every cycle by four jobs whose order is defined three different ways, while online programs write the same file.**

- TRANBKP backs the file up and then deletes it, and the delete has no dependency on the backup succeeding (`app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:40`). The posting program then opens it for output, which only works on an empty file (`app/cbl/CBTRN02C.cbl:256`).
- The order comes from a shell wrapper, from Control-M, or from CA-7, and they disagree. Control-M has no posting job at all. CA-7 puts an IMS purge ahead of it (`scripts/run_posting.sh:26`, `app/scheduler/CardDemo.controlm:8`, `app/scheduler/CardDemo.ca7:43`).
- The transaction report writes a generation of the same backup group on every run, and COMBTRAN reads the latest generation, so a report run at the wrong moment changes what gets combined (`app/jcl/TRANREPT.jcl:33`, `app/jcl/COMBTRAN.jcl:24`). This is an inference from the JCL.
- Two online programs derive the next transaction ID from the highest key in that file (`app/cbl/COBIL00C.cbl:212`, `app/cbl/COTRN02C.cbl:444`).

A port of the posting program that does not reproduce this lifecycle produces the wrong transaction master, and nobody sees it until the report or the next month end. It is why posting is wave 6 and a parallel run, and not a port.

## Open questions for the client's engineers

1. **Which scheduler is live for the daily cycle?** The shell wrappers run POSTTRAN. Control-M's daily folder runs TRANBKP but no posting. CA-7 chains CLOSEFIL, CBPAUP0J, POSTTRAN, WAITSTEP, OPENFIL. The extractor could not parse the CA-7 listing (`app/scheduler/CardDemo.ca7:24`, `app/scheduler/CardDemo.ca7:70`).
2. **Are the master refresh jobs a production process, or a test environment reset?** They delete and reload the account, card, xref and customer masters from flat files. The wrappers run the account reload just before posting and reach the mainframe through an FTP tunnel (`scripts/run_posting.sh:17`, `scripts/run_posting.sh:26`, `scripts/run_posting.sh:3`). If it is production, what holds the account balances between cycles, since nothing in the tree unloads them back to the flat file?
3. **Who produces the daily transaction file and the report date parameter?** Nothing in the tree writes DALYTRAN.PS or DATEPARM, and the report job carries a fixed window of 2022-01-01 to 2022-07-06 (`app/cbl/CBTRN02C.cbl:29`, `app/cbl/CBTRN03C.cbl:55`, `app/jcl/TRANREPT.jcl:43`). What does production use?
4. **Do the two latent defects in the report program matter?** The last transaction amount looks counted twice in the totals, and the loop exits at the first record outside the date window (`app/cbl/CBTRN03C.cbl:200`, `app/cbl/CBTRN03C.cbl:177`). Both are inferences from reading the code. Has anyone run the report against data that hits them, and is either one relied on?
5. **How many report generations are really kept?** The tree defines the TRANREPT group twice, with limits of 5 and 10 (`app/jcl/DEFGDGB.jcl:38`, `app/jcl/REPTFILE.jcl:27`). The archived generations are the cheapest oracle we have.
6. **What runs CBTRN01C, and is CBPAUP0J part of the daily chain?** No job or script runs CBTRN01C. CBPAUP0J runs an IMS purge that CA-7 places ahead of POSTTRAN (`app/cbl/CBTRN01C.cbl:5`, `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`).
7. **Has the FTP login in `FTPJCL.JCL` been rotated, and is that job live?** It carries a host, user ID and password in the JCL stream (`app/jcl/FTPJCL.JCL:33`, `app/jcl/FTPJCL.JCL:34`).
8. **Are the plain text passwords in the user file real?** Sign-on compares them as plain text (`app/cbl/COSGN00C.cbl:223`, `app/cpy/CSUSR01Y.cpy:21`). This needs a decision before the online waves.
9. **What is the target runtime for CICS transactions and BMS screens?** Refactor does not say. It decides how wave 5 is built, and it is the largest range in the estimate.
10. **What do the assembler routines do?** COBDATFT formats a date for CBACT01C, and MVSWAIT is the wait routine behind COBSWAIT (`app/cbl/CBACT01C.cbl:231`, `app/cbl/COBSWAIT.cbl:38`). The extractor does not read assembler.

### Files the extractor listed as not parsed

| File | Reason | Evidence |
|---|---|---|
| `app/scheduler/CardDemo.ca7` | CA-7 listing, not Control-M XML | `app/scheduler/CardDemo.ca7:18` |

I read the CA-7 listing by hand for the trigger chains and treated it as inference. The extractor did not list the files below as unparsed, but it does not read them, and the files are in the tree. Please confirm what each defines:

| Files | Count | Evidence |
|---|---|---|
| Assembler sources and macros (COBDATFT, MVSWAIT and two macros) | 4 | `app/asm/COBDATFT.asm:1`, `app/maclib/COCDATFT.mac:1` |
| DB2 DDL and DCLGEN members | 9 | `app/app-transaction-type-db2/ddl/TRNTYPE.ddl:1` |
| IMS DBD and PSB members | 8 | `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1`, `app/app-authorization-ims-db2-mq/ims/PSBPAUTB.psb:1` |
| IDCAMS and other control cards | 8 | `app/ctl/REPROCT.ctl:1`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1` |

### Limits from the extractor that touch this system

| Limit | What it touches here | Evidence |
|---|---|---|
| COPY REPLACING is not applied | COACTUPC copies CSSETATY with REPLACING, and the extractor expands the copybook as written | `app/cbl/COACTUPC.cbl:3208` |
| A variable call target is resolved from literals in the same program | 28 computed calls. Worked by hand in `02-coupling.md` | `app/cbl/COMEN01C.cbl:156` |
| A called subprogram gets no DDs from its caller's step | CBSTM03B has four DDs that no JCL maps | `app/cbl/CBSTM03B.CBL:31` |
| IDCAMS, SORT and other in-stream cards are not read | Every refresh, backup, combine and report job. Read by hand for the key jobs. Modes on IDCAMS steps are taken from DISP, so the masters' writer counts are understated | `app/jcl/ACCTFILE.jcl:61`, `app/jcl/TRANREPT.jcl:46` |
| IF, THEN, ELSE and COND are not modeled | Steps that skip on return codes | `app/jcl/TRANBKP.jcl:51`, `app/jcl/CREASTMT.JCL:79` |
| Nested PROCs and jobs submitted through the internal reader are not followed | The TRANREPT proc calls REPROC. CORPT00C submits the report through a TDQ | `app/proc/TRANREPT.prc:21`, `app/cbl/CORPT00C.cbl:517` |
| RETURN TRANSID, START and SEND MAP are not edges | Every online program chains screens this way, so the online call graph is understated | `app/cbl/COMEN01C.cbl:156` |
| Only Control-M XML and shell wrappers are read as schedulers | The CA-7 listing | `app/scheduler/CardDemo.ca7:18` |

## Things that made this assessment less certain

- I read the posting, report, interest and refresh code closely. I did not read COACTUPC, COCRDUPC, COCRDLIC, COCRDSLC, the authorization, transaction type or MQ programs, or CBEXPORT and CBIMPORT. Their scores in `risks.json` carry low confidence, and I marked each one.
- The tree looks partly like a demonstration. The refresh path goes through an FTP tunnel, the dates in the JCL are 2022, and the interest job has a fixed date. If this is the whole production system the plan holds. If it is a demonstration built from a larger one, the counts do not describe the estate.
- The edge and dead code tables in `01-inventory.md`, `02a-edge-tables.md` and `05a-dead-code-candidates.md` were generated by script. The rest was written by me, and every claim carries a citation or the word inference.
