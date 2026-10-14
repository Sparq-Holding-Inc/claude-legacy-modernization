# 06 Test strategy

Anchor: "the nightly batch cycle". The tree maps it to `job:MAINJOB` only by inference, since MAINJOB is the sole job (`app/jcl/MAINJOB.jcl:1`).

## Oracle

The tree holds no datasets, DDs or tables (`analysis` field `data_hubs` is empty, `app/jcl/MAINJOB.jcl:2` has no DD cards). So there is no file to diff. The oracle has to come from job output, logs and reports. Ask the client for these, in this order:

| Rank | Oracle | What to ask for | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run | Can the old MAINJOB run beside the new one on the same input for several nights? | not known | inference |
| 2 | Captured replay | The SYSIN or PARM values PGMMAIN received, over a period that holds month-end and, if financial, year-end | not known | `app/cbl/PGMMAIN.cbl:8` |
| 3 | Golden master | Archived job logs, SYSOUT, return codes and any GDG generations the job wrote, with dates | not known | inference |
| 4 | Characterization tests | Generated from source. Provisional only. | low | `app/cbl/PGMMAIN.cbl:9` |

Until the client answers, the oracle for wave 1 is rank 4, and coverage is provisional. Characterization encodes what the code says, not what it does. PGMMAIN says only "call whatever name arrives", so a characterization test says nothing about the outcome.

## What the harness asserts

1. For each name that arrives in `WS-PGM-NAME`, the new job calls the equivalent unit and the old and new job end with the same return code.
2. A name that matches no program: the old behavior is a run-time call failure. Capture what the old job did (abend code, message) and reproduce it, or record a deviation. The tree does not say what happens (inference).
3. HIDDEN01 as a target: output and return code are empty and zero (`app/cbl/HIDDEN01.cbl:4`).
4. Blank input to the ACCEPT. Same treatment as case 2.

## Normalization spec (for human sign-off)

| Item | Treatment | Evidence |
|---|---|---|
| Timestamps, job numbers, page headers in SYSOUT | Masked | inference |
| Packed decimal and collating sequence | None found in this tree. Put them in the spec when the called programs are known. | `app/cbl/PGMMAIN.cbl:5` |
| Record order | Not applicable. No output files in the tree. | `analysis` field `data_hubs` |

## Cases to add deliberately

- Boundary dates: month-end, year-end, leap day. PGMMAIN has no date logic (`app/cbl/PGMMAIN.cbl:6`), but the programs it calls might. Ask which names arrive at fiscal close, since a call that happens once a year is the common cutover failure.
- A zero-record night and an oversized night, for the called programs.

## Deviation Register

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| none yet | | | | | | inference |

## Exit bar for wave 1

Replay diff clean under the signed normalization spec, every case above passing, the harness in version control and CI, and the register signed. Keep the harness after cutover as the regression suite.

## Rollback

Run the old MAINJOB from the old load library. The harness's parallel run keeps the old job live until the exit bar is met (inference).
