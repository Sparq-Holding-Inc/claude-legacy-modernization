# 04 Estimate

Every figure here is inference. No team velocity, no telemetry and no oracle was supplied, so nothing calibrates the numbers. The method is bottom-up: unit count, the coupling edges that cross the wave boundary, and the cost of building a way to prove equivalence. Lines of code are not the driver.

## Wave 1: the nightly batch job

Size of the wave: 11 lines across three units (`app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:5`, `app/cbl/PGMLIVE.cbl:4`). Edges crossing the wave boundary: none (analysis: `edge_counts`, `data_hubs`).

| Work item | Range (person-days) | Driver | Confidence | Evidence |
|---|---|---|---|---|
| Port PGMLIVE, PGMMAIN and the job step to the refactor target | 0.5 to 1 | Three units, no data, no logic | medium | `app/cbl/PGMMAIN.cbl:4` |
| Build the comparison harness: capture job return code, job log and any outputs, then diff | 2 to 5 | No oracle in the tree, so it must be built from job output | low | inference |
| Confirm the real scope of the nightly cycle with the client's engineers | 1 to 3 | The tree has no scheduler and no datasets | low | inference |
| Parallel run or replay across a month-end | elapsed time, not effort | The capture window must span a business cycle | low | inference |
| **Total effort** | **3.5 to 9** | | low | inference |

The total is low confidence because two of the four lines have nothing behind them but the shape of the tree.

## The assumptions this range is most sensitive to

1. **Assumes `job:MAINJOB` is the whole nightly batch cycle, or the cycle is a handful of jobs shaped like it.** If the real cycle holds dozens of jobs the tree does not contain, this estimate is void and each further wave is sized from its own edges. The evidence for it is thin: one job, no scheduler (analysis: `warnings`).
2. **Assumes the real job has no dataset a port could break.** The step has no DD statement (`app/jcl/MAINJOB.jcl:2`). If the production job has DDs the tree omits, the harness cost rises from 2 to 5 days toward 5 to 10, since each dataset layout needs a normalization decision.
3. **Assumes PGMLIVE and PGMMAIN are the real programs and not stubs.** Both hold no logic (`app/cbl/PGMLIVE.cbl:4`, `app/cbl/PGMMAIN.cbl:4`). If the production versions hold business logic, the port line moves out of the 0.5 to 1 day range and port difficulty must be rescored.

## What moves the estimate

| Factor | State in this tree | Effect | Confidence | Evidence |
|---|---|---|---|---|
| Coupling edges crossing the wave boundary | None | Lowers it | high | analysis: `edge_counts` |
| A behavioral oracle | None in the tree, and telemetry is none | Raises it. The harness is the main cost | high | inference |
| God modules in the wave | None | Neutral | high | analysis: `god_modules` |
| Business logic in the database | No SQL in any source file | Neutral here, unknown for the real system | low | inference |
| Anyone who can read the source language | Not known | Unknown. Ask | low | inference |

## Where Claude Code can do the port, and where it cannot

- **Can do.** The mechanical part: PGMMAIN is a single CALL and a GOBACK, PGMLIVE is a GOBACK, and the job is one EXEC step (`app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMLIVE.cbl:4`, `app/jcl/MAINJOB.jcl:2`). This is transliteration, and it is safe once the harness exists.
- **Cannot do.** It cannot say what PGMLIVE is meant to do, since the source holds no rule to infer. It also cannot say what the nightly cycle is, or what it must produce. Those come from the client's engineers, job logs and archived output, not from this source.

## Dead code and the estimate

PGMDEAD and `cpy:UNUSED` are not in the estimate. Nothing gets ported for them. The cost of retiring them is instrumentation plus a delete, under one day once the telemetry route is agreed. That is inference (`05-dead-code.md`).
