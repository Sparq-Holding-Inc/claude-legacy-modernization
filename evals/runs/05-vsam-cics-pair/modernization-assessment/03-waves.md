# Waves

Target state: refactor. The plan is the extractor's seed with no deviations (`modernization-assessment/waves.json:1`). Machine form: `waves.json`.

| Wave | Name | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | Account inquiry (TRNR) | PROGR | low | medium | The decoded ACCTREC layout and the record-level harness | app/csd/DEMO.CSD:6, app/cbl/PROGR.cbl:7 |
| 2 | Account write (TRNW) | PROGW | medium | medium | Retiring the shared KSDS | app/csd/DEMO.CSD:4, app/cbl/PROGW.cbl:7 |

## Why this order

PROGR only reads ACCTDAT (app/cbl/PROGR.cbl:7). It proves the toolchain on the cheapest unit. The reader is ported first against records the legacy writer still produces. That works only if the ported reader decodes the packed balance the same way (app/cpy/ACCTREC.cpy:3). Wave 1 is the test of that.

PROGW is the only writer (app/cbl/PROGW.cbl:7). It goes second because a wrongly written record would corrupt what every reader sees. Once it moves, the dataset has one owner.

## Waves that are not valid on their own terms

Both waves are independently deployable and testable at the CICS transaction boundary (app/csd/DEMO.CSD:4, app/csd/DEMO.CSD:6). Rollback is the part to check. For wave 1, rollback is switching TRNR back to PROGR. For wave 2, rollback must also cover any record the new writer already wrote, so a dual-write or a reconcile step is needed before cutover (inference).

## Not placed

Nothing is unassigned. **The must-not-break item "the nightly batch cycle" is placed nowhere, because the tree has no batch job, JCL, proc, scheduler or batch program.** Both entry points are online transactions (app/csd/DEMO.CSD:4, app/csd/DEMO.CSD:6). No wave claims to protect the batch cycle. See `00-summary.md`.

Wave seed facts: `03a-wave-seed.md`. Deviations: none.
