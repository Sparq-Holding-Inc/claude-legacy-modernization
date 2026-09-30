# 03 Waves

Target state: refactor. The plan starts from the extractor's seed in `modernization-assessment/03a-wave-seed.md`.
It has two waves and no deviations from the seed. Machine-readable form: `modernization-assessment/waves.json`.
Per-unit scores are in `modernization-assessment/risks.json`.

## The plan

| Wave | Family | Units | Blast radius | Confidence | Evidence |
|---|---|---|---|---|---|
| 1 | batch-readonly | PGMR, job:READJOB | low | low | `app/jcl/READJOB.jcl:1` |
| 2 | batch-writers | PGMW, job:WRITEJOB | medium | medium | `app/cbl/PGMW.cbl:6` |

### Wave 1. Reader job: consume the master file

- **Why it is first.** READJOB runs PGMR (`app/jcl/READJOB.jcl:2`). PGMR opens the dataset for input,
  reads one record and closes (`app/cbl/PGMR.cbl:13`, `app/cbl/PGMR.cbl:14`, `app/cbl/PGMR.cbl:15`). It
  writes nothing another job uses. Both units score low-low in `modernization-assessment/risks.json`.
- **What it unblocks.** Nothing a business stakeholder can name. It proves the toolchain and gives the
  team a target-side decoder for `LAYOUTX` that wave 2 reuses. It is a chore wave, and this plan says so
  instead of dressing it up.
- **Validity tests.**
  - Independent deploy: yes. READJOB is a self-contained job (`app/jcl/READJOB.jcl:1`).
  - Independent rollback: yes. Point the step back at the legacy PGMR (`app/jcl/READJOB.jcl:2`).
  - Testable boundary: weak. PGMR has no DISPLAY and no WRITE, so the only observable behavior is the
    return code and the file status (`app/cbl/PGMR.cbl:13`, `app/cbl/PGMR.cbl:14`).
  - Stakeholder-visible deliverable: none.
- **Confidence: low.** Two of the four tests are weak or missing. The family placement is sound. The
  wave itself is thin.

### Wave 2. Writer job: produce the master file

- **Why it is second.** WRITEJOB creates the dataset the reader consumes (`app/jcl/WRITEJOB.jcl:3`).
  PGMW is the only writer (`analysis`, field `data_hubs`). It scores low-high. The port is easy. Proving
  it is the work.
- **What it unblocks.** Retiring the legacy writer, the last program on the SPARQ.TEST.MASTER contract.
  After it the layout is owned by the new code and can be written down.
- **Validity tests.**
  - Independent deploy: yes, behind a switch in the JCL step (`app/jcl/WRITEJOB.jcl:2`).
  - Independent rollback: yes, but the rollback must delete the new output first. The allocation is
    `NEW,CATLG,DELETE`, so a rerun against an existing dataset fails (`app/jcl/WRITEJOB.jcl:3`).
    Inference.
  - Testable boundary: yes. The output file is compared with a golden master
    (`app/cbl/PGMW.cbl:13`, `app/cbl/PGMW.cbl:14`).
  - Stakeholder-visible deliverable: the file the reader consumes, which is a named business dataset
    only if the client confirms it is one. See Open Questions.
- **Confidence: medium.** No scheduler was parsed, the DD says LRECL=80 against a 15 byte layout
  (`app/jcl/WRITEJOB.jcl:4`, inference), and PGMW writes a record it never fills (`app/cbl/PGMW.cbl:14`).

### Why reader first

Wave 1 moves the reader while the legacy writer still produces the file. The new reader must accept the
legacy bytes as they are. The layout stays fixed until wave 2 replaces the writer. The other order works
too, with the new writer producing bytes for the legacy reader. The seed's fixed family order picks the
reader first, and nothing in this tree gives a reason to change it (no SCC, no god module, no computed
call, no must-not-break unit that maps to the tree). Inference.

## Deviations from the seed

None. Every unit stays in the wave the seed gave it. `modernization-assessment/waves.json` has an empty
`deviations` list and an empty `unassigned` list.

## Not placed

Every unit is placed.

## The must-not-break item

"The nightly batch cycle" maps to no unit in this tree. No scheduler artifact was parsed, and neither
JCL job says when it runs (`app/jcl/READJOB.jcl:1`, `app/jcl/WRITEJOB.jcl:1`). This plan does not assume
that these two jobs are the cycle. If the client confirms they are, both waves sit on that path and the
blast radius of wave 1 rises. Inference. It is an Open Question in `modernization-assessment/00-summary.md`.
