# 00 Summary

Modernization assessment of the COBOL, CICS, JCL and VSAM system in this folder. It is written for an engineering leader who has to defend the sequence, the cost and the risk in a steering committee. Every claim carries a `path:line` citation or the word `inference`. Where a fact was computed from the dependency graph and has no source line, it says `analysis`.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor: the same behavior in restructured code, usually as services | given as a flag |
| What must not break | daily transaction posting, the account and card master refresh, and the transaction report | given as a flag |
| Runtime telemetry | none, so every dead code claim is provisional | given as a flag |

No defaults applied. All three answers came as flags.

## Result

- **Waves: seven.** 123 units in seven waves and one unit not placed. Waves 1 to 4 are the cheap and safe ones. The must-not-break work is in waves 5 and 6, and IMS, DB2 and MQ are last, in wave 7. See `03-waves.md`.
- **Estimate: about 70 to 134 person-weeks in total**, seven ranges of which none is better than medium confidence. Wave 1 measures the team's real velocity. See `04-estimate.md`.
- **Dead code:** one unreachable copybook, no dormant units, eleven unknown. Nothing can be deleted on this evidence. See `05-dead-code.md`.
- **Oracle:** the tree holds seeded test data only, so waves 5 and 6 need production replay from the client. See `06-test-strategy.md`.

## The single largest risk

The nightly posting chain has no safety net and it changes money in place. CBTRN02C opens the transaction master for output (`app/cbl/CBTRN02C.cbl:256`) after TRANBKP has deleted and redefined it (`app/jcl/TRANBKP.jcl:40-46`), and it rewrites the account and category balance masters where they stand (`app/cbl/CBTRN02C.cbl:311`, `:329`). The tree backs up the transaction master and the category balances but has no job that backs up the account master (inference). Online updates are kept off the same files only by a job that closes them (`app/jcl/CLOSEFIL.jcl:26-30`). One wrong rule in a port changes balances silently, and the only rollback is a snapshot design that does not exist yet. The port is not the hard part; the equivalence proof is.

## What else the assessment found

1. **Eight shared datasets are the real interface.** Programs in up to five different waves touch the same account, customer, card, cross reference, transaction and user files, and 46 of the 62 contract edges cross a wave boundary (`02-coupling.md`). Each reader moves before its writer through a read facade, and the system of record flips in the wave that holds the first writer.
2. **The extractor is blind in five places that change the plan.** JCL inside a COBOL literal, program names in IMS and DB2 parameters, symbolic dataset names, the CA-7 listing, and control cards each hid a dependency. Twenty-three units moved from the seed's placement, thirteen of them because of these blind spots (`03-waves.md`).
3. **The scheduler is not one thing.** Control-M, CA-7 and four shell wrappers describe overlapping and partly conflicting orders, and the wrappers rely on `sleep`, not on completion (`scripts/run_full_batch.sh:14`, `:48`). CA-7 says an IMS purge job triggers posting (`app/scheduler/CardDemo.ca7:43`, `:70`).
4. **Several legacy behaviors look like defects and must be decided, not ported by accident.** The transaction report counts the last amount twice and stops at the first record outside its window (`app/cbl/CBTRN03C.cbl:173-203`). Posting swallows a failed account rewrite (`app/cbl/CBTRN02C.cbl:554-559`). Interest truncates (`app/cbl/CBACT04C.cbl:464-465`). Twelve are seeded in the deviation register in `06-test-strategy.md`.
5. **Passwords are stored and compared in clear text** (`app/cbl/COSGN00C.cbl:223`, `app/jcl/DUSRSECJ.jcl:35-44`).
6. **Two jobs are broken as written.** CBIMPORT has no CARDOUT DD (`app/cbl/CBIMPORT.cbl:63`), and TRANREPT repeats a step name (`app/jcl/TRANREPT.jcl:23`, `:37`).

## Open Questions

For the client's own engineers. The first group are the files the extractor listed as not parsed and the limits that touch this system; the rest are what the evidence could not settle.

**Files the extractor did not read**

