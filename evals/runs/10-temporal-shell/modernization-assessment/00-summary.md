# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Scope | `.` (current directory) | no scope argument |
| Target state | refactor | `--target refactor` |
| Must not break | "the nightly batch cycle" | `--must-not-break` |
| Telemetry | none | `--telemetry none` |
| Delivery | not given. The estimate shows conventional and AI-assisted side by side. | no `--delivery` flag |

All three scoping answers came as flags, so no defaults were applied.

## Findings

- **What is in the tree:** 3 JCL jobs, 1 shell wrapper, 0 COBOL programs, 0 copybooks, 0 datasets. Nothing was left unparsed (`analysis`: `node_counts`, `unparsed`).
- **Waves:** 1 (`modernization-assessment/waves.json`, `modernization-assessment/03-waves.md`). Confidence is low.
- **Must-not-break mapping:** "the nightly batch cycle" maps to `sch:scripts/nightly.sh`, JOBA and JOBB (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`).
- **Headline estimate:** conventional 7 to 19 engineer-days, AI-assisted 6 to 17. The spread comes from approvals and cutover, which AI does not shorten (`modernization-assessment/04-estimate.md`).
- **Dead code:** JOBC is retired by the wrapper's own header and has its submit commented out (`scripts/nightly.sh:2`, `scripts/nightly.sh:6`). Dormancy was not measured, and with no telemetry every dead-code claim is provisional.

## Largest risk

The nightly cycle may not be in the tree. Every step runs only IEFBR14, a no-op utility (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`, `jcl/JOBC.jcl:2`), and the tree has no dataset. The one real behavior is the order and stop-on-failure rule in the wrapper (`scripts/nightly.sh:3`), and `submit` is not defined here. A plan, estimate or equivalence claim built on this tree describes the wrapper, not necessarily the business cycle. Confidence: high that the tree is incomplete; the size of the gap is unknown (inference).

## Open Questions for the client's engineers

1. What is `submit` in `scripts/nightly.sh:4`? Does it wait for the job to finish and return the job's return code, or only confirm the job was accepted? This decides whether `set -e` (`scripts/nightly.sh:3`) really stops JOBB when JOBA fails.
2. Is the nightly cycle only JOBA and JOBB? The jobs run IEFBR14 only (`jcl/JOBA.jcl:2`, `jcl/JOBB.jcl:2`). Where are the programs, procs and datasets that do the real work?
3. Is JOBC really retired (`scripts/nightly.sh:2`)? Does any scheduler, operator or other script submit it? The extractor lists it as unscheduled.
4. Which scheduler runs `nightly.sh` and when? The extractor reads only Control-M XML and shell wrappers that name JCL files (`meta.limits`), so any other scheduler is invisible.
5. What does JOBB depend on from JOBA? The only link is line order in the script (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`), rated medium. With no data edge, is the order a real dependency or a habit?
6. Which job logs, return-code history and archived outputs exist for the last 12 months, including month-end and fiscal-year-end? They are the oracle in `modernization-assessment/06-test-strategy.md`, and the telemetry for the dead-code register.
7. The tree is not a git repository, so no last-modified date exists. Can you provide source history? Without it the dormant bucket stays unmeasured (`analysis`: `warnings`).
8. Can the old chain stay up for a parallel run during wave 1?

## Extractor limits that touch this system

- JCL IF/THEN/ELSE and COND= are not modeled, and step order is file order (`meta.limits`). With one step per job here, that matters only if the real jobs have more.
- Only Control-M XML and shell wrappers naming JCL files are read as schedulers (`meta.limits`).
- DCB, LRECL and RECFM are not read (`meta.limits`). No dataset exists in the tree, so this is untested.
- Not parsed: nothing.

## Artifacts

`01-inventory.md`, `02-coupling.md` (with `02a-edge-tables.md`), `03-waves.md`, `waves.json`, `04-estimate.md`, `05-dead-code.md`, `dead-code.json`, `06-test-strategy.md`, `risks.json`, `graph.json`.
