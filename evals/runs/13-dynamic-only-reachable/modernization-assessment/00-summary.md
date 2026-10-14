# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target` |
| Must not break | "the nightly batch cycle" | flag `--must-not-break` |
| Telemetry | none | flag `--telemetry` |
| Delivery | not given. The estimate shows conventional and AI-assisted side by side. | flag `--delivery` missing |

All three scoping answers came as flags. No defaults applied.

## What the tree holds

2 COBOL programs and 1 JCL job (`modernization-assessment/graph.json`, `meta.files_seen`). One entry point, `job:MAINJOB` (`app/jcl/MAINJOB.jcl:1`), runs PGMMAIN (`app/jcl/MAINJOB.jcl:2`). The sequence is 1 wave, no deviations from the extractor's seed (`03-waves.md`).

| Figure | Value | Confidence | Evidence |
|---|---|---|---|
| Waves | 1 | low | `modernization-assessment/waves.json:3` |
| Estimate, conventional | 4.5 to 10 engineer-weeks | low | inference (see 04-estimate.md) |
| Estimate, AI-assisted | 3.5 to 8 engineer-weeks | low | inference (see 04-estimate.md) |
| Dead code | 0 unreachable, 0 dormant (not measured), 1 unknown | low | `app/cbl/HIDDEN01.cbl:1` |

## Largest risk

PGMMAIN calls a program whose name it reads at run time (`app/cbl/PGMMAIN.cbl:8`, `app/cbl/PGMMAIN.cbl:9`). Everything the nightly job really does lives in programs this tree does not show, and the one candidate in the tree, HIDDEN01, does nothing (`app/cbl/HIDDEN01.cbl:3`). The reachable set is a lower bound, so the wave, the estimate and the dead-code register all rest on an unknown. Risk scoring puts PGMMAIN in the high-high quadrant (`modernization-assessment/risks.json`).

## Telemetry gap

With telemetry `none`, every dead-code claim is provisional. The tree is not a git repository, so dormancy was not computed (`analysis` field `warnings`).

## Open Questions for the client's engineers

1. Where does `ACCEPT WS-PGM-NAME` read from (SYSIN, PARM, a caller), and what values arrive? MAINJOB has no SYSIN DD (`app/jcl/MAINJOB.jcl:2`). Please supply the list of names seen over a full business cycle, including month-end and year-end.
2. What are the programs PGMMAIN calls? They are not in the tree. Please supply their source, copybooks and any files they use.
3. Is `job:MAINJOB` the nightly batch cycle, or one job in it? Which other jobs make up the cycle, and in what order? No scheduler export was parsed (`analysis` field `warnings`). Please supply the Control-M export or equivalent. Without it, no cross-job order is known.
4. Is HIDDEN01 ever called? What is it for? (`app/cbl/HIDDEN01.cbl:1`)
5. Does an unmatched name abend, and is that intended? (`app/cbl/PGMMAIN.cbl:9`)
6. Can the old and new MAINJOB run in parallel, and what archived output (job logs, SYSOUT, GDG generations, return codes) exists for the oracle? (`06-test-strategy.md`)
7. Is any source outside the tree missing? The extractor reads fixed-format COBOL only and does not read stored procedures, DB2 objects, free-format COBOL or sort control cards (`meta.limits` in `modernization-assessment/graph.json`). The extractor listed no files as not parsed (`unparsed` is empty).
8. Do the programs read or write datasets? The tree has no DD cards, copybooks or datasets, so data and contract coupling are unmeasured (`analysis` field `data_hubs`).
9. Which delivery model will the team use (conventional, AI-assisted, agent-led)? It sets the headline estimate.

## Files

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`, plus `graph.json`, `waves.json`, `risks.json`, `dead-code.json` and the generated `*a-*` tables.
