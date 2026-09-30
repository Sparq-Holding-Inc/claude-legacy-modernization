# 00 Summary

Assessment of the CardDemo mainframe system: 44 COBOL programs, 55 JCL jobs, 6 procs, 62 copybooks, 21 BMS maps, CICS system definitions, Control-M and shell scheduling, and three sub applications for DB2, IMS and MQ. The extractor made 543 nodes and 1,224 edges. Facts come from `graph.json`. Judgment is mine and is marked.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | Refactor: the same behavior in restructured code | Given as `--target refactor` |
| What must not break | Daily transaction posting, the account and card master refresh, and the transaction report | Given as `--must-not-break` |
| Runtime telemetry | None. Every dead code claim is provisional. | Given as `--telemetry none` |

All three came as flags, so no defaults applied. The run was non interactive and I asked nothing.

## What must not break, mapped to units

The mapping is mine. I checked each against the JCL and the source. I did not invent one for anything that has no unit.

| Must not break | Units | Wave | Confidence | Evidence |
|---|---|---|---|---|
| Daily transaction posting | job:POSTTRAN, which runs CBTRN02C. The posting wrapper submits it. | 5 | high for the unit. Medium for the cadence: "daily" is only in a comment, and no scheduler I can parse names the job. | `app/jcl/POSTTRAN.jcl:23`, `app/cbl/CBTRN02C.cbl:5`, `scripts/run_posting.sh:26` |
| The account and card master refresh | job:ACCTFILE and job:CARDFILE. They are chained with the cross reference, customer and other refresh jobs in the refresh wrapper. | 5 | medium. The name matches the wrapper's own wording. | `app/jcl/ACCTFILE.jcl:25`, `app/jcl/CARDFILE.jcl:36`, `scripts/remote_refresh.sh:16` |
| The transaction report | job:TRANREPT (SORT plus CBTRN03C) and the online path CORPT00C, which submits proc:TRANREPT. | 5 | medium. Two paths, no scheduler names either. | `app/jcl/TRANREPT.jcl:59`, `app/cbl/CORPT00C.cbl:94` |

Two names could mislead. CBTRN01C says in its header that it posts daily transactions, and it does not (`app/cbl/CBTRN01C.cbl:254`). The Control-M folder called WEEKLY-DisclosureGroupsRefresh refreshes disclosure groups, not accounts or cards (`app/scheduler/CardDemo.controlm:32`). I mapped neither. Statements (CBSTM03A) and the category balance print (PRTCATBL) are other reports and I did not map them to "the transaction report".

## The plan in one paragraph

Seven waves, in the extractor's order, with two units moved (`03-waves.md`). Waves 1 and 4 are chores. Wave 5 holds all three must-not-break items and 56 units. Waves 6 and 7 are the online writers and the DB2, IMS and MQ subsystems. Estimate: 111 to 205 engineer weeks in total, inference, and wide for waves 6 and 7 (`04-estimate.md`).

## The single largest risk

Posting, the account refresh and the transaction backup are one destructive sequence, and its order and its failure handling live in shell scripts, not in the code.

The posting wrapper submits ACCTFILE (delete and reload the account master from a flat file), TCATBALF (delete and reload the category balances), TRANBKP (back up and then delete the transaction master) and POSTTRAN (open the transaction master for output and rebuild it) one after another, with 5 and 10 second sleeps and no wait for completion (`scripts/run_posting.sh:17`, `scripts/run_posting.sh:20`, `scripts/run_posting.sh:23`, `scripts/run_posting.sh:26`, `scripts/run_posting.sh:27`). TRANBKP's delete step has no condition on its backup step (`app/jcl/TRANBKP.jcl:37`). The datasets they rebuild are the ones 11 programs read (`analysis` field `data_hubs`). A port that gets the order, the failure handling or one truncated cent wrong changes balances silently, and the tree holds no production data or archived output to catch it. That is why wave 5 is planned as a parallel run on the same inputs and not as a cutover (`06-test-strategy.md`).

## Findings the client should hear early

