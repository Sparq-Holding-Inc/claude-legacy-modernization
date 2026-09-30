# 06 Test strategy

Skill applied: `behavioral-equivalence`. The bar: for the inputs this cycle actually sees, the refactored cycle starts the same jobs, in the same order, on the same conditions, the same number of times per order date. Where it differs, someone chose that and wrote it down.

## The oracle problem

The tree holds no datasets, no reports and no expected outputs. Both jobs run IEFBR14 with no DD statement (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`), so their output is empty and a file diff would pass no matter what. It would prove nothing. The oracle has to come from the scheduler and the job logs, and from the client.

The coupling in this system is temporal. The graph holds one temporal edge (`app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`). The skill says the temporal edges are the list of orders the harness must keep. So the thing under test is order and gating, not record content.

### Oracle for wave 1

| Rank | Oracle | Use here | Evidence |
|---|---|---|---|
| 1 | Parallel run. Run the refactored definitions in a shadow folder against the same feed events as production, and diff the ordering trace. | Preferred. Both jobs do nothing (IEFBR14), so a shadow run can touch no data. Ask whether it is possible before settling for less. | `app/jcl/JOBA.jcl:2` |
| 2 | Replay of captured scheduler history: job start and end events, condition adds and deletes, and return codes, per order date, over a window that includes month-end and year-end. | The fallback. It needs the history from the client. | inference |
| 3 | Golden master from archived job logs and operator run books. | Free test cases nobody thinks to use. | inference |
| 4 | Characterization tests from the XML alone. | Weakest. It encodes what the file says, not what operators do. Label all coverage from it provisional. | `app/scheduler/nightly.xml:9` |

### What to ask the client to supply

1. Twelve months of Control-M job history for NIGHTLY/JOBA and NIGHTLY/JOBB: start time, end time, return code, order date, and every manual action (hold, force OK, rerun, manual condition add or delete).
2. The condition log for EXTERNAL-FEED, JOBA-DONE and JOBB-DONE.
3. Whatever posts EXTERNAL-FEED, and who owns it.
4. Every job in any folder that waits on JOBB-DONE.
5. The real members behind these jobs, if IEFBR14 is a placeholder. A comparison of empty output is not a test.

## Cases the harness must cover

| Case | Expected legacy behavior | Evidence |
|---|---|---|
| Normal night: feed arrives, JOBA runs, JOBB runs | JOBA, then JOBB, once each, JOBA-DONE removed and JOBB-DONE present at the end | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:10` |
| Feed absent | JOBA does not start, and neither does JOBB | `app/scheduler/nightly.xml:5` |
| JOBA fails | JOBA-DONE is not added, so JOBB does not start. Whether the cycle is meant to stop here is a question for the operators. | `app/scheduler/nightly.xml:6` |
| JOBB reruns after a good night | JOBB waits for a fresh JOBA-DONE, because the token was deleted | `app/scheduler/nightly.xml:10` |
| Feed lands after ODAT rolls over | Unknown. Conditions are dated ODAT, and the tree does not say what a late feed does. | `app/scheduler/nightly.xml:5` |
| Day N JOBB still running when day N+1 feed arrives | Unknown. Needs history. `inference` | inference |
| Month-end, quarter-end and fiscal year-end order dates | Unknown. The XML has no calendar, so any special handling is outside this file. | inference |
| An operator forces a condition by hand | Unknown. Common in practice. It must be in the replay set. | inference |
| Restart from the middle of the chain | Unknown. Needs history. | inference |

The bad data that is already in there is the same idea here: stale conditions left from an old failed night. Ask for a snapshot of the live condition table and start the shadow run from it.

## Normalization spec

Every entry is a claim that a difference does not matter. Keep it short and have a person sign it.

| Ignore | Why it is safe | Evidence |
|---|---|---|
| Absolute timestamps, job run numbers, order ids | They change every run. Compare relative order, not clock time. | inference |
| Elapsed time of an IEFBR14 step | The step does nothing, so the time is noise. | `app/jcl/JOBA.jcl:2` |

Do not ignore: which job started, in what order, how many times per order date, and the condition state at each start.

Not applicable in this tree: packed decimal, collating sequence, REDEFINES, record padding. There is no COBOL and no dataset here. If the members behind the IEFBR14 stubs turn out to use them, add them.

## Deviation register

Nothing may differ from the legacy behavior without a row here.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact |
|---|---|---|---|---|---|
| D-001 | (empty) | | | | |

## Exit bar for wave 1

The wave is done when all four hold:

- the shadow-run trace matches the legacy trace for every case above, modulo the normalization spec and the register
- every case in the table has run, including a month-end order date and the JOBB rerun case
- the harness is in version control and runs in CI
- the register is signed by the owner of the nightly cycle

It is not done when the definitions load, and it is not done when a run of two no-op jobs goes green.

## After cutover

Keep the harness. It becomes the regression suite for the scheduler definitions, and it is the only executable statement of the order the cycle has to keep.
