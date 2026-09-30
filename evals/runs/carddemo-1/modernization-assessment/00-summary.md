# 00 Summary

Assessment of the AWS CardDemo mainframe application in this folder. The extractor found 44 COBOL programs (22,904 lines), 55 JCL jobs, 6 procs, 19 scheduler entries, 21 BMS maps and 62 copybooks, joined by 1,224 evidenced edges in `graph.json`.

## Scoping answers

| Question | Answer | Where it came from |
|---|---|---|
| Target state | refactor | Given as a flag. It is also the default |
| What must not break | Daily transaction posting, the account and card master refresh, and the transaction report | Given as a flag |
| Runtime telemetry | none | Given as a flag |

All three came as flags. This was a non-interactive run, so no question was asked, and no default had to be applied. With telemetry `none`, every dead-code claim is provisional and `dead-code.json` says so.

The three anchors map to these units. They become the equivalence anchors in `06-test-strategy.md`.

| Anchor | Units | Wave | Evidence |
|---|---|---|---|
| Daily transaction posting | job:POSTTRAN, CBTRN02C, with TRANBKP, TRANIDX, CLOSEFIL and OPENFIL around it | 6 | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:256` |
| Account and card master refresh | job:ACCTFILE, job:CARDFILE, job:XREFFILE, job:CUSTFILE, read back by job:READACCT, job:READCARD, job:READXREF, job:READCUST | 6 for the refresh, 1 and 2 for the read-back | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/READCARD.jcl:22` |
| Transaction report | job:TRANREPT and CBTRN03C in batch, CORPT00C and proc:TRANREPT online | 4 | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

## Waves

Seven. The plan is in `03-waves.md` and `waves.json`. Every write to a shared master comes from wave 6, so the earlier waves coexist with the legacy system without dual writes.

| Wave | Name | Effort (engineer-weeks) | Evidence |
|---|---|---|---|
| 1 | Read-only master readers | 5 to 9 | `app/cbl/CBACT02C.cbl:29` |
| 2 | Hard-pattern batch utilities | 7 to 13 | `app/cbl/CBACT01C.cbl:231` |
| 3 | Administration front door | 22 to 42 | `app/cbl/COSGN00C.cbl:223` |
| 4 | Read-only inquiry and the transaction report | 16 to 30 | `app/cbl/CBTRN03C.cbl:173` |
| 5 | Account statements | 13 to 26 | `app/cbl/CBSTM03A.CBL:300` |
| 6 | Money core | 52 to 100 | `app/jcl/POSTTRAN.jcl:23` |
| 7 | IMS and MQ authorization and MQ services | 54 to 101 | `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:35` |

Total 169 to 321 engineer-weeks (`04-estimate.md`). The range is not calibrated. Wave 1 is where to calibrate it.

Waves 3, 4 and 5 put high-high units in the first and middle part of the plan. `03-waves.md` says which ones and why. The weakest placement is wave 4, which holds the transaction report.

## The single largest risk

Daily posting is not one program. CBTRN02C writes three shared masters, and its correctness depends on a destructive job chain: TRANBKP empties the transaction master and its delete step runs even when the backup step fails (`app/jcl/TRANBKP.jcl:37`, `app/jcl/TRANBKP.jcl:51`), COMBTRAN rebuilds it from generations chosen by relative number (`app/jcl/COMBTRAN.jcl:23`), and the order of all this is declared in three places that disagree, plus a CA-7 listing the extractor did not read (`app/scheduler/CardDemo.ca7:70`, `app/scheduler/CardDemo.controlm:8`, `scripts/run_posting.sh:26`). A port of the program that gets every line right can still break posting.

## Other findings a steering committee should hear

| Finding | Why it matters | Evidence |
|---|---|---|
| The online account update writes through a private account layout that omits the ZIP field | If I read it correctly, edited accounts lose their group id and month-end interest falls back to default rates. Inference, not run | `app/cbl/COACTUPC.cbl:418`, `app/cbl/COACTUPC.cbl:432`, `app/cpy/CVACT01Y.cpy:15` |
| Record layouts are restated as byte offsets in JCL, and no copybook checks them | A port that changes a layout breaks the report sort and the alternate indexes silently | `app/jcl/TRANREPT.jcl:41`, `app/jcl/CARDFILE.jcl:85`, `app/jcl/TRANIDX.jcl:27` |
| The extractor missed five live programs and one live proc | JCL PARM cards and JCL held as text inside COBOL are outside what it reads. Its dead-code candidates would have led to deleting the online report's proc | `app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`, `app/cbl/CORPT00C.cbl:94` |
| The batch report hard-codes a 2022 date range, and the report program has a loop that can stop early and a total that may double count the last row | The report can be wrong with no job failure | `app/jcl/TRANREPT.jcl:43`, `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:198` |
| Clear text credentials in source | Sign-on compares clear passwords, and two JCL members hold seed users and an FTP login | `app/cbl/COSGN00C.cbl:223`, `app/jcl/DUSRSECJ.jcl:35`, `app/jcl/FTPJCL.JCL:35` |
| The tree holds sample inputs and no archived outputs | Verification needs the client's archives, and the generation groups keep only five generations | `app/data/ASCII/dailytran.txt:1`, `app/jcl/DEFGDGB.jcl:26` |

## Open Questions for the client's engineers