1. CA-7 listing `app/scheduler/CardDemo.ca7`: does CA-7 really submit these jobs in production? The listing marks jobs "MAINT ONLY" (`app/scheduler/CardDemo.ca7:28`). Is POSTTRAN really triggered by CBPAUP0J (`:43`, `:70`)? What are CLOSEFIL1 and CLOSEFIL2, which are named in the listing and not in the tree?
2. DB2 DCLGEN and DDL, 3 and 6 files (for example `app/app-authorization-ims-db2-mq/dcl/AUTHFRDS.dcl` and `app/app-transaction-type-db2/ddl/TRNTYPE.ddl`): please supply the table definitions, the plans and any stored procedures. Two DCLGEN and four DDL files belong to the transaction type tables, which I infer feed the report descriptions.
3. IMS DBD and PSB, 4 and 4 files (for example `app/app-authorization-ims-db2-mq/ims/DBPAUTP0.dbd` and `app/app-authorization-ims-db2-mq/ims/DLIGSAMP.PSB`): how many segments does the authorization database have, and how is it backed up?
4. Control cards, 8 files (for example `app/app-transaction-type-db2/ctl/DB2CREAT.ctl`, and `app/ctl/REPROCT.ctl`, the REPRO card that proc REPROC reads at `app/proc/REPROC.prc:28`): are these the exact commands run in production? CREADB2 has TYPRUN=SCAN in its job card (`app/app-transaction-type-db2/jcl/CREADB21.jcl:2`).
5. Assembler source and macros (`app/asm/COBDATFT.asm`, `app/asm/MVSWAIT.asm`, `app/maclib/ASMWAIT.mac`, `app/maclib/COCDATFT.mac`): CBACT01C calls COBDATFT (`app/cbl/CBACT01C.cbl:231`) and COBSWAIT calls MVSWAIT (`app/cbl/COBSWAIT.cbl:38`). What do they do exactly, and are there others not in the tree?

**Limits of the extractor that touch this system**

6. IDCAMS and SORT control cards are not read, so which side of every reload job writes is a guess. Who reads the transaction alternate index that TRANIDX builds (`app/jcl/TRANIDX.jcl:25`)?
7. JCL symbolic parameters such as `&HLQ` are not resolved (this limit is not in the extractor's own list). Does any other job depend on them (`app/app-transaction-type-db2/jcl/TRANEXTR.jcl:25`)?
8. JCL COND is not modeled. What stops the chain when a step fails (`app/jcl/TRANBKP.jcl:51`, `app/jcl/CREASTMT.JCL:56`)? The wrappers check no return code.
9. COPY REPLACING is not applied. It is used once (`app/app-transaction-type-db2/cbl/COTRTUPC.cbl:1358`). Does it change a layout?
10. EXEC CICS RETURN TRANSID, START and SEND MAP are not edges, so transaction to transaction flow is missing. Which transactions chain by transaction id?
11. DCB, LRECL and RECFM are not read. Are the record lengths in the JCL the ones in the copybooks?
12. A contract edge is high only when both sides copy the same layout. Does any program read a shared record through a private layout?

**What the evidence could not settle**

13. Which programs and jobs ran in the last 12 months, and which run only at month end or fiscal close? Start with CBTRN01C, the samples and the 27 jobs no scheduler names (`05-dead-code.md`).
14. TRANBKP runs twice in `scripts/run_full_batch.sh` (`:29`, `:55`) and COMBTRAN reads generation 0 of the backup (`app/jcl/COMBTRAN.jcl:24`). Does the master keep its history, and what backs up the account master?
15. Where do the flat files that ACCTFILE, CARDFILE and XREFFILE reload from come from, and who produces the daily transaction file? Nothing in the tree writes them (analysis: no data edge writes them). Does the reload discard online changes on purpose?
16. Is "account and card master refresh" the reload jobs ACCTFILE and CARDFILE, the online programs COACTUPC and COCRDUPC, or both? I planned for both.
17. Is TRANREPT run by hand, by the online request, or by something not in the tree? It has a hardcoded 2022 window (`app/jcl/TRANREPT.jcl:43-44`), and a repeated step name that a converter may reject (`app/jcl/TRANREPT.jcl:37`).
18. Program COCRDSEC is defined for transaction CDV1 and has no source (`app/csd/CARDDEMO.CSD:388`). Where is it?
19. Two definitions of the TRANREPT generation group disagree, limit 10 and limit 5 (`app/jcl/REPTFILE.jcl:25-28`, `app/jcl/DEFGDGB.jcl:36-40`). Which is live?
20. The wrappers say "FTP Tunnel to Ensono" (`scripts/run_posting.sh:5`) and the tree is headed with Amazon license notices (`app/jcl/POSTTRAN.jcl:4`). Is this the production system, a sample derived from it, or a mix? Several jobs (test, FTP, TYPRUN=SCAN) suggest a demo environment.
21. Are user passwords really stored in clear text in production, and may the target hash them (`app/cbl/COSGN00C.cbl:223`)?

## Files in this folder

| File | What it is |
|---|---|
| `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `05a-dead-code-candidates.md` | Generated fact tables |
| `02-coupling.md` | The coupling argument and the open edge findings |
| `03-waves.md`, `waves.json` | The wave plan and its 23 deviations |
| `04-estimate.md` | Ranges and their assumptions |
| `05-dead-code.md`, `dead-code.json` | Three buckets |
| `06-test-strategy.md` | Oracles, normalization, deviation register, exit bars |
| `risks.json` | Two axis scores for 99 units |
| `graph.json` | The dependency graph, every edge with file and line |
