# 00 Summary

Assessment of the CardDemo tree (COBOL, JCL, CICS, with optional DB2, IMS and MQ modules).

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag |
| Must not break | daily transaction posting; the account and card master refresh; the transaction report | flag |
| Telemetry | none | flag |
| Delivery | not given. Estimate shows conventional and AI-assisted side by side | flag missing |
| Defaults applied | no defaults applied | |

Mapping of the must-not-break items to units is in `02-coupling.md`. Posting and the report map cleanly. "Account and card master refresh" is mapped to `job:ACCTFILE` and `job:CARDFILE`; that mapping is medium confidence.

## Result

Nine waves (`03-waves.md`, `waves.json`), one deviation. Estimate: 113 to 189 engineer-weeks conventional, 75 to 129 AI-assisted, low confidence overall (`04-estimate.md`). Neither case is the headline because `--delivery` was not given, and the plugin has no calibrated productivity data.

Size: 44 programs, 55 JCL jobs, 6 procs, 19 scheduler jobs, 62 copybooks (`01-inventory.md:5`). 22,489 lines of COBOL.

## Largest risk

All three must-not-break items sit in wave 6 and share the same three VSAM masters with the online screens in wave 7 (`app/jcl/POSTTRAN.jcl:23`, `02-coupling.md`). The posting program is the single highest-risk unit (`modernization-assessment/risks.json:1`). Nothing about it can be tested against an oracle yet, because none has been supplied. If the client has no archived `TRANSACT.BKUP` and `DALYREJS` generations and cannot run a parallel run, wave 6 rests on characterization tests that encode what the code says, not what it does.

## Open Questions for the client's engineers

1. Can the old and new platforms run in parallel on the daily transaction file for one month-end? If not, which archived `TRANSACT.BKUP` and `DALYREJS` generations exist, and how far back?
2. Which scheduler is production: the Control-M file, the CA-7 listing, or the shell wrappers? They disagree, and `POSTTRAN` is in neither Control-M folder (`app/scheduler/CardDemo.controlm:4`, `scripts/run_posting.sh:26`). The CA-7 file cannot be parsed and shows identical run counts for every job (`app/scheduler/CardDemo.ca7:24`), which looks templated.
3. What does "account and card master refresh" mean here: the ACCTFILE and CARDFILE reloads, or also the interest run that rewrites account balances (`app/cbl/CBACT04C.cbl:41`)?
4. Is `job:TRANREPT` used at all, or only the online path through `CORPT00C` (`app/cbl/CORPT00C.cbl:94`)? The proc declares itself `REPROC` and appears to call itself (`app/proc/TRANREPT.prc:1`). Does it run as written in production?
5. Does anything outside this tree read the transaction, account or card files by byte offset? The report's SORT step does (`app/jcl/TRANREPT.jcl:37`), and the extractor reads no SORT cards.
6. What do the files the extractor could not parse hold? 3 DB2 DCLGEN files, 6 DDL files, 4 IMS DBD, 4 IMS PSB, 8 control-card files, 2 assembler sources (`app/asm/COBDATFT.asm:1`, `app/asm/MVSWAIT.asm:1`), 2 assembler macros, and the CA-7 listing. Does `CSUTLDTC` or the date routine depend on the assembler?
7. Which of the 35 unscheduled jobs still run (`analysis` field `unscheduled_jobs`)? Is `CBTRN01C` used by anyone (`app/cbl/CBTRN01C.cbl:1`)?
8. Are the reject-reason, expiry and last-record behaviors in `CBTRN02C` and `CBTRN03C` intended (`06-test-strategy.md`, D-1 to D-3)?
9. Is the posting wrapper's lack of waiting between jobs safe in production, or does the shop run one initiator for that class (`scripts/run_posting.sh:20`)?

## Limits that touch this system

COBOL is read as fixed format; `COPY REPLACING` is not applied; `IF/THEN/ELSE` and `COND=` in JCL are not modeled; nested PROC calls are not followed; SORT cards are not read; DCB and LRECL are not compared with copybooks; `EXEC CICS RETURN TRANSID` and `START` are not edges (`graph.json` field `meta.limits`). Every one of these bears on the three anchors.
