# 00 Summary

Assessment of the tree at `.` (one JCL job, three COBOL programs). Non-interactive run.

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | `refactor` | flag `--target refactor` |
| What must not break | "the nightly batch cycle" | flag `--must-not-break` |
| Runtime telemetry | `none` | flag `--telemetry none` |

All three came as flags, so no defaults were applied. With telemetry `none`, every dead-code claim is
provisional.

## Result

- **Wave count: 1.** `job:SEQJOB` with `PGMA`, `PGMB` and `PGMC`. The tree has no boundary to cut. Step
  order binds all four. Evidence: `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`,
  `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5`.
- **Single largest risk.** The only behavior in the tree is the order in which SEQJOB runs its steps,
  and the job as written names STEP2 twice, at lines 3 and 5. Duplicate step names are, to my
  knowledge, a JCL error on z/OS, so this file may not be what production runs. A restart, condition
  or scheduler rule that says STEP2 is ambiguous. If SEQJOB is the nightly cycle, a port that gets the
  order or the restart point wrong is silent. Inference for the z/OS behavior and for SEQJOB being the
  cycle. Evidence: `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`.
- **No dead code found, and that is weak evidence.** Every node is reachable, there is no computed
  call, and last-modified dates are missing, so dormancy was not tested. Evidence: `05-dead-code.md`
  and `app/jcl/SEQJOB.jcl:2`.

## Findings

| Finding | Confidence | Evidence |
|---|---|---|
| Step order PGMA, PGMB, PGMC, IEFBR14 is the only coupling. There are no data, contract or call edges between programs. | high | `app/jcl/SEQJOB.jcl:2`, `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:4`, `app/jcl/SEQJOB.jcl:5` |
| Step name STEP2 is used twice. The extractor labeled the second `step:SEQJOB.STEP2#2`. | high | `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5` |
| The last step runs IEFBR14 with no DDs and appears to do nothing. | medium | `app/jcl/SEQJOB.jcl:5` |
| All three programs are four-line stubs that return. | high | `app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4` |
| No scheduler artifact is in the tree. What starts SEQJOB, and what runs around it, is unknown. | high | inference |
| Estimate for wave 1 is 4 to 9 person-days, low confidence. | low | inference |

## Open Questions for the client's engineers

1. Is SEQJOB the nightly batch cycle, or one part of it? What starts it, and what runs before and
   after it? The extractor found no scheduler file. Evidence: `app/jcl/SEQJOB.jcl:1`.
2. Why is STEP2 used twice? Which step does a restart, a COND test or a runbook mean by STEP2? Is this
   file the one that runs in production? Evidence: `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5`.
3. Does the order PGMA, PGMB, PGMC matter, and why? No dataset connects them in this tree. Where do
   their inputs and outputs live? Evidence: `app/cbl/PGMB.cbl:3`.
4. Are these the real programs? Each is four lines and does nothing. Is the production source
   elsewhere? Evidence: `app/cbl/PGMA.cbl:4`.
5. What does IEFBR14 do in the last step? Can it be dropped? Evidence: `app/jcl/SEQJOB.jcl:5`.
6. When was each member last changed, and which jobs ran in the last 12 months? There is no git
   history, so dormancy could not be tested. Evidence: inference.
7. What is the intended behavior when a step ends with a nonzero return code? The job has no COND= or
   IF. Evidence: `app/jcl/SEQJOB.jcl:2`.

## Not parsed, and extractor limits that touch this system

- **Not parsed:** nothing. `graph.json` lists no unparsed file. The scheduler is absent, not
  unparsed. Evidence: `app/jcl/SEQJOB.jcl:1`.
- **IF/THEN/ELSE and COND= are not modeled,** so step order is file order. The job has neither, so the
  limit does not bite here. Evidence: `app/jcl/SEQJOB.jcl:2`.
- **Only Control-M XML and shell wrappers are read as schedulers.** Any other scheduler is invisible.
  Evidence: inference.
- **A called subprogram gets no DDs from its caller's step, and IDCAMS, SORT and other in-stream cards
  are not read.** Not triggered here. No DD exists. Evidence: `app/jcl/SEQJOB.jcl:2`.
- **Jobs submitted through the internal reader, nested PROCs and CICS chains are not followed.**
  None appear in the tree, but the stub programs could hide them. Evidence: `app/cbl/PGMA.cbl:4`.

## Files

`graph.json`, `01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `waves.json`,
`04-estimate.md`, `05-dead-code.md`, `05a-dead-code-candidates.md`, `dead-code.json`,
`06-test-strategy.md`, `risks.json`.
