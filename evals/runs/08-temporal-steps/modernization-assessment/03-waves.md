# 03 Waves

Target state: refactor. Waves: 1. Deviations from the extractor's seed: none (`modernization-assessment/waves.json:3`).

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-readonly | PGMA, PGMB, PGMC, job:SEQJOB | low | low | `app/jcl/SEQJOB.jcl:1`, `app/jcl/SEQJOB.jcl:5` |

## Wave 1. Nightly sequence job

- **Why one wave.** The job runs three programs in file order (`app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`). No shared dataset or copybook ties them to anything else. It can be deployed and rolled back as one job. `inference` that it can sit behind a flag, since no scheduler is in the tree.
- **Testable boundary.** Step order and return codes. No dataset exists, so the oracle has to come from job output and logs (see `06-test-strategy.md`).
- **What it unblocks.** Nothing. No other unit depends on it. It proves the toolchain.
- **Why confidence is low.** The programs are 4-line stubs (`app/cbl/PGMA.cbl:4`), the scheduler is absent, and the job repeats a step name (`app/jcl/SEQJOB.jcl:5`). That repeated name is normally a JCL error, so the job may not run as written. `inference`
- **Computed calls.** None. The wave does not drop below high confidence because of them.

A single wave is a valid answer for a tree this size. Cutting it further would split a step sequence that the job enforces.
