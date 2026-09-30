# 04 Estimate

Every number below is `inference`. No line count or history in the tree can support one. The tree holds 4 lines of JCL and 14 lines of scheduler XML (`app/jcl/JOBB.jcl:2`, `app/scheduler/nightly.xml:14`). The method is edge based, as the skill asks: count what crosses the wave boundary, then add the work of proving equivalence. Lines of code are not used.

## Wave 1. Nightly batch cycle

| Item | Estimate | Basis | Confidence | Evidence |
|---|---|---|---|---|
| Re-express the two jobs and the two scheduler entries on the target platform | 2 to 5 person-days | 2 jobs, 2 scheduler entries, 1 temporal edge, 1 external input, 1 consumed condition. No data edge and no program | medium | `app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`, inference |
| Build the equivalence harness for the condition chain | 5 to 10 person-days | The oracle has to come from job history and logs, not from a dataset. There are no datasets in the tree | low | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`, inference |
| Run in parallel for a full business cycle including month end | 1 to 2 calendar months elapsed, low effort per day | Needed for the must-not-break item. Length is set by the capture window, not by the work | low | inference |
| Total for wave 1 | 8 to 15 person-days plus the elapsed parallel run | Sum of the rows above | low | inference |

The range is wide on the harness and the parallel run and narrow on the port. That matches where the risk is: the port is trivial and the proof is the work.

## Assumptions the range is most sensitive to

Each is a claim that can be checked.

1. **Assumes the two IEFBR14 steps are the whole job.** If either job is a placeholder and the real program is submitted from another library, the port and harness cost grow by the size of that program, and this estimate does not cover it. Check: ask the client whether `IEFBR14` is what runs in production. `app/jcl/JOBA.jcl:2`
2. **Assumes EXTERNAL-FEED is an ordinary Control-M condition that the target scheduler can receive.** If it is set by a file watcher, another scheduler, or an operator, add 3 to 10 person-days to rebuild that trigger and test it. Check: find what adds EXTERNAL-FEED today. `app/scheduler/nightly.xml:5`
3. **Assumes the target scheduler can express a condition that is posted, waited on and then deleted.** If the target has no such concept, the deletion needs a hand written state step, and the harness needs a rerun test for each case. Add 2 to 5 person-days. `app/scheduler/nightly.xml:10`
4. **Assumes nothing outside the tree waits on JOBB-DONE.** If something does, that consumer joins the wave and the range roughly doubles. `app/scheduler/nightly.xml:11`

## Where Claude Code can do the port, and where it cannot

| Part | Claude Code fit | Why | Evidence |
|---|---|---|---|
| Transliterating the two scheduler entries to the target scheduler's format | Strong | Mechanical, and there is a written definition to read from | `app/scheduler/nightly.xml:4-12` |
| Writing the harness assertions for order (JOBB not before JOBA-DONE, JOBA-DONE removed, JOBB-DONE posted) | Strong | Every assertion is stated in the XML | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`, `app/scheduler/nightly.xml:10`, `app/scheduler/nightly.xml:11` |
| Working out what the cycle is for, and what runs behind IEFBR14 | Cannot | The intent is not in the tree. It needs the client's engineers | inference |
| Deciding how a rerun or restart of JOBB should behave | Cannot | It depends on operator practice that no file records | inference |

## What moves this estimate, in order of weight

- Edges crossing the wave boundary: 2 (EXTERNAL-FEED in, JOBB-DONE out). `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:11`
- A behavioral oracle: none in the tree. Job history and logs may supply one, and that is unconfirmed. inference
- God modules in the wave: none. `analysis` field `god_modules`
- Business logic in the database: none visible, and no DB2 reference exists in the tree. `analysis`
- Someone who can read the source language: the JCL is trivial. The Control-M definition is the part that needs a person who knows the scheduler. inference

## What is not estimated

Anything that sits outside this tree: the producer of EXTERNAL-FEED, the consumer of JOBB-DONE, the programs the real cycle may run, and the target platform's scheduler build. Those are open questions in `00-summary.md`, not numbers here.
