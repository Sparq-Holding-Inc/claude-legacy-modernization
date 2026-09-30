# 03 Waves

Target state: refactor. Two waves. The plan is the extractor's seed (`03a-wave-seed.md`) with no changes, so
`deviations` is empty. The machine-readable plan is `modernization-assessment/waves.json`, and the scores are in
`modernization-assessment/risks.json`.

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-readonly | PGMR, job:READJOB | medium | medium | `app/jcl/READJOB.jcl:1`, `app/cbl/PGMR.cbl:14` |
| 2 | batch-writers | PGMW, job:WRITEJOB | high | low | `app/cbl/PGMW.cbl:6`, `app/cbl/PGMW.cbl:14`, `app/jcl/WRITEJOB.jcl:4` |

## Wave 1. Reader side of the master file

Units: `PGMR`, `job:READJOB`.

- **Why it is a wave.** READJOB runs PGMR, which only reads `SPARQ.TEST.MASTER`. Nothing shared is written.
  Evidence: `app/jcl/READJOB.jcl:2`, `app/jcl/READJOB.jcl:3`, `app/cbl/PGMR.cbl:13`.
- **Risk quadrants.** PGMR is low-high (port 2, blast 3). READJOB is low-low (port 1, blast 2). Evidence:
  `modernization-assessment/risks.json:13`, `modernization-assessment/risks.json:63`.
- **The four wave tests.**
  - Deployable independently: yes, behind a flag. The legacy writer keeps producing the file. Inference.
  - Rollback independently: yes, by running the legacy job again. It is read-only. Evidence: `app/cbl/PGMR.cbl:13`.
  - Testable boundary: weak. PGMR uses no field it reads and prints nothing, so the only observable behavior is
    the return code. Evidence: `app/cbl/PGMR.cbl:14`. The boundary that can be tested is the input file
    (good, short and bad records).
  - Something a stakeholder can name: no. This wave is a toolchain proof and a chore in business terms.
- **Unblocks.** Wave 2. The ported reader gives the writer port a consumer that decodes the record. The wave
  should also produce one shared schema for the file, so wave 2 has something to test the writer against.
  Inference.
- **Confidence: medium.** The sequence follows from facts. The value is low, and the test boundary is thin.
  The extractor found no computed calls for this wave. Evidence: analysis: `computed_calls` for wave 1 in
  `modernization-assessment/graph.json`.

## Wave 2. Writer of the master file

Units: `PGMW`, `job:WRITEJOB`.

- **Why it is a wave.** WRITEJOB runs PGMW, which writes the file PGMR reads. Evidence:
  `app/jcl/WRITEJOB.jcl:2`, `app/jcl/WRITEJOB.jcl:3`, `app/cbl/PGMW.cbl:13`.
- **Why it comes second.** Two reasons. The seed orders write families after read families. And the reader is
  already ported by then, so the contract has a fixed, tested consumer. Evidence: analysis: `wave_seed` in
  `modernization-assessment/graph.json`.
- **Risk quadrants.** PGMW is high-high (port 3, blast 4). WRITEJOB is low-high (port 2, blast 4). Evidence:
  `modernization-assessment/risks.json:38`, `modernization-assessment/risks.json:84`. A high-high unit sits in the
  last wave, which is where the rules put it. A low-high unit can move early, but it runs a program that cannot,
  so it stays with it.
- **The four wave tests.**
  - Deployable independently: yes, once the reader has been ported. The new writer has to produce a file that the
    ported reader and the legacy reader both accept. Inference.
  - Rollback independently: yes, but note that WRITEJOB creates and catalogs the dataset with a fixed name.
    A rerun means deleting it first. Evidence: `app/jcl/WRITEJOB.jcl:3`. Inference on the rerun failure.
  - Testable boundary: yes, the output file, compared against a legacy output. The legacy output may not be
    repeatable because PGMW moves nothing into its record. Evidence: `app/cbl/PGMW.cbl:14`.
  - Something a stakeholder can name: not from this tree. The must-not-break item, the nightly batch cycle,
    maps to no unit here (see Open Questions in `00-summary.md`).
- **Unblocks.** Retiring the legacy writer, and merging the two copybooks into one schema. Inference.
- **Confidence: low.** The extractor scored the contract edge medium. The JCL sets LRECL=80 against a 15 byte
  layout. No scheduler was supplied. There is no oracle. Evidence: `app/jcl/WRITEJOB.jcl:4`,
  `modernization-assessment/graph.json` (edge PGMW to PGMR, `confidence`).
- **What sits behind a facade.** Nothing needs one. There is no god module, no cycle, and no unit that
  everything else depends on. Evidence: analysis: `god_modules` and `sccs` in `modernization-assessment/graph.json`.

## Deviations from the seed

None. The plan has no deviations and that is a fine answer for a system of this size.

- No unit was moved for a must-not-break item, because `the nightly batch cycle` cannot be tied to a unit.
  The tree holds no scheduler and no job or program named for a cycle. Evidence: analysis: `warnings` in
  `modernization-assessment/graph.json`.
- No wave has more than 25 units, so nothing needed cutting.
- Nothing the extractor could not see changes what a unit is: there are no computed calls, no embedded JCL,
  and no file listed as not parsed. Evidence: analysis: `unresolved_dynamic`, `embedded_jcl` in
  `modernization-assessment/graph.json`.
- No high-high unit was placed early. PGMW is in the last wave. Evidence:
  `modernization-assessment/risks.json:38`.

## The alternative that was considered

Moving all four units as one wave would also be defensible: there are only four units and the two sides share one
file. It was not chosen because the two sides can be deployed and rolled back on their own, the dataset is an
articulation point, and a one-wave plan would test the reader and the writer at the same time and lose the fixed
consumer. Inference. Evidence: analysis: `articulation_points` in `modernization-assessment/graph.json`.
