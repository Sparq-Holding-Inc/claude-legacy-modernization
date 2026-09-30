# 03 Waves

Target state: refactor (given as a flag). The plan is in `waves.json`.

## The wave count is zero

The tree has no entry point. It holds no JCL job, no CSD transaction, no scheduler job and no shell
wrapper (`analysis.entry_points` is empty, and `meta.files_seen` in `graph.json` shows zero for every
kind except COBOL). The wave seed builds waves from the entry points that use each unit
(`03a-wave-seed.md`). With no entry point it places nothing, and it says so for both programs.

I did not invent a wave. `modernization-assessment/waves.json:3` has `"waves": []`, and both programs are
in `unassigned`. No unit moved, so there are no deviations.

| Unit | Wave | Reason not placed | Confidence | Evidence |
|---|---|---|---|---|
| PROGA | none | No entry point reaches it in the tree. It ends in `STOP RUN`, so it looks like a batch main program, but nothing in the tree starts it. | high | `app/cbl/PROGA.cbl:7` |
| PROGB | none | No entry point in the tree. Its only caller is PROGA, so it belongs wherever PROGA goes. | high | `app/cbl/PROGA.cbl:6` |

## What the risk scores say

`risks.json` scores both programs low-low (`modernization-assessment/risks.json:13` and
`modernization-assessment/risks.json:33`). If they were placed, low-low means wave one, where the
toolchain is proved. The score for PROGA is low confidence. Its blast radius is 2 only because it writes
nothing and calls one no-op. The real blast radius depends on whether it sits inside the nightly batch
cycle, and the tree cannot say.

## What would let a plan be cut

Nothing can be sequenced until the client supplies at least one of these:

- the JCL for the nightly batch cycle, with its PROCs
- a scheduler export (Control-M XML is read by the extractor, and other schedulers are not)
- a CSD export, if any of this runs under CICS

With those, the extractor can find entry points, the wave seed will place these two programs, and
`must-not-break` ("the nightly batch cycle") can be mapped to a unit. Until then the four tests for
a valid wave (independent deploy, independent rollback, a testable boundary and a nameable business
outcome) cannot be checked against anything.

## What a wave for these two programs would unblock

Nothing that a business stakeholder could name. The pair is a chore for its own sake. If the tree is
the whole system, it proves the toolchain and nothing else. This is inference, because the full
system is not in the tree.
