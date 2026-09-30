# 06 Test strategy

This follows the `behavioral-equivalence` skill. "Correct" here means: for the names `PROGA` actually
receives in production, the ported dispatcher starts the same program and produces the same
outputs as the legacy one. Where it differs, someone chose that and wrote it down.

The tree has no waves, so the oracle is chosen per unit for now. Every choice below is provisional.

## The tree holds no datasets

The extractor found no dataset, VSAM file or DB2 table (analysis `data_hubs` is empty, and
`edge_counts` has one call edge and nothing else). So there is no file in the tree that can act
as a golden master. The oracle has to come from job output, logs and reports. The tree also holds no
JCL, so the job that runs the programs is not in it either.

## Pick the oracle

| Unit | Oracle, strongest available | Why | Fallback | Confidence | Evidence |
|---|---|---|---|---|---|
| `PROGA` | Captured production traffic replay: the names supplied to `ACCEPT`, and the return code and output of what each starts, over a window that includes month-end and fiscal year-end. | The input is one short field, so capture is cheap. The result depends on what the named program does, so the capture must include that program's outputs. | Parallel run of the old and new dispatcher on the same names, if the old job can stay up. Ask for it before settling for anything weaker. | low | `app/cbl/PROGA.cbl:8`, `app/cbl/PROGA.cbl:9` |
| `PROGB` | Characterization test from source: the program returns to its caller and does nothing else. | There is no data. This is the weakest oracle, and it is enough only because the program has no behavior to encode. Label the coverage provisional. | Confirm against a job log that shows a caller receiving control back with a normal return code. | medium | `app/cbl/PROGB.cbl:4` |
| The nightly batch cycle (the must-not-break item) | Parallel run, or replay of archived outputs from the cycle. | It maps to no unit in this tree. I have not tied it to `PROGA` or `PROGB`. | Report archives, GDG generations and extract files sent to partners. | low | inference |

## What to ask the client to supply

The oracle for this system does not exist in the tree. Ask for:

1. Job logs and SMF records for the runs that start `PROGA`, for at least 12 months. They show
   which program names were started, return codes and run times. They are also the telemetry the
   dead-code register needs.
2. The SYSIN or PARM values given to `PROGA`, and the JCL that supplies them.
3. Archived outputs of the nightly batch cycle: reports, extracts, and GDG generations of every
   file it writes. Each generation is a golden master with a date on it.
4. Extracts sent to partners from the cycle. What left the building is already a specification.
5. The load library or source list that says which program names the `ACCEPT` can match.

## Normalize before you diff

Write this spec down and have a person sign it. Each line is a place a real defect can hide.

- Run timestamps, job ids and page numbers in the output of programs `PROGA` starts. Normalize.
- Trailing spaces in the name. `WS-PGM-NAME` is `PIC X(8)` (`app/cbl/PROGA.cbl:5`), so a shorter name
  is padded with spaces and a longer input is cut to 8 characters. Decide whether the port trims,
  and test both. This is inference from the picture clause.
- Case of the name. The source does not fold case. The port must not change it silently. Inference.
- Any packed decimal or money the started programs produce. Compare in a decimal type with zero
  tolerance. `PROGA` and `PROGB` hold no arithmetic, so this applies to programs outside the tree.
- Record order and collating sequence in any output file the started programs write. EBCDIC order is
  not ASCII order. Confirm whether order was incidental before dropping it.
- Return code and abend behavior. `PROGA` ends with `STOP RUN` (`app/cbl/PROGA.cbl:10`), which ends the
  whole run unit, and `PROGB` ends with `GOBACK` (`app/cbl/PROGB.cbl:4`), which returns to its
  caller. The port must keep that difference, including which return code the job sees.

## Cover the input space deliberately

| Case | What to check | Confidence | Evidence |
|---|---|---|---|
| A name that matches a program | `PROGA` starts it, and control comes back to `STOP RUN`. | medium | `app/cbl/PROGA.cbl:9`, `app/cbl/PROGA.cbl:10` |
| A name that matches no program | The call has no `ON EXCEPTION` phrase. Capture what the legacy runtime does (abend, return code, message). The port must reproduce it or record it in the deviation register. | low | inference: `app/cbl/PROGA.cbl:9` |
| Empty input, blank name | Same as above, and a common source of an unplanned abend. | low | inference: `app/cbl/PROGA.cbl:8` |
| A name of exactly 8 characters and a name longer than 8 | Truncation to the `PIC X(8)` field. | low | inference: `app/cbl/PROGA.cbl:5` |
| `PROGA` names itself | A self call. Not modeled by the extractor. Confirm whether it recurses or is refused. | low | inference: `app/cbl/PROGA.cbl:9` |
| A name that appears only at month-end or fiscal year-end | The capture window must include it. This is the case most likely to be missed and found six months after cutover. | low | inference |
| Bad data already in the input source | Whatever malformed values the legacy job already receives must be reproduced, not fixed. | low | inference |

## Order

The graph has no temporal edge, because no JCL or scheduler is in the tree. So this harness has no list
of job orders to keep yet. When the nightly cycle's JCL and scheduler arrive, every temporal edge in
`graph.json` becomes an ordering the harness must keep.

## Deviation register

Nothing is allowed to differ without a row. It starts empty.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | | | | | | inference: no deviation is proposed |

## Exit bar for the first wave, once one exists

- Replay diff is clean, modulo the normalization spec and the deviation register.
- Every targeted case above passes, including the unknown-name case.
- The harness is under version control and runs in CI.
- A person with authority signs the deviation register.

Keep the harness after cutover. It is the only executable specification this system will have.