| Finding | Why it matters | Confidence | Evidence |
|---|---|---|---|
| Report totals may double count the last transaction, and the report loop may stop at the first record outside the date range | The must-not-break report may be wrong today, or the port may not reproduce a quirk clients rely on | medium: inference from reading | `app/cbl/CBTRN03C.cbl:177`, `app/cbl/CBTRN03C.cbl:198` |
| Posting swallows an account rewrite failure | A transaction can post with no balance change and no reject row | medium: inference | `app/cbl/CBTRN02C.cbl:554` |
| The account overlimit test uses a narrower work field than the balances | Very large balances compare wrong | medium: inference | `app/cbl/CBTRN02C.cbl:187` |
| Interest truncates and fixes its type and category codes in code | The arithmetic ports, the intent needs a decision | high | `app/cbl/CBACT04C.cbl:464`, `app/cbl/CBACT04C.cbl:482` |
| Three writers invent transaction keys three ways | Key collisions during any period both run | medium: inference | `app/cbl/COBIL00C.cbl:212`, `app/cbl/CBTRN02C.cbl:425`, `app/cbl/CBACT04C.cbl:476` |
| The report reads reference data that a wave 7 DB2 job unloads | Wave 5 depends on the wave 7 feed as a file contract | high | `app/app-transaction-type-db2/jcl/TRANEXTR.jcl:72` |
| A clear text FTP address, user and password sit in a job | Rotate before anything is copied | high | `app/jcl/FTPJCL.JCL:33` |
| Passwords are stored and compared as clear text | A security decision for the deviation register | high | `app/cbl/COSGN00C.cbl:223`, `app/cpy/CSUSR01Y.cpy:21` |
| The import job opens a file its JCL never defines | It cannot have run cleanly as shipped | high | `app/cbl/CBIMPORT.cbl:233`, `app/jcl/CBIMPORT.jcl:33` |
| Two jobs define the same report generation group with different limits | Sets how much archived output exists to test against | high | `app/jcl/DEFGDGB.jcl:36`, `app/jcl/REPTFILE.jcl:27` |

## Files in this folder

