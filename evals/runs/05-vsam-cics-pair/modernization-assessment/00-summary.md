# Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (current directory) | no scope argument |
| Target state | refactor | `--target refactor` |
| Must not break | "the nightly batch cycle" | `--must-not-break` |
| Telemetry | none | `--telemetry none` |
| Delivery | not given. The estimate shows conventional and AI-assisted side by side. | no `--delivery` flag |

No defaults applied. Every scoping answer came as a flag.

## What was found

The tree is 2 COBOL programs, 1 copybook and 1 CSD (modernization-assessment/graph.json:24). Both programs are CICS transactions (app/csd/DEMO.CSD:4, app/csd/DEMO.CSD:6). They share one VSAM file through one copybook (app/cbl/PROGW.cbl:7, app/cbl/PROGR.cbl:7, app/cpy/ACCTREC.cpy:1). There are no calls, cycles, god modules or computed calls.

- **Waves: 2.** Wave 1 is PROGR (read only). Wave 2 is PROGW (the only writer). No deviations from the seed. See `03-waves.md`.
- **Risk scores** are in `risks.json`: PROGR low-low, PROGW high-high. These come from the risk-assessor agent and rest on 11-line programs with no business logic in them (inference).

## Largest risk

**The must-not-break item has no home in this tree.** "The nightly batch cycle" maps to no unit: there is no JCL, proc, scheduler or batch program (modernization-assessment/graph.json:25). The one shared data hub, ACCTDAT, has a writer and a reader in the online region only (modernization-assessment/graph.json:199). If a batch job reads or loads it, that job is an unassessed third party to the packed-decimal balance layout (app/cpy/ACCTREC.cpy:3), and a refactor of PROGW could silently break it. This assessment cannot say that the batch cycle is safe. It can only say it was not shown the batch cycle.

## Open Questions for the client's engineers

1. Where is the nightly batch cycle? Please supply the JCL, procs and scheduler export. The extractor parsed zero JCL, zero Control-M and zero shell files (modernization-assessment/graph.json:25).
2. Does any batch job, utility (IDCAMS REPRO, for example) or other transaction read, load or back up `SPARQ.TEST.ACCTDAT.KSDS`? (app/csd/DEMO.CSD:2)
3. The dataset name contains TEST. Is this the production file, and is this tree the production region or a demo? (app/csd/DEMO.CSD:2)
4. What are the VSAM key length, record length and CI settings for ACCTDAT? None are in the tree, and the extractor does not read DCB or LRECL (modernization-assessment/graph.json:20).
5. Neither program checks a response code, and neither sets ACCT-ID or ACCT-BAL (app/cbl/PROGR.cbl:7, app/cbl/PROGW.cbl:7). Is that the whole program, or was code removed? Where do the balance arithmetic and the posting rules live?
6. Is there a parallel-run capability, CICS journals for TRNW and TRNR, or archived GDG outputs for use as the oracle? (`06-test-strategy.md`)
7. Dormancy was not computed because the tree is not a git repository (analysis `warnings`). What are the last-change dates and the usage of TRNR and TRNW over the last 12 months?
8. The extractor does not follow EXEC CICS RETURN TRANSID, START or SEND MAP (modernization-assessment/graph.json:18). Are there BMS maps or chained transactions outside this tree?
9. The extractor does not read DB2, IMS or MQ use in the tree (none seen). Does the wider system have any?

Files the extractor listed as not parsed: none (`unparsed` is empty, modernization-assessment/graph.json:169).

## Files

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, with `graph.json`, `waves.json`, `risks.json` and `dead-code.json`.
