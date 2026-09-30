# 04 Estimate

Target state: refactor. One wave, so one estimate. It is a range in person-days, and it is an
inference throughout. There is no port velocity to measure, no history for this team, and only 12
lines of source in the tree (`jcl/JOBA.jcl:1`, `scripts/nightly.sh:6`). A line-count model would say
"under a day" and would be wrong, because the lines are not where the cost is.

## Method

The estimate follows what moves the cost, in the order the skill gives, and not lines of code.

| Factor | State in this tree | Confidence | Evidence |
|---|---|---|---|
| Coupling edges crossing the wave boundary | None cross it. All edges are inside the wave. One temporal edge must be kept. | high | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| Behavioral oracle | None in the tree. No dataset, no archive, no log. It has to come from the client. | high | analysis field `data_hubs` |
| God modules in the wave | None | high | analysis field `god_modules` |
| Business logic in the database | Not visible. No SQL and no DB2 table is named. | medium | analysis field `node_counts` |
| Team can read the source language | Not known. The source is JCL and a shell wrapper. | low | inference |

## Wave 1, Nightly batch cycle: 7 to 16 person-days

| Part of the work | Range | Method | Confidence | Evidence |
|---|---|---|---|---|
| Discovery: what `submit` does, why JOBB follows JOBA, what the jobs really run, whether JOBC is retired | 2 to 5 days | Interviews and reading run history. Most of the range is waiting for the client. | low | inference |
| Harness: order, return codes, failure cases, DST and month-end timing, run against the legacy chain first | 3 to 6 days | One comparison script over job logs, plus a handful of fault-injection runs. | low | inference |
| Port: express the order and the stop-on-failure rule in the target orchestration, and move JOBA and JOBB | 1 to 3 days | The source is six shell lines and four JCL lines. | medium | `scripts/nightly.sh:3`, `jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2` |
| Parallel run and cutover watch across one business cycle that includes a month-end | 1 to 2 days of effort, and about a month of calendar time | Watch, diff, sign the deviation register. | low | inference |

The sum of the ranges is 7 to 16 person-days. Cost is dominated by discovery and verification. The
port is the smallest part.

### The assumptions this range is most sensitive to

1. **Assumes the tree is the whole nightly chain, and that JOBA and JOBB really run only IEFBR14.** If the
   production jobs run application programs or DD statements that were not supplied, this estimate does not
   hold. Each real program becomes its own unit, needs its own oracle, and the range at least doubles.
2. **Assumes `submit` returns without waiting for the job to finish** (inference, see `02-coupling.md`),
   so the harness has to read completion from JES output or scheduler logs and not from the wrapper. If
   `submit` does wait and passes the return code back, the harness shrinks by about 2 days.
3. **Assumes 12 months of run history exists for the chain, including a month-end.** If it does not,
   the oracle falls back to characterization tests written from the source, which here would prove
   almost nothing. Then verification grows by about half and the confidence of every claim drops.

## Where Claude Code helps and where it does not

| Work | Claude Code | Confidence | Evidence |
|---|---|---|---|
| Translate the wrapper's order and stop-on-failure into a target workflow definition | Strong. This is mechanical transliteration with a test. | medium | `scripts/nightly.sh:3`, `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| Write the comparison harness over job logs and return codes | Strong, once the client supplies a sample of logs | medium | inference |
| Say why JOBB follows JOBA | Cannot. The tree gives no reason. A person who runs the cycle has to say. | high | `jcl/JOBB.jcl:2` |
| Say whether JOBC is retired | Cannot. A comment claims it and no data confirms it. | high | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |
| Recover what the jobs do in production | Cannot. It is not in the tree. | high | `jcl/JOBA.jcl:2` |

## What this estimate does not cover

It covers only what is in the tree. It says nothing about whatever the real nightly cycle runs, and no
estimate for the rest of the client's system can be derived from it.
