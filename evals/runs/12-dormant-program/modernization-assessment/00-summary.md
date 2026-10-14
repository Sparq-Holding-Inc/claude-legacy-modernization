# Modernization assessment summary

## Scoping answers

| Item | Answer |
|---|---|
| Target state | refactor (given as a flag) |
| Must not break | "the nightly batch cycle" (given as a flag). It maps to `job:MAINJOB` by inference only (app/jcl/MAINJOB.jcl:1). |
| Telemetry | none (given as a flag). Every dead-code claim is provisional. |
| Delivery | not given. The estimate shows conventional and AI-assisted side by side. |
| Defaults applied | no defaults applied |

## Result

- **Scope:** 4 units. One JCL job, one batch program and two subprograms, 16 lines in all (analysis.node_counts).
- **Waves:** 1. See `03-waves.md` and `waves.json`. No deviations from the extractor's seed.
- **Estimate:** conventional 3 to 6 engineer-weeks, AI-assisted 3 to 5 engineer-weeks. Confidence is low (04-estimate.md).
- **Dead code:** nothing unreachable, nothing unknown. `OLDPGM` is dormant by date (last modified 2011-03-04) but
  `PGMMAIN` calls it unconditionally, so it probably runs. Instrument it, do not delete it
  (app/cbl/PGMMAIN.cbl:4).

## Largest risk

The tree may not be the system. All three program bodies are empty apart from GOBACK and two CALLs
(app/cbl/PGMMAIN.cbl:4, app/cbl/PGMMAIN.cbl:5), and no scheduler, dataset or copybook was supplied. The nightly
batch cycle may be much larger than `MAINJOB` (inference). Every wave and estimate here is only as complete as
the tree. The behavior that must not break cannot be shown to be inside it.

## Open Questions for the client's engineers

1. Is this tree the complete nightly batch cycle, or a fragment? Which scheduler runs `MAINJOB`, and in what
   order relative to other jobs? None was parsed (analysis.warnings). Please supply the scheduler export.
2. What does `MAINJOB` read and write? The JCL names no DD (app/jcl/MAINJOB.jcl:2). If it touches files or DB2,
   those are missing from the tree.
3. `PGMMAIN`, `OLDPGM` and `NEWPGM` hold no logic (app/cbl/PGMMAIN.cbl:6, app/cbl/OLDPGM.cbl:4,
   app/cbl/NEWPGM.cbl:4). Are these stubs, or is the real source kept elsewhere?
4. Does `OLDPGM` do anything at run time, and can anyone confirm it ran in the last 12 months? It has not changed
   since 2011-03-04 (app/cbl/OLDPGM.cbl:2). Both git commits have the message `x`, so the dates may not mean what
   they appear to (inference).
5. What output proves the nightly cycle ran correctly (reports, extracts, return codes), and is a parallel run of
   the old and new job possible? See 06-test-strategy.md.
6. Limits that touch this system: IF/THEN/ELSE and COND= in JCL are not modeled, and free-format COBOL would be
   listed as not parsed (meta.limits). Nothing was listed as not parsed here, but is any of the source in
   free format or in another language?

## Files

`01-inventory.md`, `02-coupling.md`, `02a-edge-tables.md`, `03-waves.md`, `03a-wave-seed.md`, `04-estimate.md`,
`05-dead-code.md`, `05a-dead-code-candidates.md`, `06-test-strategy.md`, `graph.json`, `waves.json`,
`risks.json`, `dead-code.json`.
