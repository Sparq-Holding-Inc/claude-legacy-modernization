# 03 Waves

Target state: refactor. `modernization-assessment/waves.json:2` holds the plan. The seed is in `03a-wave-seed.md`. **No deviations from the seed.** The seed already puts the reader before the writer, and the risk scores agree (PROGR low-low, PROGW low-high), so nothing forced a move.

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | online-readonly | PROGR (transaction TRNR) | low | medium | `app/csd/DEMO.CSD:6`, `app/cbl/PROGR.cbl:7` |
| 2 | online-writers | PROGW (transaction TRNW) | high | low | `app/csd/DEMO.CSD:4`, `app/cbl/PROGW.cbl:7` |

Two waves for two programs is deliberate. Merging them would put an irreversible write behind a read-only proof of the toolchain. Splitting them gives a first wave that can be rolled back completely.

## Wave 1. Account read transaction TRNR

- **What moves.** PROGR, which reads the ACCTDAT file into ACCT-REC and returns (`app/cbl/PROGR.cbl:7-11`). The copybook ACCTREC and the CSD entries move with it (`app/csd/DEMO.CSD:6-7`).
- **Why first.** It writes nothing. Its risk scores are low-low (`modernization-assessment/risks.json:13`). The wave proves the toolchain and builds the ACCTREC decoder that wave 2 needs.
- **Unblocks.** The decoder and a read-side harness. Wave 2 uses the reader to check what PROGW writes.
- **Deployable and reversible on its own.** The new reader runs behind transaction TRNR. Rollback is pointing TRNR at the old program again (`app/csd/DEMO.CSD:6-7`). This works only while nothing else needs the new reader. That is inference.
- **Testable boundary.** The ACCTDAT file, which is the articulation point (`modernization-assessment/graph.json:195`). Give both readers the same snapshot and the same keys, and compare what each returns.
- **Stakeholder name.** "Account read". The source has no screen and no business logic, so the name comes from the transaction name only. That is inference.
- **Condition on this wave.** The new reader must read the legacy file, or a copy that stays in step with it, while PROGW still writes it. How that copy is kept is not decided and not in the tree. It is the main cost driver in `04-estimate.md`.

## Wave 2. Account write transaction TRNW

- **What moves.** PROGW, which writes ACCT-REC to the ACCTDAT file and returns (`app/cbl/PROGW.cbl:7-11`).
- **Why second.** It is the only writer in the tree and its write cannot be undone by rerouting the transaction. Its scores are low-high (`modernization-assessment/risks.json:34`). The port is easy and the verification is the work, so it waits until the wave 1 harness is proven.
- **Unblocks.** Retiring the legacy owner of the file, so the data can move. Nothing else in the tree waits on it.
- **Deployable and reversible on its own.** Only with a shadow or parallel run against a copy of the file. Rerouting TRNW stops new writes but leaves the records the new code already wrote. Take a copy of the file before cutover. That is inference.
- **Testable boundary.** The ACCTDAT file after the run. Apply the same inputs to both writers on copies of the same file and compare the records.
- **Confidence is low.** The must-not-break item, the nightly batch cycle, maps to no unit in the tree. Whether it reads or writes this file is unknown, so the blast radius could be higher than scored.
- **Stakeholder name.** "Account update". That is inference from the transaction name only.

## What this plan cannot do

The batch cycle has no wave. Nothing in the tree is a batch job (`files_seen` at `modernization-assessment/graph.json:24-33`, no JCL, no scheduler). It cannot be sequenced until the client supplies the JCL, PROCs and scheduler export. If it uses the ACCTDAT file, wave 1 and wave 2 may need to move after or beside it. That is inference.
