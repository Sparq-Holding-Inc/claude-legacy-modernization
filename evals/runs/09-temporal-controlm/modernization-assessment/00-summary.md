# 00 Summary

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | flag `--target refactor` |
| What must not break | "the nightly batch cycle" | flag `--must-not-break` |
| Runtime telemetry | none, so every dead-code claim is provisional | flag `--telemetry none` |

All three arrived as flags. No non-interactive defaults were applied. Scope was the current directory.

## Result

- **Waves: 1.** The system is one Control-M folder and two JCL jobs. Cutting between them would put a scheduler condition across a wave boundary. See `03-waves.md`.
- **Size of the tree.** 2 JCL jobs, 2 scheduler jobs, 0 programs, 0 copybooks, 0 datasets. Both jobs have one step that runs IEFBR14, a utility that does nothing (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`).
- **Estimate.** 5 to 12 person-days for the wave as seen. `inference`. See `04-estimate.md` for the three assumptions it rests on.
- **Dead code.** None found, and provisional. Dormancy could not be tested because no file has a last-modified date. See `05-dead-code.md`.

## Largest risk

The nightly order is held by scheduler conditions, not by any code. JOBB waits for JOBA-DONE and then deletes it (`app/scheduler/nightly.xml:9`, `app/scheduler/nightly.xml:10`). JOBA waits for EXTERNAL-FEED, which nothing in the tree produces (`app/scheduler/nightly.xml:5`). A refactor that renames a condition, splits or merges a job, adds a second reader of JOBA-DONE, or moves a folder can break the order without any job abending. The failure is silent, and the cycle is the thing that must not break. The extractor draws one edge for this and does not show the delete or the external gate, so the graph understates it.

## Open Questions

For the client's engineers.

1. What posts EXTERNAL-FEED (`app/scheduler/nightly.xml:5`), and when does it arrive against the order date rollover?
2. Which jobs wait on JOBB-DONE (`app/scheduler/nightly.xml:11`)? The chain seems to continue elsewhere, and any waiting job joins wave 1.
3. Why does JOBB delete JOBA-DONE (`app/scheduler/nightly.xml:10`)? Is it rerun protection, and does anything else read that condition?
4. What do JOBA and JOBB really do? Each runs only IEFBR14 with no DD (`app/jcl/JOBA.jcl:2`, `app/jcl/JOBB.jcl:2`). If they are stand-ins, please supply the real members and this assessment must be redone.
5. When does the cycle run, and what do operators do by hand? The XML has no time, calendar or cycle setting, only the folder name (`app/scheduler/nightly.xml:3`).
6. Does the scheduler stay Control-M under this refactor? If not, the condition semantics must be rebuilt (`04-estimate.md`).
7. Can you supply twelve months of job run history and condition logs? Without them the oracle is weak and dead code stays provisional.
8. Is a parallel run of the refactored definitions possible? It is the strongest oracle available (`06-test-strategy.md`).

### Not parsed

Nothing. The extractor listed no unparsed files (`modernization-assessment/graph.json:214`).

### Extractor limits that touch this system

- Conditions are matched on name alone, and a delete (`SIGN="-"`) makes no edge, so the delete at `app/scheduler/nightly.xml:10` is not in `graph.json`. This limit is stated in the extractor's own source and is not in `meta.limits`.
- An input condition with no producer, like EXTERNAL-FEED, gets no edge and no warning (`modernization-assessment/graph.json:253`).
- IF/THEN/ELSE and COND= in JCL are not modeled (`modernization-assessment/graph.json:15`). The two jobs have none.
- Only Control-M XML and shell wrappers that name JCL files are read as schedulers (`modernization-assessment/graph.json:18`). Any other scheduler would be invisible.
- Nested PROC calls and jobs submitted through the internal reader are not followed (`modernization-assessment/graph.json:16`).
- Git dates were off, so every last-modified date is unknown (`modernization-assessment/graph.json:7`).
