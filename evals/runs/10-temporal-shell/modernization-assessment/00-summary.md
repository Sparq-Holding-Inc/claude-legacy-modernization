# 00 Summary

Assessment of the tree in `.` (a folder of 3 JCL jobs and 1 shell wrapper). Generated 2026-09-30.

## Scoping answers

- **Target state:** refactor. Given as `--target refactor`.
- **Must not break:** "the nightly batch cycle". Given as `--must-not-break`. It maps to the wrapper
  `sch:scripts/nightly.sh` and the two jobs it submits, JOBA and JOBB. The match rests on the wrapper's own
  comment, "Nightly chain" (`scripts/nightly.sh:2`). Nothing else in the tree is named as a cycle, and no
  outputs of the cycle are named anywhere. See Open Questions 1 and 5.
- **Telemetry:** none. Given as `--telemetry none`. Every dead-code claim is provisional.
- **Defaults:** no defaults applied. All three answers came as flags. This was a non-interactive run and
  nobody was asked.

## What is in the tree

The tree holds no application code. It has no COBOL, no copybook, no proc, no CSD, no dataset and no
scheduler definition beyond a six line shell wrapper (`meta.files_seen` in graph.json, analysis). Each JCL job
runs only IEFBR14, a system utility that does nothing, and has no DD statement (`jcl/JOBA.jcl:2`,
`jcl/JOBB.jcl:2`, `jcl/JOBC.jcl:2`). Under a refactor target there is no code here to restructure. What
can be assessed is the cycle's order, its failure rule and its verification.

## Result

| Finding | Confidence | Evidence |
|---|---|---|
| The plan is 1 wave. No structure in the tree offers a place to cut, and the four units total far below any size limit. | medium | `modernization-assessment/waves.json:1` |
| One temporal edge exists, JOBA before JOBB. It comes from the order of two submit lines and is rated medium by the extractor. | medium | `scripts/nightly.sh:4`, `scripts/nightly.sh:5` |
| The wrapper stops on the first failed command, so a failed JOBA submit keeps JOBB from running. | medium | `scripts/nightly.sh:3` |
| JOBC is not submitted, the submit is commented out, and a comment calls it retired. It stays in no dead-code bucket and is held from the port pending confirmation. | low | `scripts/nightly.sh:2`, `scripts/nightly.sh:6` |
| There is no data, contract or call coupling, no cycle, no god module and no computed call. The absence reflects the tree, not the system. | high | analysis fields `sccs`, `data_hubs`, `unresolved_dynamic` |
| Dormancy was not computed, because the tree has no git history. An empty dormant list means not measured. | high | analysis field `warnings` |
| Wave 1 estimate: 7 to 16 person-days, mostly discovery and verification. | low | inference |

## Wave count

**1 wave.** Wave 1, "Nightly batch cycle", holds `job:JOBA`, `job:JOBB`, `job:JOBC` and
`sch:scripts/nightly.sh`. It is the extractor's seed with no deviation (`03-waves.md`). Its blast radius is
high, because it holds the whole must-not-break item. Its confidence is low.

## Largest risk

The must-not-break nightly cycle depends on one ordering, JOBA before JOBB, and the only thing that
sets that order is the sequence of two `submit` lines in a shell wrapper (`scripts/nightly.sh:4`,
`scripts/nightly.sh:5`). Whether `submit` waits for JOBA to finish is not in the tree. If it does not wait
(as the z/OS UNIX `submit` command does not, inference), the order is not enforced today, and `set -e`
catches only a failed submit (`scripts/nightly.sh:3`). A port that replaces the wrapper with parallel jobs, or
with a scheduler that treats the order as a rule when it is a habit, or the reverse, changes the
cycle silently. The tree gives no data reason for the order (no shared dataset, `jcl/JOBA.jcl:2`,
`jcl/JOBB.jcl:2`). The harness must settle this before the wrapper is retired. Confidence: medium that the
risk is real, low on which way the answer falls.

## Open Questions

For the client's engineers.

1. **Is `scripts/nightly.sh` the whole nightly batch cycle?** What starts it, when, in which time zone, and
   on which host? Is there a second wrapper or a scheduler the tree does not hold? (`scripts/nightly.sh:2`)
2. **What does `submit` do?** It is not defined in the tree. Does it return at once or wait for the job? Does
   it pass the job's return code back to the shell, so that `set -e` sees an abend? (`scripts/nightly.sh:3`,
   `scripts/nightly.sh:4`)
3. **Why must JOBB run after JOBA?** No dataset links them. Is there a side effect the tree does not show, or
   is it habit? What should happen to JOBB when JOBA abends? (`scripts/nightly.sh:5`)
4. **Is JOBC retired, and does anything else submit it?** The comment says so and the submit is commented
   out. Can the client show run history for a full year? Should the file be kept? (`scripts/nightly.sh:2`,
   `scripts/nightly.sh:6`, `jcl/JOBC.jcl:1`)
5. **Is this JCL the real JCL, and where is the application code?** JOBA, JOBB and JOBC each run only IEFBR14
   with no DD statement. Which programs and datasets does the production nightly cycle run and touch? Which
   outputs (reports, extracts, files for partners) is "must not break" really about? (`jcl/JOBA.jcl:2`,
   `jcl/JOBB.jcl:2`)
6. **Can the client supply 12 months of job logs, return codes and SMF records for the chain?** They would turn
   the dead-code register from provisional to evidence, and they are the oracle for the harness. This includes
   at least one month-end and one year-end night.
7. **Can the client supply file dates or source history?** The tree is not a git repository, so the dormancy rule
   did not run (analysis field `warnings`).
8. **Does the team have someone who can read JCL and the site's shell tooling?** It affects the estimate
   (`04-estimate.md`).

## Files the extractor did not parse

None. `unparsed` is empty (`meta.limits` and `unparsed` in graph.json, analysis).

## Extractor limits that touch this system

- **Only Control-M XML and shell wrappers that name JCL files are read as schedulers.** The wrapper's `set -e`
  and its comments are not read as behavior. I read the six lines by hand (`scripts/nightly.sh:1` through
  `scripts/nightly.sh:6`).
- **IF/THEN/ELSE and COND= are not modeled, and step order is file order.** For the wrapper this means the
  temporal edge is the order of the lines, not proof of the order of execution. That is why the edge is
  medium (`scripts/nightly.sh:4`, `scripts/nightly.sh:5`).
- The other limits (fixed format COBOL, COPY REPLACING, computed CALL targets, DD and record lengths, CICS
  chains) do not touch this tree. It holds no COBOL and no DD statement.

## Reading order

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`.
Generated fact tables: `01-inventory.md`, `02a-edge-tables.md`, `03a-wave-seed.md`, `05a-dead-code-candidates.md`.
Machine files: `graph.json`, `waves.json`, `risks.json`, `dead-code.json`.
