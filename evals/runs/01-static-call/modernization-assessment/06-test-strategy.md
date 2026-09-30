# 06 Test strategy

This follows the `behavioral-equivalence` skill. Target state: refactor. The anchor is "the nightly
batch cycle", the item you said must not break.

"Correct" for this system means: for the inputs the nightly batch cycle actually sees, the new
implementation produces the same job output and the same condition codes as the old one, and every
difference is written in the Deviation Register.

## The tree holds no datasets

The tree has no dataset, VSAM file, DB2 table or copybook (`analysis.data_hubs` is empty and
`meta.files_seen` in `graph.json` shows zero copybooks). So there is no file to use as a golden master. The oracle
has to come from job output, logs and reports. The two programs here read and write nothing. The
only observable behavior they have is one line of console output and a return code.

## Behavior of the code in the tree

| Behavior | What the source shows | Confidence | Evidence |
|---|---|---|---|
| PROGA prints the text `CALL FAILED IF WE GET HERE` on every run. The `DISPLAY` comes before the `CALL`, so it prints whether or not the call fails. | One unconditional `DISPLAY`. | high | `app/cbl/PROGA.cbl:5` |
| PROGA then calls PROGB and ignores the outcome. There is no `ON EXCEPTION` and no check of `RETURN-CODE`. | A bare literal `CALL`. | high | `app/cbl/PROGA.cbl:6` |
| PROGA ends the run. | `STOP RUN`. | high | `app/cbl/PROGA.cbl:7` |
| PROGB returns at once. | A single `GOBACK`. | high | `app/cbl/PROGB.cbl:4` |
| The step's condition code is the default of zero, because neither program moves a value to `RETURN-CODE`. | Read as the absence of any such statement. | medium | inference |
| The wording of the message suggests it was meant to run only if the call failed. | Author intent is not in the source. | low | inference |

The last two rows are inference. A test written from this table encodes what the code says, not
what the running system does. It is the weakest oracle, and its coverage is provisional.

## The oracle, per wave

There are no waves (`03-waves.md`). The oracle is chosen for the anchor instead. Take the strongest
one the client can supply.

| Order | Oracle | What to ask the client for | Confidence | Evidence |
|---|---|---|---|---|
| 1 | Parallel run. Run the legacy and the new nightly cycle on the same production input and diff the output. | Whether the old cycle can stay up beside the new one for at least one month-end. Teams often assume it cannot and are wrong. | not assessed | inference |
| 2 | Captured production replay. | The job inputs and outputs for the cycle, over a window that includes month-end, quarter-end and fiscal year-end. | not assessed | inference |
| 3 | Golden master from archived output. | Archived job logs (SYSOUT), reports and extracts from the cycle, and GDG generations if any dataset is produced. Plus the run history from SMF type 30 or the scheduler log. | not assessed | inference |
| 4 | Characterization tests from source, for PROGA and PROGB only. | Nothing. This is what the table above gives. Label the result provisional. | low | `app/cbl/PROGA.cbl:5-7` |

To be able to name the cycle as a unit, we also need its JCL, its PROCs and its scheduler
definitions. Without them "the nightly batch cycle" maps to no unit in the tree. I have not invented
a mapping.

## Normalization spec (draft, for a human to sign)

Each line is a claim that a difference does not matter. Keep the list short.

- Ignore: job number, job start and end times, page headers and dates printed by the system.
- Compare exactly: the text of every `DISPLAY` line, including `CALL FAILED IF WE GET HERE`
  (`app/cbl/PROGA.cbl:5`). Do not fix the wording in the port. A change goes in the Deviation Register.
- Compare exactly: the step condition code at the end of PROGA, and the condition code that any later
  step tests. The cycle may branch on it, and the tree cannot show whether it does.
- Order: keep the order of steps in the cycle. The graph has no `temporal` edge because it has no
  JCL (`analysis.edge_counts`), so the order is unknown and has to come from the client.

The mainframe traps in the skill (packed decimal, EBCDIC collating sequence, `REDEFINES`, record
padding) do not occur in these two files, which hold no data description (`app/cbl/PROGA.cbl:1-7`,
`app/cbl/PROGB.cbl:1-4`). They will matter once the rest of the cycle is supplied.

## Cases to cover

- **Boundary dates for the cycle:** month end, quarter end, fiscal year end, leap day. The programs use
  no date, but the cycle around them may run different steps on those days. This is inference.
- **Zero-record and maximum-size input:** not applicable to the two programs, since they read no input.
  Ask what the rest of the cycle reads.
- **Bad data already present:** none can be found in the tree.
- **Paths that run only at close:** there is one path through PROGA and one through PROGB, since neither
  has a branch. Whether the cycle runs PROGA only at close is unknown. Ask.
- **Failure of the call:** what the link-edit or run-time load does if PROGB is missing depends on the
  compile option (static or dynamic call), which is not in the tree. Ask for the compile listing.

## Deviation Register

Nothing is approved to differ yet. The register starts with one candidate.

| ID | Legacy behavior | New behavior | Why changed | Approved by | Downstream impact | Evidence |
|---|---|---|---|---|---|---|
| D-001 (candidate, not approved) | Prints `CALL FAILED IF WE GET HERE` on every run, before the call. | Same until the client decides. If changed, print only when the call fails. | Message text and position disagree. | not approved | Unknown. Any operator or log scanner that reacts to this text would change behavior. | `app/cbl/PROGA.cbl:5` |

## Exit bar for the wave that holds these programs

A wave is done when all of these hold. A port that compiles, or that passes tests written beside it,
does not meet the bar.

- The replay diff of job output and condition codes is clean, modulo the normalization spec and the
  Deviation Register.
- The boundary cases above pass.
- The harness is under version control and runs in CI.
- Someone with the authority to sign has signed the Deviation Register.

Keep the harness after cutover. It becomes the regression suite for the modernized cycle.
