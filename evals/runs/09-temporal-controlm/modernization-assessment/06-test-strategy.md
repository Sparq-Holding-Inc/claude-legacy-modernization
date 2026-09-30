# 06 Test strategy

The bar is not "it passes tests". For the inputs the nightly cycle actually sees, the new schedule must produce the same
observable behavior as the old one. Where it does not, someone decided that on purpose, and it is written in the deviation register at the end.

## What must not break, and where it lands

The client said "the nightly batch cycle" must not break. It maps to the Control-M folder NIGHTLY
(`app/scheduler/nightly.xml:3`) and its two jobs (`app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`). That is wave 1
(`modernization-assessment/waves.json:5`). The match is by name only, so it is provisional (inference). The tree does not say the
two jobs are the whole cycle. Whether a second folder, or more jobs, belong to the cycle is an open question in `00-summary.md`.

## The oracle for wave 1

The tree holds no dataset (analysis: `data_hubs` is empty, and `modernization-assessment/01-inventory.md:33-36` lists none), and both jobs run
only IEFBR14 (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). There is no file output to diff. So the oracle has to come from what the scheduler and the job
logs record, not from data. In descending strength:

| Rank | Oracle | Fit for wave 1 | Evidence |
|---|---|---|---|
| 1 | Parallel run: the legacy Control-M folder and the new schedule both run against the same real EXTERNAL-FEED events, and the two run histories are diffed | Best fit. The jobs do no work, so running both is cheap and safe. Ask for it first, before accepting anything weaker. | `app/scheduler/nightly.xml:5` |
| 2 | Replay of captured scheduler history: the condition and job event log for at least 13 months, so it holds month end and year end | Good. Needs the client's Control-M history export. | inference |
| 3 | Golden master from archived job logs: return codes, start and end order of JOBA and JOBB per night | Free test cases nobody thinks to use. Also the telemetry that the dead-code register needs. | inference |
| 4 | Characterization tests written from the XML | Weakest. It encodes what nine lines of XML say, not what the scheduler does. Label any coverage from it provisional. | `app/scheduler/nightly.xml:4-12` |

Wave 1 should use rank 1 or 2. Rank 4 alone is not an acceptable bar for the client's must-not-break item.

## What to ask the client to supply

Because the tree has no data, the oracle has to be requested. This is the list:

1. The Control-M run history and the condition add and delete log for the NIGHTLY folder, 13 months or more.
2. The JES job output for JOBA and JOBB for the same period, with return codes.
3. The name of whatever sets EXTERNAL-FEED (`app/scheduler/nightly.xml:5`).
4. The name of whatever waits for JOBB-DONE (`app/scheduler/nightly.xml:11`), and the archived output of that consumer.
5. The production JCL members, if IEFBR14 is a stand-in.
6. The Control-M calendars and any month-end or year-end folder variations.

## Normalize before you diff

A naive diff of two run histories fails every night for reasons that do not matter. Agree this spec, and have a person sign it. Each row is a place a real bug can hide.

| Item | Treatment | Why it is safe, or the risk | Evidence |
|---|---|---|---|
| Job numbers, run ids, scheduler-assigned sequence numbers | Ignore | They differ by system and carry no behavior | inference |
| Wall-clock start and end times | Compare the order and the gap between the two jobs, not the clock | The order is the behavior. Absolute time is not. | `app/scheduler/nightly.xml:9` |
| ODAT (the order date) | Keep it. Compare per order date | Conditions are dated (inference from Control-M semantics) | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:9` |
| Order of JOBA and JOBB | Never normalize | JOBB waits for JOBA-DONE, so the order is not incidental | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |
| Conditions set and deleted | Never normalize. Compare the full set per night, including the delete of JOBA-DONE | The delete decides what happens on a rerun | `app/scheduler/nightly.xml:10` |
| Return codes | Compare exactly | A different code can change what the scheduler does next | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2` |
| Numeric fields | Not applicable in this tree. If production members handle money, compare in a decimal type with zero tolerance | Packed decimal rounds differently from IEEE floats | inference |

## Cover the input space deliberately

Production replay covers the ordinary night well and the dangerous nights badly. Add these cases on purpose:

| Case | What must hold | Evidence |
|---|---|---|
| EXTERNAL-FEED never arrives | JOBA does not start, JOBB does not start, and the cycle is reported late | `app/scheduler/nightly.xml:5` |
| EXTERNAL-FEED arrives twice for one order date | Same result as the legacy folder gives. We do not know what that is (inference) | `app/scheduler/nightly.xml:5` |
| JOBA ends with a non-zero code | JOBA-DONE is not added, and JOBB does not run | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |
| JOBB is rerun after a good run | It waits, because JOBB deleted JOBA-DONE. A rerun starts only after JOBA runs again or the condition is added by hand (inference from Control-M semantics) | `app/scheduler/nightly.xml:10` |
| JOBB ends badly, so JOBA-DONE may stay behind | Reproduce whatever legacy does. Do not assume it is sane. This is the "bad data already in there" case | `app/scheduler/nightly.xml:10` |
| The cycle runs across midnight or the order date rolls | Conditions carry the order date, so check which date each one gets | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:6` |
| Month end, quarter end, fiscal year end, leap day, DST change | The nightly cycle behaves as legacy did. The tree shows no calendar, so ask whether these nights differ | inference |
| Nothing arrives at all for several nights, then a burst | Same catch-up behavior as legacy | inference |

The plugin also asks for "the paths that only run at fiscal close". We cannot see any here. If the client's close calendar changes this folder, that is the case most likely to
be missed, and it is the first thing to ask about.

## Mainframe traps for the spec

| Trap | Status in this tree | Evidence |
|---|---|---|
| Packed decimal (COMP-3) | Not present. No COBOL in the tree | `modernization-assessment/01-inventory.md:14-17` |
| EBCDIC collating sequence and KSDS key order | Not present. No dataset | analysis: `data_hubs` is empty |
| REDEFINES | Not present | `modernization-assessment/01-inventory.md:14-17` |
| Record padding and low values | Not present | analysis: `data_hubs` is empty |
| Job order | Present. This is the one temporal edge the harness must keep: JOBA before JOBB | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |

## Deviation register

Nothing may differ from legacy without a row here. It is empty now, because no port exists.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|

## Exit bar for wave 1

Wave 1 is done when all of these hold:

- the run-history diff is clean for the full replay window, modulo the normalization spec and the deviation register
- every case in the input-space table passes
- the harness is under version control and runs in CI
- the deviation register is signed by someone with the authority to sign it
- the consumer of JOBB-DONE has confirmed it still gets the signal (`app/scheduler/nightly.xml:11`)

Not when the new schedule loads. Not when it passes tests written alongside it, since those hold the porter's understanding, which is the thing under test.

## Keep the harness after cutover

The comparison harness becomes the regression suite for the new schedule. Budget for maintaining it. For a nightly cycle it is also the only
executable statement of the order and the conditions, since the jobs themselves do nothing.
