# 06 Test strategy

The tree holds no datasets, JCL or scheduler (`modernization-assessment/graph.json:24`). The oracle has to come from job output, logs and reports. No wave exists to attach it to, so this is a strategy for the nightly cycle as a whole.

## Oracle

| Rank | Oracle | Status | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run of the nightly cycle | Ask the client. Two small programs make it cheap if the old system stays up. | low | inference |
| 2 | Replay of captured inputs | Window must include month-end and fiscal year-end | low | inference |
| 3 | Golden master from archived GDG generations, job logs, partner extracts and report archives | Likely available, not seen | low | inference |
| 4 | Characterization tests from source | Fallback only, provisional | medium | app/cbl/PROGA.cbl:5 |

## What to ask the client to supply

1. The JCL or scheduler definition of the nightly cycle, and its datasets.
2. Three months or more of SYSOUT, return codes and archived outputs, including month-end.
3. Which job runs PROGA, and what its console output is used for.

## Characterization cases from the source

| Case | Expected legacy behavior | Confidence | Evidence |
|---|---|---|---|
| Run PROGA | Prints `CALL FAILED IF WE GET HERE`, calls PROGB, ends with STOP RUN | high | app/cbl/PROGA.cbl:5 |
| Run PROGB alone | Returns at once, with no output | high | app/cbl/PROGB.cbl:4 |

The message prints on every run, before the call. Console output and return code are the only observable behavior. The normalization spec needs: timestamps and job ids on the console log. No monetary fields exist in this tree.

## Deviation Register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-1 (proposed, open) | Prints `CALL FAILED IF WE GET HERE` on every run | Unchanged until a person decides | The text looks misleading. Its intent is unknown. | not approved | A log scraper may match the text | app/cbl/PROGA.cbl:5 |

## Exit bar

Replay diff is clean modulo the normalization spec and the register, the harness runs in CI, and someone with authority signs the register. Keep the harness after cutover.
