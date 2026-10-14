# 00 Summary

## Scoping answers

| Item | Answer | Source |
|---|---|---|
| Target state | refactor | `--target refactor` |
| Must not break | Daily transaction posting, the account and card master refresh, the transaction report | `--must-not-break` |
| Telemetry | none | `--telemetry none` |
| Delivery mode | Not given. The estimate shows conventional and AI-assisted side by side | `--delivery` missing |
| Defaults applied | None. All three scoping answers came as flags | |

Mapping of the must-not-break items to units (checked, not assumed):

| Item | Units | Wave | Confidence | Evidence |
|---|---|---|---|---|
| Daily transaction posting | `job:POSTTRAN`, `CBTRN02C`, and the wrapper `sch:scripts/run_posting.sh` | 6 | medium | `app/jcl/POSTTRAN.jcl:23` |
| Account and card master refresh | `job:ACCTFILE`, `job:CARDFILE`, `sch:scripts/remote_refresh.sh` | 6 | medium | `scripts/remote_refresh.sh:17` |
| Transaction report | `job:TRANREPT`, `CBTRN03C`, `proc:TRANREPT`, and the online launcher `CORPT00C` | 6 | medium | `app/jcl/TRANREPT.jcl:59` |

## Result

Nine waves, 123 units placed, one unplaced (CBTRN01C). All three must-not-break items land in wave 6. One deviation from the extractor's seed: CARDFILE moves from wave 5 to wave 6 (`waves.json`). Estimate: 80 to 141 engineer-weeks conventional, 60 to 110 AI-assisted, both low confidence (`04-estimate.md`).

## Largest risk

Wave 6 moves the batch writers of the account and transaction files while the online writers in wave 7 still update the same files under CICS (`app/cbl/CBTRN02C.cbl:51`, `app/cbl/COACTUPC.cbl:573`). The only coordination is the CLOSEFIL and OPENFIL console jobs (`app/jcl/CLOSEFIL.jcl:26`). The plan holds only if the ported code shares the live VSAM records until wave 7 ships. Posting also has no restart logic, so a rerun after an abend posts twice (risk pass, `risks.json`).

## Open questions for the client's engineers

1. Which scheduler is live, CA-7 or Control-M? The CA-7 listing triggers POSTTRAN from CBPAUP0J, an IMS job (`app/scheduler/CardDemo.ca7:70`). The Control-M file has no POSTTRAN (`app/scheduler/CardDemo.controlm:3`).
2. What produces the daily transaction input? Nothing in the tree writes it (`app/jcl/POSTTRAN.jcl:30`).
3. Does the flat file ACCTFILE reloads from get rewritten after each posting run? If not, the refresh run before POSTTRAN resets balances (`app/jcl/ACCTFILE.jcl:61`, `scripts/run_posting.sh:17`).
4. How do the card and customer refresh run while CICS holds those files open? CLOSEFIL does not close them (`app/jcl/CLOSEFIL.jcl:26`, `app/csd/CARDDEMO.CSD:25`).
5. Is "master refresh" only ACCTFILE and CARDFILE, or the whole eleven-job chain in `remote_refresh.sh` (`scripts/remote_refresh.sh:13`)?
6. Is TRANREPT.jcl runnable as shipped? It has two steps named STEP05R (`app/jcl/TRANREPT.jcl:23`, `app/jcl/TRANREPT.jcl:37`) and a date window fixed to 2022 (`app/jcl/TRANREPT.jcl:43`).
7. Should the legacy defects in the report and the posting rerun be preserved? Each needs a decision in the deviation register (`06-test-strategy.md`).
8. Can a COMMAREA from outside the tree name other programs in the 28 computed XCTLs (`app/cbl/COMEN01C.cbl:156`)?
9. COCRDSEC (CSD transaction CDV1) has no source in the tree, and the COBDATFT and MVSWAIT assembler sources are listed as not parsed (`app/asm/COBDATFT.asm:1`, `app/asm/MVSWAIT.asm:1`). What do they do?
10. Rotate the credential in clear text in the FTP job (`app/jcl/FTPJCL.JCL:33`).

## Not parsed by the extractor

These files were not read, so wave 8 and 9 have no data model and the scheduler picture is partial.

- DB2 DCLGEN files, `.dcl` (3): `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl:1`
- DB2 DDL, `.ddl` (6): `app/app-authorization-ims-db2-mq/ddl/AUTHFRDS.ddl:1`
- IMS DBD files (4): `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd:1`
- IMS PSB files (4): `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB:1`
- DB2 control cards, `.ctl` (8): `app/app-transaction-type-db2/ctl/DB2CREAT.ctl:1`
- Assembler source (2): `app/asm/COBDATFT.asm:1`
- Assembler macros (2): `app/maclib/ASMWAIT.mac:1`
- CA-7 listing: `app/scheduler/CardDemo.ca7:1`. I read it by hand for POSTTRAN and its trigger chain, but not for every job.

## Where the evidence is weak

- Telemetry is none, so every dead-code claim is provisional (`05-dead-code.md`).
- The risk pass fully read only CBTRN02C, CBTRN03C, CORPT00C, CBSTM03A, CBACT04C and the posting and report JCL. Most other scores are low confidence (`risks.json`).
- The cartographer's resolution of the computed calls is inference (`02-coupling.md`).
