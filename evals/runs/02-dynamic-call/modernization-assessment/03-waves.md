# 03 Waves

**No waves can be cut.** The extractor found no entry point: no JCL job, CSD transaction, scheduler job or wrapper (`modernization-assessment/graph.json:86`). Per the skill, `waves.json` has an empty wave list and both programs are unassigned. A wave plan would be invented.

| Unit | Status | Reason | Evidence |
|---|---|---|---|
| PROGA | unassigned | No entry point uses it. It makes a computed call. | `app/cbl/PROGA.cbl:9` |
| PROGB | unassigned | No entry point uses it. | `app/cbl/PROGB.cbl:4` |

Target state is refactor. Deviations: none, since nothing was placed.

Nothing can be sequenced until the client supplies the JCL for the nightly batch cycle, a scheduler export, or a CSD.
