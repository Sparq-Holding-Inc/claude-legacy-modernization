# 04 Estimate

Method: effort is estimated per wave, from the coupling edges crossing the wave boundary, not from lines of
code. There is one placeholder wave. Every figure below is inference. There is no oracle, no telemetry, and
no history of this team's port velocity to calibrate against.

## Wave 1: PROGA and PROGB

| Piece of work | Range | Confidence | Evidence |
|---|---|---|---|
| Port the two programs to the refactor target | 0.5 to 1 person-day | medium | `app/cbl/PROGA.cbl:5`, `app/cbl/PROGB.cbl:4` |
| Find the run environment: the job, the schedule, the load library | 1 to 5 person-days | low | inference |
| Build the equivalence harness and locate an oracle | 2 to 8 person-days | low | inference |
| Total for wave 1 | 3.5 to 14 person-days | low | inference |

The port itself is the small part. The eleven lines of source hold one DISPLAY, one CALL, one STOP RUN and
one GOBACK. The range is wide because the surrounding job stream is not in the tree.

## What the range is most sensitive to

1. Assumes the two programs are run by one JCL step that reads and writes no dataset. If the job step passes a
   PARM, a DD or a return-code condition that a later step tests, the harness work roughly doubles, because
   the boundary is then that condition. This tree cannot confirm it.
2. Assumes nobody outside this tree calls PROGB. If a second caller exists, PROGB is a shared subprogram and
   moves earlier than PROGA, and wave 1 splits in two.
3. Assumes the client can supply job logs for a full business cycle. If not, the oracle is characterization
   tests from source alone, and the wave 1 range moves to the top of its band and the confidence stays low.

## What the range does not cover

The nightly batch cycle. It is the must-not-break item and it is not in the tree. An estimate for
the migration of the cycle itself needs the JCL, the scheduler definitions and the datasets, and cannot be given from
these two files.

## Where Claude Code helps

Strong: transliterating these two programs, and writing the harness that runs the legacy and the new one and
compares the job output and return code. Weak: anything about why PROGA prints a failure message before it
calls. That is intent in undocumented behavior, and a person who owns the batch cycle has to say what
downstream reads it. Inference.
