# 00 Summary

Scope: `.` (the whole work folder). The tree holds 3 JCL jobs (`jcl/JOBA.jcl:1`, `jcl/JOBB.jcl:1`, `jcl/JOBC.jcl:1`) and one shell wrapper (`scripts/nightly.sh:1`). It has no COBOL, copybooks, datasets, or computed calls.

## Scoping answers

All three came in as command flags in a non-interactive run, so no defaults were applied and nothing was assumed.

| Question | Answer |
|---|---|
| Target state | refactor (`--target refactor`) |
| What must not break | the nightly batch cycle (`--must-not-break`) |
| Runtime telemetry | none (`--telemetry none`). Every dead-code claim is provisional |

## Result

- **Wave count: 1.** The live system is one wrapper and two jobs, coupled only by submit order. There is no boundary to cut along. See `03-waves.md` for what would be cut if the system were ten times larger.
- **Single largest risk.** The order and failure behavior of the nightly cycle lives in a six-line shell wrapper whose `submit` command is not defined in the tree. `scripts/nightly.sh:3` sets `set -e`, and `scripts/nightly.sh:4` and `scripts/nightly.sh:5` fix the JOBA-then-JOBB order. If `submit` only queues jobs, then the order is submission order, and a refactor that moves the ordering into a scheduler can silently change when JOBB runs or what happens when JOBA fails. That is exactly the cycle the client said must not break. Scored `low-high` in `risks.json`: the port is trivial, and the verification is the work.
- **Dead code.** `job:JOBC` is retired per `scripts/nightly.sh:2` and its submit is commented out (`scripts/nightly.sh:6`). Listed as unreachable, confidence medium, provisional. The extractor left it out of every candidate list because it treats an unscheduled job as an entry point.
- **Oracle.** The tree has no datasets, so the equivalence oracle has to come from job logs, return codes and output. See `06-test-strategy.md`.
- **Estimate.** Roughly 5 to 11 person-days for wave 1, low confidence. See `04-estimate.md`.

## Files written

`01-inventory.md`, `02a-edge-tables.md`, `05a-dead-code-candidates.md` (generated). `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md` and this file (written). `graph.json` (extractor), `waves.json`, `dead-code.json`, `risks.json`.

## Open Questions for the client's engineers

1. What does the `submit` command do (`scripts/nightly.sh:4`)? Does it return when the job is queued, or when it ends, and does it return the job's return code? The answer decides whether JOBB waits for JOBA.
2. What starts `scripts/nightly.sh` each night: cron, an enterprise scheduler, or an operator? The trigger is not in the tree, and the extractor reads only Control-M XML and shell wrappers that name JCL files.
3. Do JOBA and JOBB really run only `IEFBR14` in production (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`)? If the real work lives in other programs or JCL outside this tree, where is it? Until then this assessment covers a skeleton.
4. Has JOBC run since it was retired, and does any other scheduler or operator submit it (`scripts/nightly.sh:2`, `scripts/nightly.sh:6`)? May we delete `jcl/JOBC.jcl`?
5. What consumes the output of JOBA and JOBB, or depends on their order? The tree shows no datasets, so any downstream job, partner feed or report is invisible here.
6. What should happen when JOBA fails? The wrapper stops (`scripts/nightly.sh:3`), but who is told, and is the cycle rerun by hand?
7. Can you supply 12 months of job logs or SMF records, including a fiscal year-end, so the parallel-run or replay oracle exists?

## Extractor limits that touch this system

Not parsed: nothing was skipped (`unparsed` is empty). These entries in `meta.limits` do apply:

- IF/THEN/ELSE and `COND=` in JCL are not modeled. The three JCL files have none, but the real jobs might.
- Nested PROC calls, INCLUDE members and jobs submitted through the internal reader are not followed. The extractor cannot show that a job starts another job.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers. A scheduler in another format would be invisible, and would explain what starts the wrapper, or whether JOBC is scheduled elsewhere.
- The temporal edge from JOBA to JOBB is medium confidence, because it rests on line order in a shell script.