1. Which daily sequence is the production one? The shell wrappers, Control-M and CA-7 give three different orders (`scripts/run_posting.sh:26`, `app/scheduler/CardDemo.controlm:8`, `app/scheduler/CardDemo.ca7:70`). Is CBPAUP0J really a precondition of POSTTRAN, or only a scheduling convenience?
2. Are ACCTFILE, CARDFILE, XREFFILE, CUSTFILE and TCATBALF production jobs or test resets? Each deletes a master and reloads it from a flat file that no job in the tree creates (`app/jcl/ACCTFILE.jcl:61`). Only the shell wrappers run them (`scripts/remote_refresh.sh:17`). CA-7 reloads TCATBALF and the type files and then only reads the account, card, customer and cross reference masters (`app/scheduler/CardDemo.ca7:271`, `app/scheduler/CardDemo.ca7:340`). What creates those files, and what creates the daily transaction file that CBTRN02C reads (`app/jcl/POSTTRAN.jcl:30`)?
3. Can you supply 13 months of daily posting inputs with the masters, rejects and report each run produced, plus the older generations that fell out of the five-generation groups (`app/jcl/DEFGDGB.jcl:26`)? Without them the oracle is the legacy programs run on 300 sample records.
4. Does the batch TRANREPT job run in production, and who reads its output? It selects a fixed 2022 range (`app/jcl/TRANREPT.jcl:43`), while the online path computes its own (`app/cbl/CORPT00C.cbl:220`). Its Db2 feed says daily and Control-M says weekly (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:19`, `app/scheduler/CardDemo.controlm:57`).
5. Is the account update layout in COACTUPC intentional, and has anyone compared interest for edited accounts against the default rates (`app/cbl/COACTUPC.cbl:432`, `app/cbl/CBACT04C.cbl:436`)?
6. Is the IMS and MQ authorization module in scope? It is a third of the estimate. Do CBPAUP0J, LOADPADB, UNLDPADB and UNLDGSAM run today (`app/app-authorization-ims-db2-mq/jcl/CBPAUP0J.jcl:25`)?
7. Are statements (CBSTM03A) and the branch migration export (CBEXPORT) on the must-not-break list? I scored both as customer or partner facing but did not treat them as anchors (`app/cbl/CBSTM03A.CBL:300`, `app/cbl/CBEXPORT.cbl:8`).
8. The extractor listed one file it could not parse: `app/scheduler/CardDemo.ca7`, a CA-7 listing, not Control-M XML. I read it by hand for the chains cited here. What are its schedules and calendars (`app/scheduler/CardDemo.ca7:39`)?
9. The extractor did not list, and did not read, these: the assembler routines and macros (`app/asm/COBDATFT.asm:17`, `app/asm/MVSWAIT.asm:1`, `app/maclib/COCDATFT.mac:1`), the Db2 DDL and control cards (`app/app-transaction-type-db2/ddl/TRNTYPE.ddl:1`, `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1`), the IMS database and program definitions (`app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1`), and the zipped runtime samples (`samples/m2/mf/CardDemo_runtime.zip:1`). Is there business logic in any of them, for example Db2 triggers or stored procedures?
10. Extractor limits that touch this system: a variable call target resolves only from VALUE clauses and literal MOVEs in the same program, which left 28 computed calls open (I resolved them by hand in `02-coupling.md`). COPY REPLACING is not applied, and COACTUPC uses it three times (`app/cbl/COACTUPC.cbl:3208`). A called subprogram gets no DDs from its caller's step, so CBSTM03B shows four unmapped files although the CREASTMT step maps them (`app/jcl/CREASTMT.JCL:83`). One line of that step carries stray text and may not run as shipped (`app/jcl/CREASTMT.JCL:90`). IDCAMS and SORT control cards are not read, which hides every offset cited above. JCL IF, THEN, ELSE and COND are not modeled (`app/jcl/TRANBKP.jcl:51`). A nested proc is not followed (`app/proc/TRANREPT.prc:21`). Jobs sent to the internal reader are not followed (`app/cbl/CORPT00C.cbl:517`). EXEC CICS RETURN TRANSID and SEND MAP are not edges, so the pseudo-conversational hand-offs are missing.
11. Where do last-modified dates come from? The tree's git history gives 2022 and 2025 dates. If it was squashed on import, the dormancy rule means nothing (`05-dead-code.md`).
12. The proc member TRANREPT declares itself REPROC on its first line, the same label as the REPROC proc (`app/proc/TRANREPT.prc:1`, `app/proc/REPROC.prc:1`). Is that a copy and paste slip, and does a job that names PROC=TRANREPT get the right one?

## Where to read next

| File | What it holds |
|---|---|
| `01-inventory.md` | Generated inventory of every unit |
| `02-coupling.md` | The three coupling patterns, the 28 computed calls resolved, what the extractor missed |
| `03-waves.md`, `waves.json` | The seven waves, boundaries and the units not ported |
| `04-estimate.md` | Ranges per wave and the assumptions they are most sensitive to |
| `05-dead-code.md`, `dead-code.json` | The three buckets and ten units the extractor mislabeled |
| `06-test-strategy.md` | Oracles, normalization spec, targeted cases, deviation register |
| `risks.json` | Two axis scores for 99 programs and jobs |

## How this run was produced

The command file, the two skills and the scripts were followed as written. The dependency-cartographer and the migration-risk-assessor agents could not be started in this session, so their work was done inline, following their instruction files. The computed calls and the contract exposure in `02-coupling.md` are the cartographer's output, and `risks.json` is the risk assessor's. Both are inference in the plugin's sense.
