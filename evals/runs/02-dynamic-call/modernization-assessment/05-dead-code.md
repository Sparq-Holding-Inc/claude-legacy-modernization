# 05 Dead code

Telemetry: none. Every claim in this file is provisional. The extractor's candidate lists are in `05a-dead-code-candidates.md`. The structured version is `dead-code.json`.

## Result

Nothing can be called unreachable. The extractor found no entry point: no JCL job, no scheduler job, no CSD transaction, no wrapper (`graph.json` `analysis.warnings`). With no starting point it cannot prove that anything is unreachable, so both programs are unknown. In addition, PROGA makes a computed call whose target cannot be bounded, and that keeps the unknown bucket open on its own.

## Unreachable

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | No entry point exists to measure reachability from. | high | inference |

## Reachable but dormant

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| none | The extractor could not date either file. Git dates were off (`graph.json` `meta.git_dates` is false), so `last_modified` is empty and the dormancy rule cannot fire. | medium | inference |

## Unknown

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| PROGA | No static caller and no entry point in the tree. It ACCEPTs a program name and ends with STOP RUN, the shape of a main program, so it is probably started by a job outside this tree. Do not delete. | low | `app/cbl/PROGA.cbl:8` |
| PROGB | No static caller. PROGA's computed call could reach it, and it is the only other program in the tree. I cannot bound the call, so it stays unknown. | low | `app/cbl/PROGA.cbl:9` |

## What would firm this up

- The JCL and scheduler entry that starts PROGA. It would give the extractor an entry point, and PROGA becomes reachable.
- Twelve months of job logs or SMF records for PROGA, with the values fed to its ACCEPT. Each distinct value is a program that is live. PROGB is live only if its name appears among them.
- The wider source library. A computed call that names programs outside this tree makes any dead-code claim about the whole system provisional.
