# 06 Test strategy

Must-not-break item, as given: **the nightly batch cycle**. It maps to `sch:NIGHTLY/JOBA` and `sch:NIGHTLY/JOBB` and the jobs they run (`app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8`). Whether it maps to anything beyond these is Open Question 1. Telemetry: none.

The tree holds no datasets, no reports and no program output. Both steps run IEFBR14 with no DD statements (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). So the oracle has to come from **scheduler behavior, job output, logs and reports**, not from files in the tree.

## Oracle for wave 1

1. **Parallel run (preferred).** Run the new scheduler beside Control-M for at least three consecutive cycles, one of them a month-end. Compare the scheduler trace (below). Ask the client first whether Control-M can order a shadow folder. Teams assume not, and are often wrong.
2. **Captured replay.** If parallel run is refused, replay the recorded condition events and job start times from Control-M's job history.
3. **Golden master from archived logs.** Ask for job logs (JESMSGLG, JESYSMSG), SYSOUT for JOBA and JOBB, SMF 30 records, and the Control-M job statistics for the past 12 months. They also supply the telemetry the dead-code register lacks.
4. **Characterization tests from the XML.** Used only to fill gaps, and provisional. They encode what `nightly.xml` says, not what the scheduler did.

What to ask the client to supply: all of the above, plus every program and dataset the real cycle touches if JOBA and JOBB are wrappers or stubs.

## What gets compared

The boundary is the scheduler, so the compared artifact is a trace of events per ODATE:

| Trace field | Source |
|---|---|
| Job start order and end order (JOBA, JOBB) | `app/scheduler/nightly.xml:4`, `app/scheduler/nightly.xml:8` |
| Condition events: set `EXTERNAL-FEED` (input), set `JOBA-DONE`, delete `JOBA-DONE`, set `JOBB-DONE` | `app/scheduler/nightly.xml:5`, `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:10`, `app/scheduler/nightly.xml:11` |
| Return code per step | `app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2` |
| Conditions present at end of day | `app/scheduler/nightly.xml:10` |

## Normalization spec (for a human to sign)

| Normalized | Reason it should not matter | Risk |
|---|---|---|
| Wall-clock timestamps and elapsed time, keeping the order | Only order and conditions are the contract | A new scheduler that starts JOBB earlier than JOBA ends is still caught, because order is kept |
| Job run IDs and order numbers | Allocated by the scheduler | Low |
| Job log header text and system names | Environment specific | Low |

Keep the list this short. The ODAT date is **not** normalized: `ODATE="ODAT"` is part of the contract (`app/scheduler/nightly.xml:5`).

## Targeted cases

| Case | Why | Evidence |
|---|---|---|
| `EXTERNAL-FEED` never arrives | JOBA must not run, and must not fail the cycle noisily or silently differently from legacy. Capture what legacy does, including alerts. | `app/scheduler/nightly.xml:5` |
| `EXTERNAL-FEED` arrives late, after midnight | ODAT versus wall-clock date | `app/scheduler/nightly.xml:5` |
| JOBA fails with a non-zero return code | Does `JOBA-DONE` get set? Control-M sets OUTCOND only on OK by default, which is `inference`. Check the real behavior. | `app/scheduler/nightly.xml:6` |
| JOBB reruns after success | `JOBA-DONE` was deleted, so JOBB should wait. This is the consume-once behavior. | `app/scheduler/nightly.xml:10` |
| JOBA reruns after JOBB has run | Sets `JOBA-DONE` again, which re-arms JOBB | `app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9` |
| Month-end, quarter-end, fiscal year-end, leap day, DST change | Boundary dates under ODAT. Any cycle behavior that only runs at close is invisible in this tree. | inference |
| Empty and enormous | Not testable here: the jobs process no data. | inference |

## Deviation Register

Empty. No intentional differences are proposed. Nothing may differ without a row.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none | | | | | | inference (no differences proposed) |

## Exit bar for wave 1

- The scheduler trace diff is clean across the parallel-run or replay window, modulo the normalization spec and the register.
- Every targeted case above passes, with legacy results recorded first.
- The harness is under version control and runs in CI.
- The register is signed by a person with the authority to sign it.

Keep the harness after cutover. It is the only executable specification of the cycle.

## Mainframe traps that apply here

- **Job order:** the temporal edge `sch:NIGHTLY/JOBA` to `sch:NIGHTLY/JOBB` is the only order in the tree (`app/scheduler/nightly.xml:6`, `app/scheduler/nightly.xml:9`). The harness must keep it.
- Packed decimal, collating sequence, REDEFINES and record padding do not apply: there are no records in this tree. They will apply once the real programs are in scope.