| File | What it holds |
|---|---|
| `graph.json`, `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `05a-dead-code-candidates.md` | Generated by the scripts |
| `02-coupling.md` | The coupling argument, the cluster graph, and the computed calls |
| `03-waves.md`, `waves.json` | The plan and its two deviations |
| `04-estimate.md` | Ranges, assumptions, and where Claude Code helps |
| `05-dead-code.md`, `dead-code.json` | The three buckets |
| `06-test-strategy.md` | Oracle, normalization, traps, the opened deviation register |
| `risks.json` | 99 units on two axes |

## Open Questions

For the client's engineers.

1. **Are ACCTFILE, CARDFILE and the other refresh jobs a production step or a demo reset?** The posting wrapper runs ACCTFILE before POSTTRAN (`scripts/run_posting.sh:17`). If it runs in production, where does the flat file it loads (`app/jcl/ACCTFILE.jcl:57`) get current balances from?
2. **Which scheduler runs production, and when?** The CA-7 listing is not parsed and I read it by hand. Please send its export. It triggers CLOSEFIL1 and CLOSEFIL2, which have no JCL in the tree (`app/scheduler/CardDemo.ca7:216`). Confirm the cadence of POSTTRAN, INTCALC, TRANREPT, ACCTFILE and CARDFILE. The shell wrappers submit from a workstation and show order only.
3. **What produces the daily transaction file, and what archives exist?** POSTTRAN reads it (`app/jcl/POSTTRAN.jcl:30`). Each generation group keeps five (`app/jcl/DEFGDGB.jcl:24`). Please supply month end and fiscal year end generations of the report, rejects, backup and system transactions, and a before and after snapshot of the masters for one posting run.
4. **Which transaction report is production?** There is a batch job, a proc, and an online request that submits the proc (`app/jcl/TRANREPT.jcl:59`, `app/proc/TRANREPT.prc:57`, `app/cbl/CORPT00C.cbl:94`). Why two copies of the steps? Does an archived report show the last transaction counted twice, or a short report when the date parameters differ?
5. **Is TRANBKP's delete after a failed backup intended?** The delete step has no condition on the backup step (`app/jcl/TRANBKP.jcl:37`). Has a failed backup ever been followed by the delete?
6. **How do the three transaction key schemes coexist?** COBIL00C and COTRN02C use last key plus one, CBTRN02C uses the daily file's id, CBACT04C uses a PARM date and a counter (`app/cbl/COBIL00C.cbl:212`, `app/cbl/CBTRN02C.cbl:425`, `app/cbl/CBACT04C.cbl:476`). Have collisions occurred? Who changes the typed dates in INTCALC and TRANREPT (`app/jcl/INTCALC.jcl:22`, `app/jcl/TRANREPT.jcl:43`)?
7. **Who reads the transaction alternate index?** TRANIDX rebuilds it after every posting run and nothing in the tree reads its path (`app/jcl/TRANIDX.jcl:43`, `scripts/run_posting.sh:30`).
8. **Does anyone run CBTRN01C or the import job?** CBTRN01C has no JCL and posts nothing (`app/cbl/CBTRN01C.cbl:254`). CBIMPORT lacks a CARDOUT DD (`app/jcl/CBIMPORT.jcl:33`).
9. **Where is the source for COCRDSEC?** The CSD defines it and the developer transaction CDV1 (`app/csd/CARDDEMO.CSD:211`, `app/csd/CARDDEMO.CSD:388`). What else runs that is not in the tree?
10. **Please supply the files the extractor did not read.** These are listed as not parsed, and every one of them touches this system:
    - DB2 DCLGEN: `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl`, and two more in the transaction type folder.
    - DB2 DDL: `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl`, and five more.
    - IMS DBD: `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd`, and three more.
    - IMS PSB: `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB`, and three more.
    - Control cards: `app/app-transaction-type-db2/ctl/DB2CREAT.ctl`, and seven more. One of them, `REPROCT.ctl`, is the REPRO card the core backup and report jobs run (`app/proc/REPROC.prc:28`).
    - Assembler: `app/asm/COBDATFT.asm` and `app/asm/MVSWAIT.asm`.
    - Assembler macros: `app/maclib/ASMWAIT.mac` and `app/maclib/COCDATFT.mac`.
    - The CA-7 listing: `app/scheduler/CardDemo.ca7`.
11. **Who calls the MQ services and what do the messages look like?** COACCT01 and CODATE01 answer requests from outside the tree, and COPAUA0C is an MQ triggered authorization (`app/app-vsam-mq/cbl/COACCT01.cbl:396`, `app/app-vsam-mq/cbl/CODATE01.cbl:301`, `app/app-authorization-ims-db2-mq/cbl/COPAUA0C.cbl:400`). Is any other assembler running in production that is not in the tree?
12. **Does the target keep clear text passwords and case insensitive sign on?** Sign on upper cases and compares clear text (`app/cbl/COSGN00C.cbl:132`, `app/cbl/COSGN00C.cbl:223`). Is the FTP credential in the FTP job live (`app/jcl/FTPJCL.JCL:33`)?
13. **Is DEFCUST a leftover?** It deletes a cluster under AWS.CCDA, outside the system's naming (`app/jcl/DEFCUST.jcl:25`).
14. **Can you supply telemetry?** Twelve months of job logs, SMF records or CICS statistics would turn the dead code register from speculation into evidence. The CA-7 run counts look like template values (`app/scheduler/CardDemo.ca7:24`).
15. **Do these extractor limits hide something?** Each touches this system.
    - COPY REPLACING is not applied, and COTRTUPC uses it (`app/app-transaction-type-db2/cbl/COTRTUPC.cbl:1358`).
    - SORT and in-stream control cards are not read, and the report, combine and statement jobs depend on them (`app/jcl/TRANREPT.jcl:46`, `app/jcl/COMBTRAN.jcl:30`, `app/jcl/CREASTMT.JCL:52`).
    - IF and COND in JCL are not modeled (`app/jcl/TRANBKP.jcl:51`).
    - Nested procs are not followed (REPROC under TRANREPT and TRANBKP).
    - A called subprogram gets no DDs from its caller (CBSTM03B, `app/jcl/CREASTMT.JCL:83`).
    - DCB, LRECL and RECFM are not read, so no record length is checked against a copybook (`app/jcl/POSTTRAN.jcl:36`).
    - `EXEC CICS RETURN TRANSID`, `START` and `SEND MAP` are not edges, so the online graph is a lower bound.
    - The program a step runs is read only for IMS and TSO drivers, and the wave 7 jobs run that way (`app/app-authorization-ims-db2-mq/jcl/LOADPADB.JCL:26`).

## Judgment calls I want challenged

- I kept READACCT, READCARD, READCUST and READXREF in wave 2 although the CA-7 chain would move them (`03-waves.md`).
- I did not cut wave 5 at an articulation point. I staged it inside the wave.
- I moved job:CREADB2 to wave 7 and job:TXT2PDF1 to wave 5.
- I read the CA-7 listing by hand and used it as inference only. It is not in `graph.json`.
