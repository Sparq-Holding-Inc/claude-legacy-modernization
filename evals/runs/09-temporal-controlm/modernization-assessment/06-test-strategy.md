# 06 Test strategy

Skill used: `behavioral-equivalence`. The bar is this: for the nights the cycle really runs, the new platform starts the same jobs in the same order on the same conditions, and every difference was decided and written down.

## The tree holds no datasets

Neither job maps a dataset (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`), and `analysis` field `data_hubs` is empty. So the oracle cannot be a dataset diff. It has to come from **job output, logs, scheduler history and reports**. The client should supply:

1. Scheduler history for 12 months or more: for each night, JOBA and JOBB start time, end time, return code, order date, and when each condition was added and deleted.
2. SYSOUT and job logs for a sample of nights, including month end and year end.
3. What adds EXTERNAL-FEED, and a record of when it arrived each night. `app/scheduler/nightly.xml:5`
4. Whatever consumes JOBB-DONE and the reports or files the cycle produces, if any. `app/scheduler/nightly.xml:11`
5. Confirmation of what runs behind IEFBR14 in production. `app/jcl/JOBA.jcl:2`

## Oracle for wave 1

| Rank | Oracle | Available? | Use | Evidence |
|---|---|---|---|---|
| 1 | Parallel run: the old and new schedulers both receive the same EXTERNAL-FEED and the results are compared | Ask. Teams often assume it is impossible. The jobs run a do-nothing utility, so a second run has no side effect visible in this tree | Preferred for wave 1 | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`, inference |
| 2 | Replay of captured scheduler history | Depends on the client supplying item 1 in the list above | Fallback | inference |
| 3 | Golden master from archived job logs | Depends on the client supplying item 2 in the list above | Fallback for boundary dates | inference |
| 4 | Characterization tests from the source | Weakest. The source is two null steps and a condition chain | Only as provisional cover for the assertions below | `app/scheduler/nightly.xml:4-12` |

## Assertions that come from the scheduler definition

These are the temporal edges the harness must keep. Each is stated in the XML.

| ID | Assertion | Evidence |
|---|---|---|
| T1 | JOBA does not start until EXTERNAL-FEED exists for the order date | `app/scheduler/nightly.xml:5` |
| T2 | JOBA ending OK adds JOBA-DONE for the order date | `app/scheduler/nightly.xml:6` |
| T3 | JOBB does not start until JOBA-DONE exists for the order date | `app/scheduler/nightly.xml:9` |
| T4 | JOBB ending OK removes JOBA-DONE | `app/scheduler/nightly.xml:10` |
| T5 | JOBB ending OK adds JOBB-DONE | `app/scheduler/nightly.xml:11` |
| T6 | Each condition is scoped to the order date (ODATE `ODAT`) | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:9` |

The words "ending OK" in T2, T4 and T5, and the reading of the order date scope in T6, are `inference` from how Control-M behaves. The file states the conditions and the signs and not the trigger. Confirm both with the client.

## Cases to add beyond the normal night

| Case | What to check | Evidence |
|---|---|---|
| JOBA fails, then is rerun | JOBA-DONE is added only after the good run, and JOBB does not run in between | inference |
| JOBB fails, then is rerun | JOBA-DONE is still there to release the rerun. If JOBB only deletes it on success, the rerun works. If the target deletes it early, the rerun stalls | `app/scheduler/nightly.xml:10`, inference |
| JOBB rerun after a good run | JOBA-DONE has already been deleted, so JOBB should wait. Decide whether that is wanted | `app/scheduler/nightly.xml:10`, inference |
| EXTERNAL-FEED late or missing | JOBA and JOBB both wait, and the alert behavior matches the old system | `app/scheduler/nightly.xml:5`, inference |
| Order date roll over: a run that crosses midnight | The conditions stay tied to the order date, not the calendar date | `app/scheduler/nightly.xml:5`, inference |
| Month end, quarter end, fiscal year end, leap day, DST change | The cycle still starts and ends in order. The schedule attributes are not in the tree, so the calendar has to come from the client | `app/scheduler/nightly.xml:4`, inference |
| Zero record and maximum size input | Not testable from this tree, since no dataset is named. Ask what the cycle processes | `app/jcl/JOBA.jcl:2` |

## Normalization spec (short, for a human to sign)

- Job numbers, run ids, scheduler order ids and log timestamps: ignore the value, keep the order.
- Start and end times: compare order, not clock time. Allow a stated delay for scheduler polling.
- Return codes: compare exactly. No tolerance.
- Whitespace and padding in logs: ignore trailing whitespace only.

Each line is an assertion that a difference does not matter. Keep the list at this length.

## Mainframe traps for this tree

- **Packed decimal, collating sequence, REDEFINES, record padding:** none appears, since there is no COBOL, copybook or dataset (`meta.files_seen`). They become relevant if the real work is elsewhere. Add them to this spec as soon as source arrives.
- **Job order:** the one trap that does apply. The temporal edge in `graph.json` is the list of orders the harness keeps. `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`

## Deviation Register

Empty until the port exists. Nothing may differ without a row.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D0 | none recorded | none recorded | not applicable | not applicable | not applicable | inference |

## Exit bar for wave 1

- The replay or parallel run diff is clean for a full business cycle, including a month end, modulo the normalization spec and the register.
- Assertions T1 to T6 and every case above pass.
- The harness is in version control and runs in CI.
- The register is signed by someone with authority.

## Keep the harness

After cutover it becomes the regression suite for the scheduling layer. It is the only executable statement of the cycle's order that will exist, because the order is not in the JCL. `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`
