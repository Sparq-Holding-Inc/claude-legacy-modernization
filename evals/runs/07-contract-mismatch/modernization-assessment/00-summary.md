# 00 Summary

Scope: the current directory (`.`). The tree holds 2 COBOL programs, 2 copybooks and 2 JCL jobs, and no scheduler.
Evidence: `app/cbl/PGMR.cbl:1`, `app/cbl/PGMW.cbl:1`, `app/cpy/LAYOUTX.cpy:1`, `app/cpy/LAYOUTY.cpy:1`,
`app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`.

## Scoping answers

| Question | Answer | Source | Evidence |
|---|---|---|---|
| Target state | refactor | given as `--target refactor` | `modernization-assessment/waves.json:2` |
| What must not break | "the nightly batch cycle" | given as `--must-not-break` | inference: no unit in the tree maps to it (see Open Questions) |
| Runtime telemetry | none, so every dead-code claim is provisional | given as `--telemetry none` | `modernization-assessment/dead-code.json:2` |

All three answers came as flags, so **no defaults applied**.

## Result

- **Waves: 2.** Wave 1 is the reader side (PGMR, job:READJOB). Wave 2 is the writer side (PGMW, job:WRITEJOB).
  The plan is the extractor's seed with no deviations. Evidence: `modernization-assessment/waves.json:5`,
  `modernization-assessment/waves.json:16`.
- **Dead code:** none found in any bucket. The dormant bucket was not computed, because the tree has no
  last-modified dates. It is not measured, not empty. Evidence: analysis: `warnings` in
  `modernization-assessment/graph.json`.
- **Estimate:** 8 to 16 person-days for both waves, low confidence. Inference. Evidence: `04-estimate.md`.

## Single largest risk

The file `SPARQ.TEST.MASTER` is a contract between PGMW and PGMR that is defined twice and checked nowhere.
PGMW describes the record with LAYOUTX and PGMR with LAYOUTY, two separate copybooks with different field names.
The extractor scored the edge medium for that reason. Compared field by field they are byte compatible today:
a 10 byte key and a 5 byte packed decimal amount. Nothing enforces it, so a port that changes one side breaks the
file silently. Evidence: `app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:2`,
`app/cpy/LAYOUTY.cpy:3`, `app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`.

Two things make it worse, and both are inference because the extractor does not read them. WRITEJOB asks for
LRECL=80 for a 15 byte layout, and PGMW writes its record without moving anything into it. Evidence:
`app/jcl/WRITEJOB.jcl:4`, `app/cbl/PGMW.cbl:14`.

## Open Questions

For the client's engineers.

1. **Which unit is "the nightly batch cycle"?** The tree holds no scheduler, and no job or program is named for a
   cycle. The must-not-break item maps to no unit, and no mapping was invented. Which jobs make it up, and does it
   include READJOB and WRITEJOB? Evidence: analysis: `warnings` in `modernization-assessment/graph.json`.
2. **What order do the two jobs run in, and how often?** No scheduler artifact was parsed, and the order of the jobs
   across jobs is unknown. The shared file implies the writer runs first. Please send the scheduler export.
   Evidence: `app/jcl/WRITEJOB.jcl:3`, `app/jcl/READJOB.jcl:3`.
3. **What are the real RECFM and LRECL of the catalogued `SPARQ.TEST.MASTER`, and does READJOB end with a zero return
   code?** WRITEJOB says LRECL=80, the layout is 15 bytes, and neither COBOL file description states a record
   length. The extractor does not compare DCB with copybooks. Evidence: `app/jcl/WRITEJOB.jcl:4`,
   `app/cbl/PGMW.cbl:10`, `app/cbl/PGMR.cbl:10`.
4. **Do LR-KEY and LY-ID, and LR-AMT and LY-VALUE, mean the same thing, and who else reads or writes the file?**
   The bytes match, but the names do not, and any consumer outside this tree is invisible. Evidence:
   `app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTY.cpy:2`, `app/cpy/LAYOUTX.cpy:3`, `app/cpy/LAYOUTY.cpy:3`.
5. **What does PGMW mean to write?** It writes `LAYOUT-REC` with no MOVE or INITIALIZE, so the record content is
   undefined in the source. Is the output repeatable, and is anything downstream depending on its content?
   Evidence: `app/cbl/PGMW.cbl:14`.
6. **How does WRITEJOB run more than once?** It allocates the dataset as NEW under a fixed name, so a rerun would
   very likely fail unless something outside the tree deletes the dataset first. Is there such a step, or is this a
   one-off? Evidence: `app/jcl/WRITEJOB.jcl:3`.
7. **Is `SPARQ.TEST.MASTER` a test dataset or the production master?** The name contains `TEST`. It decides
   whether these two jobs are real cycle members or scaffolding. Evidence: `app/jcl/WRITEJOB.jcl:3`.
8. **Did READJOB and WRITEJOB run in the last 12 months?** There is no telemetry, no last-modified dates, and no
   scheduler, so dormancy was not measured and reachability is on paper only. Evidence: analysis: `warnings` in
   `modernization-assessment/graph.json`.
9. **Do you have archived copies of the file, or a way to run a shadow copy of WRITEJOB?** The wave 2 oracle depends
   on it. The name has no generation suffix, so archives may not exist. Inference. Evidence:
   `app/jcl/WRITEJOB.jcl:3`.

## Not parsed, and limits that touch this system

- **Not parsed:** nothing. The extractor listed no unparsed file. Evidence: analysis: `unparsed` in
  `modernization-assessment/graph.json`.
- **Limit: DCB, LRECL and RECFM are not read.** This touches WRITEJOB directly (question 3). Evidence:
  `meta.limits` in `modernization-assessment/graph.json`, `app/jcl/WRITEJOB.jcl:4`.
- **Limit: only Control-M XML and shell wrappers are read as schedulers.** None were present (question 2).
  Evidence: `meta.limits` in `modernization-assessment/graph.json`.
- **Limit: the contract edge is high only when both sides COPY the same layout.** It is medium here for that reason,
  and the layouts are in fact compatible. Evidence: `meta.limits` in `modernization-assessment/graph.json`,
  `app/cpy/LAYOUTX.cpy:1`.
- **Limit: no last-modified dates.** The dormant bucket was not computed. Evidence: analysis: `warnings` in
  `modernization-assessment/graph.json`.
- **Not touched:** computed calls, embedded JCL, IF/THEN/ELSE and COND, nested procs, COPY REPLACING and CICS chains.
  The tree has none of them. Evidence: analysis: `unresolved_dynamic` and `embedded_jcl` in
  `modernization-assessment/graph.json`.

## Files

`01-inventory.md`, `02-coupling.md`, `03-waves.md`, `04-estimate.md`, `05-dead-code.md`, `06-test-strategy.md`,
`graph.json`, `waves.json`, `risks.json`, `dead-code.json`. Generated tables: `02a-edge-tables.md`,
`03a-wave-seed.md`, `03a-waves-draft.json`, `05a-dead-code-candidates.md`.
