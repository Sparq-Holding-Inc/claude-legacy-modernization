# 04 Estimate

Target state is `refactor`, given as a flag. One wave, so one estimate.

**Method.** Bottom-up by activity, not by lines of code. The tree has 17 lines in total (three
four-line programs and a five-line job). Lines predict nothing here. What moves the estimate is the
number of coupling edges crossing the wave boundary, whether an oracle exists, and how much has to be
learned from the client. Every figure below is inference. It is a judgment, not a measurement.

## Wave 1: SEQJOB step chain

| Activity | Range (person-days) | Confidence | Evidence |
|---|---|---|---|
| Port the three programs. Each is an empty program that returns. | 0.5 to 1 | medium | `app/cbl/PGMA.cbl:4`, `app/cbl/PGMB.cbl:4`, `app/cbl/PGMC.cbl:4` |
| Carry the four-step order into the target scheduler or workflow, and settle the duplicate step name with the client. | 1 to 3 | low | `app/jcl/SEQJOB.jcl:3`, `app/jcl/SEQJOB.jcl:5` |
| Build the comparison harness: run order, return codes and elapsed time from legacy job logs against the new run. | 2 to 4 | low | inference |
| Obtain the oracle from the client: archived job logs and SMF records for SEQJOB. Mostly elapsed time, little effort. | 0.5 to 1 | low | inference |
| **Wave total** | **4 to 9** | low | inference |

## What the range is most sensitive to

Each is stated so it can be proved wrong.

1. **Assumes the programs in this tree are the whole story.** If PGMA, PGMB and PGMC are stubs, and the
   production programs live elsewhere, this estimate is void. The port cost would then follow the
   real source. Evidence: `app/cbl/PGMA.cbl:4`.
2. **Assumes SEQJOB touches no datasets.** If the job gets DDs from a scheduler override, a PROC or
   symbolic parameters the tree does not hold, the harness gains a file oracle and contract edges
   between the steps. In that case the harness activity roughly doubles. Evidence: `app/jcl/SEQJOB.jcl:2`.
3. **Assumes the second STEP2 is a copy-paste slip that nothing references.** If a restart, a
   scheduler condition or an operator runbook addresses STEP2 by name, the port has to decide which
   step it means. Add 1 to 2 days and one client decision. Evidence: `app/jcl/SEQJOB.jcl:5`.

## Where Claude Code helps and where it does not

| Work | Claude Code | Confidence | Evidence |
|---|---|---|---|
| Transliterate the three programs | Strong. There is no logic to misread. | high | `app/cbl/PGMB.cbl:4` |
| Translate the job into the target orchestration, one task per step, in order | Strong, with a harness that checks the order. | medium | `app/jcl/SEQJOB.jcl:2` |
| Write the log comparison harness | Strong. | medium | inference |
| Decide whether the order between steps matters, or why the job exists | Weak. The source states no intent and no business rule. Ask the client's engineers. | high | `app/jcl/SEQJOB.jcl:1` |
| Say what the duplicate STEP2 was meant to be | Cannot. Ask. | high | `app/jcl/SEQJOB.jcl:5` |

## Not estimated

Anything outside the tree: the scheduler that starts SEQJOB, jobs before and after it, and any
program the extractor did not see. `graph.json` lists no unparsed file, but the scheduler artifact
is absent (`analysis.warnings`). The nightly cycle may be larger than this job. Inference.
