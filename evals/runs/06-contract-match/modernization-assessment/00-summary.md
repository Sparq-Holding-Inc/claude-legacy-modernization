# 00 Summary

Assessment of the tree at `.`: two COBOL programs, one copybook and two JCL jobs. No scheduler, no
CICS definitions, no data files. Extractor output: 8 nodes and 9 edges, none unresolved
(`modernization-assessment/graph.json`).

## Scoping answers

| Question | Answer | Source |
|---|---|---|
| Target state | refactor | given as `--target refactor` |
| What must not break | "the nightly batch cycle" | given as `--must-not-break` |
| Runtime telemetry | none | given as `--telemetry none` |

All three came as flags. No defaults applied.

The must-not-break item maps to no unit in the tree. No scheduler artifact was parsed, and neither JCL
job says it is nightly (`app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`). No mapping was invented.
See Open Questions.

Telemetry is none, so every dead-code claim is provisional. The dormant bucket was not computed, because
no last-modified dates exist (analysis, field `warnings`).

## Wave count

Two waves, no deviations from the extractor's seed.

| Wave | Units | Confidence | Evidence |
|---|---|---|---|
| 1. Reader job | PGMR, job:READJOB | low | `app/jcl/READJOB.jcl:1` |
| 2. Writer job | PGMW, job:WRITEJOB | medium | `app/cbl/PGMW.cbl:6` |

Wave 1 is a chore wave. PGMR produces no output, so it has almost nothing to test and nothing a
stakeholder can name (`app/cbl/PGMR.cbl:14`). Details: `modernization-assessment/03-waves.md`.

## Largest risk

The contract on SPARQ.TEST.MASTER. PGMW writes it and PGMR reads it, and both COPY the same layout
(`app/cbl/PGMW.cbl:11`, `app/cbl/PGMR.cbl:11`). The extractor rates the edge `high`, which means a shared
copybook and not proven equal bytes. Three things stay unproven:

- the copybook describes a 15 byte record by hand (`app/cpy/LAYOUTX.cpy:2`, `app/cpy/LAYOUTX.cpy:3`),
  while the writer's DD says `LRECL=80` (`app/jcl/WRITEJOB.jcl:4`), and the extractor does not compare
  the two;
- PGMW writes a record it never fills, packed decimal field included (`app/cbl/PGMW.cbl:14`);
- the layout is shared with no documentation, so a silent break would not be seen by PGMR, which
  discards the record (`app/cbl/PGMR.cbl:14`).

The first two are inference. Together they mean the true bytes on disk, which the port must reproduce,
are not known from the source.

## Open Questions

For the client's engineers.

1. **Which jobs are "the nightly batch cycle", and what runs them?** No scheduler was parsed. Please
   send the scheduler export. Without it the order and dates of both jobs are unknown, and the
   must-not-break item cannot be mapped to a unit.
2. **What deletes SPARQ.TEST.MASTER before WRITEJOB runs each night?** WRITEJOB allocates it `NEW`
   (`app/jcl/WRITEJOB.jcl:3`), which fails if it already exists. Is a cleanup step missing from this tree?
3. **What is the record length on disk?** The DD says LRECL=80 (`app/jcl/WRITEJOB.jcl:4`) and the copybook
   gives 15 bytes (`app/cpy/LAYOUTX.cpy:2`). Please send a LISTCAT and a hex dump of one record.
4. **Is PGMW the real program?** It writes `LAYOUT-REC` with no value moved in (`app/cbl/PGMW.cbl:14`).
   Is that intended, and what bytes actually reach the file? A strict decoder can reject an unfilled
   packed field.
5. **Is SPARQ.TEST.MASTER a production dataset or a test fixture?** The name carries the qualifier TEST
   (`app/jcl/WRITEJOB.jcl:3`). If it is a fixture, the real nightly cycle is not in this tree.
6. **Who else reads this dataset?** PGMR is the only reader here and it discards the record
   (`app/cbl/PGMR.cbl:14`). Are there other jobs, extracts or transfers to partners that read the file?
7. **Do both jobs still run?** No telemetry exists and the dormant rule did not run. Please send job
   history or SMF records for `READJOB` and `WRITEJOB` for the last 12 months, and last-change dates from
   your source library. An empty dead-code list here means not measured.
8. **Is a test region available for a parallel run?** It is the strongest oracle available, and PGMW
   needs no input (`app/cbl/PGMW.cbl:13`).

### Not parsed and extractor limits that touch this system

- Not parsed: nothing was listed as not parsed (`analysis`, field `unparsed` is empty).
- Limit: DCB, LRECL and RECFM are not read, so the DD's record length is not compared with the copybook
  (`app/jcl/WRITEJOB.jcl:4`). This is Question 3.
- Limit: a `high` contract edge means both sides COPY the same layout, not proven equal (`meta.limits`).
  This is the largest risk above.
- Limit: only Control-M XML and shell wrappers that name JCL files are read as schedulers. Any other
  scheduler format would be missed. This is Question 1.

## Where everything is

| File | Content |
|---|---|
| `modernization-assessment/01-inventory.md` | Generated inventory |
| `modernization-assessment/02-coupling.md` | Coupling argument, cluster graph |
| `modernization-assessment/03-waves.md` | Wave plan and validity tests |
| `modernization-assessment/04-estimate.md` | Ranges and sensitivities |
| `modernization-assessment/05-dead-code.md` | Three buckets, all empty, provisional |
| `modernization-assessment/06-test-strategy.md` | Oracle, normalization, deviation register |
| `modernization-assessment/risks.json` | Two-axis scores per unit |
