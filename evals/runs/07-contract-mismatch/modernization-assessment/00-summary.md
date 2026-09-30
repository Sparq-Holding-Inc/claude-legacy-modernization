# 00 Summary

A modernization assessment of the batch system in the work folder: two COBOL programs, two copybooks, two JCL jobs and one shared dataset. Facts come from the extractor and its `graph.json`. Judgment is mine, and it is labeled `inference` where the source does not prove it.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (the work folder) | command line |
| Target state | refactor | `--target refactor` |
| Must not break | the nightly batch cycle | `--must-not-break` |
| Runtime telemetry | none | `--telemetry none` |

All three answers came as flags. No defaults applied.

Telemetry is none, so every dead-code claim is provisional. Dormancy was not measured at all, because the folder holds no git history (`05-dead-code.md`).

"The nightly batch cycle" is not named anywhere in the tree, and there is no scheduler. I read it as WRITEJOB followed by READJOB. That is inference.

## Result

| Item | Result | Evidence |
|---|---|---|
| Waves | 2 | `modernization-assessment/waves.json:3` |
| Wave 1 | Reader step: `PGMR`, `job:READJOB`. Blast radius medium. | `app/jcl/READJOB.jcl:1` |
| Wave 2 | Writer step: `PGMW`, `job:WRITEJOB`. Blast radius high. | `app/cbl/PGMW.cbl:6` |
| Deviations from the extractor's seed | None | `modernization-assessment/waves.json:28` |
| Effort | About 10 to 19 engineer days, mostly harness and environment | inference |
| Dead code | None in any bucket. Dormancy not measured. | analysis |
| God modules, strongly connected components, computed calls | None | analysis |

## The single largest risk

The one contract in the system, on SPARQ.TEST.MASTER, is held together by two separate copybooks and by an LRECL that matches neither. PGMW writes through `LAYOUTX` (`app/cbl/PGMW.cbl:11`) and PGMR reads through `LAYOUTY` (`app/cbl/PGMR.cbl:11`). The extractor rated the edge medium. I compared them by hand. Both are 10 bytes of text and a 5 byte packed decimal, so 15 bytes, and I found no mismatch today (`app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTY.cpy:2`). But the output DD says `LRECL=80` (`app/jcl/WRITEJOB.jcl:4`), and the extractor never compares that with a layout. Nothing in the tree checks any of this. A silent break here would sit on the path the user said must not break, and the reader would not notice, because it never uses a field (`app/cbl/PGMR.cbl:14`). This is inference.

## Open Questions for the client's engineers

1. **Is SPARQ.TEST.MASTER a test dataset or the real master?** The name carries a `TEST` qualifier (`app/jcl/WRITEJOB.jcl:3`). If the whole pair is a test fixture, the assessment describes something other than the nightly cycle.
2. **What is the record length of SPARQ.TEST.MASTER, 15 or 80 bytes?** The DD says `LRECL=80` (`app/jcl/WRITEJOB.jcl:4`). Both copybooks describe 15 bytes. What happens at open, and does any consumer expect padding?
3. **Which scheduler runs WRITEJOB and READJOB, and in what order?** The extractor found none (`analysis.warnings`). Please supply the export. Only Control-M XML and shell wrappers that name JCL files are read. Without it the order writer then reader is inference, and so is the nightly schedule itself.
4. **What else reads SPARQ.TEST.MASTER outside this tree?** The tree holds one reader. Any other consumer changes the blast radius of wave 2, and the layout it uses matters.
5. **What does PGMW put in the record?** It writes `LAYOUT-REC` without ever filling it in (`app/cbl/PGMW.cbl:13`, `app/cbl/PGMW.cbl:14`). Is that a stub, or does something fill the record that we cannot see? Does any reader accept a packed field that is not valid?
6. **How is the dataset deleted between runs?** WRITEJOB creates it new with `DISP=(NEW,CATLG,DELETE)` (`app/jcl/WRITEJOB.jcl:3`), and no job in the tree deletes the old one.
7. **Do both jobs still run?** No telemetry and no git history exist, so dormancy was not measured. Can the client supply job history for the last 12 months, or SMF records?
8. **Can the legacy system stay up for a parallel run of the writer, and can the client supply archived copies of the dataset and the SYSOUT for a month end?** This decides the oracle for both waves (`06-test-strategy.md`).

## Not parsed, and limits that touch this system

- **Not parsed:** nothing. The extractor listed no unparsed file (`analysis`, field `unparsed` is empty in `graph.json`).
- **DCB, LRECL and RECFM are not read**, so the record length on the DD was never compared with a copybook (`meta.limits`). This is why question 2 is open.
- **No scheduler was parsed.** The order of jobs across jobs is unknown (`analysis.warnings`).
- **Dormancy was not computed.** No last-modified dates exist (`analysis.warnings`).
- **`IF/THEN/ELSE` and `COND=` are not modeled** (`meta.limits`). Neither JCL member uses them, so it does not change this result (`app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`).
- **A contract edge is high only when both sides share a layout copybook** (`meta.limits`). High would still not prove the layouts are equal. The medium rating here is why I checked by hand.
- **JCL text inside COBOL, EXEC CICS chains, IMS, DB2 and MQ:** none appear in the tree, and this plugin does not analyze them. Anything outside the tree is unseen.

## Files

| File | What it holds |
|---|---|
| `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `05a-dead-code-candidates.md` | Generated fact tables |
| `02-coupling.md` | Coupling argument and the hand check of the contract edge |
| `03-waves.md`, `waves.json` | The wave plan |
| `04-estimate.md` | Estimate with sensitivity |
| `05-dead-code.md`, `dead-code.json` | Dead code register |
| `06-test-strategy.md` | Oracle, normalization, deviation register |
| `risks.json` | Two axis risk scores |
