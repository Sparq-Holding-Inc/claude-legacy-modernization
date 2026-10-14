# 03 Waves

Target state: refactor. Machine-readable plan: `modernization-assessment/waves.json`. The extractor's seed is `03a-wave-seed.md`. I kept it as it was. There are no deviations (`modernization-assessment/waves.json:26`).

## Plan

| Wave | Family | Units | Unblocks | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|---|
| 1 | batch-readonly | PGMMAIN, job:MAINJOB | Nothing else in this tree. It proves the toolchain and the harness. | medium | low | `app/jcl/MAINJOB.jcl:1`, `app/cbl/PGMMAIN.cbl:9` |

## Why one wave

There is one entry point (`analysis` field `entry_points`: `job:MAINJOB`) and one reachable program. No strongly connected component, articulation point or shared dataset exists to cut on. Splitting one job and one program into two waves would not give either wave a business stakeholder who could name it. A plan with one wave and no deviations is the correct answer for this tree.

## Why confidence is low

The seed lists a computed call for PGMMAIN (`03a-wave-seed.md`, `app/cbl/PGMMAIN.cbl:9`). The wave cannot be `high` while the call target is unknown. The call could reach HIDDEN01 (`app/cbl/HIDDEN01.cbl:2`) or any program the client has not given us. If the called programs write shared data, the family would change (that would be inference, not shown by any file here).

## Not placed

| Unit | Reason | Confidence | Evidence |
|---|---|---|---|
| HIDDEN01 | No static edge reaches it. PGMMAIN's computed call could. It moves with the wave of PGMMAIN once the call target list is known. | low | `app/cbl/PGMMAIN.cbl:9`, `app/cbl/HIDDEN01.cbl:1` |

## Must-not-break: the nightly batch cycle

The only job in the tree is MAINJOB (`app/jcl/MAINJOB.jcl:1`). Its name and class (`CLASS=A`) do not say it is nightly, and no scheduler is present. Treating MAINJOB as the nightly cycle is `inference`. If the cycle holds other jobs, they are not in this tree, and wave 1 is only a part of it. See Open Questions in `00-summary.md`.

## Rollback

Wave 1 is one job. Rollback is to run the old MAINJOB again, from the old load library. This needs the old and new job to be switchable by a change to the job's scheduler entry or a library concatenation. Neither is in the tree (inference).
