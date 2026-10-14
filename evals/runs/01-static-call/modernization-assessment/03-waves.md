# 03 Waves

Target state: refactor. **There are no waves.** The extractor found no entry point (no CSD transaction, JCL job, scheduler job or wrapper), so the seed is empty (`modernization-assessment/03a-wave-seed.md`). Nothing can be sequenced until the client supplies JCL, a CSD or a scheduler export. Inventing a wave would be a guess.

| Unit | Status | Reason | Confidence | Evidence |
|---|---|---|---|---|
| PROGA | Not placed | No entry point runs it | low | app/cbl/PROGA.cbl:2 |
| PROGB | Not placed | Called by PROGA, so it moves with PROGA | medium | app/cbl/PROGA.cbl:6 |

Deviations from the seed: none (`modernization-assessment/waves.json:7`).

## What a plan will probably look like (inference)

When the nightly job is supplied, PROGA and PROGB are one call pair with no shared data. They move together in one wave. The batch family that holds the job sets the wave number. They are too small to need a facade or a cut.
