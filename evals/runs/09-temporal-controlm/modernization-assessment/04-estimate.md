# 04 Estimate

**Basis: no `--delivery` flag was given, so both cases are shown, conventional (no AI coding assistance) and AI-assisted (engineers using an AI coding agent, with human review).** This plugin carries no calibrated productivity data. Every rate below is a planning assumption, not a benchmark. Replace it with the team's measured velocity after wave 1.

The scope is two JCL jobs of two lines each (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`) and one 14-line Control-M file (`app/scheduler/nightly.xml:3`). There is no application code to port. The estimate is therefore almost entirely scheduler work, oracle work and client availability. It is an estimate for what is visible. If the cycle does real work elsewhere, it is invalid (assumption 1).

## Wave 1: nightly cycle

| Term | Conventional | AI-assisted | Does AI shrink it? | Evidence |
|---|---|---|---|---|
| Port (JCL and Control-M definitions to the target scheduler) | 2 to 4 days | 1 to 2 days | Partly. Transliteration of 14 lines of XML is quick. Review of condition semantics (ODAT, delete sign) is the real cost. Assumes review takes about as long as authoring for this size, because there are only three conditions. | `app/scheduler/nightly.xml:5` |
| Boundary work (trigger for `EXTERNAL-FEED`, rerun and restart behavior) | 3 to 5 days | 2 to 4 days | Little. Finding who sets the feed and agreeing restart semantics is a people task. | `app/scheduler/nightly.xml:5` |
| Equivalence harness (scheduler trace diff, see `06-test-strategy.md`) | 3 to 5 days | 2 to 3 days | Partly. Writing the trace comparer is fast. Choosing what to normalize is not. | inference |
| Oracle gathering (Control-M job logs, SMF, history for 3 or more cycles) | 3 to 10 days elapsed | same | No. Depends on the client's access and approvals. | inference |
| Parallel-run rehearsals and cutover | 5 to 10 days elapsed | same | No. Rehearsal windows, change approval and client availability. | inference |
| **Wave 1 total (engineer-days, elapsed days dominated by the last two rows)** | **16 to 34** | **12 to 26** | | inference (sum of the rows above) |

Convert at one engineer per task: roughly 3 to 7 engineer-weeks conventional, 2.5 to 5.5 AI-assisted.

## What the range is most sensitive to

1. **Assumes the two jobs are the whole cycle.** If the real jobs are elsewhere and these are stubs or wrappers, this estimate covers only the sequencing layer, and the real programs are not estimated at all. Wave count and cost then change by an order of magnitude. This is the dominant uncertainty.
2. **Assumes the target scheduler can express consume-on-complete conditions.** If it models dependencies as a DAG and cannot delete a condition, the rerun behavior at `app/scheduler/nightly.xml:10` needs custom logic, and boundary work roughly doubles.
3. **Assumes a parallel run is allowed.** If the old Control-M cannot run beside the new scheduler for at least three cycles, the oracle falls to archived logs, and the rehearsal term grows by a week or more.

## Where Claude Code helps and where it does not

- **Strong:** transliterating the XML conditions into the target scheduler's format. Writing the trace comparer. Generating restart and rerun test cases from the three conditions.
- **Weak:** inferring why JOBB deletes `JOBA-DONE`. Knowing who sets `EXTERNAL-FEED`. Both need the people who own the scheduler.
- **Not applicable:** there is no business logic in the tree for an agent to infer.

Understanding the code is already paid for by this assessment. No discovery weeks are charged. What remains is the client's answers in `00-summary.md`.
