# 03 Waves

Target state: refactor. Machine-readable plan: `modernization-assessment/waves.json:1`. Risk scores: `modernization-assessment/risks.json:1`.

The extractor cut the seed from facts (`03a-wave-seed.md`). I kept it whole. The tree has one entry point, so it has one family and one wave. I made no deviations, and a plan with no deviations is a fine answer.

## Wave 1. The whole tree: MAINJOB and its three programs

| Field | Value | Evidence |
|---|---|---|
| Family | batch-readonly | `app/jcl/MAINJOB.jcl:1` |
| Units | `job:MAINJOB`, PGMMAIN, OLDPGM, NEWPGM | `app/jcl/MAINJOB.jcl:2`, `app/cbl/PGMMAIN.cbl:4`, `app/cbl/PGMMAIN.cbl:5` |
| Blast radius | medium | inference |
| Confidence | medium | inference |
| Computed calls that cap confidence | none | `analysis` (field `unresolved_dynamic`) |
| Unblocks | Nothing else in this tree. It is the only wave. | inference |

Risk quadrants of the units, from `risks.json`: PGMMAIN and `job:MAINJOB` are low-high. OLDPGM and NEWPGM are low-low. Port difficulty is 1 for all four. Each source file is a stub of 4 to 6 lines with no logic (`app/cbl/OLDPGM.cbl:4`, `app/cbl/NEWPGM.cbl:4`, `app/cbl/PGMMAIN.cbl:6`).

### Why the family is a sound wave, and where it is thin

- The batch-readonly label means the extractor found no dataset edge for these units. It does not prove that the job writes nothing. The job has no DD statements, so a written file would not show (`app/jcl/MAINJOB.jcl:2`).
- Deployable independently: yes, in the trivial sense. The wave is the whole surface, so nothing outside it depends on it in this tree. A facade at PGMMAIN would let the new implementation run behind a flag. That is inference.
- Rollback independently: yes. Keep the legacy job and switch back. Inference.
- Testable boundary: only the job's return code, step execution and any SYSOUT. No dataset is named in the tree, so no file boundary can be asserted from what we hold. See `06-test-strategy.md`.
- Delivers something a stakeholder can name: only if `job:MAINJOB` is the nightly batch cycle, the must-not-break item. The tree does not say so. If it is not, this wave is a chore and proves only the toolchain. This is why `unblocks` says so in `waves.json`.

### Why blast radius is medium and not low

The facts alone say low: no data edge, no writer, no reader. But the only batch job in the tree is the likeliest home of the nightly batch cycle. If that is right, a wrong port here is a failure of the cycle the client said must not break. I cannot confirm the mapping, so I did not pick low or high. This is inference.

## Order inside the wave

Port order, if the wave is ever run: OLDPGM and NEWPGM first, because they have no callees; then PGMMAIN, keeping the call order of line 4 then line 5; then the job step. Cut over as one unit. Program-by-program detail waits for a `--wave 1` run, which writes `07-wave-1-plan.md`.

| Order | Unit | Reason | Evidence |
|---|---|---|---|
| 1 | OLDPGM | No callees. Called unconditionally, so it is ported, not dropped. | `app/cbl/PGMMAIN.cbl:4` |
| 2 | NEWPGM | No callees. | `app/cbl/PGMMAIN.cbl:5` |
| 3 | PGMMAIN | Calls both. It is the articulation point and the natural facade. | `analysis` (field `articulation_points`) |
| 4 | `job:MAINJOB` | Runs PGMMAIN in step S1. | `app/jcl/MAINJOB.jcl:2` |

## Not placed

Nothing. Every unit is placed (`modernization-assessment/waves.json:26`).

## Deviations from the seed

None. No must-not-break item, strongly connected component or facade dependency forces a move. No wave holds more than 25 units. Nothing the extractor could not see changes what a unit is. None of the four units sits in high-high.
