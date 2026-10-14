# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| Must not break | "the nightly batch cycle" | flag `--must-not-break` |
| Runtime telemetry | none, so every dead-code claim is provisional | flag `--telemetry none` |
| Delivery | not given, so the estimate shows conventional and AI-assisted side by side | no `--delivery` flag |

No defaults applied. All three scoping answers came as flags.

## What is in the tree

2 COBOL programs, 2 JCL jobs, 1 copybook and 1 dataset, 32 lines of COBOL in all (`01-inventory.md`). Nothing was skipped as unparsed (`modernization-assessment/graph.json:286`). There is no scheduler artifact, no CSD and no PROC (`modernization-assessment/graph.json:24`).

## Plan

**2 waves**, no deviations from the extractor's seed (`03-waves.md`).

1. Reader: `PGMR` and `job:READJOB`. Low blast radius.
2. Writer: `PGMW` and `job:WRITEJOB`. Medium blast radius.

Estimate: 4 to 9 engineer-weeks conventional, 3 to 7 AI-assisted. These are planning assumptions with no calibrated productivity data behind them (`04-estimate.md`). Dead code: none proposed, and dormancy was not measured (`05-dead-code.md`).

## Largest risk

The shared file `SPARQ.TEST.MASTER` is an undocumented interface, and its layout does not agree with itself. The copybook describes a 15-byte record with a packed-decimal amount (`app/cpy/LAYOUTX.cpy:3`), and the writer's DD declares `LRECL=80` (`app/jcl/WRITEJOB.jcl:4`). The extractor does not compare the two (`modernization-assessment/graph.json:20`). Until that is settled, a port cannot say what byte-exact output means. Separately, the "nightly batch cycle" you named maps to no unit in this tree.

## Open Questions for the client's engineers

1. **Which job or jobs are "the nightly batch cycle"?** Nothing in the tree is named nightly and no scheduler was provided (`modernization-assessment/graph.json:383`). Please supply the Control-M export, the shell wrapper or the scheduler definition. Until then the must-not-break item maps to no unit, and the anchor for the equivalence harness is unconfirmed.
2. **What is the real record length of `SPARQ.TEST.MASTER`?** The copybook gives 15 bytes (`app/cpy/LAYOUTX.cpy:2`), the writer's DD says `LRECL=80` (`app/jcl/WRITEJOB.jcl:4`), and the reader's DD names no attributes (`app/jcl/READJOB.jcl:3`). What fills the other 65 bytes?
3. **What does `PGMW` write?** It writes `LAYOUT-REC` and moves no value into it (`app/cbl/PGMW.cbl:14`). Is that a stub or test fixture, or is the content set somewhere this tree does not show?
4. **Is this a live cycle or test data?** The dataset is named `SPARQ.TEST.MASTER` (`app/jcl/WRITEJOB.jcl:3`). If it is a test pair, what is the production equivalent, and where is it?
5. **How does the file get removed between runs?** WRITEJOB creates it with `DISP=(NEW,CATLG,DELETE)` (`app/jcl/WRITEJOB.jcl:3`), which fails if the name is already cataloged. No delete or rotate step is in the tree.
6. **What must the order of the two jobs be, and who enforces it?** No condition or scheduler ties READJOB to WRITEJOB (`modernization-assessment/graph.json:383`).
7. **Can you give us archived copies of the master file and past job logs?** This is the oracle for both waves (`06-test-strategy.md`).
8. **Are there other consumers of the file** (partners, a warehouse load, reports) that read it by column offset? The extractor sees only the two programs in this tree.
9. **What are the last-modified dates and run history?** The target is not a git repository, so dormancy was not computed (`modernization-assessment/graph.json:382`).

## Extractor limits that touch this system

- Record length (`DCB`, `LRECL`) is not compared with a copybook (`modernization-assessment/graph.json:20`).
- A `high` contract edge means a shared layout, not proven equal (`modernization-assessment/graph.json:21`).
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers (`modernization-assessment/graph.json:19`).
- `IF/THEN/ELSE` and `COND=` in JCL are not modeled (`modernization-assessment/graph.json:16`).
- COBOL is read as fixed format (`modernization-assessment/graph.json:10`).

## Files

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, `waves.json`, `risks.json`, `dead-code.json`, `graph.json`, plus the generated `02a`, `03a` and `05a` tables.
