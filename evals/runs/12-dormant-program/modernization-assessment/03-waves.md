# 03 Waves

Target state: refactor (given as a flag). The wave plan is the extractor's seed, kept as it is. There
are no deviations. The machine-readable plan is `modernization-assessment/waves.json`.

## The plan

| Wave | Family | Units | Blast radius | Confidence | Unblocks | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | `job:MAINJOB`, `PGMMAIN`, `OLDPGM`, `NEWPGM` | medium | low | Nothing further in this tree. It is the whole nightly batch cycle. | `app/jcl/MAINJOB.jcl:1`, `app/cbl/PGMMAIN.cbl:4` |

## Why one wave

There is one entry point, `job:MAINJOB`, and every program is reachable only through it, so there is
one family (`analysis.wave_seed`). No strongly connected component, god module or must-not-break item
forces a unit into another wave. No wave holds more than 25 units, so there is no reason to cut at
the articulation point `PGMMAIN`. The skill says not to invent waves, so none was invented.

## The four tests for a valid wave

| Test | Holds? | Evidence |
|---|---|---|
| Deployable independently, behind a flag or a facade | Yes. The job step can point at the legacy or the new `PGMMAIN`. | `app/jcl/MAINJOB.jcl:2` |
| Rollback independently | Yes. Point the step back at the legacy `PGMMAIN`. The tree shows no write to a system of record. | inference |
| Testable boundary | Weak. The boundary is the job's return code and log, plus any output the client holds. The tree has no dataset to compare. | analysis field `data_hubs` |
| Delivers something a stakeholder can name | Yes, if `job:MAINJOB` is the nightly batch cycle. That match is an assumption, not a fact in the tree. | inference |

## What this wave is, said plainly

- A wave that holds the whole system is a big-bang cutover for four units. That is acceptable here
  only because the units are tiny (14 lines of COBOL in total, `analysis` field `node_counts` and
  `01-inventory.md`). If the client's real cycle has more code than this tree, this plan is wrong and
  must be redone on the full tree.
- The wave unblocks nothing else. By the skill's rule that makes it a chore unless it proves the
  toolchain and the equivalence harness for later work. It does that, and no more.
- `OLDPGM` looks dormant by date (2011-03-04) but `PGMMAIN` calls it unconditionally. Whatever
  target the client picks, `OLDPGM` moves with this wave and is not cut.

## Risk quadrants (from `modernization-assessment/risks.json`)

| Unit | Quadrant | Wave | Confidence | Evidence |
|---|---|---|---|---|
| `PGMMAIN` | low-high | 1 | medium | `app/cbl/PGMMAIN.cbl:4` |
| `job:MAINJOB` | low-high | 1 | low | `app/jcl/MAINJOB.jcl:2` |
| `OLDPGM` | low-low | 1 | low | `app/cbl/OLDPGM.cbl:4` |
| `NEWPGM` | low-low | 1 | low | `app/cbl/NEWPGM.cbl:4` |

Port difficulty is 1 for every unit, because there is no logic in the tree to port. The verification
is the work, not the port. Two units are low-high: easy to port, and costly if wrong because the job is
the only entry point and the client named the nightly cycle as must-not-break.
