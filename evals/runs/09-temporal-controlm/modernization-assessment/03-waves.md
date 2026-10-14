# 03 Waves

Target state: refactor. Machine-readable plan: `modernization-assessment/waves.json:1`. Starting cut: `03a-wave-seed.md`. Deviations from the seed: none.

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-utility | `job:JOBA`, `job:JOBB`, `sch:NIGHTLY/JOBA`, `sch:NIGHTLY/JOBB` | low | low | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`, `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |

## Wave 1. Nightly Control-M cycle (JOBA then JOBB)

- **What moves.** Two JCL jobs and the two Control-M job definitions that run them (`app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`).
- **Why one wave.** JOBA sets `JOBA-DONE` (`app/scheduler/nightly.xml:6`) and JOBB waits on it (`app/scheduler/nightly.xml:9`). Splitting them puts the condition across a cutover boundary. A single sentence describes the wave: the nightly cycle. That is the must-not-break item, so the whole item sits in one wave.
- **Why batch-utility.** Both steps run `IEFBR14` (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`) and no DD names a dataset. No program, dataset or copybook is shared.
- **Deployable and rollback.** Independently deployable behind the scheduler: run the new definition in a parallel folder with its own ODATE conditions. Rollback is to stop ordering the new folder and keep ordering `NIGHTLY`. Inference: nothing in the tree prevents this.
- **Testable boundary.** The boundary is the scheduler: the order jobs start in, the conditions set and deleted, and the return codes. There is no data boundary in the tree.
- **Stakeholder-nameable.** "The nightly batch cycle still runs, in order, on its trigger." That is the item the client named.
- **Unblocks.** Nothing in the tree depends on it. It would prove the scheduler cutover for any work added later.
- **Confidence: low.** The jobs do no visible work, so a green wave 1 proves the scheduler, not business logic. Whatever the cycle really does is not in this tree (see Open Questions in `00-summary.md`).
- **Computed calls.** None (`analysis.unresolved_dynamic` is empty).

## Behavior the port must keep (it is not in the edge list)

| Behavior | Detail | Confidence | Evidence |
|---|---|---|---|
| JOBA waits on an external condition | `EXTERNAL-FEED` is set by nothing in this tree. The new scheduler needs the same trigger, and whoever sets it must be told. | high that it is external | `app/scheduler/nightly.xml:5` |
| JOBB deletes `JOBA-DONE` | One-shot semantics: the condition is consumed, so a rerun of JOBB waits for another JOBA. A plain-dependency port loses this. | medium (the effect follows from the Control-M `SIGN="-"` convention; intent is `inference`) | `app/scheduler/nightly.xml:10` |
| All conditions are scoped to `ODAT` | The cycle is keyed on the order date. A scheduler that keys on wall-clock date differs around midnight and on reruns. | medium | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:9` |
